"""Portable paths and persistent session configuration."""

import os
import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask
from platformdirs import user_data_path
from sqlalchemy import URL


def data_directory() -> Path:
    configured = os.environ.get("YT_TRANSCRIPT_DATA_DIR")
    return (
        Path(configured).expanduser().resolve()
        if configured
        else user_data_path("yt-transcript", appauthor=False)
    )


def configure_app(app: Flask, config: Mapping[str, Any] | None) -> None:
    app.config.from_mapping(
        DATA_DIR=data_directory(),
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        DEBUG=False,
        INSTANCE_ID=os.environ.get("YT_TRANSCRIPT_INSTANCE_ID"),
    )
    if config:
        app.config.update(config)
    data_dir = Path(app.config["DATA_DIR"]).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    app.config["DATA_DIR"] = data_dir
    if not app.config["SECRET_KEY"]:
        key_path = data_dir / "secret.key"
        try:
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            app.config["SECRET_KEY"] = key_path.read_text(encoding="utf-8").strip()
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
                key = secrets.token_hex(32)
                key_file.write(key)
                app.config["SECRET_KEY"] = key
        if not app.config["SECRET_KEY"]:
            raise ValueError(f"Clé de session vide : {key_path}")
    if not app.config["DATABASE_URL"]:
        app.config["DATABASE_URL"] = URL.create("sqlite", database=str(data_dir / "yt_analyzer.db"))
