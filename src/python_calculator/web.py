"""Flask web application for the calculator."""

from __future__ import annotations

from math import isfinite
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from .calculator import CalculatorError, Number, evaluate


def _display_value(value: Number) -> str:
    """Return a concise, human-friendly representation of a result."""
    if isinstance(value, float):
        if not isfinite(value):
            return "∞" if value > 0 else "−∞"
        if value == 0:
            return "0"
        return format(value, ".15g")
    return str(value)


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the calculator web application."""
    app = Flask(__name__)
    app.config.from_mapping(MAX_CONTENT_LENGTH=16 * 1024)

    if test_config:
        app.config.update(test_config)

    @app.after_request
    def add_security_headers(response):  # type: ignore[no-untyped-def]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response

    @app.get("/")
    def index():  # type: ignore[no-untyped-def]
        return render_template("index.html")

    @app.get("/health")
    def health():  # type: ignore[no-untyped-def]
        return jsonify(status="ok")

    @app.post("/api/calculate")
    def calculate():  # type: ignore[no-untyped-def]
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or "expression" not in payload:
            return jsonify(error="Send an expression to calculate."), 400

        try:
            result = evaluate(payload["expression"])
        except CalculatorError as error:
            return jsonify(error=str(error)), 400

        return jsonify(result=_display_value(result))

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error: RequestEntityTooLarge):
        return jsonify(error="That expression is too long."), 413

    return app


app = create_app()
