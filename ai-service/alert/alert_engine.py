import uuid
import hashlib
from datetime import datetime
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


ALERT_INDEX = "alerts"


def generate_signature(anomalies):
    raw = str(sorted(anomalies.items()))
    return hashlib.md5(raw.encode()).hexdigest()


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


def alert_exists(signature):

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"signature.keyword": signature}},
                    {"term": {"status.keyword": "NEW"}}
                ]
            }
        }
    }

    res = es.search(index=ALERT_INDEX, body=query)

    return res["hits"]["total"]["value"] > 0


def create_alert(anomalies, rca):

    signature = generate_signature(anomalies)

    # Deduplication
    if alert_exists(signature):
        return None

    alert = {
        "id": str(uuid.uuid4()),
        "createdAt": datetime.utcnow().isoformat(),
        "type": "anomaly_detected",
        "severity": classify_severity(anomalies),
        "status": "NEW",
        "anomalies": anomalies,
        "rca": rca,
        "signature": signature
    }

    es.index(index=ALERT_INDEX, id=alert["id"], body=alert)

    return alert