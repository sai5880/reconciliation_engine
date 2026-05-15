import json
from pathlib import Path

import pandas as pd

from validators import normalize_vendor


REPORTS_DIR = Path("reports")

REPORTS_DIR.mkdir(
    exist_ok=True
)


def save_csv(
    data,
    filename,
):

    if not data:
        return

    rows = []

    for item in data:

        if hasattr(
            item,
            "model_dump",
        ):

            item = item.model_dump()

        if (
            isinstance(item, dict)
            and "candidate_matches" in item
        ):

            for candidate in item[
                "candidate_matches"
            ]:

                rows.append({

                    "bank_id": item[
                        "bank_id"
                    ],

                    "bank_description": item[
                        "bank_description"
                    ],

                    "bank_vendor_normalized": item[
                        "bank_vendor_normalized"
                    ],

                    "bank_amount": item[
                        "bank_amount"
                    ],

                    "gl_ids": json.dumps(
                        candidate["gl_ids"]
                    ),

                    "gl_descriptions": json.dumps(
                        candidate[
                            "gl_descriptions"
                        ]
                    ),

                    "gl_vendor_normalized": json.dumps(
                        candidate[
                            "gl_vendor_normalized"
                        ]
                    ),

                    "combined_gl_amount": candidate[
                        "combined_gl_amount"
                    ],

                    "amount_difference": candidate[
                        "amount_difference"
                    ],

                    "vendor_score": candidate[
                        "vendor_score"
                    ],

                    "date_difference_days": candidate.get(
                        "date_difference_days"
                    ),

                    "time_anomaly_6_months": candidate.get(
                        "time_anomaly_6_months"
                    ),

                    "confidence": candidate[
                        "confidence"
                    ],

                    "matched_rules": json.dumps(
                        candidate[
                            "matched_rules"
                        ]
                    ),

                    "match_type": item[
                        "match_type"
                    ],
                })

        else:

            explanation = item.get(
                "explanation",
                {},
            )

            rows.append({

                "bank_id": item.get(
                    "bank_id"
                ),

                "gl_id": item.get(
                    "gl_id"
                ),

                "bank_description": item.get(
                    "bank_description"
                ),

                "gl_description": item.get(
                    "gl_description"
                ),

                "confidence": item.get(
                    "confidence"
                ),

                "matched_rules": json.dumps(
                    item.get(
                        "matched_rules",
                        [],
                    )
                ),

                "match_type": explanation.get(
                    "match_type"
                ),

                "bank_amount": explanation.get(
                    "bank_amount"
                ),

                "gl_amount": explanation.get(
                    "gl_amount"
                ),

                "amount_difference": explanation.get(
                    "amount_difference"
                ),

                "bank_date": explanation.get(
                    "bank_date"
                ),

                "gl_date": explanation.get(
                    "gl_date"
                ),

                "date_difference_days": explanation.get(
                    "date_difference_days"
                ),

                "time_anomaly_6_months": explanation.get(
                    "time_anomaly_6_months"
                ),

                "normalized_bank_vendor": explanation.get(
                    "normalized_bank_vendor"
                ),

                "normalized_gl_vendor": explanation.get(
                    "normalized_gl_vendor"
                ),
            })

    pd.DataFrame(rows).to_csv(
        REPORTS_DIR / filename,
        index=False,
    )


def generate_vendor_groups(
    matches,
):

    groups = {}

    for match in matches:

        if hasattr(
            match,
            "model_dump",
        ):

            match = match.model_dump()

        bank_vendor = normalize_vendor(
            match[
                "bank_description"
            ]
        )

        gl_vendor = normalize_vendor(
            match[
                "gl_description"
            ]
        )

        if bank_vendor not in groups:

            groups[
                bank_vendor
            ] = set()

        groups[
            bank_vendor
        ].add(
            gl_vendor
        )

    return {

        k: sorted(list(v))

        for k, v in groups.items()
    }


def generate_summary(
    exact_matches,
    fuzzy_matches,
    complex_matches,
    amount_only_matches,
):

    return {
        "exact_match_count": len(exact_matches),
        "fuzzy_match_count": len(fuzzy_matches),
        "complex_match_count": len(complex_matches),
        "total_matches": (len(exact_matches) + len(fuzzy_matches) + len(complex_matches) + len(amount_only_matches)),
        "vendor_groups": generate_vendor_groups(fuzzy_matches),
        "amount_only_matches": len(amount_only_matches),
    }


def generate_readme(
    summary,
):

    lines = [

        "# Reconciliation Report",

        "",

        "## Match Summary",

        "",

        f"- Exact Matches: {summary['exact_match_count']}",

        f"- Fuzzy Matches: {summary['fuzzy_match_count']}",

        f"- Complex Matches: {summary['complex_match_count']}",

        f"- Total Matches: {summary['total_matches']}",

        "",

        "## Vendor Grouping",

        "",
    ]

    for (
        bank_vendor,
        gl_vendors,
    ) in summary[
        "vendor_groups"
    ].items():

        lines.append(
            f"### {bank_vendor}"
        )

        for vendor in gl_vendors:

            lines.append(
                f"- {vendor}"
            )

        lines.append("")

    with open(
        REPORTS_DIR / "README.md",
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "\n".join(lines)
        )


def generate_response(
    exact_matches,
    fuzzy_matches,
    complex_matches,
    amount_only_matches,
):

    save_csv(
        exact_matches,
        "exact_matches.csv",
    )

    save_csv(
        fuzzy_matches,
        "fuzzy_matches.csv",
    )

    save_csv(
        complex_matches,
        "complex_matches.csv",
    )

    save_csv(amount_only_matches, "amount_only_matches.csv")

    summary = generate_summary(
        exact_matches,
        fuzzy_matches,
        complex_matches,
        amount_only_matches,
    )

    with open(
        REPORTS_DIR / "summary.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            indent=4,
        )

    generate_readme(
        summary
    )

    return {
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "complex_matches": complex_matches,
        "amount_only_matches": amount_only_matches,
        "summary": summary,
    }