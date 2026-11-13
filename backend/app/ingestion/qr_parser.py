"""Parser for the bank payment QR string described by ГОСТ Р 56042-2014.

The receipt QR code encodes a pipe-delimited list of ``KEY=Value`` fields
starting with a two-letter template identifier such as ``ST00012``. Only
the fields required for cross-checking the receipt are extracted here:

* ``Sum``        — amount in kopecks (divided by 100 to get rubles);
* ``PaymPeriod`` — billing period in ``MMYYYY`` format (e.g. ``112026``).
"""

from typing import Dict, Optional

#: Maximum tolerated discrepancy (in rubles) between the receipt total and
#: the amount encoded in the QR code.
MAX_QR_DISCREPANCY_RUB = 1.00


def parse_qr(qr_data: str) -> Dict[str, Optional[str]]:
    """Parse a ГОСТ Р 56042-2014 string into a dict of raw ``KEY=Value`` fields."""
    fields: Dict[str, str] = {}
    if not qr_data:
        return fields

    for part in qr_data.split("|"):
        if "=" in part:
            key, _, value = part.partition("=")
            fields[key.strip()] = value.strip()

    return fields


def extract_sum_rub(qr_data: str) -> Optional[float]:
    """Extract the ``Sum`` field (kopecks) and convert it to rubles."""
    fields = parse_qr(qr_data)
    raw_sum = fields.get("Sum")
    if raw_sum is None:
        return None
    try:
        kopecks = int(raw_sum)
    except (TypeError, ValueError):
        return None
    return round(kopecks / 100.0, 2)


def extract_paym_period(qr_data: str) -> Optional[str]:
    """Extract and normalize the ``PaymPeriod`` field to ``YYYY-MM`` format."""
    fields = parse_qr(qr_data)
    raw = fields.get("PaymPeriod")
    if not raw:
        return None

    raw = raw.strip()
    if len(raw) == 6 and raw.isdigit():
        month = raw[0:2]
        year = raw[2:6]
        return f"{year}-{month}"
    return raw


def verify_qr_sum(bill_total_rub: float, qr_sum_rub: Optional[float]) -> bool:
    """Return True when the receipt total matches the QR amount.

    A discrepancy greater than ``MAX_QR_DISCREPANCY_RUB`` means the receipt
    was tampered with or the QR belongs to a different document, so the
    result is ``False``.
    """
    if qr_sum_rub is None:
        return True
    return abs(float(bill_total_rub) - float(qr_sum_rub)) <= MAX_QR_DISCREPANCY_RUB
