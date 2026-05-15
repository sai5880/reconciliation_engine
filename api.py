import io

import pandas as pd

from fastapi import FastAPI, UploadFile, File, Form
from matcher import ReconciliationMatcher
from models import Transaction

from validators import (
    normalize_amount,
    normalize_date,
    normalize_reference
)

from reporting import generate_response
from fastapi.middleware.cors import CORSMiddleware
from logger import log

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_transactions(df):

    transactions = []

    for _, row in df.iterrows():

        try:

            txn = Transaction(
                id=str(row.get("id", "")),
                amount=normalize_amount(
                    row.get("amount")
                ),
                date=normalize_date(
                    row.get("date")
                ),
                description=str(
                    row.get("description", "")
                ),
                reference=normalize_reference(
                    row.get("reference")
                ),
                source=str(
                    row.get("source", "")
                ),
            )

            transactions.append(txn)

        except Exception as e:

            print(
                f"Failed transaction: {e}"
            )

    return transactions

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reconcile")
async def reconcile(
    bank_file: UploadFile = File(...),
    gl_file: UploadFile = File(...),

    enable_exact: bool = Form(True),
    enable_fuzzy: bool = Form(True),
    enable_complex: bool = Form(False),
    enable_amount_only: bool = Form(False),
    use_reference_match: bool = Form(True),

    amount_tolerance: float = Form(100),

    date_tolerance_days: int = Form(10),

    vendor_threshold: int = Form(80),
):

    log("=" * 80)
    log("RECONCILE REQUEST RECEIVED")
    log("=" * 80)
    log(f"Enable Exact: {enable_exact}, Fuzzy: {enable_fuzzy}, Complex: {enable_complex}")

    bank_content = await bank_file.read()
    gl_content = await gl_file.read()

    log(f"Bank file size: {len(bank_content)} bytes")
    log(f"GL file size: {len(gl_content)} bytes")

    bank_df = pd.read_csv(
        io.BytesIO(bank_content),
        encoding_errors="ignore",
    )

    gl_df = pd.read_csv(
        io.BytesIO(gl_content),
        encoding_errors="ignore",
    )

    log(f"Bank transactions loaded: {len(bank_df)}")
    log(f"GL transactions loaded: {len(gl_df)}")

    bank_transactions = load_transactions(bank_df)

    gl_transactions = load_transactions(gl_df)

    log(f"Bank transactions processed: {len(bank_transactions)}")
    log(f"GL transactions processed: {len(gl_transactions)}")

    matcher = ReconciliationMatcher(
        options={
            "use_reference_match": use_reference_match,
            "amount_tolerance": amount_tolerance,
            "date_tolerance_days": date_tolerance_days,
            "vendor_threshold": vendor_threshold,
        }
    )

    exact_matches = []
    fuzzy_matches = []
    complex_matches = []
    amount_only_matches = []

    if enable_exact:
        log("Starting exact match...")
        exact_matches = matcher.exact_match(
            bank_transactions,
            gl_transactions,
        )
        log(f"Exact matches found: {len(exact_matches)}")

    if enable_fuzzy:
        log("Starting fuzzy match...")
        fuzzy_matches = matcher.fuzzy_match(
            bank_transactions,
            gl_transactions,
        )
        log(f"Fuzzy matches found: {len(fuzzy_matches)}")

    if enable_complex:
        log("Starting complex match...")
        complex_matches = matcher.complex_match(
            bank_transactions,
            gl_transactions,
        )
        log(f"Complex matches found: {len(complex_matches)}")

    if enable_amount_only:
        log("Starting amount-only match...")
        amount_only_matches = matcher.amount_only_match(
            bank_transactions,
            gl_transactions,
        )
        log(f"Amount-only matches found: {len(amount_only_matches)}")

    log("Generating response...")

    return generate_response(
        exact_matches,
        fuzzy_matches,
        complex_matches,
        amount_only_matches,
    )