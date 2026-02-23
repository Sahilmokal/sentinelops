from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

es = Elasticsearch("http://localhost:9200")

def fetch_logs(size=500, minutes=None, start_time=None, end_time=None):

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

    elif start_time and end_time:
        query = {
            "range": {
                "timestamp": {
                    "gte": start_time,
                    "lte": end_time
                }
            }
        }

    response = es.search(
        index="logs",
        size=size,
        query=query,
        sort=[{"timestamp": {"order": "desc"}}]
    )

    return [hit["_source"] for hit in response["hits"]["hits"]]