from validators import (
    normalize_amount,
    normalize_date,
    normalize_vendor,
    normalize_reference,
)


def test_normalize_amount():

    value = normalize_amount(
        "  47695. 41"
    )

    assert float(value) == 47695.41


def test_normalize_date():

    date = normalize_date(
        "05-14/2024"
    )

    assert date is not None


def test_normalize_vendor():

    left = normalize_vendor(
        "ABC Inc."
    )

    right = normalize_vendor(
        "ABC INCORPORATED"
    )

    assert left == right


def test_normalize_reference():

    value = normalize_reference(None)

    assert value is None