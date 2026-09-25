"""Focused branch coverage for application configuration."""

import pytest
from flask import Flask

import yt_transcript.config as config_module
from yt_transcript.config import configure_app, data_directory


def test_data_directory_uses_platform_default_without_override(monkeypatch, tmp_path):
    monkeypatch.delenv("YT_TRANSCRIPT_DATA_DIR", raising=False)
    monkeypatch.setattr(config_module, "user_data_path", lambda *args, **kwargs: tmp_path)

    assert data_directory() == tmp_path


def test_configure_app_without_override_uses_environment_values(monkeypatch, tmp_path):
    monkeypatch.setenv("YT_TRANSCRIPT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SECRET_KEY", "configured-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///configured.db")

    app = Flask(__name__)
    configure_app(app, None)

    assert app.config["SECRET_KEY"] == "configured-secret"
    assert app.config["DATABASE_URL"] == "sqlite:///configured.db"
    assert app.config["DATA_DIR"] == tmp_path.resolve()


def test_empty_persisted_secret_is_rejected(monkeypatch, tmp_path):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / "secret.key").write_text("", encoding="utf-8")

    app = Flask(__name__)
    with pytest.raises(ValueError, match="Clé de session vide"):
        configure_app(app, {"DATA_DIR": tmp_path})
