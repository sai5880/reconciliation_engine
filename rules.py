from rapidfuzz import fuzz

from validators import normalize_vendor


class Rule:
    name = ""
    weight = 0

    def evaluate(self, bank_txn, gl_txn, options):
        raise NotImplementedError


class ExactAmountRule(Rule):
    name = "exact_amount"
    weight = 40

    def evaluate(self, bank_txn, gl_txn, options):
        return bank_txn.amount == gl_txn.amount


class ReferenceRule(Rule):
    name = "reference"
    weight = 30

    def evaluate(self, bank_txn, gl_txn, options):
        if not options.get("use_reference_match"):
            return False

        if not bank_txn.reference or not gl_txn.reference:
            return False

        return (
            bank_txn.reference.lower().strip()
            == gl_txn.reference.lower().strip()
        )


class DateWindowRule(Rule):
    name = "date_window"
    weight = 10

    def evaluate(self, bank_txn, gl_txn, options):
        days = options.get("date_tolerance_days", 10)

        if not bank_txn.date or not gl_txn.date:
            return False

        delta = abs((bank_txn.date - gl_txn.date).days)

        return delta <= days


class AmountToleranceRule(Rule):
    name = "amount_tolerance"
    weight = 10

    def evaluate(self, bank_txn, gl_txn, options):
        tolerance = options.get("amount_tolerance", 100)

        diff = abs(bank_txn.amount - gl_txn.amount)

        return diff <= tolerance


class VendorFuzzyRule(Rule):
    name = "vendor_fuzzy"
    weight = 10

    def evaluate(self, bank_txn, gl_txn, options):
        left = normalize_vendor(bank_txn.description)
        right = normalize_vendor(gl_txn.description)

        score = fuzz.token_sort_ratio(left, right)

        return score >= options.get("vendor_threshold", 80)