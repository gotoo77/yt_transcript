"""Persistence and HTTP regressions for the saved transcript library."""

from types import SimpleNamespace

import pytest

from yt_transcript.database import (
    delete_transcript,
    find_transcript,
    list_transcripts,
    save_transcript,
)


def test_transcript_upsert_preserves_identity_and_created_at(app):
    with app.app_context():
        assert save_transcript("dQw4w9WgXcQ", "Première transcription")
        first = find_transcript("dQw4w9WgXcQ")
        assert first is not None
        first_id, created_at = first.id, first.created_at

        assert save_transcript("dQw4w9WgXcQ", "Texte mis à jour")
        updated = find_transcript("dQw4w9WgXcQ")
        assert updated is not None
        assert updated.id == first_id
        assert updated.created_at == created_at
        assert updated.text == "Texte mis à jour"
        assert len(list_transcripts()) == 1


def test_transcript_list_is_limited_and_newest_first(app):
    with app.app_context():
        for video_id in ("aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc"):
            assert save_transcript(video_id, video_id)
        assert [item.video_id for item in list_transcripts(limit=2)] == [
            "ccccccccccc",
            "bbbbbbbbbbb",
        ]
        assert list_transcripts(limit=0) == []


def test_delete_transcript_reports_absent_and_removes_only_target(app):
    with app.app_context():
        assert save_transcript("aaaaaaaaaaa", "Keep")
        assert save_transcript("bbbbbbbbbbb", "Delete")
        assert not delete_transcript("ccccccccccc")
        assert delete_transcript("bbbbbbbbbbb")
        assert not delete_transcript("bbbbbbbbbbb")
        assert find_transcript("bbbbbbbbbbb") is None
        assert find_transcript("aaaaaaaaaaa").text == "Keep"


def test_failed_transcript_save_rolls_back_without_changing_prior_text(app, monkeypatch):
    from sqlalchemy.orm import Session

    with app.app_context():
        assert save_transcript("dQw4w9WgXcQ", "Original")
        original_commit = Session.commit

        def reject_commit(self):
            raise RuntimeError("private database location")

        monkeypatch.setattr(Session, "commit", reject_commit)
        assert not save_transcript("dQw4w9WgXcQ", "Not saved")
        monkeypatch.setattr(Session, "commit", original_commit)
        assert find_transcript("dQw4w9WgXcQ").text == "Original"


def test_failed_transcript_delete_rolls_back_and_keeps_record(app, monkeypatch):
    from sqlalchemy.orm import Session

    with app.app_context():
        assert save_transcript("dQw4w9WgXcQ", "Original")
        original_commit = Session.commit

        def reject_commit(self):
            raise RuntimeError("private database location")

        monkeypatch.setattr(Session, "commit", reject_commit)
        with pytest.raises(RuntimeError, match="private database location"):
            delete_transcript("dQw4w9WgXcQ")
        monkeypatch.setattr(Session, "commit", original_commit)
        assert find_transcript("dQw4w9WgXcQ").text == "Original"


@pytest.mark.parametrize("method", ["get", "delete"])
@pytest.mark.parametrize("video_id", ["bad", "not_a_video_id", "invalid-id-12"])
def test_transcript_routes_reject_invalid_ids(client, method, video_id):
    response = getattr(client, method)("/transcripts/" + video_id)
    assert response.status_code == 400


def test_transcript_routes_return_404_for_missing_valid_id(client):
    video_id = "dQw4w9WgXcQ"
    assert client.get("/transcripts/" + video_id).status_code == 404
    assert client.delete("/transcripts/" + video_id).status_code == 404


def test_transcript_listing_exposes_preview_not_full_text(client, app):
    video_id = "dQw4w9WgXcQ"
    text = "é" * 175
    with app.app_context():
        assert save_transcript(video_id, text)
    response = client.get("/transcripts")
    assert response.status_code == 200
    entry = response.json["transcripts"][0]
    assert entry["characters"] == 175
    assert entry["preview"] == text[:160]
    assert "text" not in entry
    assert client.get("/transcripts/" + video_id).json["transcript"] == text


def test_transcript_retrieval_and_delete_manage_session_metadata(client, app):
    video_id = "dQw4w9WgXcQ"
    with app.app_context():
        assert save_transcript(video_id, "Saved transcript")
    assert client.get("/transcripts/" + video_id).status_code == 200
    with client.session_transaction() as session:
        assert session["video_id"] == video_id
    assert client.delete("/transcripts/" + video_id).status_code == 200
    with client.session_transaction() as session:
        assert "video_id" not in session


def test_transcription_storage_failure_does_not_claim_success(client, monkeypatch):
    class YouTube:
        def fetch(self, video_id, languages):
            return [SimpleNamespace(text="Transcript that cannot be stored")]

    monkeypatch.setattr("yt_transcript.web.YouTubeTranscriptApi", YouTube)
    monkeypatch.setattr("yt_transcript.web.save_transcript", lambda video_id, text: False)
    response = client.post("/transcribe", json={"video_id": "dQw4w9WgXcQ"})
    assert response.status_code == 500
    assert response.json["success"] is False
    assert client.get("/transcripts").json["transcripts"] == []
    with client.session_transaction() as session:
        assert "video_id" not in session
