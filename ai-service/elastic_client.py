from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from config import ELASTIC_HOST

es = Elasticsearch(ELASTIC_HOST)

LOG_INDEX_PATTERN = "logs-*"
ALERT_INDEX = "alerts"


# ----------------------------
# LOG FETCH (existing realtime helper)
# ----------------------------
def fetch_logs(size=1000, minutes=2):

    now = datetime.utcnow()
    past = now - timedelta(minutes=minutes)

    query = {
        "query": {
            "range": {
                "timestamp": {
                    "gte": past.isoformat(),
                    "lte": now.isoformat()
                }
            }
        },
        "size": size,
        "sort": [{"timestamp": {"order": "desc"}}]
    }

    response = es.search(index=LOG_INDEX_PATTERN, body=query)

    return [hit["_source"] for hit in response["hits"]["hits"]]


# ----------------------------
# GENERIC PAGINATED SEARCH
# ----------------------------
def search_with_pagination(index, query, page, size, sort_field, sort_order):

    if size > 100:
        size = 100

    if page < 1:
        page = 1

    from_ = (page - 1) * size

    body = {
        "from": from_,
        "size": size,
        "query": query,
        "sort": [
            {sort_field: {"order": sort_order}}
        ]
    }

    return es.search(index=index, body=body)


def search_with_pagination(index, query, page, size, sort_field, sort_order):

    if size > 100:
        size = 100

    if page < 1:
        page = 1

    from_ = (page - 1) * size

    body = {
        "from": from_,
        "size": size,
        "query": query,
        "sort": [
            {sort_field: {"order": sort_order}}
        ]
    }

    return es.search(index=index, body=body)

# ----------------------------
# ALERT ENGINE SUPPORT
# ----------------------------
def create_alert_index():
    if es.indices.exists(index=ALERT_INDEX):
        return

    mapping = {
        "mappings": {
            "properties": {
                "alertId": {"type": "keyword"},
                "dedupKey": {"type": "keyword"},
                "anomalyType": {"type": "keyword"},
                "rootService": {"type": "keyword"},
                "impactedServices": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "status": {"type": "keyword"},
                "confidence": {"type": "float"},
                "firstDetectedAt": {"type": "date"},
                "lastUpdatedAt": {"type": "date"},
                "occurrenceCount": {"type": "integer"}
            }
        }
    }

    es.indices.create(index=ALERT_INDEX, body=mapping)


def find_alert_by_dedup_key(dedup_key):

    query = {
        "query": {
            "term": {
                "dedupKey": dedup_key
            }
        }
    }

    response = es.search(index=ALERT_INDEX, body=query)

    hits = response["hits"]["hits"]

    if not hits:
        return None

    return hits[0]


def index_alert(alert_doc):
    return es.index(index=ALERT_INDEX, document=alert_doc)


def update_alert(alert_id, update_fields):
    return es.update(
        index=ALERT_INDEX,
        id=alert_id,
        body={"doc": update_fields}
    )


def get_alert_by_id(alert_id):
    return es.get(index=ALERT_INDEX, id=alert_id)