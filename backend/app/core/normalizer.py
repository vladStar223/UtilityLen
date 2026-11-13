"""Normalize raw utility service names into canonical codes.

Raw names come from the receipts of various Vladivostok providers
(ПАО «ДЭК», АО «ДГК», КГУП «Приморский водоканал», УК, АО «РКЦ») and
may differ wildly. The canonical codes below are shared across the whole
system and are the keys used by the math kernel, knowledge base and UI.
"""

from typing import Dict, Optional

# Order matters: more specific rules (e.g. СОИ / ОДН) must be checked
# before generic rules (e.g. plain ХВС) because the generic keywords are
# substrings of the specific ones.
_RULES = [
    # Recalculation / adjustment must be matched before generic energy terms
    # because names like "Перерасчет за теплоснабжение" contain the heating
    # keyword as a substring.
    (["перерасчет", "корректировка"], "recalculation"),
    (
        ["кр на сои хвс", "одн хвс", "хвс одн", "хвс сои", "хвс на сои", "сои хвс"],
        "cold_water_soi",
    ),
    (["холодная вода", "холодное водоснабжение", "холодное в/с", "хвс"], "cold_water"),
    (["горячая вода", "горячее водоснабжение", "гвс"], "hot_water"),
    (["отопление", "тепловая энергия", "теплоснабжение"], "heating"),
    (["электроэнергия", "свет"], "electricity"),
    (["содержание жилья", "содержание жилого", "текущий ремонт"], "maintenance"),
    (["обращение с тко", "вывоз мусора", "тко"], "waste"),
    (["водоотведение", "канализация"], "wastewater"),
    (["антенна", "страхование", "страхов", "радиоточка", "домофон"], "optional_service"),
]

_DISPLAY_NAMES: Dict[str, str] = {
    "cold_water": "Холодное водоснабжение (ХВС)",
    "hot_water": "Горячее водоснабжение (ГВС)",
    "heating": "Отопление",
    "electricity": "Электроэнергия",
    "cold_water_soi": "ХВС на СОИ (общедомовые нужды)",
    "hot_water_soi": "ГВС на СОИ (общедомовые нужды)",
    "maintenance": "Содержание жилого помещения",
    "waste": "Обращение с ТКО",
    "wastewater": "Водоотведение",
    "capital_repair": "Взнос на капитальный ремонт",
    "recalculation": "Перерасчет",
    "optional_service": "Дополнительная услуга",
}


def normalize_service_code(raw_name: str) -> str:
    """Map a raw service name (or code) to a canonical category code.

    Returns the original value unchanged when it is already a canonical
    code or when no rule matches.
    """
    if not raw_name:
        return "unknown"

    value = raw_name.strip().lower()

    if value in _DISPLAY_NAMES or value in _ALL_CANONICAL_CODES:
        return value

    for keywords, code in _RULES:
        for keyword in keywords:
            if keyword in value:
                return code

    return raw_name.strip()


_ALL_CANONICAL_CODES = set(_DISPLAY_NAMES.keys())


def display_name(code: str, fallback: Optional[str] = None) -> str:
    """Return a human readable name for a canonical service code."""
    if code in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[code]
    return fallback or code
