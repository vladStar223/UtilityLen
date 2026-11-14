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
from app.core.normalizer import normalize_service_code

AUDITOR_SYSTEM_PROMPT = """Вы — ведущий финансовый аудитор в сфере жилищно-коммунального хозяйства (ЖКХ) Российской Федерации, эксперт по платежным документам г. Владивостока и Приморского края.
Ваша задача — провести детальный финансовый аудит квитанции/счета за коммунальные услуги и безошибочно извлечь структурированные данные.

Извлеките данные строго в формате JSON, соответствующем следующей схеме:
{
  "bill_id": "строковый идентификатор (из квитанции или bill-YYYY-MM-XXXX)",
  "period": "расчетный период строго в формате YYYY-MM (например, 2026-09)",
  "address": "полный адрес жилого помещения (город, улица, номер дома, квартира)",
  "payer": "ФИО плательщика/собственника или null",
  "provider_name": "Наименование организации-поставщика (например, ПАО «ДЭК», КГУП «Приморский водоканал», Фонд капитального ремонта Приморского края, ООО «УК Первомайского района», АО «РКЦ»)",
  "personal_account": "номер лицевого счета (например, 10507138, 105-0713-8, 1320-9068-5)",
  "total_amount": итоговая сумма к оплате за расчетный период в рублях (число с плавающей точкой, 2 знака),
  "services": [
    {
      "service_code": "код услуги: cold_water, hot_water, heating, electricity, wastewater, maintenance, waste, capital_repair, cold_water_soi, hot_water_soi, electricity_soi, wastewater_soi, optional_service или other",
      "raw_name": "исходное наименование услуги из квитанции",
      "unit": "единица измерения (м3, Гкал, кВт·ч, м2, чел, шт, усл)",
      "volume": объем потребления (число, float),
      "tariff": тариф за единицу в рублях (число, float),
      "coefficient": повышающий коэффициент (число, по умолчанию 1.0; если 1.5 или 3.0 — укажите именно это число),
      "recalculation": сумма перерасчета в рублях (число, float, 0.0 если нет, отрицательное при уменьшении платы),
      "penalty": пени/штрафы в рублях (число, float, 0.0 если нет),
      "total": итоговая сумма начисления по услуге в рублях (число, float)
    }
  ],
  "meters": []
}

Правила классификации услуг (service_code):
- Холодное водоснабжение / ХВС / питьевая вода -> cold_water
- Горячее водоснабжение / ГВС / двухкомпонентный тариф (Компонент на тепловую энергию, Компонент на теплоноситель) -> hot_water
- Отопление / Теплоснабжение / тепловая энергия -> heating
- Электроснабжение / электроэнергия (День, Ночь, круглосуточно) -> electricity
- Водоотведение / канализация / сточные воды -> wastewater (или drainage)
- Содержание жилья / жилого помещения / управление МКД / СиРЖ -> maintenance
- Обращение с ТКО / вывоз мусора / ТБО -> waste
- Взнос на капитальный ремонт / капремонт -> capital_repair
- Общедомовые нужды (СОИ / ОДН в МКД):
  * ХВС на СОИ в МКД / Расходы при содержании ... ХВС -> cold_water_soi
  * ГВС на СОИ в МКД / Расходы при содержании ... ГВС -> hot_water_soi
  * Э/Э на СОИ в МКД / Расходы при содержании ... Электроэнергия -> electricity_soi
  * Водоотведение на СОИ в МКД / Расходы при содержании ... Водоотведение -> wastewater_soi
- Дополнительные услуги (печать квитанций по кап.ремонту, антенна, домофон) -> optional_service
- Прочие услуги -> other

Специфика региональных квитанций (г. Владивосток и Приморский край):
1. ПАО «ДЭК» / филиал «Приморские тепловые сети» АО «ДГК» / КГУП «ПЭО» (Единый платежный документ):
   - Содержит электроэнергию (день/ночь), отопление, двухкомпонентное ГВС (тепловая энергия [Гкал] + теплоноситель [м3]), обращение с ТКО.
   - total_amount берите строго из графы «Всего к оплате БЕЗ учета рекомендуемого платежа» (НЕ включайте добровольный рекомендуемый аванс!).
   - Перерасчеты из графы «Перерасчеты, руб.» заносите в recalculation.
2. КГУП «Приморский водоканал»:
   - Включает ХВС и Водоотведение.
   - Повышающий коэффициент: если в графе начисления стоит звездочка (*) или внизу указано «применен повышающий коэффициент в размере равном 3» (или 1.5) — обязательно укажите coefficient: 3.0 (или 1.5).
   - total_amount берите строго из строки «ИТОГО» (НЕ берите сумму с рекомендуемым платежом!).
3. Фонд капитального ремонта многоквартирных домов Приморского края (ФКР):
   - Взнос на капремонт: volume = площадь (кв.м), tariff = ставка взноса на кв.м, total = итого к оплате. service_code: capital_repair.
4. Управляющие компании Владивостока (АО «РКЦ», ООО «УК Первомайского района», ООО «УК Комплексное обслуживание домов»):
   - Содержит Содержание жилого помещения (maintenance) и статьи СОИ по 4 ресурсам: ХВС, ГВС, Э/Э, Водоотведение, а также доп. услуги (печать квитанций).
5. Период: строго YYYY-MM («СЕНТЯБРЬ 2026 г.» -> 2026-09, «09.2026» -> 2026-09, «(09.26)» -> 2026-09, «07.26» -> 2026-07).

Важные требования:
1. Суммы и объемы должны быть числами (float). Разделитель — точка.
2. total_amount должен соответствовать сумме к оплате за расчетный период без учета рекомендуемого аванса.
3. Ответ должен быть ИСКЛЮЧИТЕЛЬНО валидным JSON-объектом, без markdown-разметки (без ```json), без вводных и заключительных фраз.
4. Если на изображении или в тексте видна квитанция/счет за услуги ЖКХ, но таблица начислений видна не полностью или частично смазана — ВСЁ РАВНО извлеките всё, что можете различить (сумму к оплате, поставщика, лицевой счет, любые услуги), либо сформируйте общую строку услуги ("Коммунальные услуги"). Не возвращайте ошибку, если это квитанция!
5. КРИТИЧЕСКИ ВАЖНО: Только если переданный документ совершенно НЕ связан с ЖКХ (например: фото животного, еда, лицо человека, чек из супермаркета, мем, пейзаж):
   Верните строго следующий JSON:
   {
     "is_utility_bill": false,
     "error": "Загруженный документ не является квитанцией ЖКХ."
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


_MONTHS_RU = {
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


def _normalize_period_str(raw: Any) -> str:
    """Robustly parse raw period string into standard YYYY-MM format."""
    if not raw or not isinstance(raw, str):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m")

    val = raw.strip()
    # Check YYYY-MM
    m_iso = re.search(r"\b(20\d{2})[-/.](\d{1,2})\b", val)
    if m_iso:
        y, m = m_iso.group(1), int(m_iso.group(2))
        if 1 <= m <= 12:
            return f"{y}-{m:02d}"

    # Check MM.YYYY
    m_ru_full = re.search(r"\b(\d{1,2})[-/.]\s*(20\d{2})\b", val)
    if m_ru_full:
        m, y = int(m_ru_full.group(1)), m_ru_full.group(2)
        if 1 <= m <= 12:
            return f"{y}-{m:02d}"

    # Check MM.YY e.g. 09.26 or (09.26) or 07.26
    m_ru_short = re.search(r"(?:^|[^\d])(\d{2})[-/.](\d{2})(?:$|[^\d])", val)
    if m_ru_short:
        m_part, y_part = int(m_ru_short.group(1)), int(m_ru_short.group(2))
        if 1 <= m_part <= 12 and 20 <= y_part <= 35:
            return f"20{y_part}-{m_part:02d}"

    # Check Russian month names e.g. "Сентябрь 2026", "АВГУСТ 2026г."
    lowered = val.lower()
    m_year = re.search(r"(20\d\d)", lowered)
    target_year = m_year.group(1) if m_year else "2026"
    for ru_root, m_num in _MONTHS_RU.items():
        if ru_root in lowered:
            return f"{target_year}-{m_num}"

    from datetime import datetime
    return datetime.now().strftime("%Y-%m")


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
        raw_code = str(s.get("service_code") or s.get("code") or "").strip()
        s_name = str(s.get("raw_name") or s.get("name") or s.get("display_name") or s.get("наименование") or "").strip()
        if not s_name:
            s_name = raw_code or "Коммунальные услуги"

        # Deduce canonical service code
        if not raw_code or raw_code.lower() in ("null", "none", "other", "unknown") or raw_code.isdigit():
            resolved_code = normalize_service_code(s_name)
        else:
            resolved_code = normalize_service_code(raw_code)
            if resolved_code in ("other", "unknown") and s_name:
                resolved_code = normalize_service_code(s_name)

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
            if s_coeff <= 0.0:
                s_coeff = 1.0
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
            "service_code": str(resolved_code),
            "raw_name": str(s_name),
            "unit": str(s_unit),
            "volume": s_vol,
            "tariff": s_tar,
            "coefficient": s_coeff,
            "recalculation": s_recalc,
            "penalty": s_penalty,
            "total": s_tot,
        })

    # Resolve total_amount
    total_val = 0.0
    raw_tot = (
        unwrapped.get("total_amount")
        or unwrapped.get("total")
        or unwrapped.get("amount")
        or unwrapped.get("итого")
        or unwrapped.get("к_оплате")
    )
    if raw_tot:
        try:
            total_val = float(raw_tot)
        except (ValueError, TypeError):
            total_val = 0.0

    if not clean_services:
        if total_val > 0.0:
            clean_services = [{
                "service_code": "other",
                "raw_name": "Коммунальные услуги (начисление)",
                "unit": "усл",
                "volume": 1.0,
                "tariff": total_val,
                "coefficient": 1.0,
                "recalculation": 0.0,
                "penalty": 0.0,
                "total": total_val,
            }]
        else:
            raise ValueError(
                "На изображении не удалось различить коммунальные услуги или сумму к оплате. "
                "Пожалуйста, сделайте более четкое фото квитанции, где видна таблица начислений (ХВС, ГВС, отопление, свет)."
            )

    unwrapped["services"] = clean_services

    if not unwrapped.get("total_amount") or float(unwrapped.get("total_amount", 0)) <= 0:
        calc_total = sum(s["total"] for s in clean_services)
        unwrapped["total_amount"] = round(calc_total, 2)
    else:
        try:
            unwrapped["total_amount"] = float(unwrapped["total_amount"])
        except (ValueError, TypeError):
            calc_total = sum(s["total"] for s in clean_services)
            unwrapped["total_amount"] = round(calc_total, 2)

    unwrapped["period"] = _normalize_period_str(unwrapped.get("period"))

    if not unwrapped.get("address"):
        unwrapped["address"] = "Адрес не указан"

    if not unwrapped.get("provider_name"):
        service_codes_set = {s["service_code"] for s in clean_services}
        if "capital_repair" in service_codes_set:
            unwrapped["provider_name"] = "Фонд капитального ремонта многоквартирных домов Приморского края"
        elif "heating" in service_codes_set or any("дэк" in str(s.get("raw_name", "")).lower() for s in clean_services):
            unwrapped["provider_name"] = "ПАО «ДЭК» (филиал «Дальэнергосбыт») / АО «ДГК»"
        elif "cold_water" in service_codes_set and "cold_water_soi" not in service_codes_set:
            unwrapped["provider_name"] = "КГУП «Приморский водоканал»"
        else:
            unwrapped["provider_name"] = None

    raw_acc = unwrapped.get("personal_account")
    if raw_acc:
        unwrapped["personal_account"] = str(raw_acc).strip()
    else:
        unwrapped["personal_account"] = None

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
            "claude-sonnet-4.6-tunnelcode",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "gemini-3.5-flash-tunnelcode",
            "gpt-5.5-tunnelcode",
            "gpt-5.5-pro",
            "qwen-3.7-max-tunnelcode",
            "qwen-3.7-plus-tunnelcode",
        ]
    else:
        fallbacks = [
            "deepseek-v4-pro-tunnelcode",
            "deepseek-v4-flash-tunnelcode",
            "claude-sonnet-4.6-tunnelcode",
            "qwen-3.7-max-tunnelcode",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "gpt-5.5-tunnelcode",
        ]
    for fb in fallbacks:
        if fb not in candidates:
            candidates.append(fb)
        if f"gptunnel/{fb}" not in candidates:
            candidates.append(f"gptunnel/{fb}")
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
                    "content": (
                        "Проведи детальный финансовый аудит следующей квитанции ЖКХ.\n"
                        "Верни ответ ИСКЛЮЧИТЕЛЬНО в виде валидного JSON-объекта строго по схеме аудитора:\n\n"
                        f"{text_content}"
                    ),
                },
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        timeout = float(os.getenv("LLM_TIMEOUT_S", "35.0"))
        candidates = _get_model_candidates(model, is_vision=False)
        logger.info("[Text LLM] Sending document text (%d chars) to %s (candidates: %s)", len(text_content), url, candidates[:4])

        parsed_data: Optional[Dict[str, Any]] = None
        async with httpx.AsyncClient(timeout=timeout) as client:
            for idx, target_model in enumerate(candidates):
                payload["model"] = target_model
                logger.info("[Text LLM] Trying model '%s' (%d/%d)...", target_model, idx + 1, len(candidates))
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.TimeoutException:
                    logger.warning("[Text LLM] Timeout for model '%s', trying next...", target_model)
                    continue
                except Exception as net_err:
                    logger.warning("[Text LLM] Network error for model '%s': %s. Trying next...", target_model, net_err)
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
                    continue

                try:
                    data = resp.json()
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    raw_content = choices[0].get("message", {}).get("content", "") or ""
                    cleaned = _clean_json_markdown(raw_content)
                    if not cleaned or cleaned == "{}" or len(cleaned) < 15:
                        logger.warning("[Text LLM] Model '%s' returned empty or trivial output: '%s'. Trying next...", target_model, raw_content[:150])
                        continue
                    cand_parsed = json.loads(cleaned)
                    if isinstance(cand_parsed, dict):
                        logger.info("[Text LLM] Model '%s' responded successfully (HTTP %d, %d chars)", target_model, resp.status_code, len(cleaned))
                        parsed_data = cand_parsed
                        break
                except Exception as parse_err:
                    logger.warning("[Text LLM] Model '%s' JSON parse failed: %s. Trying next...", target_model, parse_err)
                    continue

        if parsed_data is None:
            return None
        normalized = _normalize_bill_dict(parsed_data)
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
                            "text": (
                                "Внимательно проведи финансовый аудит квитанции ЖКХ на этом изображении.\n"
                                "Распознай все реквизиты: организацию-поставщика/УК, номер лицевого счета, расчетный период, "
                                "адрес помещения, таблицу начислений по всем услугам (тарифы, объемы, единицы измерения, итого) "
                                "и общую сумму к оплате.\n"
                                "Верни ответ ИСКЛЮЧИТЕЛЬНО в виде валидного JSON-объекта строго по схеме финансового аудитора. "
                                "Не добавляй никаких вводных слов, пояснений или markdown вне JSON."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
                        },
                    ],
                },
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        timeout = float(os.getenv("LLM_TIMEOUT_S", "35.0"))
        candidates = _get_model_candidates(vision_model, is_vision=True)
        logger.info(
            "[Vision OCR] Sending receipt image (%d bytes, mime: %s) to %s (candidates: %s)",
            len(image_bytes),
            mime_type,
            url,
            candidates,
        )

        parsed_data: Optional[Dict[str, Any]] = None
        last_err: str = ""

        async with httpx.AsyncClient(timeout=timeout) as client:
            for idx, target_model in enumerate(candidates):
                payload["model"] = target_model
                logger.info("[Vision OCR] Trying model '%s' (%d/%d)...", target_model, idx + 1, len(candidates))
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.TimeoutException:
                    logger.warning("[Vision OCR] Timeout (%.1fs) for model '%s', trying next candidate...", timeout, target_model)
                    continue
                except Exception as net_err:
                    logger.warning("[Vision OCR] Network error for model '%s': %s. Trying next...", target_model, net_err)
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
                    last_err = f"HTTP {resp.status_code}: {resp.text}"
                    continue

                logger.info("[Vision OCR] Model '%s' responded HTTP %d", target_model, resp.status_code)
                try:
                    data = resp.json()
                    choices = data.get("choices") or []
                    if not choices:
                        logger.warning("[Vision OCR] Model '%s' returned empty choices. Trying next...", target_model)
                        continue

                    raw_content = choices[0].get("message", {}).get("content", "") or ""
                    cleaned = _clean_json_markdown(raw_content)

                    if not cleaned or cleaned == "{}" or len(cleaned) < 15:
                        logger.warning(
                            "[Vision OCR] Model '%s' returned empty or trivial output: '%s'. Trying next candidate...",
                            target_model,
                            raw_content[:150],
                        )
                        continue

                    cand_parsed = json.loads(cleaned)
                    if not isinstance(cand_parsed, dict):
                        logger.warning("[Vision OCR] Model '%s' returned non-dict JSON. Trying next...", target_model)
                        continue

                    # If model explicitly said it is not a utility bill
                    if cand_parsed.get("is_utility_bill") in (False, "false", "False", 0, "0"):
                        logger.info("[Vision OCR] Model '%s' classified image as non-utility bill.", target_model)
                        parsed_data = cand_parsed
                        break

                    unwrapped = _unwrap_envelope(cand_parsed)
                    has_receipt_data = any(
                        k in unwrapped
                        for k in ("services", "total_amount", "period", "provider_name", "total", "amount", "услуги", "итого")
                    )
                    if not has_receipt_data:
                        logger.warning(
                            "[Vision OCR] Model '%s' JSON lacks receipt keys: '%s'. Trying next candidate...",
                            target_model,
                            cleaned[:150],
                        )
                        continue

                    logger.info(
                        "[Vision OCR] Model '%s' successfully recognized receipt JSON (%d chars)",
                        target_model,
                        len(cleaned),
                    )
                    parsed_data = cand_parsed
                    break

                except Exception as parse_err:
                    logger.warning(
                        "[Vision OCR] Failed to parse output from model '%s': %s. Trying next...",
                        target_model,
                        parse_err,
                    )
                    continue

        if parsed_data is None:
            err_detail = f" ({last_err})" if last_err else ""
            raise ValueError(
                f"Нейросети не удалось распознать данные на изображении{err_detail}. "
                "Пожалуйста, сделайте более четкое фото квитанции, где видна таблица начислений (ХВС, ГВС, отопление, свет)."
            )

        normalized = _normalize_bill_dict(parsed_data)

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
