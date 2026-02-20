from fastapi import FastAPI, Query
from elastic_client import fetch_logs
from clustering import cluster_logs

app = FastAPI()

@app.get("/clusters")
def get_clusters(
    size: int = Query(500, ge=10, le=5000),
    minutes: int = Query(None, ge=1, le=1440)
):
    logs = fetch_logs(size=size, minutes=minutes)
    clusters = cluster_logs(logs)

    return {
        "totalLogsFetched": len(logs),
        "totalClusters": len(clusters),
        "clusters": clusters
    }