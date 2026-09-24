from types import SimpleNamespace

import pytest

from yt_transcript import create_app
from yt_transcript.database import get_analysis_by_id


@pytest.mark.parametrize("url", ["/", "/dashboard", "/static/app.js", "/api/docs/", "/health"])
def test_packaged_pages(client, url):
    with client.get(url) as response:
        assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "text",
        {"text": 12},
        {"text": ""},
        {"text": "robot science", "mode": "bad"},
        {"text": "robot science", "max_words": "bad"},
    ],
)
def test_bad_analysis_input_is_400(client, payload):
    response = client.post("/analyze", json=payload)
    assert response.status_code == 400
    assert response.json["success"] is False


def test_invalid_youtube_url_is_400(client):
    response = client.post(
        "/transcribe", json={"video_id": "https://evil.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 400


def test_analysis_persists_real_statistics(client, app):
    response = client.post("/analyze", json={"text": "Robot robot python science.", "max_words": 2})
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["result"] == [["robot", 2], ["python", 1]]
    with app.app_context():
        saved = get_analysis_by_id(response.json["analysis_id"])
        assert saved.total_words == 4
        assert saved.unique_words == 3
        assert saved.original_text == "Robot robot python science."


def test_databases_are_isolated(client, tmp_path):
    client.post("/analyze", json={"text": "Robot science python."})
    second = create_app({"TESTING": True, "DATA_DIR": tmp_path / "second", "SECRET_KEY": "other"})
    try:
        assert second.test_client().get("/history").json["history"] == []
        assert len(client.get("/history").json["history"]) == 1
    finally:
        second.extensions["database_engine"].dispose()


@pytest.mark.parametrize(
    "url,code",
    [
        ("/api/v1/analyses/987", 404),
        ("/api/v1/export/json/987", 404),
        ("/api/v1/analyses/search", 400),
        ("/api/v1/export/csv", 400),
        ("/api/v1/analyses/?limit=-1", 400),
        ("/api/v1/analyses/?limit=abc", 400),
    ],
)
def test_api_preserves_client_error_status(client, url, code):
    assert client.get(url).status_code == code


def test_transcription_fallback_and_session_isolation(client, app, monkeypatch):
    class Unavailable:
        language_code = "fr"

        def fetch(self):
            raise RuntimeError("unavailable")

    class Available:
        language_code = "es"

        def fetch(self):
            return [SimpleNamespace(text="Robot"), SimpleNamespace(text="science")]

    class YouTube:
        def fetch(self, video_id, languages):
            raise RuntimeError("preferred languages unavailable")

        def list(self, video_id):
            return [Unavailable(), Available()]

    monkeypatch.setattr("yt_transcript.web.YouTubeTranscriptApi", YouTube)
    response = client.post("/transcribe", json={"video_id": "dQw4w9WgXcQ"})
    assert response.json == {"success": True, "transcript": "Robot science"}
    with client.session_transaction() as session:
        assert session["video_id"] == "dQw4w9WgXcQ"
        assert "transcript" not in session  # Long transcripts do not belong in cookies.
    with app.test_client().session_transaction() as session:
        assert "video_id" not in session


def test_transcription_failure_is_502(client, monkeypatch):
    class YouTube:
        def fetch(self, *args, **kwargs):
            raise RuntimeError("private diagnostic")

        def list(self, *args, **kwargs):
            raise RuntimeError("private diagnostic")

    monkeypatch.setattr("yt_transcript.web.YouTubeTranscriptApi", YouTube)
    response = client.post("/transcribe", json={"video_id": "dQw4w9WgXcQ"})
    assert response.status_code == 502
    assert "private diagnostic" not in response.get_data(as_text=True)


def test_failed_database_commit_is_not_success(client, monkeypatch):
    def fail_commit(self):
        raise RuntimeError("secret database location")

    monkeypatch.setattr("sqlalchemy.orm.Session.commit", fail_commit)
    response = client.post("/analyze", json={"text": "Robot science python."})
    assert response.status_code == 500
    assert response.json["success"] is False
    assert "secret database location" not in response.get_data(as_text=True)
    assert client.get("/history").json["history"] == []


def test_analysis_failure_has_generic_error(client, monkeypatch):
    def fail(*args):
        raise RuntimeError("private detail")

    monkeypatch.setattr("yt_transcript.web.analyze_text", fail)
    response = client.post("/analyze", json={"text": "Robot science python."})
    assert response.status_code == 500
    assert "private detail" not in response.get_data(as_text=True)


def test_read_endpoints_return_persisted_analysis(client):
    created = client.post("/analyze", json={"text": "Robot robot science python."}).json
    analysis_id = created["analysis_id"]
    assert client.get(f"/history/{analysis_id}").json["analysis"]["total_words"] == 4
    assert len(client.get("/history/search?q=robot").json["results"]) == 1
    assert client.get("/api/v1/analyses/").json[0]["id"] == analysis_id
    assert client.get(f"/api/v1/analyses/{analysis_id}").json["total_words"] == 4
    assert len(client.get("/api/v1/analyses/search?query=robot").json) == 1
    assert client.get(f"/api/v1/export/json/{analysis_id}").json["statistics"]["total_words"] == 4
    assert "4" in client.get(f"/api/v1/export/csv?ids={analysis_id}").get_data(as_text=True)
    assert client.get("/api/v1/dashboard/stats").json["total_words"] == 4
    assert client.get("/api/v1/dashboard/").json["summary"]["total_analyses"] == 1
    for suffix in ("data", "kpis", "trends", "insights"):
        response = client.get(f"/api/dashboard/{suffix}")
        assert response.status_code == 200
        assert response.json["success"] is True


def test_text_tools_have_meaningful_results(client):
    text = "Robot robot science python."
    assert client.post("/statistics", json={"text": text}).json["statistics"]["total_words"] == 4
    cloud = client.post("/wordcloud", json={"text": text, "max_words": 1}).json
    assert cloud["wordcloud_data"][0]["word"] == "robot"
    assert cloud["wordcloud_data"][0]["count"] == 2
    text = "Robot robot robot science. " + "Un jardin propose des fleurs et des arbres dans la nature. " * 2
    response = client.post("/summary", json={"text": text, "num_sentences": 1})
    assert response.json["success"] is True
    assert response.json["summary_length"] < response.json["original_length"]


def test_modern_ui_stylesheet_is_packaged(client):
    page = client.get("/")
    assert page.status_code == 200
    assert b'href="/static/modern.css"' in page.data
    with client.get("/static/modern.css") as stylesheet:
        assert stylesheet.status_code == 200
        assert b"prefers-reduced-motion" in stylesheet.data


@pytest.mark.parametrize("url", ["/", "/dashboard"])
def test_workspace_theme_and_accessible_navigation(client, url):
    response = client.get(url)
    assert response.status_code == 200
    for expected in (b'data-bs-theme="dark"', b'id="theme-toggle"',
                     b'href="#main-content"', b'id="main-content"',
                     b'/static/modern.css', b'/static/theme.js'):
        assert expected in response.data


def test_theme_script_is_packaged(client):
    with client.get("/static/theme.js") as response:
        assert response.status_code == 200
        assert b"yt-transcript-theme" in response.data
