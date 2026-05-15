from decimal import Decimal
from datetime import datetime

from models import Transaction

from rules import (
    ExactAmountRule,
    VendorFuzzyRule,
)


def sample_transaction():

    return Transaction(
        id="1",
        amount=Decimal("100.00"),
        date=datetime.now(),
        description="ABC Inc",
        reference="REF1",
        source="bank",
    )


def test_exact_amount_rule():

    left = sample_transaction()

    right = sample_transaction()

    rule = ExactAmountRule()

    result = rule.evaluate(
        left,
        right,
        {},
    )

    assert result is True


def test_vendor_fuzzy_rule():

    left = sample_transaction()

    right = sample_transaction()

    right.description = (
        "ABC Incorporated"
    )

    rule = VendorFuzzyRule()

    result = rule.evaluate(
        left,
        right,
        {
            "vendor_threshold": 80
        },
    )

    assert result is True