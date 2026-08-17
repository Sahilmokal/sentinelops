"""
Legacy baseline storage module.

Rule-based detectors are now stateless and no longer use
baseline.json.

Isolation Forest persistence is handled by Elasticsearch
through storage.ml_storage.
"""

from storage.ml_storage import (
    load_ml_baseline,
    save_ml_baseline_window,
    save_ml_result,
    ml_baseline_window_exists,
    load_latest_ml_result,
)


__all__ = [
    "load_ml_baseline",
    "save_ml_baseline_window",
    "save_ml_result",
    "ml_baseline_window_exists",
    "load_latest_ml_result",
]