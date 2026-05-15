from collections import defaultdict
from datetime import timedelta

from validators import normalize_vendor


def detect_time_series_anomalies(
    transactions,
    months=1,
):

    anomalies = []

    vendor_history = defaultdict(list)

    sorted_txns = sorted(
        transactions,
        key=lambda x: x.date,
    )

    print("\n" + "=" * 80)
    print("RUNNING TIME SERIES ANOMALY DETECTION")
    print("=" * 80)

    for txn in sorted_txns:

        vendor = normalize_vendor(
            txn.description
        )

        current_amount = round(
            float(txn.amount),
            2,
        )

        cutoff_date = txn.date - timedelta(
            days=30 * months
        )

        historical_transactions = [

            old

            for old in vendor_history[vendor]

            if cutoff_date <= old.date < txn.date
        ]

        historical_amounts = {

            round(float(old.amount), 2)

            for old in historical_transactions
        }

        print("\n" + "-" * 80)

        print(
            f"TXN: {txn.id}"
        )

        print(
            f"Vendor: {vendor}"
        )

        print(
            f"Current Amount: {current_amount}"
        )

        print(
            f"Historical Count: {len(historical_transactions)}"
        )

        print(
            f"Historical Amounts: {sorted(list(historical_amounts))[:15]}"
        )

        if (
            historical_transactions
            and current_amount not in historical_amounts
        ):

            print(
                "ANOMALY DETECTED"
            )

            anomalies.append({

                "transaction_id": txn.id,

                "vendor": vendor,

                "amount": current_amount,

                "source": txn.source,

                "date": str(txn.date),

                "historical_transaction_count": len(
                    historical_transactions
                ),

                "historical_amounts": sorted(
                    list(historical_amounts)
                )[:10],

                "anomaly_type": f"amount_not_seen_in_{months}_months",
            })

        vendor_history[vendor].append(
            txn
        )

    print("\n" + "=" * 80)

    print(
        f"TOTAL ANOMALIES DETECTED: {len(anomalies)}"
    )

    print("=" * 80)

    return anomalies