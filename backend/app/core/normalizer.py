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
        [
            "кр на сои хвс", "одн хвс", "хвс одн", "хвс сои", "хвс на сои", "сои хвс",
            "хвс на сои в мкд", "содержании общего имущества многоквартирного дома: хвс",
            "содержании общего имущества: хвс", "сои в мкд: хвс"
        ],
        "cold_water_soi",
    ),
    (
        [
            "кр на сои гвс", "одн гвс", "гвс одн", "гвс сои", "гвс на сои", "сои гвс",
            "гвс на сои в мкд", "содержании общего имущества многоквартирного дома: гвс",
            "содержании общего имущества: гвс", "сои в мкд: гвс"
        ],
        "hot_water_soi",
    ),
    (
        [
            "э/э на сои", "сои э/э", "одн э/э", "э/э одн", "э/э на сои в мкд",
            "электроэнергия на сои", "сои электроэнергия",
            "содержании общего имущества многоквартирного дома: электроэнергия",
            "содержании общего имущества: электроэнергия"
        ],
        "electricity_soi",
    ),
    (
        [
            "водоотведение на сои", "сои водоотведение", "одн водоотведение",
            "водоотведение одн", "водоотведение на сои в мкд",
            "содержании общего имущества многоквартирного дома: водоотведение",
            "содержании общего имущества: водоотведение"
        ],
        "wastewater_soi",
    ),
    (
        [
            "капитальный ремонт", "капитального ремонта", "взнос на капитальный ремонт",
            "взнос на капремонт", "капремонт", "capital_repairs", "capital_repair"
        ],
        "capital_repair",
    ),
    (["холодная вода", "холодное водоснабжение", "холодное в/с", "хвс"], "cold_water"),
    (
        [
            "горячая вода", "горячее водоснабжение", "гвс",
            "компонент на теплоноситель", "компонент на тепловую энергию"
        ],
        "hot_water",
    ),
    (["отопление", "тепловая энергия", "теплоснабжение"], "heating"),
    (["электроэнергия", "электроснабжение", "э/э", "свет"], "electricity"),
    (["содержание жилья", "содержание жилого", "текущий ремонт", "управление мкд"], "maintenance"),
    (["обращение с тко", "вывоз мусора", "тко", "тбо"], "waste"),
    (["водоотведение", "канализация", "отведение сточных вод", "drainage"], "wastewater"),
    (
        ["печать квитанций", "антенна", "страхование", "страхов", "радиоточка", "домофон"],
        "optional_service",
    ),
]

_DISPLAY_NAMES: Dict[str, str] = {
    "cold_water": "Холодное водоснабжение (ХВС)",
    "hot_water": "Горячее водоснабжение (ГВС)",
    "heating": "Отопление",
    "electricity": "Электроэнергия",
    "cold_water_soi": "ХВС на СОИ (общедомовые нужды)",
    "hot_water_soi": "ГВС на СОИ (общедомовые нужды)",
    "electricity_soi": "Электроэнергия на СОИ (общедомовые нужды)",
    "wastewater_soi": "Водоотведение на СОИ (общедомовые нужды)",
    "maintenance": "Содержание жилого помещения",
    "waste": "Обращение с ТКО",
    "wastewater": "Водоотведение",
    "drainage": "Водоотведение",
    "capital_repair": "Взнос на капитальный ремонт",
    "capital_repairs": "Взнос на капитальный ремонт",
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

    if value == "drainage":
        return "wastewater"
    if value == "capital_repairs":
        return "capital_repair"

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
