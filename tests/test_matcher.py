import pandas as pd

from matcher import ReconciliationMatcher

from models import Transaction

from validators import (
    normalize_amount,
    normalize_date,
    normalize_reference,
)

from config import (
    BANK_FIXTURE_FILE,
    GL_FIXTURE_FILE,
)


def load_transactions(df):

    transactions = []

    for _, row in df.iterrows():

        txn = Transaction(
            id=str(row.get("id")),
            amount=normalize_amount(
                row.get("amount")
            ),
            date=normalize_date(
                row.get("date")
            ),
            description=str(
                row.get("description")
            ),
            reference=normalize_reference(
                row.get("reference")
            ),
            source=str(
                row.get("source")
            ),
        )

        transactions.append(txn)

    return transactions


def test_matching_engine():

    bank_df = pd.read_csv(
        BANK_FIXTURE_FILE,
        encoding_errors="ignore",
    )

    gl_df = pd.read_csv(
        GL_FIXTURE_FILE,
        encoding_errors="ignore",
    )

    bank_transactions = load_transactions(
        bank_df
    )

    gl_transactions = load_transactions(
        gl_df
    )

    matcher = ReconciliationMatcher(
        options={
            "use_reference_match": False,
            "amount_tolerance": 100,
            "date_tolerance_days": 10,
            "vendor_threshold": 80,
        }
    )

    exact_matches = matcher.exact_match(
        bank_transactions,
        gl_transactions,
    )

    fuzzy_matches = matcher.fuzzy_match(
        bank_transactions,
        gl_transactions,
    )

    complex_matches = matcher.complex_match(
        bank_transactions,
        gl_transactions,
    )

    assert isinstance(
        exact_matches,
        list,
    )

    assert isinstance(
        fuzzy_matches,
        list,
    )

    assert isinstance(
        complex_matches,
        list,
    )