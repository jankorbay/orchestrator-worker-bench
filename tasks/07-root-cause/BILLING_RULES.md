# Billing rules (agreed with finance)

## Amounts
- Catalog prices are in EUR. An invoice is in the customer's currency.
- Line amount = qty × unit price, converted at the daily rate (`billing/rates.py`) and
  rounded to cents (half up).

## Discount codes
- **Percent codes**: each eligible line gets `line amount × percent`, rounded to cents.
  A code with a category applies only to lines of that category.
- **Fixed codes** are defined in EUR. Convert the code amount to the invoice currency and
  round it to cents. Split it over the lines in proportion to their line amounts; round
  each share to cents. Add the rounding remainder (positive or negative) to the line with
  the largest line amount (the first such line on ties), so the shares add up exactly to
  the converted code amount. The discount never exceeds the order's total.
- A code's minimum order value is checked in EUR, before any discount.

## VAT
- VAT is computed per line on the discounted line amount and rounded per line.
- Customers outside the EU: 0% (export).
- EU business customers in another member state than ours (DE) with a valid VAT ID:
  reverse charge, 0% VAT, and the invoice carries the reverse-charge note.
- Everyone else in the EU pays the VAT of their country (reduced rate for books and food).

## VAT IDs
- Customers type VAT IDs in many ways: any letter case, with spaces, dots or dashes.
  All of these must be accepted. VAT IDs are stored in canonical form: uppercase letters
  and digits only, e.g. `ATU12345678`.

## Credit notes
- A credit note refunds lines exactly as they were invoiced (same discount, net and VAT,
  negated).
