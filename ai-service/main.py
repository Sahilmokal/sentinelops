import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from anomaly.ml_result_store import load_ml_result
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from storage.ml_storage import ensure_ml_storage
from storage.ml_storage import load_latest_ml_result
from clustering.cluster_service import process_cluster_window
from elastic_client import (
    es,
    fetch_logs,
    search_with_pagination,
    ALERT_INDEX,
    create_alert_index,
    update_alert,
    get_alert_by_id
)
from clustering.semantic_cluster import cluster_logs
from clustering.cluster_store import ensure_cluster_storage
from rca.rca_engine import perform_rca
from anomaly.anomaly import (
    detect_rare_logs,
    detect_spike_anomalies,
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
        ensure_ml_storage()
        ensure_cluster_storage()
        start_scheduler()

        print("Scheduler started.")
        print("ML storage initialized.")
        print("Semantic clustering storage initialized.")
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
@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):

    create_alert_index()

    try:
        alert = es.get(
            index=ALERT_INDEX,
            id=alert_id
        )

    except Exception:
        return {
            "message": "Alert not found",
            "alertId": alert_id,
            "found": False
        }

    return {
        "found": True,
        "alertId": alert_id,
        "alert": alert.get("_source", {})
    }

# ============================================================
# RCA - INCIDENT BASED
# ============================================================

# ============================================================
# RCA - EXACT INCIDENT
#
# Behaviour:
#
# 1. Find the exact alert by alertId.
# 2. If RCA already exists, return it.
# 3. If RCA is missing, calculate RCA for this incident.
# 4. Persist the RCA back into the SAME alert.
# 5. Return the exact incident + RCA.
#
# No "latest alert" guessing.
# No unrelated incident fallback.
# ============================================================

@app.get("/rca/incident/{alert_id}")
def get_incident_rca(
    alert_id: str
):

    print("=" * 70)
    print("[RCA API] EXACT INCIDENT RCA REQUEST")
    print("[RCA API] alertId:", alert_id)
    print("=" * 70)

    create_alert_index()

    # --------------------------------------------------------
    # GET EXACT ALERT
    # --------------------------------------------------------

    try:

        alert_response = get_alert_by_id(
            alert_id
        )

    except Exception as e:

        print(
            "[RCA API] Alert lookup failed:",
            str(e)
        )

        return {
            "mode": "incident",
            "alertId": alert_id,
            "rca": None,
            "message": "Incident not found."
        }

    # --------------------------------------------------------
    # EXTRACT ALERT
    # --------------------------------------------------------

    alert = alert_response.get(
        "_source",
        {}
    )

    if not alert:

        return {
            "mode": "incident",
            "alertId": alert_id,
            "rca": None,
            "message": "Incident not found."
        }

    # --------------------------------------------------------
    # VERIFY CANONICAL ID
    # --------------------------------------------------------

    stored_alert_id = (
        alert.get("alertId")
    )

    if (
        stored_alert_id and
        str(stored_alert_id) != str(alert_id)
    ):

        print(
            "[RCA API] ALERT ID MISMATCH"
        )

        return {
            "mode": "incident",
            "alertId": alert_id,
            "rca": None,
            "message": "Alert identity mismatch."
        }

    # --------------------------------------------------------
    # EXISTING RCA
    # --------------------------------------------------------

    rca = alert.get(
        "rca"
    )

    # --------------------------------------------------------
    # IF RCA DOES NOT EXIST
    #
    # Calculate it now using logs belonging to the
    # incident time range.
    # --------------------------------------------------------

    if rca is None:

        print(
            "[RCA API] No stored RCA."
        )

        print(
            "[RCA API] Calculating RCA for exact incident:",
            alert_id
        )

        first_detected_at = (
            alert.get(
                "firstDetectedAt"
            )
        )

        last_updated_at = (
            alert.get(
                "lastUpdatedAt"
            )
        )

        # ----------------------------------------------------
        # FETCH INCIDENT LOG WINDOW
        # ----------------------------------------------------

        try:

            if (
                first_detected_at and
                last_updated_at
            ):

                logs = fetch_logs(
                    size=10000,
                    start_time=first_detected_at,
                    end_time=last_updated_at
                )

            else:

                # Safe fallback for old alerts that do not have
                # proper timestamps.
                logs = fetch_logs(
                    size=1000,
                    minutes=5
                )

        except Exception as e:

            print(
                "[RCA API] Failed to fetch incident logs:",
                str(e)
            )

            return {
                "mode": "incident",
                "alertId": alert_id,
                "incidentFamily":
                    alert.get(
                        "incidentFamily"
                    ),
                "severity":
                    alert.get(
                        "severity"
                    ),
                "status":
                    alert.get(
                        "status"
                    ),
                "rootService":
                    alert.get(
                        "rootService"
                    ),
                "impactedServices":
                    alert.get(
                        "impactedServices",
                        []
                    ),
                "confidence":
                    alert.get(
                        "confidence",
                        0.0
                    ),
                "rca": None,
                "message":
                    "RCA could not be calculated because incident logs could not be loaded."
            }

        print(
            "[RCA API] Logs available for RCA:",
            len(logs)
        )

        # ----------------------------------------------------
        # CALCULATE RCA
        # ----------------------------------------------------

        if logs:

            try:

                rca = perform_rca(
                    logs=logs
                )

            except Exception as e:

                print(
                    "[RCA API] RCA calculation failed:",
                    str(e)
                )

                return {
                    "mode": "incident",
                    "alertId": alert_id,
                    "incidentFamily":
                        alert.get(
                            "incidentFamily"
                        ),
                    "severity":
                        alert.get(
                            "severity"
                        ),
                    "status":
                        alert.get(
                            "status"
                        ),
                    "rootService":
                        alert.get(
                            "rootService"
                        ),
                    "impactedServices":
                        alert.get(
                            "impactedServices",
                            []
                        ),
                    "confidence":
                        alert.get(
                            "confidence",
                            0.0
                        ),
                    "rca": None,
                    "message":
                        "RCA calculation failed."
                }

        else:

            print(
                "[RCA API] No logs found for incident."
            )

            return {
                "mode": "incident",
                "alertId": alert_id,
                "incidentFamily":
                    alert.get(
                        "incidentFamily"
                    ),
                "severity":
                    alert.get(
                        "severity"
                    ),
                "status":
                    alert.get(
                        "status"
                    ),
                "rootService":
                    alert.get(
                        "rootService"
                    ),
                "impactedServices":
                    alert.get(
                        "impactedServices",
                        []
                    ),
                "confidence":
                    alert.get(
                        "confidence",
                        0.0
                    ),
                "rca": None,
                "message":
                    "No logs were found for this incident."
            }

        # ----------------------------------------------------
        # PERSIST RCA INTO SAME ALERT
        # ----------------------------------------------------

        if isinstance(
            rca,
            dict
        ):

            root_service = rca.get(
                "rootService",
                alert.get(
                    "rootService",
                    "unknown-service"
                )
            )

            impacted_services = rca.get(
                "impactedServices",
                alert.get(
                    "impactedServices",
                    []
                )
            )

            confidence = rca.get(
                "confidence",
                alert.get(
                    "confidence",
                    0.0
                )
            )

            now = datetime.now(
                timezone.utc
            ).isoformat()

            update_fields = {

                "rca":
                    rca,

                "rootService":
                    root_service,

                "impactedServices":
                    impacted_services,

                "confidence":
                    confidence,

                "lastUpdatedAt":
                    now,
            }

            try:

                update_alert(
                    alert_id,
                    update_fields
                )

                print(
                    "[RCA API] RCA persisted successfully:",
                    alert_id
                )

                # Keep local response synchronized.
                alert.update(
                    update_fields
                )

            except Exception as e:

                print(
                    "[RCA API] Failed to persist RCA:",
                    str(e)
                )

        else:

            print(
                "[RCA API] perform_rca returned no valid RCA."
            )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    print(
        "[RCA API] RCA found/generated for:",
        alert_id
    )

    return {

        "mode":
            "incident",

        "alertId":
            alert_id,

        "incidentFamily":
            alert.get(
                "incidentFamily"
            ),

        "anomalyType":
            alert.get(
                "anomalyType"
            ),

        "severity":
            alert.get(
                "severity"
            ),

        "status":
            alert.get(
                "status"
            ),

        "sources":
            alert.get(
                "sources",
                []
            ),

        "firstDetectedAt":
            alert.get(
                "firstDetectedAt"
            ),

        "lastUpdatedAt":
            alert.get(
                "lastUpdatedAt"
            ),

        "occurrenceCount":
            alert.get(
                "occurrenceCount",
                0
            ),

        "rootService":
            alert.get(
                "rootService"
            ),

        "impactedServices":
            alert.get(
                "impactedServices",
                []
            ),

        "confidence":
            alert.get(
                "confidence",
                0.0
            ),

        "anomalies":
            alert.get(
                "anomalies",
                {}
            ),

        "rca":
            alert.get(
                "rca"
            ),

        "mlRca":
            alert.get(
                "mlRca"
            ),

        "mlEvidence":
            alert.get(
                "mlEvidence"
            ),

        "mlAnomaly":
            alert.get(
                "mlAnomaly"
            ),

        "mlScore":
            alert.get(
                "mlScore"
            ),

        "alert":
            alert
    }

# ============================================================
# RCA HISTORY
#
# Returns previously created incidents whose firstDetectedAt
# falls inside the requested time period.
#
# IMPORTANT:
# This does NOT recalculate RCA.
# It returns the RCA already stored on the incident.
# ============================================================

@app.get("/rca/history")
def get_rca_history(
    start_time: str = None,
    end_time: str = None,
    status: str = None,
    severity: str = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):

    print("=" * 70)
    print("[RCA HISTORY] REQUEST")
    print("[RCA HISTORY] start_time:", start_time)
    print("[RCA HISTORY] end_time:", end_time)
    print("[RCA HISTORY] status:", status)
    print("[RCA HISTORY] severity:", severity)
    print("=" * 70)

    create_alert_index()

    must = []

    # --------------------------------------------------------
    # ONLY INCIDENTS THAT ACTUALLY HAVE RCA
    # --------------------------------------------------------

    must.append({
        "exists": {
            "field": "rca"
        }
    })

    # --------------------------------------------------------
    # PERIOD
    #
    # History is based on when the incident was first detected.
    # --------------------------------------------------------

    if start_time and end_time:

        must.append({
            "range": {
                "firstDetectedAt": {
                    "gte": start_time,
                    "lte": end_time
                }
            }
        })

    elif start_time:

        must.append({
            "range": {
                "firstDetectedAt": {
                    "gte": start_time
                }
            }
        })

    elif end_time:

        must.append({
            "range": {
                "firstDetectedAt": {
                    "lte": end_time
                }
            }
        })

    # --------------------------------------------------------
    # OPTIONAL STATUS
    # --------------------------------------------------------

    if status:

        must.append({
            "term": {
                "status": status
            }
        })

    # --------------------------------------------------------
    # OPTIONAL SEVERITY
    # --------------------------------------------------------

    if severity:

        must.append({
            "term": {
                "severity": severity
            }
        })

    query = {
        "bool": {
            "must": must
        }
    }

    response = search_with_pagination(
        ALERT_INDEX,
        query,
        page,
        size,
        "firstDetectedAt",
        "desc"
    )

    hits = response[
        "hits"
    ]["hits"]

    total = response[
        "hits"
    ]["total"]["value"]

    data = []

    for hit in hits:

        alert = hit.get(
            "_source",
            {}
        )

        # ----------------------------------------------------
        # Return the stored incident RCA.
        #
        # No RCA recalculation happens here.
        # ----------------------------------------------------

        data.append({

            "alertId":
                alert.get(
                    "alertId",
                    hit.get("_id")
                ),

            "incidentFamily":
                alert.get(
                    "incidentFamily"
                ),

            "anomalyType":
                alert.get(
                    "anomalyType"
                ),

            "severity":
                alert.get(
                    "severity"
                ),

            "status":
                alert.get(
                    "status"
                ),

            "rootService":
                alert.get(
                    "rootService",
                    "unknown-service"
                ),

            "impactedServices":
                alert.get(
                    "impactedServices",
                    []
                ),

            "confidence":
                alert.get(
                    "confidence",
                    0.0
                ),

            "firstDetectedAt":
                alert.get(
                    "firstDetectedAt"
                ),

            "lastUpdatedAt":
                alert.get(
                    "lastUpdatedAt"
                ),

            "resolvedAt":
                alert.get(
                    "resolvedAt"
                ),

            "occurrenceCount":
                alert.get(
                    "occurrenceCount",
                    0
                ),

            "rcaStage":
                alert.get(
                    "rcaStage",
                    1
                ),

            "rcaSource":
                alert.get(
                    "rcaSource",
                    "RULE"
                ),

            # ------------------------------------------------
            # Preserve all RCA levels.
            # ------------------------------------------------

            "ruleRca":
                alert.get(
                    "ruleRca"
                ),

            "stage2Rca":
                alert.get(
                    "stage2Rca"
                ),

            "mlRca":
                alert.get(
                    "mlRca"
                ),

            "rca":
                alert.get(
                    "rca"
                ),

            "sources":
                alert.get(
                    "sources",
                    []
                ),

        })

    print(
        "[RCA HISTORY] "
        f"Found {len(data)} incidents "
        f"out of {total}"
    )

    return {

        "mode":
            "historical",

        "startTime":
            start_time,

        "endTime":
            end_time,

        "page":
            page,

        "size":
            size,

        "total":
            total,

        "data":
            data,
    }
# =====================================================
# ANOMALIES
# =====================================================

@app.get("/anomalies")
def get_anomalies(
    minutes: int = Query(5, ge=1, le=1440),
    size: int = Query(1000, ge=10, le=10000)
):

    logs = fetch_logs(
        size=size,
        minutes=minutes
    )

    # Isolation Forest is executed by the scheduler.
    # Here we only read its latest persisted result.
    latest_ml_result = load_latest_ml_result()

    return {
        "mode": "realtime",
        "totalLogsAnalyzed": len(logs),

        "trafficDrop": detect_traffic_drop(logs),
        "errorRate": detect_error_rate_anomaly(logs),
        "critical": detect_critical_errors(logs),
        "rare": detect_rare_logs(logs),
        "spike": detect_spike_anomalies(logs),

        "isolationForest": latest_ml_result,
    }
# =====================================================
# 
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

    print("=" * 70)
    print("[ALERT API] ACK REQUEST")
    print("[ALERT API] alertId:", alert_id)
    print("[ALERT API] index:", ALERT_INDEX)
    print("=" * 70)

    create_alert_index()

    try:
        alert = es.get(
            index=ALERT_INDEX,
            id=alert_id
        )

        print(
            "[ALERT API] Elasticsearch document found"
        )

        print(
            "[ALERT API] ES _id:",
            alert.get("_id")
        )

        print(
            "[ALERT API] source.alertId:",
            alert.get("_source", {}).get("alertId")
        )

        print(
            "[ALERT API] current status:",
            alert.get("_source", {}).get("status")
        )

    except Exception as e:

        print(
            "[ALERT API] ACK LOOKUP FAILED"
        )

        print(
            "[ALERT API] exception type:",
            type(e).__name__
        )

        print(
            "[ALERT API] exception:",
            str(e)
        )

        return {
            "message": "Alert not found",
            "alertId": alert_id,
            "status": "NOT_FOUND",
            "updated": False
        }

    current_status = alert["_source"].get(
        "status",
        "NEW"
    )

    if current_status != "NEW":

        print(
            "[ALERT API] ACK rejected"
        )

        print(
            "[ALERT API] current status:",
            current_status
        )

        return {
            "message": (
                f"Invalid lifecycle transition: "
                f"{current_status} -> ACKNOWLEDGED"
            ),
            "alertId": alert_id,
            "status": current_status,
            "updated": False
        }

    now = datetime.now(
        timezone.utc
    ).isoformat()

    print(
        "[ALERT API] Updating alert..."
    )

    print(
        "[ALERT API] alertId:",
        alert_id
    )

    result = update_alert(
        alert_id,
        {
            "status": "ACKNOWLEDGED",
            "lastUpdatedAt": now
        }
    )

    print(
        "[ALERT API] UPDATE RESULT:",
        result
    )

    print(
        "[ALERT API] ACK SUCCESS"
    )

    return {
        "message": "Alert acknowledged",
        "alertId": alert_id,
        "status": "ACKNOWLEDGED",
        "updated": True
    }
@app.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):

    print("=" * 70)
    print("[ALERT API] RESOLVE REQUEST")
    print("[ALERT API] alertId:", alert_id)
    print("[ALERT API] index:", ALERT_INDEX)
    print("=" * 70)

    create_alert_index()

    try:
        alert = es.get(
            index=ALERT_INDEX,
            id=alert_id
        )

        print(
            "[ALERT API] Elasticsearch document found"
        )

        print(
            "[ALERT API] ES _id:",
            alert.get("_id")
        )

        print(
            "[ALERT API] source.alertId:",
            alert.get("_source", {}).get("alertId")
        )

        print(
            "[ALERT API] current status:",
            alert.get("_source", {}).get("status")
        )

    except Exception as e:

        print(
            "[ALERT API] RESOLVE LOOKUP FAILED"
        )

        print(
            "[ALERT API] exception type:",
            type(e).__name__
        )

        print(
            "[ALERT API] exception:",
            str(e)
        )

        return {
            "message": "Alert not found",
            "alertId": alert_id,
            "status": "NOT_FOUND",
            "updated": False
        }

    current_status = alert["_source"].get(
        "status",
        "NEW"
    )

    if current_status != "ACKNOWLEDGED":

        print(
            "[ALERT API] RESOLVE rejected"
        )

        print(
            "[ALERT API] current status:",
            current_status
        )

        return {
            "message": (
                f"Invalid lifecycle transition: "
                f"{current_status} -> RESOLVED"
            ),
            "alertId": alert_id,
            "status": current_status,
            "updated": False
        }

    now = datetime.now(
        timezone.utc
    ).isoformat()

    print(
        "[ALERT API] Updating alert..."
    )

    result = update_alert(
        alert_id,
        {
            "status": "RESOLVED",
            "resolvedAt": now,
            "lastUpdatedAt": now
        }
    )

    print(
        "[ALERT API] UPDATE RESULT:",
        result
    )

    print(
        "[ALERT API] RESOLVE SUCCESS"
    )

    return {
        "message": "Alert resolved",
        "alertId": alert_id,
        "status": "RESOLVED",
        "updated": True
    }
# =====================================================
# CLUSTERS
# =====================================================


@app.get("/clusters")
def get_clusters(
        size: int = Query(500, ge=10, le=5000),
        minutes: int = Query(5, ge=1, le=1440)
    ):
    logs = fetch_logs(
        size=size,
        minutes=minutes
    )

    result = cluster_logs(logs)

    return {
        "mode": "realtime",
        "totalLogsFetched": len(logs),
        "totalMessages": result["totalMessages"],
        "uniqueMessages": result["uniqueMessages"],
        "totalClusters": result["clusterCount"],
        "noiseCount": result["noiseCount"],
        "noiseMessages": result["noiseMessages"],
        "clusters": result["clusters"]
    }