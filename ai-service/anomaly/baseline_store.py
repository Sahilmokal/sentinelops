import json
import os

BASELINE_FILE = "baseline.json"


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return {}

    with open(BASELINE_FILE, "r") as f:
        return json.load(f)


def save_baseline(data):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f)