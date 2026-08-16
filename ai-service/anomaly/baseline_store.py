import json
import os


# ============================================================
# EXISTING RULE-BASED BASELINE
# ============================================================

BASELINE_FILE = "baseline.json"


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return {}

    with open(BASELINE_FILE, "r") as f:
        return json.load(f)


def save_baseline(data):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f)


# ============================================================
# ISOLATION FOREST BASELINE
# ============================================================

ML_BASELINE_FILE = "ml_baseline.json"


def load_ml_baseline():
    if not os.path.exists(ML_BASELINE_FILE):
        return []

    try:
        with open(ML_BASELINE_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        return data

    except (json.JSONDecodeError, OSError):
        return []


def save_ml_baseline(data):
    with open(ML_BASELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)