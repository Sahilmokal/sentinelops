from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from zoneinfo import ZoneInfo

from elastic_client import (
    fetch_logs,
    find_active_alerts_for_ml_window,
)

from anomaly.anomaly import (
    detect_rare_logs,
    detect_error_rate_anomaly,
    detect_traffic_drop,
    detect_critical_errors,
    detect_spike_anomalies,
)

from anomaly.isolation_forest import (
    detect_isolation_forest_anomaly,
)

from storage.ml_storage import (
    save_ml_result,
)

from clustering.cluster_service import (
    process_cluster_window,
)

from rca.rca_engine import (
    perform_rca,
)

from alert.alert_engine import (
    create_alert,
    enrich_active_alert_with_ml,
)


# ============================================================
# CONFIGURATION
# ============================================================

IST = ZoneInfo(
    "Asia/Kolkata"
)

RULE_WINDOW_MINUTES = 2

ML_WINDOW_MINUTES = 5


# ============================================================
# RULE-BASED MONITORING
# ============================================================

def monitor_rules():

    print(
        "[Rules] 30-second scheduler fired at:",
        datetime.now(
            IST
        ).isoformat()
    )

    try:

        # ====================================================
        # ROLLING 2-MINUTE WINDOW
        # ====================================================

        logs = fetch_logs(
            size=1000,
            minutes=RULE_WINDOW_MINUTES
        )

        if not logs:
            return

        # ====================================================
        # RULE DETECTORS
        # ====================================================

        anomalies = {

            "trafficDrop":
                detect_traffic_drop(
                    logs
                ),

            "errorRate":
                detect_error_rate_anomaly(
                    logs
                ),

            "critical":
                detect_critical_errors(
                    logs
                ),

            "rare":
                detect_rare_logs(
                    logs
                ),

            "spike":
                detect_spike_anomalies(
                    logs
                ),
        }

        # ====================================================
        # ACTIVE ANOMALIES
        # ====================================================

        active_anomalies = {

            key: value

            for key, value
            in anomalies.items()

            if value
        }

        if not active_anomalies:

            return

        print(
            "[Rules] Detected anomalies: "
            f"{list(active_anomalies.keys())}"
        )

        # ====================================================
        # TRAFFIC DROP
        #
        # Traffic drop does not require RCA.
        # ====================================================

        if (
            "trafficDrop"
            in active_anomalies
        ):

            create_alert(
                anomalies={
                    "trafficDrop":
                        active_anomalies[
                            "trafficDrop"
                        ]
                },

                rca=None,

                source="RULE"
            )

        # ====================================================
        # REMOVE TRAFFIC DROP
        # ====================================================

        remaining_anomalies = {

            key: value

            for key, value
            in active_anomalies.items()

            if key != "trafficDrop"
        }

        if not remaining_anomalies:

            return

        # ====================================================
        # STAGE 1 RCA
        # ====================================================

        rca_result = perform_rca(
            logs=logs
        )

        print(
            "[Rules] Stage 1 RCA result: "
            f"{rca_result}"
        )

        # ====================================================
        # CREATE OR UPDATE INCIDENT
        # ====================================================

        create_alert(
            anomalies=
                remaining_anomalies,

            rca=
                rca_result,

            source=
                "RULE"
        )

    except Exception as e:

        print(
            "[Rules] Monitoring error: "
            f"{e}"
        )


# ============================================================
# CANONICAL 5-MINUTE ML PIPELINE
# ============================================================

def run_ml_pipeline():

    print(
        "============================================================"
    )

    print(
        "[ML Pipeline] START"
    )

    try:

        # ====================================================
        # CURRENT IST TIME
        # ====================================================

        now = datetime.now(
            IST
        )

        # ====================================================
        # COMPLETED 5-MINUTE BOUNDARY
        # ====================================================

        window_end = now.replace(
            second=0,
            microsecond=0
        )

        window_end = window_end.replace(
            minute=(
                window_end.minute
                // ML_WINDOW_MINUTES
            )
            * ML_WINDOW_MINUTES
        )

        window_start = (
            window_end
            - timedelta(
                minutes=
                    ML_WINDOW_MINUTES
            )
        )

        # ====================================================
        # ISO IDENTIFIERS
        # ====================================================

        window_start_iso = (
            window_start.isoformat()
        )

        window_end_iso = (
            window_end.isoformat()
        )

        window_id = (
            f"{window_start_iso}_"
            f"{window_end_iso}"
        )

        print(
            "[ML Pipeline] Canonical window:"
        )

        print(
            f"[ML Pipeline] START = "
            f"{window_start_iso}"
        )

        print(
            f"[ML Pipeline] END   = "
            f"{window_end_iso}"
        )

        print(
            f"[ML Pipeline] ID    = "
            f"{window_id}"
        )

        # ====================================================
        # EXACT 5-MINUTE LOG WINDOW
        # ====================================================

        logs = fetch_logs(
            size=10000,

            start_time=
                window_start_iso,

            end_time=
                window_end_iso
        )

        print(
            "[ML Pipeline] "
            f"Window logs = {len(logs)}"
        )

        # ====================================================
        # FIND EXACT INCIDENTS FOR THIS WINDOW
        #
        # THIS IS THE CRITICAL FIX.
        #
        # We determine the alert ID BEFORE enrichment.
        # ====================================================

        target_alerts = []

        try:

            target_alerts = (
                find_active_alerts_for_ml_window(
                    window_start=
                        window_start_iso,

                    window_end=
                        window_end_iso
                )
            )

        except Exception as e:

            print(
                "[ML Pipeline] "
                "Failed to find target incidents: "
                f"{e}"
            )

            target_alerts = []

        print(
            "[ML Pipeline] "
            f"Target incidents = "
            f"{len(target_alerts)}"
        )

        for target in target_alerts:

            print(
                "[ML Pipeline] "
                f"TARGET alertId="
                f"{target.get('alertId')}"
            )

        # ====================================================
        # NO LOG DATA
        # ====================================================

        if not logs:

            result = {

                "type":
                    "ISOLATION_FOREST_NO_DATA",

                "anomaly":
                    False,

                "prediction":
                    None,

                "score":
                    None,

                "baselineWindows":
                    None,

                "requiredBaselineWindows":
                    30,

                "features":
                    None,

                "errors": {

                    "errorMessages":
                        [],

                    "errorServices":
                        [],

                    "criticalErrors":
                        [],
                },
            }

            save_ml_result(
                window_id=
                    window_id,

                window_start=
                    window_start_iso,

                window_end=
                    window_end_iso,

                result=
                    result
            )

            print(
                "[ML Pipeline] "
                "No logs for completed window."
            )

            return None

        # ====================================================
        # SEMANTIC CLUSTERING
        # ====================================================

        cluster_result = None

        try:

            cluster_result = (
                process_cluster_window(

                    logs=
                        logs,

                    window_id=
                        window_id,

                    window_start=
                        window_start_iso,

                    window_end=
                        window_end_iso
                )
            )

            print(
                "[Semantic Clustering] "
                f"Clusters found: "
                f"{cluster_result.get('clusterCount', 0)}"
            )

        except Exception as e:

            print(
                "[Semantic Clustering] "
                f"Processing error: {e}"
            )

        # ====================================================
        # ISOLATION FOREST
        # ====================================================

        try:

            ml_result = (
                detect_isolation_forest_anomaly(

                    logs=
                        logs,

                    window_id=
                        window_id,

                    window_start=
                        window_start_iso,

                    window_end=
                        window_end_iso
                )
            )

            print(
                "[Isolation Forest] Result: "
                f"{ml_result}"
            )

        except Exception as e:

            print(
                "[Isolation Forest] "
                f"Processing error: {e}"
            )

            ml_result = {

                "type":
                    "ISOLATION_FOREST_ERROR",

                "anomaly":
                    False,

                "prediction":
                    None,

                "score":
                    None,

                "baselineWindows":
                    None,

                "requiredBaselineWindows":
                    30,

                "features":
                    None,

                "errors": {

                    "errorMessages":
                        [],

                    "errorServices":
                        [],

                    "criticalErrors":
                        [],
                },
            }

        # ====================================================
        # STAGE 2 RCA
        # ====================================================

        rca_result = None

        try:

            rca_result = perform_rca(

                logs=
                    logs,

                cluster_result=
                    cluster_result,

                ml_result=
                    ml_result
            )

            print(
                "[ML RCA] Stage 2 result:"
            )

            print(
                rca_result
            )

        except Exception as e:

            print(
                "[ML RCA] "
                f"Processing error: {e}"
            )

        # ====================================================
        # EXACT ALERT ENRICHMENT
        #
        # NEVER GUESS THE INCIDENT.
        #
        # Every target alert gets the SAME completed
        # ML window evidence, but is updated by its
        # OWN exact alertId.
        # ====================================================

        if not target_alerts:

            print(
                "[ML Alert Enrichment] "
                "No active incidents belong to "
                f"window {window_id}"
            )

        else:

            for target in target_alerts:

                alert_id = (
                    target.get(
                        "alertId"
                    )
                )

                if not alert_id:

                    print(
                        "[ML Alert Enrichment] "
                        "Skipping target without alertId."
                    )

                    continue

                print(
                    "------------------------------------------------------------"
                )

                print(
                    "[ML Alert Enrichment] "
                    "ENRICHING EXACT INCIDENT"
                )

                print(
                    "[ML Alert Enrichment] "
                    f"alertId={alert_id}"
                )

                print(
                    "[ML Alert Enrichment] "
                    f"window={window_id}"
                )

                try:

                    enriched = (
                        enrich_active_alert_with_ml(

                            alert_id=
                                alert_id,

                            window_id=
                                window_id,

                            window_start=
                                window_start_iso,

                            window_end=
                                window_end_iso,

                            cluster_result=
                                cluster_result,

                            ml_result=
                                ml_result,

                            rca_result=
                                rca_result
                        )
                    )

                    if enriched:

                        print(
                            "[ML Alert Enrichment] "
                            "SUCCESS"
                        )

                        print(
                            "[ML Alert Enrichment] "
                            f"alertId={alert_id}"
                        )

                    else:

                        print(
                            "[ML Alert Enrichment] "
                            "SKIPPED/FAILED"
                        )

                except Exception as e:

                    print(
                        "[ML Alert Enrichment] "
                        f"FAILED | "
                        f"alertId={alert_id} | "
                        f"error={e}"
                    )

        # ====================================================
        # RETURN PIPELINE RESULT
        # ====================================================

        return {

            "windowId":
                window_id,

            "windowStart":
                window_start_iso,

            "windowEnd":
                window_end_iso,

            "targetAlerts":
                [
                    target.get(
                        "alertId"
                    )
                    for target
                    in target_alerts
                ],

            "clusterResult":
                cluster_result,

            "mlResult":
                ml_result,

            "rcaResult":
                rca_result,
        }

    except Exception as e:

        print(
            "[ML Pipeline] "
            f"Monitoring error: {e}"
        )

        return None

    finally:

        print(
            "[ML Pipeline] END"
        )

        print(
            "============================================================"
        )


# ============================================================
# SCHEDULER
# ============================================================

def start_scheduler():

    scheduler = BackgroundScheduler(
        timezone=IST
    )

    # ========================================================
    # RULE MONITOR
    #
    # Every 30 seconds
    # Rolling 2-minute window
    # Stage 1 RCA
    # ========================================================

    scheduler.add_job(

        monitor_rules,

        "interval",

        seconds=30,

        id=
            "rule_monitor",

        replace_existing=
            True,

        max_instances=
            1,

        coalesce=
            True,

        misfire_grace_time=
            30
    )

    # ========================================================
    # ML PIPELINE
    #
    # Every 5 minutes
    #
    # Runs at second 5 so the previous 5-minute window
    # is definitely complete.
    # ========================================================

    scheduler.add_job(

        run_ml_pipeline,

        CronTrigger(

            minute="*/5",

            second=5,

            timezone=IST
        ),

        id=
            "ml_pipeline",

        replace_existing=
            True,

        max_instances=
            1,

        coalesce=
            True,

        misfire_grace_time=
            60
    )

    # ========================================================
    # START
    # ========================================================

    scheduler.start()

    print(
        "============================================================"
    )

    print(
        "[Scheduler] Started"
    )

    print(
        "[Scheduler] "
        f"Rules = {RULE_WINDOW_MINUTES}m rolling / 30s"
    )

    print(
        "[Scheduler] "
        f"ML = {ML_WINDOW_MINUTES}m canonical window"
    )

    print(
        "[Scheduler] "
        "ML = clustering + Isolation Forest + Stage 2 RCA"
    )

    print(
        "[Scheduler] "
        "ML = exact alertId enrichment"
    )

    print(
        "============================================================"
    )