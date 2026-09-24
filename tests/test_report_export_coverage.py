"""Behavioral tests for dashboard report exports; no network or production database."""

from io import BytesIO

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from yt_transcript.report_export import ReportExportService


@pytest.fixture
def sample_dashboard():
    return {
        "kpis": {
            "period": {"start_date": "2026-09-01", "end_date": "2026-09-24"},
            "totals": {
                "analyses_period": 3,
                "analyses_ever": 7,
                "words_analyzed": 1250,
                "reading_time_hours": 1.5,
            },
            "averages": {
                "complexity_score": 0.45,
                "sentiment_polarity": 0.2,
                "analyses_per_day": 1.25,
            },
            "distributions": {
                "sentiment": {"positive": 2, "neutral": 1},
                "analysis_mode": {"style": 2, "concepts": 1},
            },
        },
        "trends": {
            "daily_analyses": [
                {"date": "2026-09-22", "count": 1},
                {"date": "2026-09-23", "count": 2},
            ]
        },
        "insights": {
            "content_metrics": {
                "avg_words_per_analysis": 100,
                "avg_unique_words": 80,
                "avg_vocabulary_richness": 0.75,
                "avg_complexity": 0.4,
                "avg_sentiment": 0.2,
            },
            "top_analyses": {
                "most_words": [{"id": 1, "words": 800}],
                "most_complex": [{"id": 2, "complexity": 0.9}],
                "richest_vocabulary": [{"id": 3, "richness": 0.8}],
            },
        },
    }


@pytest.fixture
def fake_dashboard(monkeypatch, sample_dashboard):
    calls = []

    def generate_comprehensive_dashboard(days):
        calls.append(days)
        return sample_dashboard

    monkeypatch.setattr(
        "yt_transcript.report_export.dashboard_service.generate_comprehensive_dashboard",
        generate_comprehensive_dashboard,
    )
    return calls


def test_full_dashboard_excel_contains_real_values(fake_dashboard):
    service = ReportExportService()
    buffer = service.generate_dashboard_report(days=14, format_type="EXCEL")
    assert buffer.getvalue().startswith(b"PK")
    assert fake_dashboard == [14]
    workbook = load_workbook(BytesIO(buffer.getvalue()), read_only=True)
    try:
        assert workbook.sheetnames == ["KPIs", "Tendances", "Insights"]
        assert workbook["KPIs"]["B3"].value == 3
        assert workbook["KPIs"]["B4"].value == 1250
        assert workbook["KPIs"]["B5"].value == 1.5
        assert workbook["Tendances"]["A4"].value == "2026-09-22"
        assert workbook["Tendances"]["B5"].value == 2
        assert workbook["Insights"]["B3"].value == 100
        assert workbook["Insights"]["B4"].value == 0.4
    finally:
        workbook.close()


def test_full_dashboard_pdf_contains_period_and_sections(fake_dashboard):
    buffer = ReportExportService().generate_dashboard_report(days=14, format_type="PDF")
    assert buffer.getvalue().startswith(b"%PDF")
    assert fake_dashboard == [14]
    reader = PdfReader(BytesIO(buffer.getvalue()))
    assert len(reader.pages) >= 1
    text = " ".join(page.extract_text() for page in reader.pages)
    for fragment in (
        "14 derniers jours",
        "2026-09-01",
        "Indicateurs",
        "Tendances",
        "Distributions",
        "Analyses Remarquables",
    ):
        assert fragment in text


@pytest.mark.parametrize("format_type", ["csv", "", "pdfx"])
def test_unsupported_report_formats_fail_explicitly(fake_dashboard, format_type):
    with pytest.raises(ValueError, match="Format non supporté"):
        ReportExportService().generate_dashboard_report(format_type=format_type)


@pytest.mark.parametrize("empty", [None, {}])
def test_missing_dashboard_data_fails_explicitly(monkeypatch, empty):
    monkeypatch.setattr(
        "yt_transcript.report_export.dashboard_service.generate_comprehensive_dashboard",
        lambda days: empty,
    )
    with pytest.raises(ValueError, match="Impossible de récupérer"):
        ReportExportService().generate_dashboard_report()


@pytest.mark.parametrize("format_type,signature", [("pdf", b"%PDF"), ("excel", b"PK")])
def test_empty_sections_still_produce_valid_documents(monkeypatch, format_type, signature):
    monkeypatch.setattr(
        "yt_transcript.report_export.dashboard_service.generate_comprehensive_dashboard",
        lambda days: {"kpis": {}, "trends": {}, "insights": {}},
    )
    payload = ReportExportService().generate_dashboard_report(format_type=format_type).getvalue()
    assert payload.startswith(signature)
    if format_type == "pdf":
        assert "Aucune donnée KPI" in " ".join(
            page.extract_text() for page in PdfReader(BytesIO(payload)).pages
        )
    else:
        workbook = load_workbook(BytesIO(payload), read_only=True)
        try:
            assert workbook.sheetnames == ["KPIs", "Tendances", "Insights"]
            assert workbook["KPIs"]["B3"].value is None
        finally:
            workbook.close()


def test_optional_report_sections_absent_are_not_invented(sample_dashboard):
    service = ReportExportService()
    sample_dashboard["kpis"].pop("averages")
    sample_dashboard["kpis"].pop("distributions")
    sample_dashboard["insights"].pop("top_analyses")
    pdf = service._generate_pdf_report(sample_dashboard, 7).getvalue()
    text = " ".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
    assert "Distributions" not in text
    assert "Analyses Remarquables" not in text


def test_excel_export_propagates_write_errors(monkeypatch, sample_dashboard):
    def fail_save(self, destination):
        raise OSError("simulated destination failure")

    monkeypatch.setattr("openpyxl.Workbook.save", fail_save)
    with pytest.raises(OSError, match="simulated destination failure"):
        ReportExportService()._generate_excel_report(sample_dashboard, 30)
