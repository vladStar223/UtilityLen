"""Utilities for masking personal data (ПДн) before rendering to the UI."""
import re


def mask_personal_account(account: str) -> str:
    """Маскирует номер лицевого счета: оставляет первые 3 и последние 4 цифры."""
    if not account:
        return ""
    digits = re.sub(r"\D", "", str(account))
    if len(digits) <= 7:
        return "***"
    return f"{digits[:3]}***{digits[-4:]}"


def mask_address(address: str) -> str:
    """Обезличивает точный номер квартиры в адресе."""
    if not address:
        return ""
    # Заменяет 'кв. 25' / 'кв. 102' на 'кв. **'
    return re.sub(r"(кв\.?\s*)\d+", r"\1**", str(address), flags=re.IGNORECASE)


def mask_fio(fio: str) -> str:
    """Заменяет полное ФИО на обезличенного собственника."""
    if not fio:
        return "Собственник помещения"
    return "Собственник помещения"
