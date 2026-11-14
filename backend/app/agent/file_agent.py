"""AI-Agent for intelligent utility bill analysis and multimodal parsing.

Acts as a professional housing and utility (ЖКХ) financial auditor:
- Accepts PDF, images (PNG, JPG, JPEG, WEBP), and JSON formats.
- Extracts structured receipt data conforming to the BillDocument domain schema.
- Provides robust, graceful fallback to deterministic local parsers when LLM API keys
  are missing or external API calls time out/fail.
"""

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx

from app.agent.parser import JsonBillParser, PdfBillParser, VisionBillParser
from app.core.config import settings
from app.core.models import BillDocument, ServiceLine

logger = logging.getLogger(__name__)

AUDITOR_SYSTEM_PROMPT = """Вы — профессиональный финансовый аудитор в сфере жилищно-коммунального хозяйства (ЖКХ) Российской Федерации.
Ваша задача — провести детальный финансовый аудит квитанции/счета за коммунальные услуги и безошибочно извлечь структурированные данные.

Извлеките данные строго в формате JSON, соответствующем следующей схеме:
{
  "bill_id": "строковый идентификатор (из квитанции или bill-YYYY-MM-XXXX)",
  "period": "расчетный период строго в формате YYYY-MM (например, 2024-02)",
  "address": "полный адрес жилого помещения (город, улица, номер дома, квартира)",
  "payer": "ФИО плательщика/собственника или null",
  "total_amount": итоговая сумма к оплате в рублях (число с плавающей точкой, 2 знака),
  "services": [
    {
      "service_code": "код услуги: cold_water, hot_water, heating, electricity, drainage, maintenance, waste, capital_repairs или other",
      "raw_name": "исходное наименование услуги из квитанции",
      "unit": "единица измерения (м3, Гкал, кВт·ч, м2, чел, шт)",
      "volume": объем потребления (число),
      "tariff": тариф за единицу в рублях (число),
      "coefficient": повышающий коэффициент (число, обычно 1.0),
      "recalculation": сумма перерасчета в рублях (число, 0.0 если нет),
      "penalty": пени/штрафы в рублях (число, 0.0 если нет),
      "total": итоговая сумма начисления по услуге в рублях (число)
    }
  ],
  "meters": []
}

Правила классификации услуг (service_code):
- Холодное водоснабжение / ХВС / питьевая вода -> cold_water
- Горячее водоснабжение / ГВС / подогрев воды -> hot_water
- Отопление / Теплоснабжение / тепловая энергия -> heating
- Электроснабжение / электроэнергия / день-ночь -> electricity
- Водоотведение / канализация / сточные воды -> drainage
- Содержание жилья / управление МКД / СиРЖ -> maintenance
- Обращение с ТКО / вывоз мусора / ТБО -> waste
- Взнос на капитальный ремонт / капремонт -> capital_repairs
- Прочие услуги -> other

Важные требования:
1. Период строго YYYY-MM. Если указан месяц словом (например, 'Декабрь 2024'), переведите в '2024-12'.
2. Суммы и объемы должны быть числами (float). Разделитель — точка.
3. total_amount должен соответствовать общей сумме к оплате за расчетный период.
4. Ответ должен быть ИСКЛЮЧИТЕЛЬНО валидным JSON-объектом, без markdown-разметки (без ```json), без вводных и заключительных фраз.
5. КРИТИЧЕСКИ ВАЖНО: Если переданный документ или изображение НЕ является квитанцией, счетом или платежным документом за коммунальные/жилищные услуги ЖКХ (например: фото животного, чек из магазина/кафе, резюме, договор, мем, пейзаж):
   Верните строго следующий JSON:
   {
     "is_utility_bill": false,
     "error": "Загруженный документ не является квитанцией ЖКХ. Пожалуйста, загрузите квитанцию или счет за коммунальные услуги."
   }
"""

_UTILITY_KEYWORDS = [
    "квитанция", "епд", "платежный документ", "лицевой счет", "начислено",
    "к оплате", "коммунальн", "жилищн", "хвс", "гвс", "отопление", "электроэнерг",
    "водоотведен", "сирж", "тко", "капремонт", "показания", "ипу", "водоснабжение",
    "теплоснабжение", "содержание жилья", "управляющая компания"
]


def _is_likely_utility_text(text: str) -> bool:
    """Return True if text contains common utility bill markers or service keywords."""
    if not text:
        return False
    lowered = text.lower()
    matches = sum(1 for kw in _UTILITY_KEYWORDS if kw in lowered)
    return matches >= 2


def _clean_json_markdown(text: str) -> str:
    """Strip markdown code block fences and whitespace from model response, extracting pure JSON."""
    clean = text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()
    first_brace = clean.find("{")
    last_brace = clean.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        clean = clean[first_brace : last_brace + 1]
    return clean.strip()


def _unwrap_envelope(data: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap common nested wrapper keys from JSON response."""
    for envelope_key in ("bill", "curr_bill", "prev_bill", "document", "data", "result"):
        if envelope_key in data and isinstance(data[envelope_key], dict):
            return data[envelope_key]
    return data


class BillAnalysisAgent:
    """Autonomous AI-agent for utility bill document understanding.

    Orchestrates parsing of PDF, images, and JSON receipts using LLM with
    an auditor persona and automatic deterministic fallback.
    """

    @classmethod
    def _get_api_credentials(cls) -> tuple[Optional[str], str, str]:
        """Resolve LLM API key, endpoint URL, and model name."""
        api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("GPTUNNEL_API_KEY")
            or getattr(settings, "GPTUNNEL_API_KEY", "")
        )
        base_url = (
            os.getenv("LLM_API_URL")
            or os.getenv("GPTUNNEL_BASE_URL")
            or getattr(settings, "GPTUNNEL_BASE_URL", "https://gptunnel.ru/v1")
        )

        url = base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        model = (
            os.getenv("LLM_MODEL")
            or getattr(settings, "LLM_MODEL", "gpt-4o-mini")
        )
        return api_key if api_key else None, url, model

    @classmethod
    async def _call_llm_text(cls, text_content: str) -> Optional[BillDocument]:
        """Call text LLM with extracted receipt text and parse result into BillDocument."""
        api_key, url, model = cls._get_api_credentials()
        if not api_key:
            return None

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": AUDITOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Проведи аудит следующей квитанции ЖКХ и верни структурированный JSON:\n\n{text_content}",
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        timeout = float(os.getenv("LLM_TIMEOUT_S", "45.0"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 400 and "response_format" in payload:
                # Retry without strict json_object for models that do not support it (e.g. DeepSeek on GPTunnel)
                payload.pop("response_format", None)
                resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        cleaned = _clean_json_markdown(content)
        parsed = json.loads(cleaned)
        unwrapped = _unwrap_envelope(parsed)

        if unwrapped.get("is_utility_bill") is False:
            raise ValueError(
                unwrapped.get("error")
                or "Загруженный документ не является квитанцией ЖКХ. Пожалуйста, загрузите квитанцию или счет за коммунальные услуги."
            )

        if not unwrapped.get("bill_id"):
            unwrapped["bill_id"] = f"bill-ai-{uuid4().hex[:8]}"

        return BillDocument.model_validate(unwrapped)

    @classmethod
    async def _call_llm_vision(cls, image_bytes: bytes, mime_type: str) -> Optional[BillDocument]:
        """Call multimodal vision LLM to inspect bill image."""
        api_key, url, model = cls._get_api_credentials()
        if not api_key:
            return None

        vision_model = os.getenv("VISION_LLM_MODEL") or model or "gpt-4o-mini"
        b64_img = base64.b64encode(image_bytes).decode("ascii")

        payload = {
            "model": vision_model,
            "messages": [
                {"role": "system", "content": AUDITOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Распознай эту квитанцию ЖКХ как финансовый аудитор и верни валидный JSON:",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
                        },
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        timeout = float(os.getenv("LLM_TIMEOUT_S", "45.0"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 400 and "response_format" in payload:
                # Retry without strict json_object for models that do not support it
                payload.pop("response_format", None)
                resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        cleaned = _clean_json_markdown(content)
        parsed = json.loads(cleaned)
        unwrapped = _unwrap_envelope(parsed)

        if unwrapped.get("is_utility_bill") is False:
            raise ValueError(
                unwrapped.get("error")
                or "Загруженное изображение не является квитанцией ЖКХ. Пожалуйста, сфотографируйте квитанцию так, чтобы была видна таблица начислений."
            )

        if not unwrapped.get("bill_id"):
            unwrapped["bill_id"] = f"bill-vision-{uuid4().hex[:8]}"

        return BillDocument.model_validate(unwrapped)

    @classmethod
    async def analyze_document(
        cls,
        content: bytes,
        filename: str,
        mime_type: str = "",
    ) -> BillDocument:
        """Main entry point: analyze utility receipt document of any supported format.

        - JSON: parsed and validated directly.
        - PDF: text extracted and audited by LLM, with fallback to deterministic heuristic parser.
        - Image: inspected via Vision LLM, with fallback to structured demo document.
        """
        ext = Path(filename).suffix.lower()
        m_type = (mime_type or "").lower()

        # 1. JSON bills
        if ext == ".json" or m_type == "application/json":
            return JsonBillParser.parse(content)

        # 2. PDF bills
        if ext == ".pdf" or m_type == "application/pdf":
            # Extract text first
            extracted_text = ""
            try:
                extracted_text = PdfBillParser._extract_text(content)
            except Exception as exc:
                logger.warning("PDF text extraction note: %s", exc)

            # Check if extracted text represents a utility receipt
            if extracted_text and len(extracted_text.strip()) > 30:
                has_service = any(pat[0].search(extracted_text) for pat in PdfBillParser._SERVICE_PATTERNS)
                has_utility_kw = _is_likely_utility_text(extracted_text)
                if not (has_service or has_utility_kw):
                    raise ValueError(
                        "Загруженный PDF-документ не является квитанцией ЖКХ. "
                        "В файле не найдены коммунальные начисления (ХВС, ГВС, отопление, свет и др.) или реквизиты платежа."
                    )

                # Try LLM text audit if text was extracted
                try:
                    llm_doc = await cls._call_llm_text(extracted_text)
                    if llm_doc is not None and llm_doc.services:
                        logger.info("PDF successfully parsed and audited via LLM agent.")
                        return llm_doc
                except ValueError:
                    raise
                except Exception as exc:
                    logger.warning(
                        "LLM agent PDF analysis failed (%s), falling back to deterministic parser.",
                        exc,
                    )

            # Deterministic heuristic fallback
            logger.info("Using deterministic PdfBillParser fallback for PDF document.")
            return PdfBillParser.parse(content)

        # 3. Image bills (PNG, JPG, JPEG, WEBP)
        if ext in {".png", ".jpg", ".jpeg", ".webp"} or m_type.startswith("image/"):
            api_key, _, _ = cls._get_api_credentials()
            if not api_key:
                raise ValueError(
                    "Мультимодальное распознавание изображений (Vision OCR) недоступно: "
                    "на сервере не настроен API-ключ нейросети (GPTUNNEL_API_KEY). "
                    "Пожалуйста, загрузите квитанцию в формате PDF или JSON, либо укажите API-ключ в .env."
                )

            if m_type.startswith("image/"):
                img_mime = m_type
            else:
                clean_ext = ext.lstrip(".").replace("jpg", "jpeg")
                img_mime = f"image/{clean_ext}"

            try:
                vision_doc = await cls._call_llm_vision(content, mime_type=img_mime)
                if vision_doc is not None and vision_doc.services:
                    logger.info("Image bill successfully parsed via Vision LLM agent.")
                    return vision_doc
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Vision LLM agent failed (%s)", exc)
                raise ValueError(
                    f"Сервис распознавания изображений (Vision LLM) временно недоступен: {exc}. "
                    "Пожалуйста, повторите попытку позже или загрузите квитанцию в формате PDF."
                )

            raise ValueError("Не удалось извлечь данные из изображения квитанции через Vision OCR.")

        raise ValueError(f"Unsupported file format: {filename}")
