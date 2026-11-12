"""Shared data-quality rules for the Online Retail project."""
import pandas as pd

# StockCodes that are bookkeeping entries rather than goods. Each one was checked by
# reading its Description in the raw file.
ADMIN_CODES = {
    "POST": "postage",
    "DOT": "dotcom postage",
    "C2": "carriage",
    "M": "manual entry",
    "D": "discount",
    "S": "samples",
    "B": "adjust bad debt",
    "BANK CHARGES": "bank charges",
    "AMAZONFEE": "Amazon fee",
    "CRUK": "CRUK commission",
}
GIFT_VOUCHER_PREFIX = "GIFT_0001"  # gift vouchers: a payment instrument, not goods

# Deliberately NOT administrative: DCGS... codes and PADS have real product names
# (e.g. "BOXED GLASS ASHTRAY", "CAMOUFLAGE DOG COLLAR"), although they break the
# documented 5-digit format.

# The three kinds of record held in the returns file (column RecordType).
RECORD_PRODUCT_CANCELLATION = "product cancellation"        # 'C' invoice for real goods
RECORD_ADMIN_REVERSAL = "administrative reversal"           # 'C' invoice for postage, fees, discounts, manual entries...
RECORD_STOCK_ADJUSTMENT = "stock adjustment"                # negative quantity, no 'C' invoice, price 0

COUNTRY_RENAME = {"EIRE": "Ireland", "RSA": "South Africa", "USA": "United States"}

# ISO 3166-1 alpha-2 codes (proposed by Component A, implemented by Component C).
# "Channel Islands", "European Community" and "Unspecified" have no single code and
# are therefore left blank instead of being guessed.
COUNTRY_ISO2 = {
    "United Kingdom": "GB", "Germany": "DE", "France": "FR", "Ireland": "IE", "Spain": "ES",
    "Netherlands": "NL", "Belgium": "BE", "Switzerland": "CH", "Portugal": "PT",
    "Australia": "AU", "Norway": "NO", "Italy": "IT", "Finland": "FI", "Cyprus": "CY",
    "Sweden": "SE", "Austria": "AT", "Denmark": "DK", "Japan": "JP", "Poland": "PL",
    "Israel": "IL", "United States": "US", "Hong Kong": "HK", "Singapore": "SG",
    "Iceland": "IS", "Canada": "CA", "Greece": "GR", "Malta": "MT",
    "United Arab Emirates": "AE", "South Africa": "ZA", "Lebanon": "LB", "Lithuania": "LT",
    "Brazil": "BR", "Czech Republic": "CZ", "Bahrain": "BH", "Saudi Arabia": "SA",
}


def standard_stock_code(series: pd.Series) -> pd.Series:
    """Text, trimmed, upper case, so that 85123a and 85123A are one product."""
    return series.astype(str).str.strip().str.upper()


def standard_description(series: pd.Series) -> pd.Series:
    """Text with outer spaces removed and repeated spaces collapsed; missing stays missing."""
    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def is_cancellation(invoice_no: pd.Series) -> pd.Series:
    return invoice_no.astype(str).str.upper().str.startswith("C")


def is_admin_code(stock_code: pd.Series) -> pd.Series:
    code = standard_stock_code(stock_code)
    return code.isin(ADMIN_CODES) | code.str.startswith(GIFT_VOUCHER_PREFIX)


def admin_category(stock_code: pd.Series) -> pd.Series:
    """Readable category of an administrative code (postage, discount, ...); missing for products."""
    code = standard_stock_code(stock_code)
    category = code.map(ADMIN_CODES).astype("string")
    return category.mask(code.str.startswith(GIFT_VOUCHER_PREFIX), "gift voucher")


def needs_case_fix(stock_code: pd.Series) -> pd.Series:
    """Issue Q9: the code as stored differs from its standard upper-case form."""
    return stock_code.astype(str) != standard_stock_code(stock_code)


def is_catalogue_format(stock_code: pd.Series) -> pd.Series:
    """5 digits, optionally followed by letter(s): a catalogue item or a colour/size variant."""
    return standard_stock_code(stock_code).str.fullmatch(r"\d{5}[A-Z]{0,2}")
