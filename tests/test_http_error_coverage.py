"""HTTP error-path coverage for Flask routes and REST resources."""

import pytest


@pytest.mark.parametrize(
    ("url", "patch_target"),
    [
        ("/history", "yt_transcript.web.get_recent_analyses"),
        ("/history/1", "yt_transcript.web.get_analysis_by_id"),
        ("/history/search?q=robot", "yt_transcript.web.search_analyses"),
    ],
)
def test_history_backends_hide_internal_failures(client, monkeypatch, url, patch_target):
    def fail(*args, **kwargs):
        raise RuntimeError("private backend detail")

    monkeypatch.setattr(patch_target, fail)
    response = client.get(url)
    assert response.status_code == 500
    assert response.json["success"] is False
    assert "private backend detail" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("url", "patch_target"),
    [
        ("/api/dashboard/data", "generate_comprehensive_dashboard"),
        ("/api/dashboard/kpis", "get_global_kpis"),
        ("/api/dashboard/trends", "get_temporal_trends"),
        ("/api/dashboard/insights", "get_content_insights"),
    ],
)
def test_dashboard_web_routes_report_empty_results(client, monkeypatch, url, patch_target):
    monkeypatch.setattr(
        "yt_transcript.web.dashboard_service." + patch_target,
        lambda *args, **kwargs: {},
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.json["success"] is False


@pytest.mark.parametrize(
    ("url", "patch_target"),
    [
        ("/api/dashboard/data", "generate_comprehensive_dashboard"),
        ("/api/dashboard/kpis", "get_global_kpis"),
        ("/api/dashboard/trends", "get_temporal_trends"),
        ("/api/dashboard/insights", "get_content_insights"),
    ],
)
def test_dashboard_web_routes_hide_service_exceptions(client, monkeypatch, url, patch_target):
    def fail(*args, **kwargs):
        raise RuntimeError("private dashboard detail")

    monkeypatch.setattr("yt_transcript.web.dashboard_service." + patch_target, fail)
    response = client.get(url)
    assert response.status_code == 500
    assert response.json["success"] is False
    assert "private dashboard detail" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("url", "patch_target"),
    [
        ("/statistics", "yt_transcript.web.get_text_statistics"),
        ("/summary", "yt_transcript.web.generate_summary"),
        ("/wordcloud", "yt_transcript.web.get_word_cloud_data"),
    ],
)
def test_text_tool_exceptions_are_generic(client, monkeypatch, url, patch_target):
    def fail(*args, **kwargs):
        raise RuntimeError("private text detail")

    monkeypatch.setattr(patch_target, fail)
    payload = {"text": "word " * 30}
    response = client.post(url, json=payload)
    assert response.status_code == 500
    assert response.json["success"] is False
    assert "private text detail" not in response.get_data(as_text=True)


def test_dashboard_export_rejects_unknown_format(client):
    response = client.get("/api/dashboard/export/xml")
    assert response.status_code == 200
    assert response.json["success"] is False
    assert "Format non supporté" in response.json["error"]


def test_dashboard_export_exception_is_generic(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("private export detail")

    monkeypatch.setattr(
        "yt_transcript.web.report_export_service.generate_dashboard_report",
        fail,
    )
    response = client.get("/api/dashboard/export/pdf")
    assert response.status_code == 500
    assert response.json["success"] is False
    assert "private export detail" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("url", "patch_target"),
    [
        ("/api/v1/analyses/", "yt_transcript.api.get_recent_analyses"),
        ("/api/v1/analyses/1", "yt_transcript.api.get_analysis_by_id"),
        ("/api/v1/analyses/search?query=robot", "yt_transcript.api.search_analyses"),
    ],
)
def test_rest_analysis_resources_return_500_on_backend_failure(
    client, monkeypatch, url, patch_target
):
    def fail(*args, **kwargs):
        raise RuntimeError("private REST detail")

    monkeypatch.setattr(patch_target, fail)
    response = client.get(url)
    assert response.status_code == 500
    assert "private REST detail" not in response.get_data(as_text=True)


def test_rest_export_failures_have_expected_status(client, monkeypatch):
    monkeypatch.setattr(
        "yt_transcript.api.export_service.export_analysis_json",
        lambda analysis_id: None,
    )
    assert client.get("/api/v1/export/json/1").status_code == 404

    monkeypatch.setattr(
        "yt_transcript.api.export_service.export_analysis_csv",
        lambda analysis_ids: None,
    )
    assert client.get("/api/v1/export/csv?ids=1").status_code == 500


def test_rest_dashboard_empty_and_stats_empty(client, monkeypatch):
    monkeypatch.setattr(
        "yt_transcript.api.export_service.create_dashboard_data",
        lambda limit: None,
    )
    assert client.get("/api/v1/dashboard/").status_code == 500

    monkeypatch.setattr("yt_transcript.api.get_recent_analyses", lambda limit: [])
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    assert response.json == {
        "total_analyses": 0,
        "total_words": 0,
        "average_sentiment": 0,
        "average_complexity": 0,
    }
