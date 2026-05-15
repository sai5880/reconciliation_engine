from rapidfuzz import fuzz
from itertools import combinations
from models import MatchResult
from rules import (
    AmountToleranceRule,
    DateWindowRule,
    ExactAmountRule,
    ReferenceRule,
    VendorFuzzyRule,
)
from logger import log
from validators import normalize_vendor
from config import TIME_ANOMALY_DAYS
import pandas as pd

RULES = [
    ExactAmountRule(),
    ReferenceRule(),
    DateWindowRule(),
    AmountToleranceRule(),
    VendorFuzzyRule(),
]

class ReconciliationMatcher:

    def __init__(self, options):
        self.options = options
    def safe_date_diff(self, date1, date2):

        if pd.isna(date1) or pd.isna(date2):
            return None

        return abs((date1 - date2).days)
    def calculate_confidence(self, matched_rules):
        total = sum(rule.weight for rule in RULES)
        matched = sum(rule.weight for rule in matched_rules)

        return round((matched / total) * 100, 2)

    def build_anomaly_flags(
        self,
        bank,
        gl,
        amount_difference,
        time_threshold,
        tolerance,
    ):

        bank_amount = float(bank.amount)
        gl_amount = float(gl.amount)

        date_diff = self.safe_date_diff(
            bank.date,
            gl.date,
        )

        round_amount_match = (
            int(gl_amount) == int(bank_amount)
            or round(gl_amount, 1)
            == round(bank_amount, 1)
        )

        unusual_amount = (
            amount_difference > tolerance
        )

        unusual_dates = (
            date_diff is not None
            and date_diff > time_threshold
        )

        missing_data = (
            pd.isna(bank.date)
            or pd.isna(bank.amount)
            or not bank.description
            or pd.isna(gl.date)
            or pd.isna(gl.amount)
            or not gl.description
        )

        confidence = round(
            max(
                0,
                (
                    1 -
                    (
                        abs(
                            bank_amount
                            - gl_amount
                        )
                        /
                        max(bank_amount, 1)
                    )
                ) * 100
            ),
            2,
        )

        return {
            "round_amount_match":
                round_amount_match,

            "unusual_amount":
                unusual_amount,

            "unusual_dates":
                unusual_dates,

            "missing_data":
                missing_data,

            "confidence":
                confidence,
        }


    def exact_match(self, bank_txns, gl_txns):

        matches = []
        used_gl = set()
        # date_tolerance is the date window used by matching rules
        date_tolerance = self.options.get(
            "date_tolerance_days",
            10,
        )

        # time anomaly threshold (separate single-point config)
        time_threshold = self.options.get(
            "time_anomaly_days",
            TIME_ANOMALY_DAYS,
        )

        for bank in bank_txns:

            for gl in gl_txns:

                if gl.id in used_gl:
                    continue

                matched_rules = [
                    rule
                    for rule in RULES
                    if rule.evaluate(bank, gl, self.options)
                ]

                names = [r.name for r in matched_rules]

                if "exact_amount" not in names:
                    continue

                if "date_window" not in names:
                    continue
                date_difference_days = 0
                if bank.date and gl.date:
                    date_difference_days = abs((bank.date - gl.date).days)
                date_diff = self.safe_date_diff(
                    bank.date,
                    gl.date,
                )
                time_anomaly_6_months = (
                    date_diff is not None
                    and date_diff > time_threshold
                )
                confidence = self.calculate_confidence(matched_rules)
                amount_difference = round(
                    abs(
                        float(bank.amount)
                        - float(gl.amount)
                    ),
                    2,
                )

                anomaly_flags = self.build_anomaly_flags(
                    bank,
                    gl,
                    amount_difference,
                    time_threshold,
                    date_tolerance,
                )
                matches.append(
                    MatchResult(
                        bank_id=bank.id,
                        gl_id=gl.id,
                        bank_description=bank.description,
                        gl_description=gl.description,
                        confidence=confidence,
                        matched_rules=names,
                        explanation={"match_type": "exact","anomaly_flags": anomaly_flags,"bank_amount": float(bank.amount),"gl_amount": float(gl.amount),"bank_date": str(bank.date),"gl_date": str(gl.date),"date_difference_days": date_difference_days,"time_anomaly_6_months": time_anomaly_6_months,},
                    )
                )
                used_gl.add(gl.id)
                break
        return matches

    def fuzzy_match(self, bank_txns, gl_txns):
        matches = []
        used_gl = set()
        amount_tolerance = self.options.get("amount_tolerance",100)
        date_tolerance = self.options.get("date_tolerance_days",10)
        time_threshold = self.options.get("time_anomaly_days", TIME_ANOMALY_DAYS)

        for bank in bank_txns:
            for gl in gl_txns:
                if gl.id in used_gl:
                    continue

                matched_rules = [
                    rule
                    for rule in RULES
                    if rule.evaluate(bank, gl, self.options)
                ]

                names = [r.name for r in matched_rules]
                required = {"amount_tolerance","date_window","vendor_fuzzy",}
                if not required.issubset(names):
                    continue

                # confidence = self.calculate_confidence(matched_rules)
                vendor_score = fuzz.token_sort_ratio(normalize_vendor(bank.description),normalize_vendor(gl.description))
                amount_diff = abs(float(bank.amount) - float(gl.amount))
                date_diff = self.safe_date_diff(
                    bank.date,
                    gl.date,
                )

                time_anomaly_6_months = (
                    date_diff is not None
                    and date_diff > time_threshold
                )
                amount_score = max(0,100 - (amount_diff / amount_tolerance) * 100)
                date_score = max(0,100 - (date_diff / date_tolerance) * 100)
                confidence = round(amount_score * 0.4 +date_score * 0.2 +vendor_score * 0.4,2)
                anomaly_flags = self.build_anomaly_flags(
                    bank,
                    gl,
                    amount_diff,
                    time_threshold,
                    amount_tolerance,
                )
                matches.append(
                    MatchResult(
                        bank_id=bank.id,
                        gl_id=gl.id,
                        bank_description=bank.description,
                        gl_description=gl.description,
                        confidence=confidence,
                        matched_rules=names,
                        explanation={
                            "match_type": "fuzzy",
                            "anomaly_flags": anomaly_flags,
                            "normalized_bank_vendor": normalize_vendor(bank.description),
                            "normalized_gl_vendor": normalize_vendor(gl.description),
                            "bank_amount": float(bank.amount),
                            "gl_amount": float(gl.amount),
                            "amount_difference": round(abs(float(bank.amount) - float(gl.amount)),2),
                            "bank_date": str(bank.date),
                            "gl_date": str(gl.date),
                            "date_difference_days": abs((bank.date - gl.date).days),
                            "time_anomaly_6_months": time_anomaly_6_months,
                        },
                    )
                )

                used_gl.add(gl.id)
                break

        return matches
    
    def amount_only_match(self,bank_txns,gl_txns):
        matches = []
        tolerance = self.options.get("amount_tolerance",100)
        date_tolerance = self.options.get("date_tolerance_days",10)
        time_threshold = self.options.get("time_anomaly_days", TIME_ANOMALY_DAYS)
        used_gl = set()
        for bank in bank_txns:
            for gl in gl_txns:
                if gl.id in used_gl:
                    continue

                amount_diff = abs(float(bank.amount) - float(gl.amount))
                if amount_diff > tolerance:
                    continue

                date_diff = self.safe_date_diff(
                    bank.date,
                    gl.date,
                )
                
                time_anomaly = (date_diff is not None and date_diff > time_threshold)
                confidence = round(max(0,100 - ((amount_diff / tolerance) * 100),),2,)
                anomaly_flags = self.build_anomaly_flags(
                    bank,
                    gl,
                    amount_diff,
                    time_threshold,
                    tolerance,
                )
                matches.append(
                    MatchResult(
                        bank_id=bank.id,
                        gl_id=gl.id,
                        bank_description=bank.description,
                        gl_description=gl.description,
                        confidence=confidence,
                        matched_rules=["amount_only_match"],
                        explanation={
                            "match_type":"amount_only",
                            "anomaly_flags": anomaly_flags,
                            "bank_amount":float(bank.amount),
                            "gl_amount":float(gl.amount),
                            "amount_difference":round(amount_diff,2,),
                            "bank_date":str(bank.date),
                            "gl_date":str(gl.date),
                            "date_difference_days":date_diff,
                            "time_anomaly":time_anomaly,
                            "vendor_check_skipped":True,
                        },
                    )
                )

                used_gl.add(gl.id)

                break

        return matches


    def complex_match(self,bank_txns,gl_txns):
        matches=[]
        tolerance=self.options.get("amount_tolerance",100)
        date_tolerance=self.options.get("date_tolerance_days",10)
        time_threshold = self.options.get("time_anomaly_days", TIME_ANOMALY_DAYS)
        vendor_threshold=self.options.get("vendor_threshold",80)
        max_matches=self.options.get("max_complex_matches",100000)
        max_candidates_per_bank=self.options.get("max_candidates_per_bank",50)
        max_candidate_date_window=self.options.get("max_candidate_date_window",5)

        log(f"Complex match starting: {len(bank_txns)} bank txns, {len(gl_txns)} GL txns")

        for bank_idx,bank in enumerate(bank_txns,1):

            if bank_idx % 10 == 0: log(f"Complex match processing: {bank_idx}/{len(bank_txns)}")

            bank_vendor=normalize_vendor(bank.description)
            candidates=[]
            valid_gl=[]

            for gl in gl_txns:

                gl_vendor=normalize_vendor(gl.description)
                vendor_score=fuzz.token_sort_ratio(bank_vendor,gl_vendor,)

                if vendor_score < vendor_threshold: continue

                date_delta=self.safe_date_diff(bank.date,gl.date,)

                if (date_delta is not None and date_delta > max_candidate_date_window): continue

                valid_gl.append(gl)

            valid_gl.sort(key=lambda x: abs(float(bank.amount) - float(x.amount),))
            valid_gl=valid_gl[:max_candidates_per_bank]

            for size in [2,3]:

                if len(valid_gl) < size: continue

                for combo in combinations(valid_gl,size):

                    combo_total=sum(float(x.amount) for x in combo)
                    amount_diff=abs(float(bank.amount) - combo_total)

                    if amount_diff > tolerance: continue

                    vendor_scores=[fuzz.token_sort_ratio(bank_vendor,normalize_vendor(x.description),) for x in combo]
                    avg_vendor_score=(sum(vendor_scores) / len(vendor_scores))

                    date_deltas=[]

                    for x in combo:
                        diff=self.safe_date_diff(bank.date,x.date,)
                        if diff is not None: date_deltas.append(diff)

                    max_date_delta=max(date_deltas) if date_deltas else None

                    time_anomaly_6_months=(max_date_delta is not None and max_date_delta > time_threshold)

                    confidence=round(((100 - amount_diff) * 0.5) + (avg_vendor_score * 0.5),2,)
                    bank_amount = float(bank.amount)
                    gl_amount = combo_total
                    
                    round_amount_match = (
                        int(gl_amount) == int(bank_amount)
                        or round(gl_amount, 1) == round(bank_amount, 1)
                    )
                    
                    unusual_amount = (
                        abs(bank_amount - gl_amount)
                        > tolerance
                    )
                    anomaly_flags = {
                        "round_amounts":
                            round_amount_match,

                        "unusual_amount":
                            unusual_amount,

                        "unusual_dates": (
                            time_anomaly_6_months
                        ),

                        "missing_data": (
                            pd.isna(bank.date)
                            or pd.isna(bank.amount)
                            or not bank.description
                            or any(
                                pd.isna(x.date)
                                or pd.isna(x.amount)
                                or not x.description
                                for x in combo
                            )
                        ),
                    }
                    candidates.append({
                        "gl_ids":[x.id for x in combo],
                        "gl_descriptions":[x.description for x in combo],
                        "gl_vendor_normalized":[normalize_vendor(x.description) for x in combo],
                        "gl_dates":[str(x.date) for x in combo],
                        "date_differences_days":[self.safe_date_diff(bank.date,x.date,) for x in combo],
                        "date_differences":[
                            {
                                "bank_date": str(bank.date),
                                "gl_date": str(x.date),
                                "difference_days": self.safe_date_diff(
                                    bank.date,
                                    x.date,
                                ),
                                "bank_id": bank.id,
                                "gl_id": x.id,
                            }
                            for x in combo
                        ],
                        "candidate_anomalies": [
                            {
                                "bank_id": bank.id,
                                "gl_id": x.id,
                                "confidence": round(
                                    max(
                                        0,
                                        (
                                            1 -
                                            (
                                                abs(
                                                    float(bank.amount)
                                                    - float(x.amount)
                                                )
                                                /
                                                max(float(bank.amount), 1)
                                            )
                                        ) * 100
                                    ),
                                    2,
                                ),
                                "round_amount_match": (
                                    int(float(x.amount)) == int(float(bank.amount))
                                    or round(float(x.amount), 1)
                                    == round(float(bank.amount), 1)
                                ),

                                "unusual_amount": (
                                    abs(float(bank.amount) - float(x.amount))
                                    > tolerance
                                ),

                                "unusual_dates": (
                                    self.safe_date_diff(
                                        bank.date,
                                        x.date,
                                    ) > time_threshold
                                    if self.safe_date_diff(
                                        bank.date,
                                        x.date,
                                    ) is not None
                                    else False
                                ),

                                "missing_data": (
                                    pd.isna(x.date)
                                    or pd.isna(x.amount)
                                    or not x.description
                                ),

                                "difference_days": self.safe_date_diff(
                                    bank.date,
                                    x.date,
                                ),

                                "amount_difference": round(
                                    abs(
                                        float(bank.amount)
                                        - float(x.amount)
                                    ),
                                    2,
                                ),
                            }

                            for x in combo
                        ],
                        "combined_gl_amount":round(combo_total,2),
                        "amount_difference":round(amount_diff,2),
                        
                        "vendor_score":round(avg_vendor_score,2),
                        "date_difference_days":max_date_delta,
                        "time_anomaly_6_months":time_anomaly_6_months,
                        "confidence":confidence,
                        "matched_rules":["multi_transaction_match","vendor_group_match","date_window_match"],
                    })

            candidates.sort(key=lambda x: x["confidence"],reverse=True,)

            if not candidates: continue

            matches.append({
                "bank_id":bank.id,
                "bank_description":bank.description,
                "bank_vendor_normalized":bank_vendor,
                "bank_amount":float(bank.amount),
                "bank_date":str(bank.date),
                "candidate_matches":candidates[:5],
                "match_type":"complex",
                "explanation":{"matching_strategy":"multi_transaction_group_matching","candidate_count":len(candidates),},
            })

            if len(matches) >= max_matches: break

        log(f"Complex match completed: {len(matches)} matches found")

        return matches

