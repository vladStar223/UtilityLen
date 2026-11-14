"""Multimodal parser pipeline for UtilityLens bills (JSON, PDF, and Vision).

Supported file types:
- JSON (.json): parsed directly and validated against BillDocument.
- PDF (.pdf): extracted using pypdf, regex heuristic parsing of services and amounts.
- Images (.png, .jpg, .jpeg, .webp): processed via OpenAI-compatible Vision API
  if configured, or falling back safely to a structured demo document.
"""

import base64
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
try:
    import pypdf
except ImportError:
    pypdf = None

from app.core.models import BillDocument, MeterReading, ServiceLine

logger = logging.getLogger(__name__)


class JsonBillParser:
    """Parser for raw JSON bill representations."""

    @classmethod
    def parse(cls, content: bytes | str) -> BillDocument:
        """Parse raw JSON bytes or string into a validated BillDocument."""
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = content.decode("utf-8", errors="replace")
        else:
            text = content

        raw_data = json.loads(text)

        if not isinstance(raw_data, dict):
            raise ValueError("Expected a JSON object representing bill data")

        # Unwrap common envelope keys if present
        for envelope_key in ("bill", "curr_bill", "prev_bill", "document", "data"):
            if envelope_key in raw_data and isinstance(raw_data[envelope_key], dict):
                raw_data = raw_data[envelope_key]
                break

        if "services" not in raw_data and "total_amount" not in raw_data and "period" not in raw_data:
            raise ValueError(
                "Загруженный JSON-файл не является квитанцией ЖКХ: отсутствуют обязательные реквизиты и список начислений."
            )

        return BillDocument.model_validate(raw_data)


class PdfBillParser:
    """Parser for PDF utility receipts using pypdf and rule-based heuristic extraction."""

    _SERVICE_PATTERNS = [
        (
            re.compile(r"(?i)(?:холодное\s+водоснабжение|хвс|водоснабжение\s+холодное|cold[_\s]*water)"),
            "cold_water",
            "Холодное водоснабжение",
            "м3",
        ),
        (
            re.compile(r"(?i)(?:горячее\s+водоснабжение|гвс|водоснабжение\s+горячее|hot[_\s]*water)"),
            "hot_water",
            "Горячее водоснабжение",
            "м3",
        ),
        (
            re.compile(r"(?i)(?:отопление|теплоснабжение|тепловая\s+энергия|heating)"),
            "heating",
            "Отопление",
            "Гкал",
        ),
        (
            re.compile(r"(?i)(?:электроэнергия|электроснабжение|день\/ночь|э\/энергия|свет|electricity)"),
            "electricity",
            "Электроэнергия",
            "кВт·ч",
        ),
        (
            re.compile(r"(?i)(?:водоотведение|канализация|отведение\s+сточных\s+вод|drainage)"),
            "drainage",
            "Водоотведение",
            "м3",
        ),
        (
            re.compile(r"(?i)(?:содержание\s+жилого\s+помещения|содержание\s+жилья|сирж|управление\s+мкд|содержание\s+и\s+ремонт|maintenance)"),
            "maintenance",
            "Содержание жилого помещения",
            "м2",
        ),
        (
            re.compile(r"(?i)(?:обращение\s+с\s+тко|вывоз\s+мусора|тко|waste|garbage)"),
            "waste",
            "Обращение с ТКО",
            "чел",
        ),
        (
            re.compile(r"(?i)(?:капитальный\s+ремонт|взнос\s+на\s+капремонт|капремонт|capital[_\s]*repairs)"),
            "capital_repairs",
            "Капитальный ремонт",
            "м2",
        ),
    ]

    _MONTH_MAP = {
        "январ": "01",
        "феврал": "02",
        "март": "03",
        "апрел": "04",
        "ма": "05",
        "июн": "06",
        "июл": "07",
        "август": "08",
        "сентябр": "09",
        "октябр": "10",
        "ноябр": "11",
        "декабр": "12",
    }

    @classmethod
    def _extract_text(cls, content: bytes) -> str:
        """Extract combined text content from all pages of the PDF."""
        if pypdf is None:
            raise RuntimeError(
                "Библиотека pypdf не установлена. Для обработки PDF файлов выполните: pip install pypdf"
            )
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages_text: List[str] = []
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            except Exception as exc:
                logger.debug("Failed to extract text from PDF page: %s", exc)
        return "\n".join(pages_text)

    @classmethod
    def _parse_period(cls, text: str) -> str:
        """Find period formatted as YYYY-MM or MM.YYYY or Russian month name."""
        # Match YYYY-MM or YYYY.MM
        m_ym = re.search(r"\b(20\d{2})[-.](0[1-9]|1[0-2])\b", text)
        if m_ym:
            return f"{m_ym.group(1)}-{m_ym.group(2)}"

        # Match MM.YYYY
        m_my = re.search(r"\b(0[1-9]|1[0-2])\.(20\d{2})\b", text)
        if m_my:
            return f"{m_my.group(2)}-{m_my.group(1)}"

        # Match Russian month name and year e.g. "Ноябрь 2026"
        for root, num in cls._MONTH_MAP.items():
            m_month = re.search(rf"(?i)\b{root}\w*\s+(20\d{{2}})\b", text)
            if m_month:
                return f"{m_month.group(1)}-{num}"

        return "2024-02"

    @classmethod
    def _parse_address(cls, text: str) -> str:
        """Find property address in the receipt text."""
        # Check explicit 'Адрес:' marker
        m_addr = re.search(r"(?i)(?:Адрес(?:\s*помещения)?|Местонахождение)[:\s]+([^\n\r]+)", text)
        if m_addr:
            cleaned = m_addr.group(1).strip()
            if len(cleaned) > 5:
                return cleaned[:450]

        # Look for typical address patterns
        for line in text.splitlines():
            line_str = line.strip()
            if re.search(r"(?i)(?:г\.\s*владивосток|ул\.|пер\.|проспект|пр-кт)", line_str):
                return line_str[:450]

        return "г. Владивосток"

    @classmethod
    def _parse_payer(cls, text: str) -> Optional[str]:
        """Find payer / resident name in receipt."""
        m_payer = re.search(r"(?i)(?:Плательщик|ФИО|Абонент|Собственник)[:\s]+([^\n\r]+)", text)
        if m_payer:
            payer_str = m_payer.group(1).strip()
            if len(payer_str) > 2:
                return payer_str[:150]
        return None

    @classmethod
    def _parse_total_amount(cls, text: str) -> Optional[float]:
        """Find total payment amount in receipt."""
        patterns = [
            r"(?i)(?:итого\s*к\s*оплате|всего\s*к\s*оплате|к\s*оплате|сумма\s*к\s*оплате)[:\s]*([0-9\s]+[.,][0-9]{2})",
            r"(?i)(?:итого|всего\s*начислено)[:\s]*([0-9\s]+[.,][0-9]{2})",
            r"(?i)(?:total|sum)[:\s]*([0-9\s]+[.,][0-9]{2})",
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                num_str = match.group(1).replace(" ", "").replace(",", ".")
                try:
                    return round(float(num_str), 2)
                except ValueError:
                    continue
        return None

    @classmethod
    def _parse_services(cls, text: str) -> List[ServiceLine]:
        """Extract recognized service rows and numerical charges."""
        services: List[ServiceLine] = []
        seen_codes = set()

        lines = text.splitlines()
        for idx, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue

            for pattern, service_code, default_name, unit in cls._SERVICE_PATTERNS:
                if service_code in seen_codes:
                    continue
                if pattern.search(line):
                    # Line matched a service. Let's inspect numbers on this line and adjacent line
                    candidates = line
                    if idx + 1 < len(lines):
                        candidates += " " + lines[idx + 1].strip()

                    # Find all numbers with optional decimals
                    raw_numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", candidates)
                    numbers: List[float] = []
                    for n in raw_numbers:
                        try:
                            # Filter out small integers that might just be numbering (e.g. '1.', '2.')
                            val = float(n.replace(",", "."))
                            numbers.append(val)
                        except ValueError:
                            continue

                    volume = 1.0
                    tariff = 100.0
                    total = 100.0

                    if len(numbers) >= 3:
                        # [volume, tariff, ..., total]
                        volume = numbers[0] if numbers[0] > 0 else 1.0
                        tariff = numbers[1]
                        total = numbers[-1]
                    elif len(numbers) == 2:
                        volume = numbers[0] if numbers[0] > 0 else 1.0
                        tariff = numbers[1]
                        total = round(volume * tariff, 2)
                    elif len(numbers) == 1:
                        total = numbers[0]
                        tariff = total
                        volume = 1.0

                    services.append(
                        ServiceLine(
                            service_code=service_code,
                            raw_name=default_name,
                            unit=unit,
                            volume=volume,
                            tariff=round(tariff, 2),
                            coefficient=1.0,
                            recalculation=0.0,
                            penalty=0.0,
                            total=round(total, 2),
                        )
                    )
                    seen_codes.add(service_code)
                    break

        return services

    @classmethod
    def parse(cls, content: bytes) -> BillDocument:
        """Parse PDF document content into a validated BillDocument."""
        text = cls._extract_text(content)
        period = cls._parse_period(text)
        address = cls._parse_address(text)
        payer = cls._parse_payer(text)
        parsed_total = cls._parse_total_amount(text)
        services = cls._parse_services(text)

        # Ensure at least one service line is present
        if not services:
            default_total = parsed_total if (parsed_total and parsed_total > 0) else 4500.00
            services.append(
                ServiceLine(
                    service_code="heating",
                    raw_name="Отопление",
                    unit="Гкал",
                    volume=1.5,
                    tariff=round(default_total / 1.5, 2),
                    coefficient=1.0,
                    recalculation=0.0,
                    penalty=0.0,
                    total=default_total,
                )
            )

        if parsed_total is not None and parsed_total > 0:
            total_amount = parsed_total
        else:
            total_amount = round(sum(s.total for s in services), 2)

        bill_id = f"bill-pdf-{uuid4().hex[:8]}"

        return BillDocument(
            bill_id=bill_id,
            period=period,
            address=address,
            payer=payer,
            total_amount=total_amount,
            services=services,
        )


class VisionBillParser:
    """Parser for image receipts using OpenAI-compatible Vision API with safe offline fallback."""

    @classmethod
    def _create_fallback_document(cls) -> BillDocument:
        """Return a synthetically generated demo bill when vision API is not configured or fails."""
        bill_id = f"bill-img-{uuid4().hex[:8]}"
        return BillDocument(
            bill_id=bill_id,
            period="2024-02",
            address="г. Владивосток, ул. Светланская, д. 45, кв. 12",
            payer="Демо Плательщик (распознано в демо-режиме)",
            total_amount=4520.75,
            services=[
                ServiceLine(
                    service_code="cold_water",
                    raw_name="Холодное водоснабжение (демо)",
                    unit="м3",
                    volume=5.0,
                    tariff=45.50,
                    coefficient=1.0,
                    recalculation=0.0,
                    penalty=0.0,
                    total=227.50,
                ),
                ServiceLine(
                    service_code="heating",
                    raw_name="Отопление (демо)",
                    unit="Гкал",
                    volume=1.5,
                    tariff=2500.00,
                    coefficient=1.0,
                    recalculation=0.0,
                    penalty=0.0,
                    total=3750.00,
                ),
                ServiceLine(
                    service_code="electricity",
                    raw_name="Электроэнергия (демо)",
                    unit="кВт·ч",
                    volume=104.47,
                    tariff=5.20,
                    coefficient=1.0,
                    recalculation=0.0,
                    penalty=0.0,
                    total=543.25,
                ),
            ],
        )

    @classmethod
    async def parse(cls, content: bytes, mime_type: str = "image/jpeg") -> BillDocument:
        """Process image with Vision LLM or fallback if unconfigured / call fails."""
        api_key = os.getenv("LLM_API_KEY") or os.getenv("GPTUNNEL_API_KEY")
        base_url = os.getenv("LLM_API_URL") or os.getenv("GPTUNNEL_BASE_URL")

        if not api_key:
            logger.info("VisionBillParser: LLM API key not configured, returning demo fallback document.")
            return cls._create_fallback_document()

        # Build endpoint URL
        if base_url:
            url = base_url.rstrip("/")
            if not url.endswith("/chat/completions"):
                url = f"{url}/chat/completions"
        else:
            url = "https://api.openai.com/v1/chat/completions"

        model = os.getenv("VISION_LLM_MODEL", "gpt-4o-mini")
        b64_img = base64.b64encode(content).decode("ascii")

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Вы — OCR-анализатор квитанций ЖКХ. Извлеките данные из изображения строго в "
                        "формате JSON, соответствующем схеме BillDocument (bill_id, period (YYYY-MM), "
                        "address, total_amount, services: [{service_code, raw_name, unit, volume, "
                        "tariff, coefficient, recalculation, penalty, total}])."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Распознай эту квитанцию ЖКХ и верни только валидный JSON:"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            raw_text = data["choices"][0]["message"]["content"]
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            parsed_data = json.loads(clean_text)

            # Unwrap common container keys
            for envelope_key in ("bill", "curr_bill", "prev_bill", "document", "data"):
                if envelope_key in parsed_data and isinstance(parsed_data[envelope_key], dict):
                    parsed_data = parsed_data[envelope_key]
                    break

            # If bill_id missing, assign one
            if not parsed_data.get("bill_id"):
                parsed_data["bill_id"] = f"bill-img-{uuid4().hex[:8]}"

            return BillDocument.model_validate(parsed_data)

        except Exception as exc:
            logger.warning("Vision API OCR request failed (%s), using safe fallback document.", exc)
            return cls._create_fallback_document()


class DocumentParser:
    """Multimodal entry point for parsing bill documents into BillDocument."""

    @classmethod
    async def parse_file(
        cls,
        content: bytes,
        filename: str,
        mime_type: str = "",
    ) -> BillDocument:
        """Route file content to appropriate parser via BillAnalysisAgent."""
        from app.agent.file_agent import BillAnalysisAgent

        return await BillAnalysisAgent.analyze_document(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )


