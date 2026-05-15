import pandas as pd

from logger import log, section
from matcher import ReconciliationMatcher
from reporting import generate_response

from models import Transaction

from validators import (
    normalize_amount,
    normalize_date,
    normalize_reference,
)

from config import (
    BANK_FIXTURE_FILE,
    GL_FIXTURE_FILE,
    LOG_MATCH_SAMPLES,
    LOG_MATCH_LIMIT,
)


def load_transactions(df):

    transactions = []

    for _, row in df.iterrows():

        try:

            txn = Transaction(
                id=str(row.get("id", "")),
                amount=normalize_amount(row.get("amount")),
                date=normalize_date(row.get("date")),
                description=str(row.get("description", "")),
                reference=normalize_reference(row.get("reference")),
                source=str(row.get("source", "")),
            )

            transactions.append(txn)

        except Exception as e:

            log(f"Failed transaction: {e}")

    return transactions


def print_match_sample(title, matches):

    if not LOG_MATCH_SAMPLES:
        return

    section(title)

    if not matches:
        log("No matches found")
        return

    for idx, match in enumerate(matches[:LOG_MATCH_LIMIT], start=1):

        item = match.model_dump() if hasattr(match, "model_dump") else match

        log(f"\nMatch #{idx}")

        for key, value in item.items():
            log(f"{key}: {value}")


def run_cli():

    section("LOADING RECONCILIATION ENGINE")

    log(f"Loading Bank File: {BANK_FIXTURE_FILE}")
    log(f"Loading GL File: {GL_FIXTURE_FILE}")

    bank_df = pd.read_csv(BANK_FIXTURE_FILE, encoding_errors="ignore")
    gl_df = pd.read_csv(GL_FIXTURE_FILE, encoding_errors="ignore")

    bank_transactions = load_transactions(bank_df)
    gl_transactions = load_transactions(gl_df)

    section("TRANSACTION SUMMARY")

    log(f"Bank Transactions Loaded: {len(bank_transactions)}")
    log(f"GL Transactions Loaded: {len(gl_transactions)}")

    matcher = ReconciliationMatcher(
        options={
            "use_reference_match": False,
            "amount_tolerance": 100,
            "date_tolerance_days": 10,
            "vendor_threshold": 80,
        }
    )

    section("RUNNING EXACT MATCH ENGINE")

    exact_matches = matcher.exact_match(
        bank_transactions,
        gl_transactions,
    )

    log(f"Exact Matches Found: {len(exact_matches)}")

    section("RUNNING FUZZY MATCH ENGINE")

    fuzzy_matches = matcher.fuzzy_match(
        bank_transactions,
        gl_transactions,
    )

    log(f"Fuzzy Matches Found: {len(fuzzy_matches)}")

    section("RUNNING COMPLEX MATCH ENGINE")

    complex_matches = matcher.complex_match(
        bank_transactions,
        gl_transactions,
    )

    log(f"Complex Matches Found: {len(complex_matches)}")

    section("RUNNING AMOUNT-ONLY MATCH ENGINE")

    amount_only_matches = matcher.amount_only_match(
        bank_transactions,
        gl_transactions,
    )

    log(f"Amount-Only Matches Found: {len(amount_only_matches)}")

    report = generate_response(
        exact_matches,
        fuzzy_matches,
        complex_matches,
        amount_only_matches,
    )

    matched_bank_ids = set()

    for match in exact_matches:
        matched_bank_ids.add(match.bank_id)

    for match in fuzzy_matches:
        matched_bank_ids.add(match.bank_id)

    for match in complex_matches:
        matched_bank_ids.add(match["bank_id"])

    for match in amount_only_matches:
        matched_bank_ids.add(match.bank_id)

    unmatched = [
        txn
        for txn in bank_transactions
        if txn.id not in matched_bank_ids
    ]

    section("FINAL RECONCILIATION SUMMARY")

    log(f"Exact Matches: {len(exact_matches)}")
    log(f"Fuzzy Matches: {len(fuzzy_matches)}")
    log(f"Complex Matches: {len(complex_matches)}")
    log(f"Amount-Only Matches: {len(amount_only_matches)}")
    log(f"Pending / Unmatched Transactions: {len(unmatched)}")
    log(f"Completed Reconciliations: {len(matched_bank_ids)}")

    completion_rate = round(
        (len(matched_bank_ids) / len(bank_transactions)) * 100,
        2,
    )

    log(f"Completion Rate: {completion_rate}%")

    print_match_sample("EXACT MATCH SAMPLE", exact_matches)
    print_match_sample("FUZZY MATCH SAMPLE", fuzzy_matches)
    print_match_sample("COMPLEX MATCH SAMPLE", complex_matches)

    section("REPORT FILES GENERATED")

    log("reports/exact_matches.csv")
    log("reports/fuzzy_matches.csv")
    log("reports/complex_matches.csv")
    log("reports/summary.json")
    log("reports/README.md")

    section("RECONCILIATION COMPLETE")