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
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from app.agent.parser import JsonBillParser, PdfBillParser, VisionBillParser
from app.core.config import settings
from app.core.logging import logger
from app.core.models import BillDocument, ServiceLine

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


def _unwrap_envelope(data: Any) -> Dict[str, Any]:
    """Unwrap common nested wrapper keys from JSON response."""
    if not isinstance(data, dict):
        return {}
    if "services" in data or "total_amount" in data or "period" in data:
        return data
    for envelope_key in (
        "bill", "curr_bill", "prev_bill", "document", "data", "result",
        "receipt", "invoice", "utility_bill", "bill_document", "output", "response"
    ):
        if envelope_key in data and isinstance(data[envelope_key], dict):
            nested = data[envelope_key]
            if any(k in nested for k in ("services", "total_amount", "period", "address")):
                return nested
    for v in data.values():
        if isinstance(v, dict) and any(k in v for k in ("services", "total_amount", "period")):
            return v
    return data


def _normalize_bill_dict(data: Any) -> Dict[str, Any]:
    """Sanitize and normalize raw dictionary into a valid BillDocument payload."""
    if not isinstance(data, dict):
        raise ValueError("Модель вернула некорректный ответ (не словарь JSON).")

    is_utility = data.get("is_utility_bill")
    if is_utility in (False, "false", "False", "0", 0) or str(is_utility).lower() == "false":
        err = data.get("error") or "Загруженное изображение не является квитанцией ЖКХ."
        raise ValueError(err)

    unwrapped = _unwrap_envelope(data)

    is_utility = unwrapped.get("is_utility_bill")
    if is_utility in (False, "false", "False", "0", 0) or str(is_utility).lower() == "false":
        err = unwrapped.get("error") or "Загруженное изображение не является квитанцией ЖКХ."
        raise ValueError(err)

    key_mapping = {
        "период": "period",
        "расчетный_период": "period",
        "billing_period": "period",
        "month": "period",
        "адрес": "address",
        "город_улица_дом": "address",
        "итого": "total_amount",
        "сумма": "total_amount",
        "к_оплате": "total_amount",
        "начислено": "total_amount",
        "total": "total_amount",
        "amount": "total_amount",
        "услуги": "services",
        "начисления": "services",
        "service_lines": "services",
        "lines": "services",
        "items": "services",
        "поставщик": "provider_name",
        "ук": "provider_name",
        "организация": "provider_name",
        "лицевой_счет": "personal_account",
        "лс": "personal_account",
        "account": "personal_account",
        "account_number": "personal_account",
    }
    for alt_key, standard_key in key_mapping.items():
        if alt_key in unwrapped and standard_key not in unwrapped:
            unwrapped[standard_key] = unwrapped[alt_key]

    raw_services = unwrapped.get("services")
    if not isinstance(raw_services, list):
        raw_services = []

    clean_services = []
    for s in raw_services:
        if not isinstance(s, dict):
            continue
        s_code = s.get("service_code") or s.get("code") or "other"
        s_name = s.get("raw_name") or s.get("name") or s.get("display_name") or s.get("наименование") or str(s_code)
        s_unit = s.get("unit") or s.get("единица") or "руб"
        try:
            s_vol = float(s.get("volume") or s.get("объем") or 1.0)
        except (ValueError, TypeError):
            s_vol = 1.0
        try:
            s_tar = float(s.get("tariff") or s.get("тариф") or 0.0)
        except (ValueError, TypeError):
            s_tar = 0.0
        try:
            s_tot = float(s.get("total") or s.get("итого") or s.get("сумма") or (s_vol * s_tar if s_tar > 0 else 0.0))
        except (ValueError, TypeError):
            s_tot = 0.0
        try:
            s_coeff = float(s.get("coefficient") or s.get("коэффициент") or 1.0)
        except (ValueError, TypeError):
            s_coeff = 1.0
        try:
            s_recalc = float(s.get("recalculation") or s.get("перерасчет") or 0.0)
        except (ValueError, TypeError):
            s_recalc = 0.0
        try:
            s_penalty = float(s.get("penalty") or s.get("пени") or 0.0)
        except (ValueError, TypeError):
            s_penalty = 0.0

        clean_services.append({
            "service_code": str(s_code),
            "raw_name": str(s_name),
            "unit": str(s_unit),
            "volume": s_vol,
            "tariff": s_tar,
            "coefficient": s_coeff,
            "recalculation": s_recalc,
            "penalty": s_penalty,
            "total": s_tot,
        })

    if not clean_services:
        raise ValueError(
            "На изображении не удалось распознать коммунальные услуги и суммы начислений. "
            "Пожалуйста, сделайте более четкое фото квитанции, где видна таблица начислений (ХВС, ГВС, отопление, свет)."
        )

    unwrapped["services"] = clean_services

    if not unwrapped.get("total_amount"):
        calc_total = sum(s["total"] for s in clean_services)
        unwrapped["total_amount"] = round(calc_total, 2)
    else:
        try:
            unwrapped["total_amount"] = float(unwrapped["total_amount"])
        except (ValueError, TypeError):
            calc_total = sum(s["total"] for s in clean_services)
            unwrapped["total_amount"] = round(calc_total, 2)

    if not unwrapped.get("period"):
        from datetime import datetime
        unwrapped["period"] = datetime.now().strftime("%Y-%m")

    if not unwrapped.get("address"):
        unwrapped["address"] = "г. Владивосток"

    if not unwrapped.get("bill_id"):
        unwrapped["bill_id"] = f"bill-vision-{uuid4().hex[:8]}"

    return unwrapped


def _normalize_chat_url(raw_url: Optional[str]) -> str:
    if not raw_url:
        return "https://gptunnel.ru/v1/chat/completions"
    cleaned = raw_url.strip().rstrip("/")
    if not cleaned.endswith("/chat/completions"):
        if cleaned.endswith("/v1"):
            cleaned = f"{cleaned}/chat/completions"
        else:
            cleaned = f"{cleaned}/v1/chat/completions"
    return cleaned


def _normalize_model_name(raw_model: Optional[str], default: str = "deepseek-v4-pro-tunnelcode") -> str:
    if not raw_model:
        return default
    return raw_model.strip()


def _get_model_candidates(primary_model: str, is_vision: bool = False) -> List[str]:
    candidates = [primary_model]
    if primary_model.startswith("gptunnel/"):
        candidates.append(primary_model.removeprefix("gptunnel/"))
    else:
        candidates.append(f"gptunnel/{primary_model}")

    if is_vision:
        fallbacks = [
            "gemini-3.7-flash",
            "gemini-3.5-flash-tunnelcode",
            "gpt-5.5-tunnelcode",
            "gpt-4o-mini",
        ]
    else:
        fallbacks = [
            "deepseek-v4-pro-tunnelcode",
            "gemini-3.7-flash",
            "gpt-5.5-tunnelcode",
            "gpt-4o-mini",
        ]
    for fb in fallbacks:
        if fb not in candidates:
            candidates.append(fb)
    return candidates


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
        url = _normalize_chat_url(base_url)

        raw_model = (
            os.getenv("LLM_MODEL")
            or getattr(settings, "LLM_MODEL", "deepseek-v4-pro-tunnelcode")
        )
        model = _normalize_model_name(raw_model, default="deepseek-v4-pro-tunnelcode")
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

        timeout = float(os.getenv("LLM_TIMEOUT_S", "25.0"))
        candidates = _get_model_candidates(model, is_vision=False)
        logger.info("[Text LLM] Sending document text (%d chars) to %s (candidates: %s)", len(text_content), url, candidates[:3])
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = None
            for idx, target_model in enumerate(candidates):
                payload["model"] = target_model
                logger.info("[Text LLM] Trying model '%s' (%d/%d)...", target_model, idx + 1, len(candidates))
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.TimeoutException:
                    logger.warning("[Text LLM] Timeout for model '%s', trying next...", target_model)
                    continue
                if resp.status_code == 400 and "response_format" in payload:
                    payload.pop("response_format", None)
                    try:
                        resp = await client.post(url, json=payload, headers=headers)
                    except httpx.TimeoutException:
                        continue
                if resp.status_code == 404:
                    logger.warning("[Text LLM] Model '%s' returned 404: %s. Trying next...", target_model, resp.text)
                    continue
                if resp.status_code >= 400:
                    logger.warning(
                        "[Text LLM Error] HTTP %d from %s (model: '%s'): %s",
                        resp.status_code,
                        url,
                        target_model,
                        resp.text,
                    )
                    resp.raise_for_status()
                logger.info("[Text LLM] Model '%s' responded successfully (HTTP %d)", target_model, resp.status_code)
                break
            if resp is None or resp.status_code >= 400:
                err_msg = resp.text if resp is not None else "no response"
                last_code = getattr(resp, "status_code", "None")
                logger.error("[Text LLM] Все модели отклонены шлюзом (HTTP %s): %s", last_code, err_msg)
                raise ValueError(f"Сервис анализа текста квитанции GPTunnel вернул ошибку (HTTP {last_code}: {err_msg})")
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        logger.info("[Text LLM Output Text]:\n%s", content)
        cleaned = _clean_json_markdown(content)
        parsed = json.loads(cleaned)
        normalized = _normalize_bill_dict(parsed)

        return BillDocument.model_validate(normalized)

    @classmethod
    async def _call_llm_vision(cls, image_bytes: bytes, mime_type: str) -> Optional[BillDocument]:
        """Call multimodal vision LLM to inspect bill image."""
        api_key, url, _ = cls._get_api_credentials()
        if not api_key:
            logger.warning("[Vision OCR] No API key available")
            return None

        raw_vision = (
            os.getenv("VISION_LLM_MODEL")
            or getattr(settings, "VISION_LLM_MODEL", "gemini-3.7-flash")
            or "gemini-3.7-flash"
        ).strip()
        vision_model = _normalize_model_name(raw_vision, default="gemini-3.7-flash")

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

        timeout = float(os.getenv("LLM_TIMEOUT_S", "25.0"))
        candidates = _get_model_candidates(vision_model, is_vision=True)
        logger.info(
            "[Vision OCR] Sending receipt image (%d bytes, mime: %s) to %s (candidates: %s)",
            len(image_bytes),
            mime_type,
            url,
            candidates,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = None
            for idx, target_model in enumerate(candidates):
                payload["model"] = target_model
                logger.info("[Vision OCR] Trying model '%s' (%d/%d)...", target_model, idx + 1, len(candidates))
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.TimeoutException:
                    logger.warning("[Vision OCR] Timeout for model '%s', trying next...", target_model)
                    continue
                if resp.status_code == 400 and "response_format" in payload:
                    logger.info("[Vision OCR] HTTP 400 with json_object. Retrying without response_format...")
                    payload.pop("response_format", None)
                    try:
                        resp = await client.post(url, json=payload, headers=headers)
                    except httpx.TimeoutException:
                        continue
                if resp.status_code == 404:
                    logger.warning(
                        "[Vision OCR] Model '%s' returned 404: %s. Trying next candidate...",
                        target_model,
                        resp.text,
                    )
                    continue
                if resp.status_code >= 400:
                    logger.warning(
                        "[Vision OCR Error] HTTP %d from %s (model: '%s'): %s",
                        resp.status_code,
                        url,
                        target_model,
                        resp.text,
                    )
                    resp.raise_for_status()
                logger.info("[Vision OCR] Model '%s' responded successfully (HTTP %d)", target_model, resp.status_code)
                break

            if resp is None or resp.status_code >= 400:
                err_msg = resp.text if resp is not None else "no response"
                last_code = getattr(resp, "status_code", "None")
                logger.error("[Vision OCR] Все модели отклонены шлюзом (HTTP %s): %s", last_code, err_msg)
                raise ValueError(f"Сервис распознавания (Vision) шлюза GPTunnel вернул ошибку (HTTP {last_code}: {err_msg})")
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        logger.info("[Vision OCR Raw Text]:\n%s", content)
        cleaned = _clean_json_markdown(content)
        parsed = json.loads(cleaned)
        normalized = _normalize_bill_dict(parsed)

        logger.info(
            "[Vision OCR Parsed] provider='%s', account='%s', period='%s', services=%d, total=%.2f",
            normalized.get("provider_name"),
            normalized.get("personal_account"),
            normalized.get("period"),
            len(normalized.get("services") or []),
            normalized.get("total_amount") or 0.0,
        )

        return BillDocument.model_validate(normalized)

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
