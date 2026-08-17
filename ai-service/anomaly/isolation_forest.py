import numpy as np
from sklearn.ensemble import IsolationForest

from storage.ml_storage import (
    load_ml_baseline,
    save_ml_baseline_window,
    save_ml_result,
)


# ============================================================
# CONFIGURATION
# ============================================================

MINIMUM_BASELINE_WINDOWS = 30
MAX_BASELINE_WINDOWS = 100

CONTAMINATION = 0.10
N_ESTIMATORS = 100


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

FEATURE_NAMES = [
    "totalLogs",
    "errorCount",
    "errorRatio",
    "warnCount",
    "warnRatio",
    "infoCount",
    "debugCount",
    "uniqueMessages",
    "uniqueServices",
    "uniqueTraceIds",
    "uniqueErrorMessages",
    "criticalErrorCount",
]


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(logs):
    """
    Convert one 5-minute log window into numerical features.
    """

    if not logs:
        return None

    total_logs = len(logs)

    error_count = sum(
        1
        for log in logs
        if log.get("logLevel", "").upper() == "ERROR"
    )

    warn_count = sum(
        1
        for log in logs
        if log.get("logLevel", "").upper() == "WARN"
    )

    info_count = sum(
        1
        for log in logs
        if log.get("logLevel", "").upper() == "INFO"
    )

    debug_count = sum(
        1
        for log in logs
        if log.get("logLevel", "").upper() == "DEBUG"
    )

    error_ratio = error_count / total_logs
    warn_ratio = warn_count / total_logs

    unique_messages = len({
        log.get("message")
        for log in logs
        if log.get("message")
    })

    unique_services = len({
        log.get("serviceName")
        for log in logs
        if log.get("serviceName")
    })

    unique_trace_ids = len({
        log.get("traceId")
        for log in logs
        if log.get("traceId")
    })

    unique_error_messages = len({
        log.get("message")
        for log in logs
        if (
            log.get("logLevel", "").upper() == "ERROR"
            and log.get("message")
        )
    })

    critical_keywords = [
        "critical",
        "panic",
        "corruption",
        "fatal",
    ]

    critical_error_count = 0

    for log in logs:

        if log.get("logLevel", "").upper() != "ERROR":
            continue

        message = log.get("message", "").lower()

        if any(
            keyword in message
            for keyword in critical_keywords
        ):
            critical_error_count += 1

    return {
        "totalLogs": total_logs,
        "errorCount": error_count,
        "errorRatio": round(error_ratio, 6),
        "warnCount": warn_count,
        "warnRatio": round(warn_ratio, 6),
        "infoCount": info_count,
        "debugCount": debug_count,
        "uniqueMessages": unique_messages,
        "uniqueServices": unique_services,
        "uniqueTraceIds": unique_trace_ids,
        "uniqueErrorMessages": unique_error_messages,
        "criticalErrorCount": critical_error_count,
    }


# ============================================================
# FEATURE → VECTOR
# ============================================================

def features_to_vector(features):

    return [
        features["totalLogs"],
        features["errorCount"],
        features["errorRatio"],
        features["warnCount"],
        features["warnRatio"],
        features["infoCount"],
        features["debugCount"],
        features["uniqueMessages"],
        features["uniqueServices"],
        features["uniqueTraceIds"],
        features["uniqueErrorMessages"],
        features["criticalErrorCount"],
    ]


# ============================================================
# ERROR SUMMARY
# ============================================================

def extract_error_summary(logs):

    error_logs = [
        log
        for log in logs
        if log.get("logLevel", "").upper() == "ERROR"
    ]

    if not error_logs:
        return {
            "errorMessages": [],
            "errorServices": [],
            "criticalErrors": [],
        }

    error_messages = list({
        log.get("message")
        for log in error_logs
        if log.get("message")
    })

    error_services = list({
        log.get("serviceName")
        for log in error_logs
        if log.get("serviceName")
    })

    critical_keywords = [
        "critical",
        "panic",
        "corruption",
        "fatal",
    ]

    critical_errors = []

    for log in error_logs:

        message = log.get("message", "")
        message_lower = message.lower()

        if any(
            keyword in message_lower
            for keyword in critical_keywords
        ):
            critical_errors.append({
                "message": message,
                "service": log.get("serviceName"),
                "traceId": log.get("traceId"),
            })

    return {
        "errorMessages": error_messages[:20],
        "errorServices": error_services,
        "criticalErrors": critical_errors[:20],
    }


# ============================================================
# ISOLATION FOREST
# ============================================================

def detect_isolation_forest_anomaly(
    logs,
    window_id,
    window_start,
    window_end,
):
    """
    Analyze one canonical 5-minute window.

    The scheduler supplies:
        window_id
        window_start
        window_end

    This function NEVER derives window boundaries from
    individual log timestamps.
    """

    if not logs:
        return None

    # --------------------------------------------------------
    # Extract current window features
    # --------------------------------------------------------

    current_features = extract_features(logs)

    if current_features is None:
        return None

    # --------------------------------------------------------
    # Load historical NORMAL baseline
    # --------------------------------------------------------

    baseline = load_ml_baseline(
        limit=MAX_BASELINE_WINDOWS
    )

    baseline_count = len(baseline)

    # ========================================================
    # WARM-UP
    # ========================================================

    if baseline_count < MINIMUM_BASELINE_WINDOWS:

        # During warm-up we assume these windows represent
        # normal system behaviour.
        save_ml_baseline_window(
            window_id=window_id,
            window_start=window_start,
            window_end=window_end,
            features=current_features,
        )

        new_count = baseline_count + 1

        result = {
            "type": "ISOLATION_FOREST_WARMING_UP",
            "anomaly": False,
            "prediction": None,
            "score": None,
            "baselineWindows": new_count,
            "requiredBaselineWindows": MINIMUM_BASELINE_WINDOWS,
            "features": current_features,
            "errors": extract_error_summary(logs),
        }

        save_ml_result(
            window_id=window_id,
            window_start=window_start,
            window_end=window_end,
            result=result,
        )

        return result

    # ========================================================
    # TRAIN ISOLATION FOREST
    # ========================================================

    X = np.array([
        features_to_vector(features)
        for features in baseline
    ])

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=CONTAMINATION,
        random_state=42,
    )

    model.fit(X)

    # ========================================================
    # CURRENT WINDOW
    # ========================================================

    current_vector = np.array([
        features_to_vector(current_features)
    ])

    # ========================================================
    # PREDICTION
    # ========================================================

    prediction = model.predict(
        current_vector
    )[0]

    score = model.decision_function(
        current_vector
    )[0]

    is_anomaly = prediction == -1

    # ========================================================
    # RESULT
    # ========================================================

    result = {
        "type": "ISOLATION_FOREST",
        "anomaly": bool(is_anomaly),
        "prediction": int(prediction),
        "score": round(float(score), 4),
        "baselineWindows": baseline_count,
        "requiredBaselineWindows": MINIMUM_BASELINE_WINDOWS,
        "features": current_features,
        "errors": extract_error_summary(logs),
    }

    # --------------------------------------------------------
    # ALWAYS save result
    # --------------------------------------------------------

    save_ml_result(
        window_id=window_id,
        window_start=window_start,
        window_end=window_end,
        result=result,
    )

    # --------------------------------------------------------
    # ONLY NORMAL windows enter future baseline
    # --------------------------------------------------------

    if not is_anomaly:

        save_ml_baseline_window(
            window_id=window_id,
            window_start=window_start,
            window_end=window_end,
            features=current_features,
        )

    return result