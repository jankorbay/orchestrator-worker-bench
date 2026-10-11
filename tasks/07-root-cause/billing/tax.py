"""VAT rules. The seller is established in Germany."""
from decimal import Decimal

from billing.customers import EU_COUNTRIES, Customer

SELLER_COUNTRY = "DE"
STANDARD = {"AT": "20", "BE": "21", "DE": "19", "ES": "21", "FR": "20",
            "IE": "23", "IT": "22", "NL": "21", "PL": "23", "SE": "25"}
REDUCED = {"AT": "10", "BE": "6", "DE": "7", "ES": "4", "FR": "5.5",
           "IE": "0", "IT": "4", "NL": "9", "PL": "5", "SE": "6"}
REDUCED_CATEGORIES = {"books", "food"}


def is_reverse_charge(customer: Customer) -> bool:
    """EU business customer in another member state: the customer accounts for VAT."""
    return (customer.country in EU_COUNTRIES and customer.country != SELLER_COUNTRY
            and customer.is_business)


def vat_rate(customer: Customer, category: str) -> Decimal:
    """VAT rate in percent for one invoice line."""
    if customer.country not in EU_COUNTRIES:
        return Decimal(0)  # export outside the EU
    if is_reverse_charge(customer):
        return Decimal(0)
    table = REDUCED if category in REDUCED_CATEGORIES else STANDARD
    return Decimal(table[customer.country])
