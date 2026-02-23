from fastapi import FastAPI, Query
from elastic_client import (
    fetch_logs,
    search_with_pagination,
    es,
    ALERT_INDEX
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
from scheduler import start_scheduler

app = FastAPI()

start_scheduler()

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
        "logs-*",
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
    start_time: str,
    end_time: str,
    size: int = Query(5000, ge=10, le=20000)
):
    logs = fetch_logs(
        size=size,
        start_time=start_time,
        end_time=end_time
    )

    rca = perform_rca(logs)

    return {
        "mode": "historical",
        "totalLogsAnalyzed": len(logs),
        "rca": rca
    }


# =====================================================
# ANOMALIES (Realtime + Unified)
# =====================================================

@app.get("/anomalies")
def get_anomalies(
    minutes: int = Query(5, ge=1, le=1440),
    size: int = Query(1000, ge=10, le=10000)
):

    logs = fetch_logs(size=size, minutes=minutes)

    return {
        "mode": "realtime",
        "trafficDrop": detect_traffic_drop(logs),
        "errorRate": detect_error_rate_anomaly(logs),
        "critical": detect_critical_errors(logs),
        "rare": detect_rare_logs(logs),
        "spike": detect_spike_with_baseline(logs)
    }


# =====================================================
# ALERTS (Pagination + Filtering + Sorting)
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

    es.update(
        index=ALERT_INDEX,
        id=alert_id,
        body={"doc": {"status": "ACKNOWLEDGED"}}
    )

    return {"message": "Alert acknowledged"}


@app.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):

    es.update(
        index=ALERT_INDEX,
        id=alert_id,
        body={"doc": {"status": "RESOLVED"}}
    )

    return {"message": "Alert resolved"}