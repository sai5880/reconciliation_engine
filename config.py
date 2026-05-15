from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

FIXTURES_DIR = BASE_DIR / "tests"/ "fixtures"

BANK_FIXTURE_FILE = FIXTURES_DIR /"bank.csv"

GL_FIXTURE_FILE = FIXTURES_DIR /"gl.csv"


ENABLE_FASTAPI = True

# =========================
# LOGGING CONFIG
# =========================

ENABLE_LOGGING = True

LOG_MATCH_SAMPLES = True

LOG_MATCH_LIMIT = 5

# Time anomaly threshold (days). Change in one place to adjust UI/backend behavior.
# Default 10 days to make it easy to spot distant-date matches during debugging.
TIME_ANOMALY_DAYS = 10