"""AI-lawyer orchestration and SSE streaming.

The agent never performs calculations on its own: every number is read from
the computed ``ComparisonReport``. Answers are marked with three trust levels
(``[Факт из квитанции]``, ``[Математический расчет]``, ``[Аналитическая
гипотеза]``). When the external LLM is unavailable, a deterministic offline
fallback built from ``rules_and_faq.json`` is streamed instead.
"""

import json
import os
import re
from typing import Any, AsyncIterator, Dict, List, Optional

from app.agent import tools
from app.core.models import ComparisonReport

SYSTEM_PROMPT = (
    "Вы — опытный юрист по жилищному праву Российской Федерации, "
    "специализирующийся на Владивостоке и Приморском крае. "
    "Общайтесь спокойно и по-деловому, понятно человеку без юридического "
    "образования, ссылайтесь на конкретные пункты ПП РФ № 354 и Жилищного "
    "кодекса РФ.\n"
    "Категорически запрещено выдумывать или изменять суммы: все цифры берутся "
    "строго из переданного JSON-отчета ComparisonReport.\n"
    "Каждое утверждение обязательно маркируйте одним из трёх уровней:\n"
    "- [Факт из квитанции] — прямое извлечение из документа;\n"
    "- [Математический расчет] — результат детерминированного ядра;\n"
    "- [Аналитическая гипотеза] — юридическое толкование причины."
)

_ANOMALY_LAW_REF: Dict[str, str] = {
    "APPLYING_COEFF_1_5": "п. 31(д), п. 59, п. 60(1) ПП РФ № 354",
    "APPLYING_COEFF_3_0": "п. 31(д), п. 59, п. 60(1) ПП РФ № 354",
    "METER_VERIFICATION_DUE": "п. 60(1) ПП РФ № 354",
    "SOI_SPIKE": "п. 31(д), п. 44 ПП РФ № 354",
    "OPTIONAL_SERVICE_DETECTED": "ст. 16 ЗоЗПП РФ, ч. 2 ст. 154 ЖК РФ",
}

_LLM_API_URL = os.getenv("LLM_API_URL")
_LLM_API_KEY = os.getenv("LLM_API_KEY")
_LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "3.0"))

_ADDRESS_RE = re.compile(r"г\.\s*[А-Яа-яЁё\-]+[^,]*(?:,\s*[^.]*)?", re.UNICODE)
_ACCOUNT_RE = re.compile(r"\b\d{10,}\b")


def mask_personal_account(account: str) -> str:
    """Mask a personal account number, keeping the first 5 and last 4 digits."""
    digits = re.sub(r"\D", "", account)
    if len(digits) < 10:
        return account
    return f"{digits[:5]}***{digits[-4:]}"


def mask_pii(text: str) -> str:
    """Mask ПДн: long account numbers, addresses and full names."""
    if not text:
        return text
    masked = _ACCOUNT_RE.sub(lambda m: mask_personal_account(m.group(0)), text)
    masked = re.sub(
        r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.\b",
        "Собственник помещения",
        masked,
    )
    masked = _ADDRESS_RE.sub("г. Владивосток, МКД", masked)
    return masked


def sse_event(payload: Dict[str, Any]) -> str:
    """Serialize a single Server-Sent Event frame."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def build_fallback_answer(report: ComparisonReport) -> str:
    """Build a deterministic offline answer from the report and knowledge base."""
    lines: List[str] = []
    summary = report.summary

    if not report.anomalies:
        lines.append(
            f"[Факт из квитанции] Платеж за {summary.curr_period} составил "
            f"{summary.curr_total:.2f} ₽, изменение к предыдущему периоду — "
            f"{summary.delta_abs:+.2f} ₽ ({summary.delta_pct:+.2f}%)."
        )
        lines.append(
            "[Математический расчет] Значимых аномалий не выявлено."
        )
        return "\n".join(lines)

    for anomaly in report.anomalies:
        item = next(
            (i for i in report.items if i.category == anomaly.service_category), None
        )
        name = item.display_name if item else anomaly.service_category
        lines.append(
            f"[Факт из квитанции] В квитанции за {summary.curr_period} по услуге "
            f"«{name}» выявлена аномалия: {anomaly.title}."
        )
        lines.append(
            f"[Математический расчет] Сумма переплаты составляет "
            f"{anomaly.impact_rub:.2f} ₽."
        )
        lines.append(f"[Аналитическая гипотеза] {anomaly.hint}")

        plan = tools.get_anomaly_action_plan(anomaly.code)
        if plan:
            lines.append("Рекомендации:")
            for step in plan["action_steps"]:
                lines.append(f"- {step}")
        law_ref = _ANOMALY_LAW_REF.get(anomaly.code)
        if law_ref:
            lines.append(f"Правовое основание: {law_ref}.")

    return "\n".join(lines)


async def _call_llm(prompt: str, context: str) -> Optional[str]:
    """Best-effort call to an external LLM. Returns None on any failure."""
    if not _LLM_API_URL:
        return None
    try:
        import httpx

        headers = {"Content-Type": "application/json"}
        if _LLM_API_KEY:
            headers["Authorization"] = f"Bearer {_LLM_API_KEY}"
        payload = {
            "model": os.getenv("LLM_MODEL", "default"),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
        }
        async with httpx.AsyncClient(timeout=_LLM_TIMEOUT_S) as client:
            resp = await client.post(_LLM_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        return content or None
    except Exception:
        return None


def _chunks(text: str, size: int = 12) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


async def generate_stream(
    comparison_id: str,
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> AsyncIterator[str]:
    """Stream a lawyer answer as Server-Sent Events.

    Event types emitted: ``tool_call``, ``token`` and ``done``.
    """
    record = tools.get_report(comparison_id)
    if record is None:
        yield sse_event(
            {"type": "token", "content": "Отчет не найден. Сначала выполните сравнение квитанций."}
        )
        yield sse_event({"type": "done"})
        return

    report: ComparisonReport = record["report"]

    # Announce tool calls so the frontend can visualize agent activity.
    if report.anomalies:
        yield sse_event({"type": "tool_call", "name": "lookup_glossary"})
        for anomaly in report.anomalies:
            yield sse_event({"type": "tool_call", "name": "get_anomaly_action_plan", "code": anomaly.code})

    context = json.dumps(report.model_dump(), ensure_ascii=False)
    llm_answer = await _call_llm(SYSTEM_PROMPT, context)

    answer = llm_answer if llm_answer else build_fallback_answer(report)

    for chunk in _chunks(answer):
        yield sse_event({"type": "token", "content": chunk})

    yield sse_event({"type": "done"})
