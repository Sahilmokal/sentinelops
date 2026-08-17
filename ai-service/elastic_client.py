from elasticsearch import Elasticsearch
from datetime import datetime, timedelta, timezone

from config import ELASTIC_HOST


# ============================================================
# ELASTICSEARCH
# ============================================================

es = Elasticsearch(
    ELASTIC_HOST
)


# ============================================================
# INDEXES
# ============================================================

LOG_INDEX_PATTERN = "logs"

ALERT_INDEX = "alerts"


# ============================================================
# LOG FETCH
# ============================================================

def fetch_logs(
    size: int = 1000,
    minutes: int = None,
    start_time: str = None,
    end_time: str = None
):
    """
    Fetch logs from Elasticsearch.

    Supports:

        minutes
            rolling realtime window

        start_time + end_time
            exact historical/canonical window
    """

    if size <= 0:
        size = 1000

    if size > 10000:
        size = 10000

    if minutes and (
        start_time
        or end_time
    ):
        raise ValueError(
            "Use either minutes OR "
            "start_time/end_time, not both."
        )

    must = []

    # ========================================================
    # ROLLING WINDOW
    # ========================================================

    if minutes:

        now = datetime.now(
            timezone.utc
        )

        past = (
            now
            - timedelta(
                minutes=minutes
            )
        )

        must.append({
            "range": {
                "timestamp": {
                    "gte":
                        past.isoformat(),

                    "lte":
                        now.isoformat(),
                }
            }
        })

    # ========================================================
    # EXACT WINDOW
    # ========================================================

    if (
        start_time
        and end_time
    ):

        must.append({
            "range": {
                "timestamp": {
                    "gte":
                        start_time,

                    "lte":
                        end_time,
                }
            }
        })

    # ========================================================
    # QUERY
    # ========================================================

    query = {
        "query": {
            "bool": {
                "must":
                    must
                    if must
                    else [
                        {
                            "match_all": {}
                        }
                    ]
            }
        },

        "size":
            size,

        "sort": [
            {
                "timestamp": {
                    "order":
                        "desc"
                }
            }
        ]
    }

    response = es.search(
        index=LOG_INDEX_PATTERN,
        body=query
    )

    return [
        hit["_source"]
        for hit in response[
            "hits"
        ]["hits"]
    ]


# ============================================================
# GENERIC PAGINATED SEARCH
# ============================================================

def search_with_pagination(
    index,
    query,
    page,
    size,
    sort_field,
    sort_order
):

    if size > 100:
        size = 100

    if page < 1:
        page = 1

    from_ = (
        page - 1
    ) * size

    body = {

        "from":
            from_,

        "size":
            size,

        "query":
            query,

        "sort": [
            {
                sort_field: {
                    "order":
                        sort_order
                }
            }
        ]
    }

    return es.search(
        index=index,
        body=body
    )


# ============================================================
# ALERT INDEX
# ============================================================

def create_alert_index():

    if es.indices.exists(
        index=ALERT_INDEX
    ):
        return

    mapping = {

        "mappings": {

            "properties": {

                "alertId": {
                    "type": "keyword"
                },

                "signature": {
                    "type": "keyword"
                },

                "dedupKey": {
                    "type": "keyword"
                },

                "incidentFamily": {
                    "type": "keyword"
                },

                "anomalyType": {
                    "type": "keyword"
                },

                "rootService": {
                    "type": "keyword"
                },

                "impactedServices": {
                    "type": "keyword"
                },

                "severity": {
                    "type": "keyword"
                },

                "status": {
                    "type": "keyword"
                },

                "sources": {
                    "type": "keyword"
                },

                "confidence": {
                    "type": "float"
                },

                "firstDetectedAt": {
                    "type": "date"
                },

                "lastUpdatedAt": {
                    "type": "date"
                },

                "resolvedAt": {
                    "type": "date"
                },

                "occurrenceCount": {
                    "type": "integer"
                },

                "mlEnrichmentCount": {
                    "type": "integer"
                },

                "rcaStage": {
                    "type": "integer"
                },

                "rcaSource": {
                    "type": "keyword"
                },

                "anomalies": {
                    "type": "object"
                },

                "ruleRca": {
                    "type": "object"
                },

                "stage2Rca": {
                    "type": "object"
                },

                "rca": {
                    "type": "object"
                },

                "mlRca": {
                    "type": "object"
                },

                "mlEvidence": {
                    "type": "object"
                },

                "mlAnomaly": {
                    "type": "boolean"
                },

                "mlScore": {
                    "type": "float"
                },

                "mlWindowId": {
                    "type": "keyword"
                }
            }
        }
    }

    es.indices.create(
        index=ALERT_INDEX,
        body=mapping
    )

    print(
        "[Alerts] "
        "alerts index created."
    )


# ============================================================
# FIND ALERT BY DEDUP KEY
# ============================================================

def find_alert_by_dedup_key(
    dedup_key
):

    query = {
        "query": {
            "term": {
                "dedupKey":
                    dedup_key
            }
        }
    }

    response = es.search(
        index=ALERT_INDEX,
        body=query
    )

    hits = response[
        "hits"
    ]["hits"]

    if not hits:
        return None

    return hits[0]


# ============================================================
# FIND INCIDENTS FOR EXACT COMPLETED ML WINDOW
# ============================================================

def find_active_alerts_for_ml_window(
    window_start,
    window_end
):
    """
    Find ACTIVE incidents whose FIRST detection
    occurred inside the exact completed 5-minute
    ML window.

    Example:

        window:
            19:20:00 -> 19:25:00

        incident:
            firstDetectedAt = 19:24:49

        RESULT:
            incident is selected.

    This deliberately uses firstDetectedAt.

    It does NOT select:
        - latest alert
        - latest incident
        - same service
        - same anomaly
        - same dedup key

    Each returned document contains its exact
    alertId.
    """

    create_alert_index()

    query = {
        "bool": {
            "must": [

                # ------------------------------------------------
                # ACTIVE INCIDENTS ONLY
                # ------------------------------------------------

                {
                    "terms": {
                        "status": [
                            "NEW",
                            "ACKNOWLEDGED"
                        ]
                    }
                },

                # ------------------------------------------------
                # INCIDENT CREATED INSIDE THIS ML WINDOW
                # ------------------------------------------------

                {
                    "range": {
                        "firstDetectedAt": {
                            "gte":
                                window_start,

                            "lt":
                                window_end
                        }
                    }
                }
            ]
        }
    }

    body = {

        "query":
            query,

        "size":
            1000,

        "sort": [
            {
                "firstDetectedAt": {
                    "order":
                        "asc"
                }
            }
        ]
    }

    response = es.search(
        index=ALERT_INDEX,
        body=body
    )

    hits = response[
        "hits"
    ]["hits"]

    print(
        "[Alerts] "
        f"ML window lookup | "
        f"window={window_start} -> {window_end} | "
        f"active incidents={len(hits)}"
    )

    results = []

    for hit in hits:

        source = hit.get(
            "_source",
            {}
        )

        alert_id = (
            source.get(
                "alertId"
            )
            or hit.get(
                "_id"
            )
        )

        if not alert_id:

            print(
                "[Alerts] "
                "Skipping incident without alertId | "
                f"source={source}"
            )

            continue

        results.append({
            "alertId":
                str(alert_id),

            "documentId":
                hit.get(
                    "_id"
                ),

            "alert":
                source,
        })

        print(
            "[Alerts] "
            f"ML target found | "
            f"alertId={alert_id} | "
            f"family={source.get('incidentFamily')} | "
            f"firstDetectedAt={source.get('firstDetectedAt')}"
        )

    return results


# ============================================================
# INDEX ALERT
# ============================================================

def index_alert(
    alert_doc
):

    return es.index(
        index=ALERT_INDEX,
        document=alert_doc,
        refresh="wait_for"
    )


# ============================================================
# UPDATE ALERT
# ============================================================

def update_alert(
    alert_id,
    update_fields
):

    return es.update(
        index=ALERT_INDEX,
        id=alert_id,
        doc=update_fields,
        refresh="wait_for"
    )


# ============================================================
# GET ALERT
# ============================================================

def get_alert_by_id(
    alert_id
):

    return es.get(
        index=ALERT_INDEX,
        id=alert_id
    )