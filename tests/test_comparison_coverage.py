"""Behavioral coverage for comparison service edge cases and branch boundaries."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from yt_transcript.comparison_service import ComparisonService


def analysis(**changes):
    values = {
        "id": 1,
        "created_at": datetime(2026, 9, 25, 12),
        "analysis_mode": "style",
        "video_id": None,
        "video_url": None,
        "text_length": 100,
        "summary_text": None,
        "total_words": 1000,
        "unique_words": 500,
        "sentences": 50,
        "vocabulary_richness": 50.0,
        "complexity_score": 0.5,
        "reading_time_minutes": 5.0,
        "sentiment_polarity": 0.0,
        "sentiment_subjectivity": 0.5,
        "sentiment_label": "neutral",
        "emotions_detected": None,
        "word_frequency": None,
        "concepts_detected": None,
        "flesch_reading_ease": 70.0,
        "flesch_kincaid_grade": 8.0,
    }
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, "Très facile"),
        (85, "Facile"),
        (75, "Assez facile"),
        (65, "Standard"),
        (55, "Assez difficile"),
        (35, "Difficile"),
        (20, "Très difficile"),
    ],
)
def test_readability_level_boundaries(score, expected):
    assert ComparisonService()._get_readability_level(score) == expected


def test_similarity_with_no_available_factors_is_zero():
    first = analysis(
        vocabulary_richness=None,
        complexity_score=None,
        sentiment_polarity=None,
        total_words=None,
    )
    second = analysis(
        id=2,
        vocabulary_richness=None,
        complexity_score=None,
        sentiment_polarity=None,
        total_words=None,
    )
    assert ComparisonService()._calculate_content_similarity(first, second) == 0


def test_similarity_uses_all_available_factors():
    first = analysis(
        vocabulary_richness=80,
        complexity_score=0.8,
        sentiment_polarity=0.8,
        total_words=1000,
    )
    second = analysis(
        id=2,
        vocabulary_richness=60,
        complexity_score=0.4,
        sentiment_polarity=-0.2,
        total_words=500,
    )
    score = ComparisonService()._calculate_content_similarity(first, second)
    assert 0 < score < 1


def test_overview_truncates_long_summary_and_handles_missing_date():
    rows = [
        analysis(summary_text="x" * 150),
        analysis(id=2, created_at=None, summary_text=None),
    ]
    result = ComparisonService()._get_analyses_overview(rows)
    assert result[0]["summary_preview"] == "x" * 100 + "..."
    assert result[1]["created_at"] is None
    assert result[1]["summary_preview"] == ""


def test_sentiment_comparison_handles_missing_values_and_unknown_label():
    rows = [
        analysis(
            sentiment_polarity=None,
            sentiment_subjectivity=None,
            sentiment_label="other",
        ),
        analysis(
            id=2,
            sentiment_polarity=None,
            sentiment_subjectivity=None,
            sentiment_label=None,
        ),
    ]
    result = ComparisonService()._compare_sentiment(rows)
    assert result["statistics"] == {}
    assert result["sentiment_spread"] == 0
    assert result["distribution"] == {"positive": 0, "negative": 0, "neutral": 0}


def test_readability_comparison_handles_missing_metrics():
    rows = [
        analysis(flesch_reading_ease=None, flesch_kincaid_grade=None),
        analysis(id=2, flesch_reading_ease=0.0, flesch_kincaid_grade=None),
    ]
    result = ComparisonService()._compare_readability(rows)
    assert result["statistics"]["flesch_ease"]["min"] == 0.0
    assert result["statistics"]["flesch_kincaid"] == {"min": 0, "max": 0, "avg": 0}
    assert result["flesch_ease_data"][0]["level"] == "Non défini"
    assert result["flesch_ease_data"][1]["level"] == "Non défini"


def test_differential_insights_cover_large_differences_and_mixed_modes():
    rows = [
        analysis(
            total_words=100,
            complexity_score=0.1,
            sentiment_polarity=-0.8,
            analysis_mode="style",
        ),
        analysis(
            id=2,
            total_words=2200,
            complexity_score=0.8,
            sentiment_polarity=0.7,
            analysis_mode="concepts",
        ),
        analysis(
            id=3,
            total_words=500,
            complexity_score=0.4,
            sentiment_polarity=0.0,
            analysis_mode="style",
        ),
    ]
    result = ComparisonService()._generate_differential_insights(rows)
    difference_types = {item["type"] for item in result["key_differences"]}
    assert difference_types == {"content_length", "complexity", "sentiment"}
    assert result["patterns"] == ["Modes d'analyse variés utilisés"]
    assert len(result["recommendations"]) == 2


def test_differential_insights_same_mode_without_large_differences():
    rows = [
        analysis(total_words=100, complexity_score=0.2, sentiment_polarity=0.1),
        analysis(id=2, total_words=200, complexity_score=0.3, sentiment_polarity=0.2),
    ]
    result = ComparisonService()._generate_differential_insights(rows)
    assert result["key_differences"] == []
    assert result["patterns"] == ["Toutes les analyses utilisent le même mode d'analyse"]
    assert result["recommendations"] == []


def test_compare_analyses_backend_exception_is_reported(monkeypatch):
    def fail(_analysis_id):
        raise RuntimeError("simulated lookup failure")

    monkeypatch.setattr("yt_transcript.comparison_service.get_analysis_by_id", fail)
    result = ComparisonService().compare_analyses([1, 2])
    assert "error" in result
    assert "simulated lookup failure" in result["error"]


def test_compare_content_single_analysis_skips_pairwise_similarity():
    row = analysis(word_frequency={"robot": 2}, concepts_detected=["technology"])
    result = ComparisonService()._compare_content([row])
    assert result["mode_distribution"] == {"style": 1}
    assert result["content_similarity"] == []


def test_readability_comparison_without_ease_scores_has_no_statistics():
    rows = [
        analysis(flesch_reading_ease=None, flesch_kincaid_grade=8.0),
        analysis(id=2, flesch_reading_ease=None, flesch_kincaid_grade=None),
    ]
    result = ComparisonService()._compare_readability(rows)
    assert result["statistics"] == {}


def test_similarity_failure_returns_zero():
    class Broken:
        @property
        def vocabulary_richness(self):
            raise RuntimeError("simulated similarity failure")

    assert ComparisonService()._calculate_content_similarity(Broken(), Broken()) == 0.0


def test_differential_insights_empty_input_covers_empty_metric_paths():
    result = ComparisonService()._generate_differential_insights([])
    assert result["key_differences"] == []
    assert result["patterns"] == ["Modes d'analyse variés utilisés"]
    assert result["recommendations"] == []


def test_differential_insights_handles_internal_failure():
    class Broken:
        @property
        def total_words(self):
            raise RuntimeError("simulated insight failure")

    result = ComparisonService()._generate_differential_insights([Broken()])
    assert result == {"key_differences": [], "patterns": [], "recommendations": []}
