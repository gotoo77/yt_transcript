"""Focused branch coverage for web routes and transcript fallbacks."""

from datetime import datetime
from types import SimpleNamespace

import pytest


def test_transcribe_returns_404_when_no_language_is_available(client, monkeypatch):
    class Unavailable:
        language_code = "fr"

        def fetch(self):
            raise RuntimeError("unavailable")

    class YouTube:
        def fetch(self, *args, **kwargs):
            raise RuntimeError("preferred unavailable")

        def list(self, video_id):
            return [Unavailable()]

    monkeypatch.setattr("yt_transcript.web.YouTubeTranscriptApi", YouTube)
    response = client.post("/transcribe", json={"video_id": "dQw4w9WgXcQ"})
    assert response.status_code == 404
    assert response.json["success"] is False


def test_transcribe_reports_persistence_failure(client, monkeypatch):
    class YouTube:
        def fetch(self, video_id, languages):
            return [SimpleNamespace(text="Aujourd hui le robot fonctionne")]

    monkeypatch.setattr("yt_transcript.web.YouTubeTranscriptApi", YouTube)
    monkeypatch.setattr("yt_transcript.web.save_transcript", lambda *args, **kwargs: False)

    response = client.post("/transcribe", json={"video_id": "dQw4w9WgXcQ"})
    assert response.status_code == 500
    assert response.json["success"] is False


@pytest.mark.parametrize(
    ("method", "url", "expected"),
    [
        ("get", "/transcripts/not-a-video-id", 400),
        ("delete", "/transcripts/not-a-video-id", 400),
        ("delete", "/transcripts/dQw4w9WgXcQ", 404),
    ],
)
def test_transcript_routes_reject_invalid_or_missing_entries(client, method, url, expected):
    response = getattr(client, method)(url)
    assert response.status_code == expected


def test_transcript_delete_without_matching_session_keeps_success(client, monkeypatch):
    monkeypatch.setattr("yt_transcript.web.delete_transcript", lambda video_id: True)
    with client.session_transaction() as sess:
        sess["video_id"] = "aaaaaaaaaaa"

    response = client.delete("/transcripts/dQw4w9WgXcQ")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["video_id"] == "aaaaaaaaaaa"


def test_analyze_rejects_too_short_text(client):
    response = client.post("/analyze", json={"text": "robot"})
    assert response.status_code == 200
    assert response.json["success"] is False
    assert "trop court" in response.json["error"]


def test_analyze_without_advanced_analysis_omits_field(client, monkeypatch):
    monkeypatch.setattr("yt_transcript.web.get_comprehensive_analysis", lambda text: {})

    response = client.post("/analyze", json={"text": "Robot science python."})
    assert response.status_code == 200
    assert response.json["success"] is True
    assert "advanced_analysis" not in response.json


def test_summary_rejects_text_under_minimum_length(client):
    text = "robot science " * 5
    assert len(text) < 100
    response = client.post("/summary", json={"text": text})
    assert response.status_code == 200
    assert response.json["success"] is False
    assert "trop court" in response.json["error"]


def test_history_detail_and_empty_search_have_expected_responses(client):
    missing = client.get("/history/999999")
    assert missing.status_code == 404
    assert missing.json["success"] is False

    empty = client.get("/history/search?q=%20%20")
    assert empty.status_code == 200
    assert empty.json["success"] is False


def test_history_serializes_optional_date_and_long_preview(client, monkeypatch):
    row = SimpleNamespace(
        id=7,
        created_at=None,
        analysis_mode="style",
        original_text="x" * 120,
        video_id=None,
        total_words=120,
        sentiment_label=None,
        complexity_score=None,
    )
    monkeypatch.setattr("yt_transcript.web.get_recent_analyses", lambda limit: [row])
    monkeypatch.setattr("yt_transcript.web.get_analysis_stats", lambda: {})

    response = client.get("/history")
    assert response.status_code == 200
    item = response.json["history"][0]
    assert item["created_at"] is None
    assert item["text_preview"].endswith("...")


def test_search_history_serializes_optional_date_and_short_preview(client, monkeypatch):
    row = SimpleNamespace(
        id=8,
        created_at=None,
        analysis_mode="style",
        original_text="short preview",
        video_id=None,
        total_words=2,
        sentiment_label=None,
    )
    monkeypatch.setattr("yt_transcript.web.search_analyses", lambda query: [row])

    response = client.get("/history/search?q=short")
    assert response.status_code == 200
    item = response.json["results"][0]
    assert item["created_at"] is None
    assert item["text_preview"] == "short preview"
