from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from config import ELASTIC_HOST


# ============================================================
# ELASTICSEARCH
# ============================================================

es = Elasticsearch(ELASTIC_HOST)


# ============================================================
# INDEX NAMES
# ============================================================

ML_BASELINE_INDEX = "ml_baseline"
ML_RESULTS_INDEX = "ml_results"


# ============================================================
# CREATE INDICES
# ============================================================

def ensure_ml_storage():
    """
    Create persistent Isolation Forest Elasticsearch indices
    if they do not already exist.
    """

    # ========================================================
    # ML BASELINE
    # ========================================================

    if not es.indices.exists(index=ML_BASELINE_INDEX):

        es.indices.create(
            index=ML_BASELINE_INDEX,
            mappings={
                "properties": {

                    "windowId": {
                        "type": "keyword"
                    },

                    "windowStart": {
                        "type": "date"
                    },

                    "windowEnd": {
                        "type": "date"
                    },

                    "features": {
                        "type": "object"
                    },

                    "createdAt": {
                        "type": "date"
                    }
                }
            }
        )

    # ========================================================
    # ML RESULTS
    # ========================================================

    if not es.indices.exists(index=ML_RESULTS_INDEX):

        es.indices.create(
            index=ML_RESULTS_INDEX,
            mappings={
                "properties": {

                    "windowId": {
                        "type": "keyword"
                    },

                    "windowStart": {
                        "type": "date"
                    },

                    "windowEnd": {
                        "type": "date"
                    },

                    "type": {
                        "type": "keyword"
                    },

                    "anomaly": {
                        "type": "boolean"
                    },

                    "prediction": {
                        "type": "integer"
                    },

                    "score": {
                        "type": "float"
                    },

                    "baselineWindows": {
                        "type": "integer"
                    },

                    "requiredBaselineWindows": {
                        "type": "integer"
                    },

                    "features": {
                        "type": "object"
                    },

                    "errors": {
                        "type": "object"
                    },

                    "createdAt": {
                        "type": "date"
                    }
                }
            }
        )

    print("ML storage indices ready.")


# ============================================================
# ML BASELINE
# ============================================================

def save_ml_baseline_window(
    window_id,
    window_start,
    window_end,
    features
):
    """
    Store one NORMAL Isolation Forest baseline window.

    IMPORTANT:
    Only windows considered normal should be stored here.
    """

    document = {
        "windowId": window_id,
        "windowStart": window_start,
        "windowEnd": window_end,
        "features": features,
        "createdAt": datetime.now(
            timezone.utc
        ).isoformat()
    }

    es.index(
        index=ML_BASELINE_INDEX,
        id=window_id,
        document=document
    )


def load_ml_baseline(limit=100):
    """
    Load the most recent normal ML baseline windows.

    Returns only feature dictionaries, ordered from
    oldest to newest.
    """

    try:

        response = es.search(
            index=ML_BASELINE_INDEX,
            size=limit,
            query={
                "match_all": {}
            },
            sort=[
                {
                    "windowEnd": {
                        "order": "desc"
                    }
                }
            ]
        )

    except NotFoundError:

        return []

    hits = response["hits"]["hits"]

    # Elasticsearch returns newest first.
    # Reverse to chronological order.
    hits.reverse()

    return [
        hit["_source"]["features"]
        for hit in hits
    ]


def ml_baseline_window_exists(window_id):
    """
    Check whether a particular window already exists
    in the ML baseline.
    """

    try:

        return es.exists(
            index=ML_BASELINE_INDEX,
            id=window_id
        )

    except NotFoundError:

        return False


def get_ml_baseline_count():
    """
    Return the number of stored normal ML baseline windows.
    """

    try:

        response = es.count(
            index=ML_BASELINE_INDEX
        )

        return response["count"]

    except NotFoundError:

        return 0


# ============================================================
# ML RESULTS
# ============================================================

def save_ml_result(
    window_id,
    window_start,
    window_end,
    result
):
    """
    Persist one Isolation Forest result.

    Every analyzed window gets a result:
        - warming up
        - normal
        - anomaly
        - no data
    """

    document = {
        "windowId": window_id,
        "windowStart": window_start,
        "windowEnd": window_end,
        **result,
        "createdAt": datetime.now(
            timezone.utc
        ).isoformat()
    }

    es.index(
        index=ML_RESULTS_INDEX,
        id=window_id,
        document=document
    )


def load_latest_ml_result():
    """
    Load the most recent Isolation Forest result.
    """

    try:

        response = es.search(
            index=ML_RESULTS_INDEX,
            size=1,
            query={
                "match_all": {}
            },
            sort=[
                {
                    "windowEnd": {
                        "order": "desc"
                    }
                }
            ]
        )

    except NotFoundError:

        return None

    hits = response["hits"]["hits"]

    if not hits:
        return None

    return hits[0]["_source"]


def get_ml_result_count():
    """
    Return the number of stored Isolation Forest results.
    """

    try:

        response = es.count(
            index=ML_RESULTS_INDEX
        )

        return response["count"]

    except NotFoundError:

        return 0