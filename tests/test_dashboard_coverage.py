"""Focused coverage for dashboard aggregations, distributions and failure fallbacks."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from yt_transcript.dashboard_service import DashboardService


def record(**changes):
    values = {
        "id": 1,
        "created_at": datetime.now(),
        "analysis_mode": "style",
        "total_words": 100,
        "unique_words": 60,
        "vocabulary_richness": 60.0,
        "complexity_score": 0.5,
        "sentiment_polarity": 0.0,
        "sentiment_label": "neutral",
        "reading_time_minutes": 2.0,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_distribution_helpers_cover_all_ranges_and_empty():
    service = DashboardService()

    assert service._get_word_count_distribution([]) == {}
    assert service._get_word_count_distribution([100, 700, 1500, 3000, 7000]) == {
        "0-500": 1,
        "501-1000": 1,
        "1001-2000": 1,
        "2001-5000": 1,
        "5000+": 1,
    }

    assert service._get_complexity_distribution([]) == {}
    assert service._get_complexity_distribution([0.1, 0.3, 0.5, 0.7, 0.9]) == {
        "Très faible (0-0.2)": 1,
        "Faible (0.2-0.4)": 1,
        "Modérée (0.4-0.6)": 1,
        "Élevée (0.6-0.8)": 1,
        "Très élevée (0.8-1.0)": 1,
    }

    assert service._get_sentiment_distribution([]) == {}
    assert service._get_sentiment_distribution([-0.8, -0.3, 0.0, 0.3, 0.8]) == {
        "Très négatif (-1 à -0.5)": 1,
        "Négatif (-0.5 à -0.1)": 1,
        "Neutre (-0.1 à 0.1)": 1,
        "Positif (0.1 à 0.5)": 1,
        "Très positif (0.5 à 1)": 1,
    }


def test_temporal_trends_ignore_old_rows_and_keep_optional_series(monkeypatch):
    now = datetime.now()
    rows = [
        record(
            id=1,
            created_at=now,
            total_words=100,
            complexity_score=0.4,
            sentiment_polarity=0.2,
            reading_time_minutes=2.0,
        ),
        record(
            id=2,
            created_at=now,
            total_words=None,
            complexity_score=None,
            sentiment_polarity=None,
            reading_time_minutes=None,
        ),
        record(id=3, created_at=now - timedelta(days=60)),
    ]
    monkeypatch.setattr(
        "yt_transcript.dashboard_service.get_recent_analyses",
        lambda limit: rows,
    )

    result = DashboardService().get_temporal_trends(days=30)
    assert result is not None
    assert result["daily_analyses"][0]["count"] == 2
    assert result["daily_words"][0]["words"] == 100
    assert result["complexity_trend"][0]["average"] == 0.4
    assert result["sentiment_trend"][0]["average"] == 0.2
    assert result["reading_time_trend"][0]["average"] == 2.0


def test_temporal_trends_empty_period(monkeypatch):
    monkeypatch.setattr(
        "yt_transcript.dashboard_service.get_recent_analyses",
        lambda limit: [],
    )
    assert DashboardService().get_temporal_trends() == {
        "message": "Aucune donnée disponible pour la période"
    }


def test_content_insights_cover_empty_optional_metrics(monkeypatch):
    rows = [
        record(
            total_words=None,
            unique_words=None,
            vocabulary_richness=None,
            complexity_score=None,
            sentiment_polarity=None,
        )
    ]
    monkeypatch.setattr(
        "yt_transcript.dashboard_service.get_recent_analyses",
        lambda limit: rows,
    )
    result = DashboardService().get_content_insights()
    assert result is not None
    assert result["content_metrics"] == {
        "avg_words_per_analysis": 0,
        "avg_unique_words": 0,
        "avg_vocabulary_richness": 0,
        "avg_complexity": 0,
        "avg_sentiment": 0,
    }
    assert result["top_analyses"] == {
        "most_words": [],
        "most_complex": [],
        "richest_vocabulary": [],
    }


def test_content_patterns_cover_modes_weekdays_and_hours():
    rows = [
        record(id=1, analysis_mode="style", created_at=datetime(2026, 9, 25, 10)),
        record(id=2, analysis_mode="concepts", created_at=datetime(2026, 9, 25, 10)),
        record(id=3, analysis_mode="style", created_at=None),
    ]
    result = DashboardService()._analyze_content_patterns(rows)
    assert result["preferred_modes"] == {"style": 2, "concepts": 1}
    assert result["peak_hours"] == {10: 2}
    assert result["total_patterns_analyzed"] == 3


@pytest.mark.parametrize(
    ("method", "patch_target"),
    [
        ("get_global_kpis", "get_db_session"),
        ("get_temporal_trends", "get_recent_analyses"),
        ("get_content_insights", "get_recent_analyses"),
    ],
)
def test_dashboard_service_failures_return_none(monkeypatch, method, patch_target):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated dashboard backend failure")

    monkeypatch.setattr("yt_transcript.dashboard_service." + patch_target, fail)
    assert getattr(DashboardService(), method)() is None


def test_pattern_failure_returns_empty_dict(monkeypatch):
    service = DashboardService()

    class Broken:
        @property
        def analysis_mode(self):
            raise RuntimeError("simulated bad row")

    assert service._analyze_content_patterns([Broken()]) == {}


def test_comprehensive_dashboard_contains_all_sections(monkeypatch):
    service = DashboardService()
    monkeypatch.setattr(service, "get_global_kpis", lambda days: {"days": days})
    monkeypatch.setattr(service, "get_temporal_trends", lambda days: {"days": days})
    monkeypatch.setattr(service, "get_content_insights", lambda limit: {"limit": limit})

    result = service.generate_comprehensive_dashboard(days=14)
    assert result is not None
    assert result["period_days"] == 14
    assert result["kpis"] == {"days": 14}
    assert result["trends"] == {"days": 14}
    assert result["insights"] == {"limit": 200}


def test_temporal_trends_skip_empty_optional_metric_series(monkeypatch):
    now = datetime.now()
    rows = [
        record(
            id=1,
            created_at=now,
            total_words=50,
            complexity_score=None,
            sentiment_polarity=None,
            reading_time_minutes=None,
        )
    ]
    monkeypatch.setattr(
        "yt_transcript.dashboard_service.get_recent_analyses",
        lambda limit: rows,
    )

    result = DashboardService().get_temporal_trends(days=30)
    assert result is not None
    assert result["daily_analyses"][0]["count"] == 1
    assert result["complexity_trend"] == []
    assert result["sentiment_trend"] == []
    assert result["reading_time_trend"] == []


def test_top_analyses_empty_input_returns_empty_dict():
    assert DashboardService()._get_top_analyses([]) == {}


def test_comprehensive_dashboard_failure_returns_none(monkeypatch):
    service = DashboardService()

    def fail(_days):
        raise RuntimeError("simulated comprehensive dashboard failure")

    monkeypatch.setattr(service, "get_global_kpis", fail)
    assert service.generate_comprehensive_dashboard(days=7) is None
