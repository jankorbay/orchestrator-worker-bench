"""Customers and VAT ID handling."""
import re
from dataclasses import dataclass

EU_COUNTRIES = {"AT", "BE", "DE", "ES", "FR", "IE", "IT", "NL", "PL", "SE"}

# VAT ID body (after the two-letter country prefix), per country.
VAT_PATTERNS = {
    "AT": r"U\d{8}",
    "BE": r"0\d{9}",
    "DE": r"\d{9}",
    "ES": r"[A-Z0-9]\d{7}[A-Z0-9]",
    "FR": r"[A-Z0-9]{2}\d{9}",
    "IE": r"\d{7}[A-Z]{1,2}",
    "IT": r"\d{11}",
    "NL": r"\d{9}B\d{2}",
    "PL": r"\d{10}",
    "SE": r"\d{12}",
}


def normalize_vat_id(raw: str | None) -> str | None:
    """Canonical VAT ID, e.g. 'ATU12345678'. None when empty."""
    if not raw:
        return None
    return re.sub(r"[\s.\-]", "", raw).upper() or None


def valid_vat_id(vat_id: str | None, country: str) -> bool:
    """True if `vat_id` is a well-formed VAT ID for `country`."""
    if not vat_id or vat_id[:2] != country:
        return False
    pattern = VAT_PATTERNS.get(country)
    return bool(pattern and re.fullmatch(pattern, vat_id[2:]))


@dataclass
class Customer:
    name: str
    country: str  # ISO 3166 alpha-2
    currency: str
    vat_id: str | None = None

    def __post_init__(self):
        self.country = self.country.strip().upper()
        self.vat_id = normalize_vat_id(self.vat_id)

    @property
    def is_business(self) -> bool:
        return valid_vat_id(self.vat_id, self.country)
