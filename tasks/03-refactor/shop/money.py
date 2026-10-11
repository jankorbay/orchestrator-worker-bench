def fmt_money(cents, currency="USD"):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
    return f"{sign}{symbol}{cents // 100:,}.{cents % 100:02d}"


def parse_money(text):
    text = text.strip().lstrip("$€£").replace(",", "")
    negative = text.startswith("-")
    whole, _, frac = text.lstrip("-").partition(".")
    cents = int(whole or 0) * 100 + int((frac + "00")[:2])
    return -cents if negative else cents
