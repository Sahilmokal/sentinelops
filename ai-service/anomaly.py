from collections import Counter
import numpy as np


from baseline_store import load_baseline, save_baseline


def detect_spike_with_baseline(logs):

    messages = [log["message"] for log in logs if "message" in log]

    if not messages:
        return []

    counter = Counter(messages)
    baseline = load_baseline()

    spike_anomalies = []

    for message, current_count in counter.items():

        previous_count = baseline.get(message, 0)

        # detect 3x increase
        if previous_count > 0 and current_count > previous_count * 3:
            spike_anomalies.append({
                "message": message,
                "previous": previous_count,
                "current": current_count
            })

    # Save current as new baseline
    save_baseline(counter)

    return spike_anomalies
# -----------------------------
# Rare Detection (Low Frequency)
# -----------------------------
def detect_rare_logs(logs, threshold=3):

    if not logs:
        return []

    messages = [log["message"] for log in logs if "message" in log]
    counter = Counter(messages)

    rare_messages = []

    for message, count in counter.items():
        if count < threshold:
            rare_messages.append({
                "message": message,
                "count": count
            })

    return rare_messages


# -----------------------------
# Spike Detection (Statistical)
# -----------------------------
def detect_spike_anomalies(logs):

    messages = [log["message"] for log in logs if "message" in log]

    if not messages:
        return []

    counter = Counter(messages)
    counts = np.array(list(counter.values()))

    mean = np.mean(counts)
    std = np.std(counts)

    threshold = mean + 2 * std

    spike_anomalies = []

    for message, count in counter.items():
        if count > threshold:
            spike_anomalies.append({
                "message": message,
                "count": int(count)
            })

    return spike_anomalies


# -----------------------------
# Error Rate Detection
# -----------------------------
def detect_error_rate_anomaly(logs, error_threshold_ratio=0.3):

    if not logs:
        return None

    total = len(logs)
    error_logs = [log for log in logs if log.get("logLevel") == "ERROR"]

    error_ratio = len(error_logs) / total

    if error_ratio > error_threshold_ratio:
        return {
            "type": "HIGH_ERROR_RATE",
            "errorRatio": round(error_ratio, 2),
            "message": "High percentage of ERROR logs detected"
        }

    return None


# -----------------------------
# Traffic Drop Detection
# -----------------------------
def detect_traffic_drop(logs, minimum_expected=10):

    total = len(logs)

    if total < minimum_expected:
        return {
            "type": "TRAFFIC_DROP",
            "message": f"Log volume below expected threshold. Only {total} logs detected."
        }

    return None


# -----------------------------
# Critical Keyword Detection
# -----------------------------
def detect_critical_errors(logs):

    critical_keywords = ["critical", "panic", "corruption", "fatal"]

    critical_events = []

    for log in logs:
        message = log.get("message", "").lower()
        level = log.get("logLevel", "").upper()

        if level == "ERROR":
            for keyword in critical_keywords:
                if keyword in message:
                    critical_events.append({
                        "message": log["message"],
                        "level": level
                    })
                    break

    return critical_events