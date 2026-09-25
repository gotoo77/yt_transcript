"""Additional branch coverage for tag service error handling and optional paths."""

from datetime import datetime
from types import SimpleNamespace

from yt_transcript.tags_service import TagsService


def analysis(**changes):
    values = {
        "id": 1,
        "created_at": datetime(2026, 9, 25, 12),
        "analysis_mode": "style",
        "video_id": None,
        "original_text": "",
        "complexity_score": None,
        "sentiment_polarity": None,
        "sentiment_label": None,
        "total_words": None,
        "flesch_reading_ease": None,
        "vocabulary_richness": None,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_auto_tag_failure_returns_empty_list():
    class Broken:
        id = 42

        @property
        def complexity_score(self):
            raise RuntimeError("simulated broken analysis")

    assert TagsService().auto_tag_analysis(Broken()) == []


def test_add_custom_tag_success_normalizes_name(monkeypatch):
    monkeypatch.setattr(
        "yt_transcript.tags_service.get_analysis_by_id",
        lambda analysis_id: analysis(id=analysis_id),
    )
    result = TagsService().add_custom_tag(7, "  Important  ", "yes")
    assert result["success"] is True
    assert result["analysis_id"] == 7
    assert result["tag_added"]["name"] == "important"
    assert result["tag_added"]["value"] == "yes"
    assert "added_at" in result["tag_added"]


def test_add_custom_tag_backend_failure_is_reported(monkeypatch):
    def fail(_analysis_id):
        raise RuntimeError("simulated lookup failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_analysis_by_id", fail)
    result = TagsService().add_custom_tag(7, "topic")
    assert "error" in result
    assert "simulated lookup failure" in result["error"]


def test_get_analysis_tags_backend_failure_is_reported(monkeypatch):
    def fail(_analysis_id):
        raise RuntimeError("simulated lookup failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_analysis_by_id", fail)
    result = TagsService().get_analysis_tags(7)
    assert "error" in result


def test_filter_failure_is_reported(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated recent analyses failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", fail)
    result = TagsService().filter_analyses_by_tags({"mode:style": True})
    assert "error" in result


def test_tag_statistics_handle_plain_tags_and_missing_dates(monkeypatch):
    rows = [analysis(id=1, created_at=None), analysis(id=2)]
    monkeypatch.setattr(
        "yt_transcript.tags_service.get_recent_analyses",
        lambda limit: rows,
    )

    service = TagsService()
    service.auto_tag_analysis = lambda row: ["plain", "mode:style"]

    result = service.get_tag_statistics()
    assert result["analyses_processed"] == 2
    assert result["category_statistics"]["mode"]["total_occurrences"] == 2
    assert result["monthly_distribution"] == {"2026-09": 1}


def test_tag_statistics_failure_is_reported(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated stats failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", fail)
    assert "error" in TagsService().get_tag_statistics()


def test_suggest_tags_without_text_or_contextual_thresholds(monkeypatch):
    row = analysis(
        original_text="",
        total_words=3000,
        vocabulary_richness=75,
        complexity_score=0.7,
    )
    monkeypatch.setattr(
        "yt_transcript.tags_service.get_analysis_by_id",
        lambda analysis_id: row,
    )

    result = TagsService().suggest_tags(1)
    assert result["content_suggestions"] == []
    assert result["contextual_suggestions"] == []


def test_suggest_tags_backend_failure_is_reported(monkeypatch):
    def fail(_analysis_id):
        raise RuntimeError("simulated suggestion failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_analysis_by_id", fail)
    assert "error" in TagsService().suggest_tags(1)


def test_hierarchy_ignores_tags_without_category_and_reports_failures(monkeypatch):
    row = analysis()
    monkeypatch.setattr(
        "yt_transcript.tags_service.get_recent_analyses",
        lambda limit: [row],
    )

    service = TagsService()
    service.auto_tag_analysis = lambda record: ["plain"]
    result = service.create_tag_hierarchy()
    assert result == {"categories": {}, "total_analyses": 1}

    def fail(*args, **kwargs):
        raise RuntimeError("simulated hierarchy failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", fail)
    assert "error" in TagsService().create_tag_hierarchy()


def test_export_propagates_filter_error(monkeypatch):
    service = TagsService()
    monkeypatch.setattr(
        service,
        "filter_analyses_by_tags",
        lambda filters: {"error": "simulated filter failure"},
    )
    assert service.export_tagged_analyses({"mode:style": True}) == {
        "error": "simulated filter failure"
    }


def test_export_backend_failure_is_reported(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated export failure")

    monkeypatch.setattr("yt_transcript.tags_service.get_recent_analyses", fail)
    assert "error" in TagsService().export_tagged_analyses()
