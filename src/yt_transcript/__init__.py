"""Application factory. Importing this package does not create files or databases."""

from collections.abc import Mapping
from typing import Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .config import configure_app
from .database import init_database


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    configure_app(app, config)
    init_database(app)

    from .api import create_api_routes
    from .web import bp, validate_request

    app.register_blueprint(bp)
    app.before_request(validate_request)
    create_api_routes(app)

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> tuple[Any, int]:
        return jsonify(success=False, error=error.description), error.code or 500

    @app.get("/health")
    def health() -> dict[str, str]:
        if app.config["INSTANCE_ID"]:
            return {"status": "ok", "instance": app.config["INSTANCE_ID"]}
        return {"status": "ok"}

    return app
