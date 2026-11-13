"""Knowledge-base lookups and claim drafting for the AI-lawyer agent.

The knowledge base is frozen in ``docs/vladivostok_kb_design/knowledge_base``
and is read-only here. It provides the glossary of ЖКХ terms, the regional
rules / FAQ and the legally verified claim templates.
"""

import json
import re
from datetime import date
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

from app.core import cache
from app.core.models import BillDocument, ComparisonReport
from app.core.normalizer import display_name

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent
_KB_DIR = _REPO_ROOT / "docs" / "vladivostok_kb_design" / "knowledge_base"
_LEGACY_KB_DIR = _REPO_ROOT / "data" / "knowledge_base"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve(name: str) -> Optional[Path]:
    primary = _KB_DIR / name
    if primary.exists():
        return primary
    legacy = _LEGACY_KB_DIR / name
    if legacy.exists():
        return legacy
    return None


def lookup_glossary(term: str) -> Optional[Dict[str, Any]]:
    """Return a human-readable glossary entry for a term or service code."""
    path = _resolve("glossary.json")
    if path is None:
        return None

    data = _load_json(path)

    # Frozen KB layout: {"terms": {code: {...}}, "epd_24_fields": {...}}.
    terms = data.get("terms", data.get("glossary", {}))
    if term in terms:
        entry = terms[term]
        return {
            "term": term,
            "name": entry.get("short_name") or entry.get("name") or term,
            "explanation": entry.get("plain_explanation") or entry.get("description", ""),
            "provider": entry.get("provider_vl", ""),
            "law_ref": entry.get("law_ref") or entry.get("legal_basis", ""),
        }

    # Fall back to a case-insensitive substring match on the display name.
    lowered = term.strip().lower()
    for code, entry in terms.items():
        name = entry.get("short_name") or entry.get("name") or code
        if lowered in name.lower() or lowered == code:
            return {
                "term": code,
                "name": name,
                "explanation": entry.get("plain_explanation") or entry.get("description", ""),
                "provider": entry.get("provider_vl", ""),
                "law_ref": entry.get("law_ref") or entry.get("legal_basis", ""),
            }
    return None


def get_anomaly_action_plan(anomaly_code: str) -> Optional[Dict[str, Any]]:
    """Return the verified step-by-step action plan for an anomaly code."""
    path = _resolve("rules_and_faq.json")
    if path is None:
        return None

    data = _load_json(path)
    for entry in data.get("faq_and_explanations", []):
        if anomaly_code in entry.get("trigger_codes", []):
            return {
                "topic": entry.get("topic", ""),
                "explanation": entry.get("explanation", ""),
                "action_steps": entry.get("action_steps", []),
            }
    return None


def _claim_templates() -> Dict[str, Any]:
    path = _resolve("claim_templates.json")
    if path is None:
        return {}
    return _load_json(path)


def _template_field_names(template: str) -> List[str]:
    return re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::[^}]*)?\}", template)


_TEMPLATE_FIELD_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


def safe_render_template(template_str: str, values: Dict[str, Any]) -> str:
    """Render ``{field}`` / ``{field:spec}`` placeholders without ``str.format``.

    ``str.format`` evaluates arbitrary attribute/index chains (``{0.__class__}``,
    ``{0[0]}``), which is a template-injection risk.  Here only a strict
    identifier pattern is matched, the optional format spec is applied
    explicitly, and any leftover brace tokens are stripped rather than
    evaluated.
    """
    def _resolve(match: re.Match) -> str:
        name = match.group(1)
        spec = match.group(2)
        value = values.get(name, "")
        if spec:
            try:
                return format(value, spec)
            except (ValueError, TypeError):
                return str(value)
        return str(value)

    rendered = _TEMPLATE_FIELD_RE.sub(_resolve, template_str)

    # string.Template resolves any genuine ``$field`` tokens already present in
    # the source template without ever evaluating code.
    rendered = Template(rendered).safe_substitute(
        {k: str(v) for k, v in values.items()}
    )

    # Strip any brace-style tokens we did not recognise (e.g. ``{0[0]}`` or
    # ``{__class__}``) so they can never reach a ``.format`` call.
    rendered = re.sub(r"\{[^{}]*\}", "", rendered)
    return rendered


def store_comparison(
    comparison_id: str,
    report: ComparisonReport,
    curr_bill: BillDocument,
    prev_bill: BillDocument,
    owner_id: Optional[str] = None,
) -> None:
    """Register a computed report for later claim drafting.

    The record is serialized to JSON and cached under
    ``comparison:{comparison_id}`` (Redis with an in-memory fallback).
    ``owner_id`` records the subject that created the report so that later
    reads can be scoped to that owner.
    """
    data = {
        "owner_id": owner_id,
        "report": report.model_dump(mode="json"),
        "curr_bill": curr_bill.model_dump(mode="json"),
        "prev_bill": prev_bill.model_dump(mode="json"),
    }
    cache.set_report(comparison_id, data)


def get_report(
    comparison_id: str,
    owner_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return a stored report record, rehydrating the Pydantic models.

    When the record carries an ``owner_id`` and a caller supplies its own
    ``owner_id`` that does not match, ``PermissionError`` is raised so the
    API layer can answer 403 Forbidden.
    """
    data = cache.get_report(comparison_id)
    if data is None:
        return None
    stored_owner = data.get("owner_id")
    if stored_owner is not None and owner_id is not None and stored_owner != owner_id:
        raise PermissionError(f"Comparison '{comparison_id}' belongs to another owner")
    return {
        "report": ComparisonReport.model_validate(data["report"]),
        "curr_bill": BillDocument.model_validate(data["curr_bill"]),
        "prev_bill": BillDocument.model_validate(data["prev_bill"]),
    }


def draft_uk_claim(comparison_id: str, anomaly_code: str) -> Optional[Dict[str, Any]]:
    """Draft a claim against the УК / ГЖИ for a specific anomaly.

    Exact figures are taken from the computed ``ComparisonReport``; no number
    is ever invented here.
    """
    record = get_report(comparison_id)
    if record is None:
        return None

    templates = _claim_templates()
    template_entry = templates.get(anomaly_code)
    if template_entry is None:
        return None

    report: ComparisonReport = record["report"]
    curr_bill: BillDocument = record["curr_bill"]

    anomaly = next((a for a in report.anomalies if a.code == anomaly_code), None)
    if anomaly is None:
        return None

    item = next((i for i in report.items if i.category == anomaly.service_category), None)

    coefficient = 3.0 if anomaly_code == "APPLYING_COEFF_3_0" else 1.5
    meter_id = "ИПУ"
    for meter in curr_bill.meters or []:
        if meter.service_code == anomaly.service_category:
            meter_id = meter.meter_id
            break

    context: Dict[str, Any] = {
        "organization_name": template_entry.get("recipient_default", ""),
        "payer_name": "Собственник помещения",
        "address": "г. Владивосток, МКД",
        "bill_id": curr_bill.bill_id,
        "period": report.summary.curr_period,
        "service_name": item.display_name if item else display_name(anomaly.service_category),
        "curr_total": item.curr_total if item else report.summary.curr_total,
        "delta_abs": item.delta_abs if item else report.summary.delta_abs,
        "delta_pct": item.delta_pct if item else report.summary.delta_pct,
        "coefficient": coefficient,
        "impact_rub": anomaly.impact_rub,
        "meter_id": meter_id,
        "current_date": date.today().strftime("%d.%m.%Y"),
        "curr_rate": item.curr_tariff if item else 0.0,
        "curr_volume": item.curr_volume if item else 0.0,
    }

    template_text = template_entry.get("template", "")
    text = safe_render_template(template_text, context)

    return {
        "title": template_entry.get("title", ""),
        "recipient": template_entry.get("recipient_default", ""),
        "law_basis": template_entry.get("law_basis", ""),
        "text": text,
    }
