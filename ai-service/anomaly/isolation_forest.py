import numpy as np
from sklearn.ensemble import IsolationForest

from anomaly.baseline_store import (
    load_ml_baseline,
    save_ml_baseline
)


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

FEATURE_NAMES = [
    "totalLogs",
    "errorCount",
    "errorRatio",
    "warnCount",
    "uniqueMessages",
    "uniqueServices",
    "uniqueTraceIds"
]


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(logs):
    """
    Convert one log-analysis window into numerical features.

    One feature vector represents one time window.
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

    error_ratio = error_count / total_logs

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

    return {
        "totalLogs": total_logs,
        "errorCount": error_count,
        "errorRatio": error_ratio,
        "warnCount": warn_count,
        "uniqueMessages": unique_messages,
        "uniqueServices": unique_services,
        "uniqueTraceIds": unique_trace_ids
    }


# ============================================================
# FEATURE DICTIONARY → ML VECTOR
# ============================================================

def features_to_vector(features):
    """
    Convert feature dictionary into the numerical vector
    expected by Isolation Forest.
    """

    return [
        features["totalLogs"],
        features["errorCount"],
        features["errorRatio"],
        features["warnCount"],
        features["uniqueMessages"],
        features["uniqueServices"],
        features["uniqueTraceIds"]
    ]


# ============================================================
# ISOLATION FOREST ANOMALY DETECTION
# ============================================================

def detect_isolation_forest_anomaly(logs):
    """
    Detect whether the current log window is anomalous
    compared with previously observed log windows.

    Workflow:

        Current logs
              ↓
        Feature extraction
              ↓
        Historical ML baseline
              ↓
        Isolation Forest
              ↓
        Normal / Anomaly
              ↓
        Save current window to baseline
    """

    # --------------------------------------------------------
    # Extract features from current window
    # --------------------------------------------------------

    current_features = extract_features(logs)

    if current_features is None:
        return None

    # --------------------------------------------------------
    # Load historical ML baseline
    # --------------------------------------------------------

    baseline = load_ml_baseline()

    # --------------------------------------------------------
    # Warm-up period
    #
    # Isolation Forest needs multiple historical observations
    # to learn what normal behavior looks like.
    # --------------------------------------------------------
    MINIMUM_BASELINE_WINDOWS = 30
    if len(baseline) < MINIMUM_BASELINE_WINDOWS:

        baseline.append(current_features)

        # Keep only the most recent 100 windows
        baseline = baseline[-100:]

        save_ml_baseline(baseline)

        return {
    "type": "ISOLATION_FOREST_WARMING_UP",
    "anomaly": False,
    "prediction": None,
    "score": None,
    "message": (
        f"Collecting ML baseline: "
        f"{len(baseline)}/10 windows"
    ),
    "features": current_features
}

    # --------------------------------------------------------
    # Convert historical baseline into ML matrix
    # --------------------------------------------------------

    X = np.array([
        features_to_vector(item)
        for item in baseline
    ])

    # --------------------------------------------------------
    # Train Isolation Forest
    #
    # IMPORTANT:
    # The current window is NOT included in training.
    # The model learns only from historical windows.
    # --------------------------------------------------------

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )

    model.fit(X)

    # --------------------------------------------------------
    # Convert current window into ML vector
    # --------------------------------------------------------

    current_vector = np.array([
        features_to_vector(current_features)
    ])

    # --------------------------------------------------------
    # Predict current window
    #
    #  1  = Normal
    # -1  = Anomaly
    # --------------------------------------------------------

    prediction = model.predict(current_vector)[0]

    # --------------------------------------------------------
    # Calculate anomaly score
    #
    # Higher score → more normal
    # Lower score → more anomalous
    # --------------------------------------------------------

    score = model.decision_function(current_vector)[0]

    # --------------------------------------------------------
    # Save current window AFTER prediction
    #
    # This makes the current window available as historical
    # data for future predictions.
    # --------------------------------------------------------

    baseline.append(current_features)

    # Keep only the latest 100 windows
    baseline = baseline[-100:]

    save_ml_baseline(baseline)

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "type": "ISOLATION_FOREST",
        "anomaly": bool(prediction == -1),
        "prediction": int(prediction),
        "score": round(float(score), 4),
        "features": current_features
    }