from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

es = Elasticsearch("http://localhost:9200")

def fetch_logs(size=500, minutes=None):
    query = {"match_all": {}}

    if minutes:
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        query = {
            "range": {
                "timestamp": {
                    "gte": time_threshold.isoformat()
                }
            }
        }

    response = es.search(
        index="logs",
        size=size,
        query=query,
        sort=[{"timestamp": {"order": "desc"}}]
    )

    logs = []
    for hit in response["hits"]["hits"]:
        logs.append(hit["_source"])

    return logs