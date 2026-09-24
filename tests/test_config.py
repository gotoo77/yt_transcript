from yt_transcript import create_app
from yt_transcript.config import data_directory


def test_configuration_uses_persistent_secret_and_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("YT_TRANSCRIPT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert data_directory() == tmp_path
    first = create_app({"TESTING": True})
    second = create_app({"TESTING": True})
    try:
        assert first.secret_key == second.secret_key
        assert len(first.secret_key) == 64
        assert first.debug is False
        assert first.config["DATA_DIR"] == tmp_path
    finally:
        first.extensions["database_engine"].dispose()
        second.extensions["database_engine"].dispose()
