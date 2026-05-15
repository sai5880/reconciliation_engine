import math
import re
import unicodedata

from decimal import Decimal
from dateutil import parser


LEGAL_SUFFIXES = {
    "inc",
    "incorporated",
    "corporation",
    "corp",
    "co",
    "company",
    "llc",
    "ltd",
    "limited",
}


def clean_text(text: str) -> str:

    if text is None:
        return ""

    if isinstance(text, float) and math.isnan(text):
        return ""

    text = unicodedata.normalize(
        "NFKD",
        str(text),
    )

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    words = []

    for word in text.split():

        if word not in LEGAL_SUFFIXES:
            words.append(word)

    return " ".join(words).strip()


def normalize_vendor(description):

    description = clean_text(description)

    description = description.replace(
        "payment to",
        ""
    )

    description = description.replace(
        "gl entry",
        ""
    )

    return description.strip()


def normalize_amount(value):

    if value is None:
        return Decimal("0.00")

    if isinstance(value, float):

        if math.isnan(value):
            return Decimal("0.00")

    value = str(value)

    value = value.replace(",", "")
    value = value.replace(" ", "")

    value = re.sub(
        r"[^0-9.-]",
        "",
        value,
    )

    if value == "":
        value = "0"

    return Decimal(value).quantize(
        Decimal("0.01")
    )


def normalize_date(value):

    if value is None:
        return None

    if isinstance(value, float):

        if math.isnan(value):
            return None

    value = str(value).strip()

    value = value.replace(
        "/",
        "-"
    )

    return parser.parse(
        value,
        fuzzy=True,
    )


def normalize_reference(value):

    if value is None:
        return None

    if isinstance(value, float):

        import math

        if math.isnan(value):
            return None

    value = str(value).strip()

    if value.lower() == "nan":
        return None

    if value == "":
        return None

    return value.lower()