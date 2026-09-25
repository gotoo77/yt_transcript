import pytest

from yt_transcript import create_app


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("YT_TRANSCRIPT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("SECRET_KEY", raising=False)

    def no_youtube(*args, **kwargs):
        raise AssertionError("Tests must not contact YouTube")

    monkeypatch.setattr("youtube_transcript_api.YouTubeTranscriptApi.fetch", no_youtube)
    monkeypatch.setattr("youtube_transcript_api.YouTubeTranscriptApi.list", no_youtube)


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {"TESTING": True, "DATA_DIR": tmp_path, "DATABASE_URL": None, "SECRET_KEY": "test-secret"}
    )
    yield application
    application.extensions["database_engine"].dispose()


@pytest.fixture
def client(app):
    return app.test_client()
