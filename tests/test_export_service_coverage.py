"""Regression tests for JSON/CSV exports and the legacy dashboard projection."""

import csv
import json
from datetime import datetime
from io import StringIO
from types import SimpleNamespace

import pytest

from yt_transcript.export_service import ExportService


def make_analysis(**changes):
    fields = {
        "id": 7,
        "created_at": datetime(2026, 9, 24, 12, 30),
        "analysis_mode": "style",
        "video_id": "dQw4w9WgXcQ",
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "original_text": "Bonjour été",
        "text_length": 11,
        "word_frequency": [["bonjour", 1]],
        "concepts_detected": None,
        "total_words": 2,
        "unique_words": 2,
        "sentences": 1,
        "vocabulary_richness": 100.0,
        "reading_time_minutes": 0.1,
        "complexity_score": 2.0,
        "sentiment_polarity": 0.0,
        "sentiment_subjectivity": 0.0,
        "sentiment_label": "neutral",
        "emotions_detected": None,
        "flesch_reading_ease": 80.0,
        "flesch_kincaid_grade": 2.0,
        "summary_text": "Court résumé",
        "summary_compression_ratio": 20.0,
    }
    fields.update(changes)
    return SimpleNamespace(**fields)


def test_json_export_preserves_unicode_zero_values_and_metadata(monkeypatch):
    monkeypatch.setattr(
        "yt_transcript.export_service.get_analysis_by_id", lambda analysis_id: make_analysis()
    )
    payload = ExportService().export_analysis_json(7)
    assert payload is not None
    data = json.loads(payload)
    assert data["metadata"]["analysis_id"] == 7
    assert data["metadata"]["created_at"] == "2026-09-24T12:30:00"
    assert data["content"]["original_text"] == "Bonjour été"
    assert data["sentiment_analysis"]["polarity"] == 0.0
    assert data["analysis_results"]["word_frequency"] == [["bonjour", 1]]


def test_csv_export_preserves_order_skips_missing_and_truncates_long_summary(monkeypatch):
    rows = {
        7: make_analysis(),
        8: make_analysis(id=8, created_at=None, video_id=None, video_url=None,
                         summary_text="x" * 105, sentiment_label=None),
    }
    monkeypatch.setattr(
        "yt_transcript.export_service.get_analysis_by_id", lambda analysis_id: rows.get(analysis_id)
    )
    payload = ExportService().export_analysis_csv([8, 99, 7])
    assert payload is not None
    result = list(csv.DictReader(StringIO(payload)))
    assert [item["ID"] for item in result] == ["8", "7"]
    assert result[0]["Date Création"] == ""
    assert result[0]["ID Vidéo"] == ""
    assert result[0]["Texte Résumé"] == "x" * 100 + "..."
    assert result[1]["Texte Résumé"] == "Court résumé"
    assert result[1]["Sentiment Polarité"] == "0"


def test_empty_csv_is_header_only(monkeypatch):
    monkeypatch.setattr("yt_transcript.export_service.get_analysis_by_id", lambda analysis_id: None)
    payload = ExportService().export_analysis_csv([999])
    assert payload is not None
    assert len(list(csv.reader(StringIO(payload)))) == 1


@pytest.mark.parametrize("method,lookup", [
    ("export_analysis_json", "get_analysis_by_id"),
    ("export_analysis_csv", "get_analysis_by_id"),
    ("create_dashboard_data", "get_recent_analyses"),
])
def test_export_backends_fail_without_leaking_exception(monkeypatch, method, lookup):
    def fail(*args, **kwargs):
        raise RuntimeError("private-storage-path")

    monkeypatch.setattr("yt_transcript.export_service." + lookup, fail)
    argument = [7] if method == "export_analysis_csv" else 7 if method == "export_analysis_json" else 5
    assert getattr(ExportService(), method)(argument) is None


def test_dashboard_projection_empty_and_populated(monkeypatch):
    service = ExportService()
    monkeypatch.setattr("yt_transcript.export_service.get_recent_analyses", lambda limit: [])
    empty = service.create_dashboard_data(limit=3)
    assert empty is not None
    assert empty["summary"]["total_analyses"] == 0
    assert empty["summary"]["average_complexity"] == 0
    assert empty["top_metrics"]["most_complex"] is None

    analyses = [
        make_analysis(id=1, total_words=5, complexity_score=4.0,
                      vocabulary_richness=10.0, sentiment_label="neutral",
                      sentiment_polarity=0.0),
        make_analysis(id=2, total_words=10, complexity_score=8.0,
                      vocabulary_richness=90.0, sentiment_label="positive",
                      sentiment_polarity=None, created_at=None),
    ]
    monkeypatch.setattr("yt_transcript.export_service.get_recent_analyses", lambda limit: analyses)
    result = service.create_dashboard_data(limit=2)
    assert result is not None
    assert result["summary"]["total_words_analyzed"] == 15
    assert result["summary"]["average_complexity"] == 6.0
    assert result["summary"]["sentiment_distribution"] == {"neutral": 1, "positive": 1}
    assert result["trends"]["analyses_per_day"] == {"2026-09-24": 1}
    assert result["trends"]["sentiment_over_time"][0]["polarity"] == 0.0
    assert result["top_metrics"]["most_complex"] == {"id": 2, "score": 8.0}
    assert result["top_metrics"]["longest_text"] == {"id": 2, "words": 10}
    assert result["top_metrics"]["richest_vocabulary"] == {"id": 2, "richness": 90.0}
