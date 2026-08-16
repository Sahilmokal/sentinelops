import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch

from elastic_client import (
    fetch_logs,
    search_with_pagination,
    ALERT_INDEX,
    create_alert_index
)
from clustering.clustering import cluster_logs
from rca.rca_engine import perform_rca
from anomaly.anomaly import (
    detect_rare_logs,
    detect_spike_with_baseline,
    detect_traffic_drop,
    detect_error_rate_anomaly,
    detect_critical_errors
)
from anomaly.isolation_forest import detect_isolation_forest_anomaly
from scheduler import start_scheduler


# =====================================================
# ELASTICSEARCH CONNECTION
# =====================================================

ELASTIC_HOST = os.getenv("ELASTIC_HOST", "http://elasticsearch:9200")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")


def create_es_client(host: str):
    for attempt in range(20):
        try:
            client = Elasticsearch(host)
            if client.ping():
                print(f"Connected to Elasticsearch at {host}")
                return client
            else:
                print(f"Elasticsearch ping failed (attempt {attempt + 1})")
        except Exception as e:
            print(f"Elasticsearch not ready (attempt {attempt + 1}): {e}")
        time.sleep(5)

    print("Elasticsearch not available after retries")
    return None


# =====================================================
# APP LIFECYCLE
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting AI Service...")

    app.state.es = create_es_client(ELASTIC_HOST)

    if app.state.es is None:
        print("WARNING: Elasticsearch connection failed. Some endpoints may not work.")

    try:
        create_alert_index()
        start_scheduler()
        print("Scheduler started and alert index ensured.")
    except Exception as e:
        print(f"Startup warning: {e}")

    yield

    print("Shutting down AI Service...")
    if app.state.es:
        app.state.es.close()


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(lifespan=lifespan)

# =====================================================
# CORS CONFIG
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def root():
    return {"message": "AI Service is running"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-service"}


# =====================================================
# LOGS (Dashboard Ready + Historical Support)
# =====================================================

@app.get("/logs")
def get_logs(
    service: str = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    minutes: int = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_field: str = "timestamp",
    sort_order: str = "desc"
):
    must = []

    if service:
        must.append({"term": {"serviceName.keyword": service}})

    if level:
        must.append({"term": {"logLevel.keyword": level}})

    if minutes:
        must.append({
            "range": {
                "timestamp": {
                    "gte": f"now-{minutes}m",
                    "lte": "now"
                }
            }
        })

    if start_time and end_time:
        must.append({
            "range": {
                "timestamp": {
                    "gte": start_time,
                    "lte": end_time
                }
            }
        })

    query = {"bool": {"must": must}} if must else {"match_all": {}}

    response = search_with_pagination(
        "logs",
        query,
        page,
        size,
        sort_field,
        sort_order
    )

    return {
        "page": page,
        "size": size,
        "total": response["hits"]["total"]["value"],
        "data": [hit["_source"] for hit in response["hits"]["hits"]]
    }


# =====================================================
# RCA (Realtime + Historical)
# =====================================================

@app.get("/rca/realtime")
def get_realtime_rca(
    minutes: int = Query(5, ge=1, le=1440),
    size: int = Query(1000, ge=10, le=10000)
):
    logs = fetch_logs(size=size, minutes=minutes)
    rca = perform_rca(logs)

    return {
        "mode": "realtime",
        "totalLogsAnalyzed": len(logs),
        "rca": rca
    }


@app.get("/rca/historical")
def get_historical_rca(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    size: int = Query(2000, ge=10, le=20000)
):
    if not start_time and not end_time:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)

    if (start_time and not end_time) or (end_time and not start_time):
        return {"error": "Provide both start_time and end_time or neither."}

    if start_time >= end_time:
        return {"error": "start_time must be earlier than end_time."}

    logs = fetch_logs(
        size=size,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat()
    )

    rca = perform_rca(logs)

    return {
        "mode": "historical",
        "windowStart": start_time,
        "windowEnd": end_time,
        "totalLogsAnalyzed": len(logs),
        "rca": rca
    }


# =====================================================
# ANOMALIES
# =====================================================

@app.get("/anomalies")
def get_anomalies(
    minutes: int = Query(5, ge=1, le=1440),
    size: int = Query(1000, ge=10, le=10000)
):
    logs = fetch_logs(size=size, minutes=minutes)

    isolation_forest_result = detect_isolation_forest_anomaly(logs)

    return {
        "mode": "realtime",
        "totalLogsAnalyzed": len(logs),

        # Existing rule-based detectors
        "trafficDrop": detect_traffic_drop(logs),
        "errorRate": detect_error_rate_anomaly(logs),
        "critical": detect_critical_errors(logs),
        "rare": detect_rare_logs(logs),
        "spike": detect_spike_with_baseline(logs),

        # ML detector
        "isolationForest": isolation_forest_result
    }
# =====================================================
# ALERTS
# =====================================================

@app.get("/alerts")
def get_alerts(
    status: str = None,
    severity: str = None,
    start_time: str = None,
    end_time: str = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_field: str = "firstDetectedAt",
    sort_order: str = "desc"
):
    must = []

    if status:
        must.append({"term": {"status": status}})

    if severity:
        must.append({"term": {"severity": severity}})

    if start_time and end_time:
        must.append({
            "range": {
                "firstDetectedAt": {
                    "gte": start_time,
                    "lte": end_time
                }
            }
        })

    query = {"bool": {"must": must}} if must else {"match_all": {}}

    response = search_with_pagination(
        ALERT_INDEX,
        query,
        page,
        size,
        sort_field,
        sort_order
    )

    return {
        "page": page,
        "size": size,
        "total": response["hits"]["total"]["value"],
        "data": [hit["_source"] for hit in response["hits"]["hits"]]
    }


@app.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: str):
    es = Elasticsearch(ELASTIC_HOST)
    es.update(
        index=ALERT_INDEX,
        id=alert_id,
        body={"doc": {"status": "ACKNOWLEDGED"}}
    )
    return {"message": "Alert acknowledged"}


@app.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    es = Elasticsearch(ELASTIC_HOST)
    es.update(
        index=ALERT_INDEX,
        id=alert_id,
        body={"doc": {"status": "RESOLVED"}}
    )
    return {"message": "Alert resolved"}


# =====================================================
# CLUSTERS
# =====================================================

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