import json
import os


ML_RESULT_FILE = "ml_result.json"


def save_ml_result(result):
    with open(ML_RESULT_FILE, "w") as f:
        json.dump(result, f, indent=2)


def load_ml_result():
    if not os.path.exists(ML_RESULT_FILE):
        return None

    with open(ML_RESULT_FILE, "r") as f:
        return json.load(f)