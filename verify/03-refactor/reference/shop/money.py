def format_money(cents: int, currency: str = "USD") -> str:
    """Format integer cents as a currency string, e.g. 123456 -> '$1,234.56'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
    return f"{sign}{symbol}{cents // 100:,}.{cents % 100:02d}"


def parse_money(text: str) -> int:
    """Parse a money string like '$1,234.56' into integer cents."""
    text = text.strip().lstrip("$€£").replace(",", "")
    negative = text.startswith("-")
    whole, _, frac = text.lstrip("-").partition(".")
    cents = int(whole or 0) * 100 + int((frac + "00")[:2])
    return -cents if negative else cents
