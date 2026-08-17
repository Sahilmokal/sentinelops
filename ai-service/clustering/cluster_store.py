from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from config import ELASTIC_HOST


# ============================================================
# ELASTICSEARCH
# ============================================================

es = Elasticsearch(ELASTIC_HOST)


# ============================================================
# INDEX
# ============================================================

SEMANTIC_CLUSTER_INDEX = "semantic_clusters"


# ============================================================
# CREATE INDEX
# ============================================================

def ensure_cluster_storage():
    """
    Create the semantic clustering index if it does not exist.
    """

    if es.indices.exists(index=SEMANTIC_CLUSTER_INDEX):
        return

    es.indices.create(
        index=SEMANTIC_CLUSTER_INDEX,
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

                "totalMessages": {
                    "type": "integer"
                },

                "uniqueMessages": {
                    "type": "integer"
                },

                "clusterCount": {
                    "type": "integer"
                },

                "noiseCount": {
                    "type": "integer"
                },

                "clusters": {
                    "type": "object"
                },

                "createdAt": {
                    "type": "date"
                }
            }
        }
    )

    print(
        "[Semantic Clustering] "
        "semantic_clusters index created."
    )


# ============================================================
# SAVE CLUSTER RESULT
# ============================================================

def save_cluster_result(
    window_id,
    window_start,
    window_end,
    result
):
    """
    Store one semantic clustering result for one
    canonical time window.

    Raw logs are NOT stored here.
    """

    document = {
        "windowId": window_id,
        "windowStart": window_start,
        "windowEnd": window_end,

        "totalMessages": result.get(
            "totalMessages",
            0
        ),

        "uniqueMessages": result.get(
            "uniqueMessages",
            0
        ),

        "clusterCount": result.get(
            "clusterCount",
            0
        ),

        "noiseCount": result.get(
            "noiseCount",
            0
        ),

        "clusters": result.get(
            "clusters",
            []
        ),

        "createdAt": datetime.now(
            timezone.utc
        ).isoformat()
    }

    es.index(
        index=SEMANTIC_CLUSTER_INDEX,
        id=window_id,
        document=document
    )


# ============================================================
# LOAD LATEST RESULT
# ============================================================

def load_latest_cluster_result():
    """
    Load the most recent semantic clustering result.
    """

    try:

        response = es.search(
            index=SEMANTIC_CLUSTER_INDEX,
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


# ============================================================
# COUNT
# ============================================================

def get_cluster_result_count():
    """
    Return the number of stored clustering windows.
    """

    try:

        response = es.count(
            index=SEMANTIC_CLUSTER_INDEX
        )

        return response["count"]

    except NotFoundError:

        return 0

    
def load_cluster_result(window_id):
    """
    Load the semantic clustering result for
    one exact canonical window.
    """

    try:
        response = es.get(
            index=SEMANTIC_CLUSTER_INDEX,
            id=window_id
        )

        return response["_source"]

    except NotFoundError:
        return None