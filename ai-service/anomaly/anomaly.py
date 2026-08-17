from collections import Counter

import numpy as np

from storage.ml_storage import load_latest_ml_result
# ============================================================
# RARE LOG DETECTION
# ============================================================

def detect_rare_logs(logs, threshold=3):
    """
    Detect messages that occur only a small number of times
    in the current analysis window.

    This detector is stateless.
    """

    if not logs:
        return []

    messages = [
        log["message"]
        for log in logs
        if "message" in log
    ]

    counter = Counter(messages)

    rare_messages = []

    for message, count in counter.items():

        if count < threshold:
            rare_messages.append({
                "message": message,
                "count": count
            })

    return rare_messages


# ============================================================
# STATISTICAL SPIKE DETECTION
# ============================================================

def detect_spike_anomalies(logs):
    """
    Detect unusually frequent log messages within the
    current analysis window.

    Logic:

        message frequencies
              ↓
        calculate mean
              ↓
        calculate standard deviation
              ↓
        threshold = mean + 2 * std
              ↓
        messages above threshold = spike
    """

    messages = [
        log["message"]
        for log in logs
        if "message" in log
    ]

    if not messages:
        return []

    counter = Counter(messages)

    counts = np.array(
        list(counter.values())
    )

    mean = np.mean(counts)
    std = np.std(counts)

    threshold = mean + (2 * std)

    spike_anomalies = []

    for message, count in counter.items():

        if count > threshold:
            spike_anomalies.append({
                "message": message,
                "count": int(count),
                "threshold": round(float(threshold), 2)
            })

    return spike_anomalies


# ============================================================
# ERROR RATE DETECTION
# ============================================================

def detect_error_rate_anomaly(
    logs,
    error_threshold_ratio=0.3
):
    """
    Detect a high percentage of ERROR logs
    within the current analysis window.

    This detector is stateless.
    """

    if not logs:
        return None

    total = len(logs)

    error_logs = [
        log
        for log in logs
        if log.get("logLevel", "").upper() == "ERROR"
    ]

    error_ratio = len(error_logs) / total

    if error_ratio > error_threshold_ratio:
        return {
            "type": "HIGH_ERROR_RATE",
            "errorRatio": round(error_ratio, 2),
            "message": "High percentage of ERROR logs detected"
        }

    return None


# ============================================================
# TRAFFIC DROP DETECTION
# ============================================================

def detect_traffic_drop(
    logs,
    minimum_expected=10
):
    """
    Detect unusually low log volume.

    This detector is stateless.
    """

    total = len(logs)

    if total < minimum_expected:
        return {
            "type": "TRAFFIC_DROP",
            "message": (
                f"Log volume below expected threshold. "
                f"Only {total} logs detected."
            )
        }

    return None


# ============================================================
# CRITICAL ERROR DETECTION
# ============================================================

def detect_critical_errors(logs):
    """
    Detect ERROR logs containing critical keywords.

    This detector is stateless.
    """

    critical_keywords = [
        "critical",
        "panic",
        "corruption",
        "fatal"
    ]

    critical_events = []

    for log in logs:

        message = log.get(
            "message",
            ""
        ).lower()

        level = log.get(
            "logLevel",
            ""
        ).upper()

        if level != "ERROR":
            continue

        for keyword in critical_keywords:

            if keyword in message:
                critical_events.append({
                    "message": log["message"],
                    "level": level
                })
                break

    return critical_events