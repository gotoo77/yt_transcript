"""Focused branch coverage for REST API resource error handling and limits."""

from types import SimpleNamespace

from flask import abort


def test_analysis_list_reraises_http_exception(client, monkeypatch):
    def conflict(*args, **kwargs):
        abort(409, "simulated conflict")

    monkeypatch.setattr("yt_transcript.api.get_recent_analyses", conflict)
    assert client.get("/api/v1/analyses/").status_code == 409


def test_json_export_exception_becomes_500(client, monkeypatch):
    def fail(_analysis_id):
        raise RuntimeError("simulated JSON export failure")

    monkeypatch.setattr(
        "yt_transcript.api.export_service.export_analysis_json",
        fail,
    )
    response = client.get("/api/v1/export/json/1")
    assert response.status_code == 500
    assert "simulated JSON export failure" not in response.get_data(as_text=True)


def test_csv_export_rejects_no_valid_ids_and_too_many_ids(client):
    assert client.get("/api/v1/export/csv?ids=foo,bar").status_code == 400

    ids = ",".join(str(value) for value in range(1, 52))
    response = client.get(f"/api/v1/export/csv?ids={ids}")
    assert response.status_code == 400


def test_csv_export_exception_becomes_500(client, monkeypatch):
    def fail(_analysis_ids):
        raise RuntimeError("simulated CSV export failure")

    monkeypatch.setattr(
        "yt_transcript.api.export_service.export_analysis_csv",
        fail,
    )
    response = client.get("/api/v1/export/csv?ids=1")
    assert response.status_code == 500
    assert "simulated CSV export failure" not in response.get_data(as_text=True)


def test_dashboard_exception_becomes_500(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated dashboard failure")

    monkeypatch.setattr(
        "yt_transcript.api.export_service.create_dashboard_data",
        fail,
    )
    response = client.get("/api/v1/dashboard/")
    assert response.status_code == 500
    assert "simulated dashboard failure" not in response.get_data(as_text=True)


def test_dashboard_stats_ignore_missing_sentiment_labels(client, monkeypatch):
    rows = [
        SimpleNamespace(
            total_words=10,
            sentiment_polarity=None,
            complexity_score=None,
            sentiment_label=None,
        ),
        SimpleNamespace(
            total_words=20,
            sentiment_polarity=0.5,
            complexity_score=0.8,
            sentiment_label="positive",
        ),
    ]
    monkeypatch.setattr(
        "yt_transcript.api.get_recent_analyses",
        lambda limit: rows,
    )

    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    assert response.json["total_words"] == 30
    assert response.json["average_sentiment"] == 0.5
    assert response.json["average_complexity"] == 0.8
    assert response.json["sentiment_distribution"] == {"positive": 1}


def test_dashboard_stats_exception_becomes_500(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated stats failure")

    monkeypatch.setattr("yt_transcript.api.get_recent_analyses", fail)
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 500
    assert "simulated stats failure" not in response.get_data(as_text=True)
