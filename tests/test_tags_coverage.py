"""Behavioral coverage for automatic tags, filtering, suggestions and hierarchy."""

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from yt_transcript.tags_service import TagsService


def analysis(**changes):
    values = dict(
        id=1,
        created_at=datetime(2026, 9, 24, 12),
        analysis_mode="style",
        video_id=None,
        original_text="Science et informatique.",
        complexity_score=0.9,
        sentiment_polarity=-0.8,
        sentiment_label="negative",
        total_words=6000,
        flesch_reading_ease=20,
        vocabulary_richness=90,
    )
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        (
            {},
            {
                "complexity:very_complex",
                "sentiment:very_negative",
                "length:very_long",
                "readability:very_difficult",
                "source:text",
            },
        ),
        (
            {
                "complexity_score": 0.1,
                "sentiment_polarity": 0.8,
                "total_words": 100,
                "flesch_reading_ease": 95,
                "video_id": "dQw4w9WgXcQ",
            },
            {
                "complexity:very_simple",
                "sentiment:very_positive",
                "length:very_short",
                "readability:very_easy",
                "source:youtube",
            },
        ),
        (
            {
                "complexity_score": None,
                "sentiment_polarity": None,
                "total_words": None,
                "flesch_reading_ease": None,
                "created_at": None,
            },
            {"mode:style", "source:text"},
        ),
    ],
)
def test_auto_tags_cover_metric_extremes_and_missing_fields(changes, expected):
    tags = TagsService().auto_tag_analysis(analysis(**changes))
    assert expected.issubset(tags)
    if changes.get("created_at", 1) is None:
        assert not any(tag.startswith("year:") for tag in tags)


def test_filtered_tags_limit_and_missing_values(monkeypatch):
    records = [
        analysis(id=1),
        analysis(id=2, sentiment_polarity=0.8),
        analysis(id=3, sentiment_polarity=-0.9),
    ]
    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", lambda limit: records)
    service = TagsService()
    result = service.filter_analyses_by_tags({"sentiment:very_negative": True}, limit=1)
    assert result["results_count"] == 1
    assert [entry["id"] for entry in result["analyses"]] == [1]
    assert service.filter_analyses_by_tags({"not:a-tag": True})["analyses"] == []


def test_suggest_tags_matches_content_and_context(monkeypatch):
    record = analysis(original_text="Informatique école entreprise recherche santé")
    monkeypatch.setattr("yt_transcript.tags_service.get_analysis_by_id", lambda analysis_id: record)
    result = TagsService().suggest_tags(1)
    assert set(result["content_suggestions"]) == {
        "theme:technology",
        "theme:education",
        "theme:business",
        "theme:science",
        "theme:health",
    }
    assert set(result["contextual_suggestions"]) == {
        "format:long_form",
        "quality:rich_vocabulary",
        "level:advanced",
    }


def test_hierarchy_and_non_json_export(monkeypatch):
    records = [analysis(id=1), analysis(id=2, complexity_score=0.1)]
    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", lambda limit: records)
    service = TagsService()
    hierarchy = service.create_tag_hierarchy()
    assert hierarchy["total_analyses"] == 2
    assert hierarchy["categories"]["complexity"]["values"]["very_complex"] == {
        "count": 1,
        "label": "Très Complexe",
    }
    export = service.export_tagged_analyses(output_format="dict")
    assert export["total_analyses"] == 2
    assert export["format"] == "dict"
    filtered = json.loads(
        service.export_tagged_analyses(tag_filters={"complexity:very_simple": True})
    )
    assert [row["id"] for row in filtered["analyses"]] == [2]


def test_empty_tag_statistics_and_missing_custom_tag(monkeypatch):
    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", lambda limit: [])
    monkeypatch.setattr("yt_transcript.tags_service.get_analysis_by_id", lambda analysis_id: None)
    service = TagsService()
    assert service.get_tag_statistics() == {"message": "Aucune analyse disponible"}
    assert "error" in service.add_custom_tag(123, "topic")
    assert "error" in service.suggest_tags(123)
