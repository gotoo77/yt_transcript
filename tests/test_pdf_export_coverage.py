"""Focused PDF export regression tests using isolated SQLite and temporary paths."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from yt_transcript.database import get_analysis_by_id, save_analysis
from yt_transcript.pdf_export_service import PDFExportService


@pytest.fixture
def pdf_record(app):
    with app.app_context():
        analysis_id = save_analysis(
            original_text="A short analysis of nature and science.",
            analysis_mode="style",
            results=[["science", 1]],
            statistics={
                "total_words": 7,
                "unique_words": 7,
                "sentences": 1,
                "vocabulary_richness": 100,
                "reading_time_minutes": 0.1,
                "complexity_score": 2,
            },
            sentiment_data={"polarity": 0.25, "subjectivity": 0.4, "label": "positive"},
            readability_metrics={"flesch_ease": 75, "flesch_kincaid": 5},
            summary_data={"text": "Short summary.", "compression_ratio": 40},
        )
        assert analysis_id is not None
        yield analysis_id


def test_pdf_with_optional_sections_and_explicit_output_path(app, pdf_record, tmp_path):
    with app.app_context():
        output = tmp_path / "report.pdf"
        result = PDFExportService().export_analysis_to_pdf(pdf_record, str(output))
        assert result == str(output)
        assert output.read_bytes().startswith(b"%PDF")
        text = " ".join(page.extract_text() for page in PdfReader(str(output)).pages)
        for label in ("Informations", "Analyse de sentiment", "Lisibilit", "Résumé automatique"):
            assert label in text


def test_pdf_still_exports_when_optional_charts_are_unavailable(
    app, pdf_record, tmp_path, monkeypatch
):
    service = PDFExportService()
    monkeypatch.setattr(service, "create_sentiment_chart", lambda analysis: None)
    monkeypatch.setattr(service, "create_metrics_chart", lambda analysis: None)
    with app.app_context():
        output = tmp_path / "no-charts.pdf"
        assert service.export_analysis_to_pdf(pdf_record, str(output)) == str(output)
        assert len(PdfReader(str(output)).pages) >= 1


def test_pdf_generation_failure_returns_none_without_creating_output(
    app, pdf_record, tmp_path, monkeypatch
):
    def fail_build(self, story):
        raise OSError("simulated output failure")

    monkeypatch.setattr("yt_transcript.pdf_export_service.SimpleDocTemplate.build", fail_build)
    with app.app_context():
        output = tmp_path / "unwritable.pdf"
        assert PDFExportService().export_analysis_to_pdf(pdf_record, str(output)) is None
        assert not output.exists()


@pytest.mark.parametrize("function", ["create_sentiment_chart", "create_metrics_chart"])
def test_chart_rendering_failure_is_handled(monkeypatch, function):
    def fail_figure(*args, **kwargs):
        raise RuntimeError("simulated chart error")

    monkeypatch.setattr("yt_transcript.pdf_export_service.Figure", fail_figure)
    analysis = SimpleNamespace(
        sentiment_polarity=0.1,
        sentiment_subjectivity=0.2,
        sentiment_label="positive",
        total_words=3,
        unique_words=2,
        sentences=1,
        vocabulary_richness=50,
        complexity_score=10,
        flesch_reading_ease=60,
    )
    assert getattr(PDFExportService(), function)(analysis) is None


@pytest.mark.parametrize("label", [None, "positive", "negative", "neutral", "unclassified"])
def test_sentiment_charts_are_valid_pngs_for_label_variants(label):
    analysis = SimpleNamespace(
        sentiment_polarity=0.1, sentiment_subjectivity=0.2, sentiment_label=label
    )
    chart = PDFExportService().create_sentiment_chart(analysis)
    assert chart is not None
    assert chart.getvalue().startswith(b"\\x89PNG")


def test_pdf_without_optional_fields_uses_fallbacks(app, tmp_path, monkeypatch):
    analysis = SimpleNamespace(
        id=11,
        created_at=None,
        analysis_mode="style",
        video_url=None,
        text_length=10,
        total_words=None,
        unique_words=None,
        sentences=None,
        vocabulary_richness=None,
        reading_time_minutes=None,
        complexity_score=None,
        sentiment_polarity=None,
        flesch_reading_ease=None,
        summary_text=None,
    )
    monkeypatch.setattr("yt_transcript.pdf_export_service.get_analysis_by_id", lambda _id: analysis)
    monkeypatch.setattr(PDFExportService, "create_metrics_chart", lambda self, _analysis: None)
    with app.app_context():
        output = tmp_path / "minimal.pdf"
        assert PDFExportService().export_analysis_to_pdf(11, str(output)) == str(output)
        assert "N/A" in " ".join(page.extract_text() for page in PdfReader(str(output)).pages)
