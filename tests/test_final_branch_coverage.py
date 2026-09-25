"""Final reachable branch coverage for entrypoints and residual edge paths."""

import runpy
from datetime import datetime
from types import SimpleNamespace

import pytest

import yt_transcript.cli as cli_module
import yt_transcript.runtime as runtime
from yt_transcript.database import get_analysis_by_id, save_analysis
from yt_transcript.export_service import ExportService
from yt_transcript.pdf_export_service import PDFExportService
from yt_transcript.tags_service import TagsService
from yt_transcript.video import extract_video_id


def test_health_includes_instance_id(app, client):
    app.config["INSTANCE_ID"] = "coverage-instance"
    assert client.get("/health").json == {
        "status": "ok",
        "instance": "coverage-instance",
    }


def test_module_entrypoint_delegates_to_cli(monkeypatch):
    monkeypatch.setattr(cli_module, "main", lambda: 23)
    with pytest.raises(SystemExit) as error:
        runpy.run_module("yt_transcript.__main__", run_name="__main__")
    assert error.value.code == 23


def test_save_analysis_unknown_mode_leaves_mode_specific_results_empty(app):
    with app.app_context():
        analysis_id = save_analysis(
            original_text="Robot science.",
            analysis_mode="other",
            results=[["robot", 1]],
            statistics={"total_words": 2},
        )
        assert analysis_id is not None
        saved = get_analysis_by_id(analysis_id)
        assert saved is not None
        assert saved.word_frequency is None
        assert saved.concepts_detected is None


def test_dashboard_projection_skips_missing_sentiment_fields(monkeypatch):
    row = SimpleNamespace(
        id=1,
        created_at=datetime(2026, 9, 25, 12),
        total_words=10,
        complexity_score=0.2,
        vocabulary_richness=50.0,
        sentiment_label=None,
        sentiment_polarity=None,
    )
    monkeypatch.setattr(
        "yt_transcript.export_service.get_recent_analyses",
        lambda limit: [row],
    )

    result = ExportService().create_dashboard_data()
    assert result is not None
    assert result["summary"]["sentiment_distribution"] == {}
    assert result["trends"]["sentiment_over_time"] == []


def test_pdf_summary_without_compression_ratio(app, tmp_path, monkeypatch):
    analysis = SimpleNamespace(
        id=12,
        created_at=None,
        analysis_mode="style",
        video_url=None,
        text_length=20,
        total_words=3,
        unique_words=3,
        sentences=1,
        vocabulary_richness=100.0,
        reading_time_minutes=0.1,
        complexity_score=1.0,
        sentiment_polarity=None,
        flesch_reading_ease=None,
        summary_text="Résumé sans taux de compression.",
        summary_compression_ratio=None,
    )
    monkeypatch.setattr(
        "yt_transcript.pdf_export_service.get_analysis_by_id",
        lambda _id: analysis,
    )
    monkeypatch.setattr(
        PDFExportService,
        "create_metrics_chart",
        lambda self, _analysis: None,
    )

    with app.app_context():
        output = tmp_path / "summary-no-ratio.pdf"
        assert PDFExportService().export_analysis_to_pdf(12, str(output)) == str(output)


def test_start_ignores_health_response_from_wrong_instance(tmp_path, monkeypatch):
    terminated = {"value": False}

    class Child:
        pid = 4321
        returncode = None

        def poll(self):
            return None

        def terminate(self):
            terminated["value"] = True

        def wait(self, timeout=None):
            return 0

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    ticks = iter([0.0, 0.0, 31.0])

    monkeypatch.setattr(runtime, "managed_process", lambda directory: None)
    monkeypatch.setattr(
        runtime.socket,
        "create_connection",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError()),
    )
    monkeypatch.setattr(runtime.subprocess, "Popen", lambda *args, **kwargs: Child())
    monkeypatch.setattr(
        runtime.psutil,
        "Process",
        lambda pid: SimpleNamespace(create_time=lambda: 1.0),
    )
    monkeypatch.setattr(runtime, "urlopen", lambda *args, **kwargs: Response())
    monkeypatch.setattr(runtime.json, "load", lambda response: {"instance": "wrong-instance"})
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(ticks))

    with pytest.raises(RuntimeError, match="ne répond pas après 30 secondes"):
        runtime.start(tmp_path, "127.0.0.1", 5001)

    assert terminated["value"] is True


def test_auto_tags_handle_values_outside_predefined_ranges():
    analysis = SimpleNamespace(
        id=1,
        complexity_score=2.0,
        sentiment_polarity=2.0,
        total_words=1_000_000,
        flesch_reading_ease=101.0,
        analysis_mode="style",
        video_id=None,
        created_at=None,
    )

    tags = TagsService().auto_tag_analysis(analysis)
    assert tags == ["mode:style", "source:text"]


def test_youtube_host_with_unsupported_path_is_rejected():
    with pytest.raises(ValueError):
        extract_video_id("https://youtube.com/channel/foo")
