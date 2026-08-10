import uuid
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from elastic_client import (
    es,
    ALERT_INDEX,
    create_alert_index
)


IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# ALERT SIGNATURE / DEDUPLICATION
# ============================================================

def generate_signature(anomalies):
    """
    Generate a deterministic signature for an anomaly set.

    Used to prevent duplicate NEW alerts for the same
    anomaly condition.
    """

    raw = str(sorted(anomalies.items()))

    return hashlib.sha256(
        raw.encode()
    ).hexdigest()


# ============================================================
# SEVERITY CLASSIFICATION
# ============================================================

def classify_severity(anomalies):

    if "trafficDrop" in anomalies:
        return "CRITICAL"

    if "critical" in anomalies:
        return "HIGH"

    if "errorRate" in anomalies:
        return "HIGH"

    if "spike" in anomalies:
        return "MEDIUM"

    if "rare" in anomalies:
        return "LOW"

    return "LOW"


# ============================================================
# CHECK EXISTING ALERT
# ============================================================

def alert_exists(signature):

    # Ensure alerts index exists
    create_alert_index()

    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "signature": signature
                        }
                    },
                    {
                        "term": {
                            "status": "NEW"
                        }
                    }
                ]
            }
        }
    }

    response = es.search(
        index=ALERT_INDEX,
        body=query
    )

    return response["hits"]["total"]["value"] > 0


# ============================================================
# CREATE ALERT
# ============================================================

def create_alert(anomalies, rca=None):

    if not anomalies:
        return None

    # --------------------------------------------------------
    # Generate deduplication signature
    # --------------------------------------------------------

    signature = generate_signature(anomalies)

    # --------------------------------------------------------
    # Prevent duplicate active alerts
    # --------------------------------------------------------

    if alert_exists(signature):
        print(
            f"[ALERT ENGINE] Duplicate alert ignored: "
            f"{signature}"
        )

        return None

    # --------------------------------------------------------
    # Determine RCA information
    # --------------------------------------------------------

    root_service = "unknown-service"
    impacted_services = []
    confidence = 0.0

    if isinstance(rca, dict):

        # Your current RCA engine returns "rootService"
        root_service = rca.get(
            "rootService",
            "unknown-service"
        )

        impacted_services = rca.get(
            "impactedServices",
            []
        )

        confidence = rca.get(
            "confidence",
            0.0
        )

    # --------------------------------------------------------
    # Determine primary anomaly type
    # --------------------------------------------------------

    anomaly_type = next(
        iter(anomalies.keys()),
        "anomaly_detected"
    )

    # --------------------------------------------------------
    # Timestamp — IST
    # --------------------------------------------------------

    now = datetime.now(IST).isoformat()

    # --------------------------------------------------------
    # Build alert document
    # --------------------------------------------------------

    alert_id = str(uuid.uuid4())

    alert = {

        "alertId": alert_id,

        "signature": signature,

        "anomalyType": anomaly_type,

        "severity": classify_severity(anomalies),

        "status": "NEW",

        "anomalies": anomalies,

        "rca": rca,

        "rootService": root_service,

        "impactedServices": impacted_services,

        "confidence": confidence,

        "firstDetectedAt": now,

        "lastUpdatedAt": now,

        "occurrenceCount": 1
    }

    # --------------------------------------------------------
    # Store in Elasticsearch
    # --------------------------------------------------------

    es.index(
        index=ALERT_INDEX,
        id=alert_id,
        document=alert,
        refresh="wait_for"
    )

    print(
        f"[ALERT ENGINE] Alert created | "
        f"type={anomaly_type} | "
        f"severity={alert['severity']} | "
        f"root={root_service}"
    )

    return alert