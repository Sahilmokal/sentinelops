from fastapi import FastAPI, Query
from elastic_client import fetch_logs
from clustering import cluster_logs
from anomaly import (
    detect_rare_logs,
    detect_spike_anomalies,
    detect_traffic_drop,
    detect_error_rate_anomaly,
    detect_critical_errors
)

from scheduler import start_scheduler

app = FastAPI()

start_scheduler()



# ----------------------------------
# Clustering Endpoint
# ----------------------------------
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


# ----------------------------------
# Realtime Anomalies
# ----------------------------------
@app.get("/anomalies/realtime")
def get_realtime_anomalies(
    minutes: int = Query(5, ge=1, le=1440),
    size: int = Query(1000, ge=10, le=10000)
):
    logs = fetch_logs(size=size, minutes=minutes)

    return {
        "mode": "realtime",
        "totalLogsAnalyzed": len(logs),
        "trafficDrop": detect_traffic_drop(logs),
        "errorRateAnomaly": detect_error_rate_anomaly(logs),
        "criticalAnomalies": detect_critical_errors(logs),
        "rareAnomalies": detect_rare_logs(logs),
        "spikeAnomalies": detect_spike_anomalies(logs)
    }


# ----------------------------------
# Historical Anomalies
# ----------------------------------
@app.get("/anomalies/historical")
def get_historical_anomalies(
    start_time: str,
    end_time: str,
    size: int = Query(5000, ge=10, le=20000)
):
    logs = fetch_logs(
        size=size,
        start_time=start_time,
        end_time=end_time
    )

    return {
        "mode": "historical",
        "totalLogsAnalyzed": len(logs),
        "trafficDrop": detect_traffic_drop(logs),
        "errorRateAnomaly": detect_error_rate_anomaly(logs),
        "criticalAnomalies": detect_critical_errors(logs),
        "rareAnomalies": detect_rare_logs(logs),
        "spikeAnomalies": detect_spike_anomalies(logs)
    }