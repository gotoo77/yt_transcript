import csv
import json
from io import StringIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from yt_transcript.comparison_service import ComparisonService
from yt_transcript.dashboard_service import DashboardService
from yt_transcript.database import get_analysis_by_id, save_analysis, search_analyses
from yt_transcript.export_service import ExportService
from yt_transcript.sentiment_analyzer import (
    analyze_sentiment,
    calculate_readability_metrics,
    detect_emotions,
    estimate_syllables,
)
from yt_transcript.tags_service import TagsService


@pytest.fixture
def records(app):
    with app.app_context():
        first = save_analysis(
            "Robot science excellent.",
            "style",
            [("robot", 2), ("science", 1)],
            {
                "total_words": 100,
                "unique_words": 60,
                "complexity_score": 0.3,
                "vocabulary_richness": 60,
                "reading_time_minutes": 1.2,
                "sentences": 10,
            },
            video_id="dQw4w9WgXcQ",
            sentiment_data={"polarity": 0.8, "subjectivity": 0.6, "label": "positive"},
            readability_metrics={"flesch_ease": 70, "flesch_kincaid": 5},
        )
        second = save_analysis(
            "Jardin nature terrible.",
            "concepts",
            [("environnement", {"score": 2})],
            {
                "total_words": 300,
                "unique_words": 150,
                "complexity_score": 0.7,
                "vocabulary_richness": 50,
                "reading_time_minutes": 2.4,
                "sentences": 20,
            },
            sentiment_data={"polarity": -0.8, "subjectivity": 0.4, "label": "negative"},
            readability_metrics={"flesch_ease": 40, "flesch_kincaid": 10},
        )
        yield first, second


def test_database_search_and_json_roundtrip(records):
    first, second = records
    assert [row.id for row in search_analyses("Jardin")] == [second]
    assert [row.id for row in search_analyses("dQw4w9WgXcQ")] == [first]
    exported = json.loads(ExportService().export_analysis_json(first))
    assert exported["statistics"]["total_words"] == 100
    assert exported["content"]["original_text"] == "Robot science excellent."
    assert ExportService().export_analysis_json(999) is None


def test_csv_contains_both_records(records):
    rows = list(csv.reader(StringIO(ExportService().export_analysis_csv(list(records)))))
    assert len(rows) == 3
    assert rows[1][0] == str(records[0])
    assert rows[2][0] == str(records[1])


def test_dashboard_totals_and_daily_aggregation(records):
    service = DashboardService()
    kpis = service.get_global_kpis()
    assert kpis["totals"]["words_analyzed"] == 400
    assert kpis["totals"]["analyses_period"] == 2
    assert kpis["averages"]["sentiment_polarity"] == 0
    trends = service.get_temporal_trends()
    assert len(trends["daily_analyses"]) == 1
    assert trends["daily_analyses"][0]["count"] == 2
    assert trends["daily_words"][0]["words"] == 400
    assert trends["complexity_trend"][0]["average"] == 0.5
    assert service.get_content_insights()["top_analyses"]["most_words"][0]["id"] == records[1]
    assert ExportService().create_dashboard_data()["summary"]["total_analyses"] == 2


def test_comparison_includes_both_and_rejects_missing(records):
    service = ComparisonService()
    result = service.compare_analyses(list(records))
    assert "error" not in result
    assert result["analyses_count"] == 2
    assert [row["id"] for row in result["analyses_overview"]] == list(records)
    assert "error" in service.compare_analyses([records[0]])
    assert "error" in service.compare_analyses([records[0], 999])
    assert "error" in service.compare_analyses([1, 2, 3, 4, 5, 6])


def test_auto_tags_and_filtered_export(records):
    service = TagsService()
    tags = service.get_analysis_tags(records[0])
    assert "source:youtube" in tags["auto_tags"]
    assert "source:text" in service.get_analysis_tags(records[1])["auto_tags"]
    stats = service.get_tag_statistics()
    assert stats["analyses_processed"] == 2
    assert stats["total_unique_tags"] > 0
    exported = json.loads(service.export_tagged_analyses())
    assert len(exported["analyses"]) == 2
    assert "error" not in service.create_tag_hierarchy()
    assert "error" not in service.suggest_tags(records[0])
    assert "error" in service.get_analysis_tags(999)


@pytest.mark.parametrize(
    "text,label",
    [
        ("This is excellent and wonderful.", "positive"),
        ("This is horrible and terrible.", "negative"),
        ("The item is on the desk.", "neutral"),
    ],
)
def test_sentiment_works_without_downloaded_corpus(text, label, monkeypatch, tmp_path):
    import nltk

    monkeypatch.setattr(nltk.data, "path", [str(tmp_path)])
    result = analyze_sentiment(text)
    assert result["label"] == label
    assert result["sentences_analysis"]["total_sentences"] == 1


def test_readability_and_emotion_boundaries():
    assert analyze_sentiment("") is None
    assert calculate_readability_metrics("") is None
    assert calculate_readability_metrics("le et un") is None
    assert estimate_syllables("robot nature") == 4
    assert estimate_syllables("123") == 0
    assert detect_emotions("happy smile joy")["dominant_emotion"] == "joie"
    assert detect_emotions("") is None


def test_individual_pdf_uses_portable_default_directory(records, app):
    from yt_transcript.pdf_export_service import PDFExportService

    service = PDFExportService()
    result = service.export_analysis_to_pdf(records[0])
    assert result is not None
    assert Path(result).is_relative_to(app.config["DATA_DIR"])
    assert "Rapport" in PdfReader(result).pages[0].extract_text()
    analysis = get_analysis_by_id(records[0])
    assert service.create_sentiment_chart(analysis).getvalue().startswith(b"\x89PNG")
    assert service.create_metrics_chart(analysis).getvalue().startswith(b"\x89PNG")
    assert service.export_analysis_to_pdf(999) is None
