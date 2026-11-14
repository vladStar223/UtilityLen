"""Unit tests for the multimodal parser pipeline (JSON, PDF, and Vision)."""

import io
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.agent.parser import (
    DocumentParser,
    JsonBillParser,
    PdfBillParser,
    VisionBillParser,
)
from app.core.models import BillDocument


def _make_minimal_pdf(text_lines: list[str]) -> bytes:
    """Generate a minimal valid PDF containing the specified lines of text."""
    escaped_lines = []
    for idx, line in enumerate(text_lines):
        clean = line.replace("(", "\\(").replace(")", "\\)")
        escaped_lines.append(f"0 -18 Td ({clean}) Tj")

    content_stream = "BT\n/F1 12 Tf\n50 720 Td\n" + "\n".join(escaped_lines) + "\nET\n"
    stream_bytes = content_stream.encode("latin-1", errors="replace")

    pdf_body = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(len(stream_bytes)).encode("ascii") + b" >> stream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000227 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n500\n%%EOF"
    )
    return pdf_body


# =========================================================================
# 1. JsonBillParser Tests
# =========================================================================

def test_json_parser_case_01():
    """Verify parsing real fixture case_01_heating_spike."""
    bill_path = Path("data/cases/case_01_heating_spike/curr_bill.json")
    assert bill_path.exists(), f"Fixture missing: {bill_path}"

    raw_bytes = bill_path.read_bytes()
    doc = JsonBillParser.parse(raw_bytes)

    assert isinstance(doc, BillDocument)
    assert doc.bill_id == "bill_heat_2026_11"
    assert doc.period == "2026-11"
    assert doc.total_amount == 6900.00
    assert len(doc.services) == 1
    assert doc.services[0].service_code == "heating"
    assert doc.services[0].volume == 1.725
    assert doc.services[0].tariff == 4000.00


def test_json_parser_case_02():
    """Verify parsing multi-service fixture case_02_coeff_15."""
    bill_path = Path("data/cases/case_02_coeff_15/curr_bill.json")
    assert bill_path.exists(), f"Fixture missing: {bill_path}"

    raw_bytes = bill_path.read_bytes()
    doc = JsonBillParser.parse(raw_bytes)

    assert isinstance(doc, BillDocument)
    assert doc.bill_id == "bill_2026_11_001"
    assert doc.period == "2026-11"
    assert doc.total_amount == 6890.50
    assert len(doc.services) == 4


def test_json_parser_enveloped_structure():
    """Verify parser can unwrap envelopes like {'bill': {...}} or {'curr_bill': {...}}."""
    inner = {
        "bill_id": "bill-env-001",
        "period": "2026-12",
        "address": "г. Владивосток, ул. Океанская, д. 2",
        "total_amount": 1500.00,
        "services": [
            {
                "service_code": "cold_water",
                "raw_name": "Холодная вода",
                "unit": "м3",
                "volume": 30.0,
                "tariff": 50.00,
                "total": 1500.00,
            }
        ],
    }

    envelope_bill = json.dumps({"bill": inner}).encode("utf-8")
    doc1 = JsonBillParser.parse(envelope_bill)
    assert doc1.bill_id == "bill-env-001"
    assert doc1.total_amount == 1500.00

    envelope_curr = json.dumps({"curr_bill": inner}).encode("utf-8")
    doc2 = JsonBillParser.parse(envelope_curr)
    assert doc2.bill_id == "bill-env-001"


def test_json_parser_invalid_content():
    """Verify invalid JSON raises ValueError or json.JSONDecodeError."""
    with pytest.raises(Exception):
        JsonBillParser.parse(b"not json at all")

    with pytest.raises(ValueError, match="Expected a JSON object"):
        JsonBillParser.parse(b"[1, 2, 3]")


# =========================================================================
# 2. PdfBillParser Tests
# =========================================================================

def test_pdf_parser_synthetic_pdf():
    """Verify parsing a valid synthetic PDF with period, total, and service lines."""
    pdf_bytes = _make_minimal_pdf([
        "Address: Vladivostok, Svetlanskaya 10",
        "Period: 2026-10",
        "Total: 5400.00",
        "Heating: 2.0 2700.00 5400.00",
    ])

    doc = PdfBillParser.parse(pdf_bytes)

    assert isinstance(doc, BillDocument)
    assert doc.period == "2026-10"
    assert doc.total_amount == 5400.00
    assert len(doc.services) >= 1
    assert doc.services[0].service_code == "heating"
    assert doc.services[0].volume == 2.0
    assert doc.services[0].tariff == 2700.00
    assert doc.services[0].total == 5400.00


def test_pdf_parser_russian_receipt_text():
    """Verify regex heuristic extraction on full Russian utility receipt text."""
    sample_text = """
    ПЛАТЕЖНЫЙ ДОКУМЕНТ ЗА НОЯБРЬ 2026
    Адрес помещения: г. Владивосток, пр-кт 100-летия Владивостока, д. 12, кв. 44
    Плательщик: Сидоров С.С.
    
    Расчет размера платы за коммунальные услуги:
    Холодное водоснабжение: объем 10.0 м3, тариф 45.50, итого 455.00
    Горячее водоснабжение: объем 4.0 м3, тариф 210.00, итого 840.00
    Отопление: объем 1.2 Гкал, тариф 3000.00, итого 3600.00
    Электроэнергия: объем 200.0 кВтч, тариф 5.00, итого 1000.00
    Водоотведение: объем 14.0 м3, тариф 30.00, итого 420.00
    Содержание жилого помещения: объем 60.0 м2, тариф 35.00, итого 2100.00
    Обращение с ТКО: объем 2.0 чел, тариф 120.00, итого 240.00
    Взнос на капремонт: объем 60.0 м2, тариф 10.00, итого 600.00
    
    ИТОГО К ОПЛАТЕ: 9255.00 руб.
    """

    with patch.object(PdfBillParser, "_extract_text", return_value=sample_text):
        doc = PdfBillParser.parse(b"dummy pdf bytes")

    assert doc.period == "2026-11"
    assert "Владивосток" in doc.address
    assert doc.payer == "Сидоров С.С."
    assert doc.total_amount == 9255.00

    service_codes = {s.service_code for s in doc.services}
    assert "cold_water" in service_codes
    assert "hot_water" in service_codes
    assert "heating" in service_codes
    assert "electricity" in service_codes
    assert "drainage" in service_codes
    assert "maintenance" in service_codes
    assert "waste" in service_codes
    assert "capital_repairs" in service_codes


def test_pdf_parser_empty_pdf_fallback():
    """Verify completely empty or unparseable PDF falls back cleanly without crashing."""
    with patch.object(PdfBillParser, "_extract_text", return_value=""):
        doc = PdfBillParser.parse(b"dummy pdf bytes")

    assert isinstance(doc, BillDocument)
    assert doc.period == "2024-02"
    assert doc.address == "г. Владивосток"
    assert len(doc.services) >= 1
    assert doc.total_amount > 0


# =========================================================================
# 3. VisionBillParser Tests
# =========================================================================

@pytest.mark.anyio
async def test_vision_parser_fallback_when_no_api_key(monkeypatch):
    """Verify VisionBillParser returns safe fallback document when no API key is provided."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GPTUNNEL_API_KEY", raising=False)

    doc = await VisionBillParser.parse(b"fake image bytes", mime_type="image/jpeg")

    assert isinstance(doc, BillDocument)
    assert doc.bill_id.startswith("bill-img-")
    assert doc.period == "2024-02"
    assert doc.total_amount == 4520.75
    assert len(doc.services) == 3


@pytest.mark.anyio
async def test_vision_parser_mocked_llm_success(monkeypatch):
    """Verify VisionBillParser processes LLM response when API key is provided."""
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_API_URL", "https://api.test-llm.com/v1")

    mock_bill_json = {
        "bill_id": "bill-ocr-999",
        "period": "2026-05",
        "address": "г. Владивосток, ул. Фокина, д. 18",
        "payer": "Алексеев А.А.",
        "total_amount": 3200.00,
        "services": [
            {
                "service_code": "electricity",
                "raw_name": "Электроэнергия",
                "unit": "кВт·ч",
                "volume": 200.0,
                "tariff": 5.00,
                "total": 1000.00,
            },
            {
                "service_code": "heating",
                "raw_name": "Отопление",
                "unit": "Гкал",
                "volume": 1.0,
                "tariff": 2200.00,
                "total": 2200.00,
            },
        ],
    }

    # Simulate response wrapped in markdown block
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": f"```json\n{json.dumps(mock_bill_json)}\n```"
                }
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=response_payload,
        request=httpx.Request("POST", "https://api.test-llm.com/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        doc = await VisionBillParser.parse(b"fake image bytes", mime_type="image/png")

    assert isinstance(doc, BillDocument)
    assert doc.bill_id == "bill-ocr-999"
    assert doc.period == "2026-05"
    assert doc.total_amount == 3200.00
    assert len(doc.services) == 2


@pytest.mark.anyio
async def test_vision_parser_api_error_graceful_fallback(monkeypatch):
    """Verify VisionBillParser gracefully falls back on HTTP errors or network timeouts."""
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        doc = await VisionBillParser.parse(b"fake image bytes", mime_type="image/jpeg")

    assert isinstance(doc, BillDocument)
    assert doc.bill_id.startswith("bill-img-")
    assert doc.total_amount == 4520.75


# =========================================================================
# 4. DocumentParser Routing & Error Tests
# =========================================================================

@pytest.mark.anyio
async def test_document_parser_route_json():
    """Verify DocumentParser routes .json to JsonBillParser."""
    bill_path = Path("data/cases/case_01_heating_spike/curr_bill.json")
    doc = await DocumentParser.parse_file(bill_path.read_bytes(), "receipt.json")
    assert doc.bill_id == "bill_heat_2026_11"


@pytest.mark.anyio
async def test_document_parser_route_pdf():
    """Verify DocumentParser routes .pdf to PdfBillParser."""
    pdf_bytes = _make_minimal_pdf(["Period: 2026-03", "Total: 1000.00"])
    doc = await DocumentParser.parse_file(pdf_bytes, "receipt.pdf")
    assert doc.period == "2026-03"


@pytest.mark.anyio
async def test_document_parser_route_image(monkeypatch):
    """Verify DocumentParser routes .png and .jpg to VisionBillParser."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GPTUNNEL_API_KEY", raising=False)

    doc_png = await DocumentParser.parse_file(b"dummy png", "bill.png")
    assert doc_png.bill_id.startswith("bill-img-")

    doc_jpg = await DocumentParser.parse_file(b"dummy jpg", "bill.jpg")
    assert doc_jpg.bill_id.startswith("bill-img-")

    doc_mime = await DocumentParser.parse_file(b"dummy bytes", "bill_no_ext", mime_type="image/jpeg")
    assert doc_mime.bill_id.startswith("bill-img-")


@pytest.mark.anyio
async def test_document_parser_unsupported_format():
    """Verify unsupported file extension raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported file format: statement.docx"):
        await DocumentParser.parse_file(b"content", "statement.docx")

    with pytest.raises(ValueError, match="Unsupported file format: archive.zip"):
        await DocumentParser.parse_file(b"content", "archive.zip")


@pytest.mark.anyio
async def test_document_parser_rejects_non_utility_pdf():
    """Verify PDF with non-utility content is rejected with helpful error."""
    resume_text = "Резюме разработчика Python. Опыт работы в IT 5 лет. Навыки: Docker, Kubernetes, Linux."
    with patch.object(PdfBillParser, "_extract_text", return_value=resume_text):
        with pytest.raises(ValueError, match="не является квитанцией ЖКХ"):
            await DocumentParser.parse_file(b"dummy pdf bytes", "resume.pdf")


@pytest.mark.anyio
async def test_document_parser_rejects_non_utility_json():
    """Verify JSON with arbitrary data is rejected."""
    arbitrary_json = json.dumps({"user": "john", "city": "Vladivostok"}).encode("utf-8")
    with pytest.raises(ValueError, match="не является квитанцией ЖКХ"):
        await DocumentParser.parse_file(arbitrary_json, "data.json")


@pytest.mark.anyio
async def test_vision_parser_rejects_non_utility_image():
    """Verify Vision LLM response with is_utility_bill=False raises ValueError."""
    from app.agent.file_agent import BillAnalysisAgent

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "is_utility_bill": False,
                        "error": "На фото кот, а не квитанция ЖКХ."
                    })
                }
            }
        ]
    }

    with patch.object(BillAnalysisAgent, "_get_api_credentials", return_value=("fake_key", "http://fake/v1/chat/completions", "model")):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            with pytest.raises(ValueError, match="На фото кот, а не квитанция ЖКХ"):
                await BillAnalysisAgent.analyze_document(b"fake image", "cat.png", "image/png")
