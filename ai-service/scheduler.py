from apscheduler.schedulers.background import BackgroundScheduler
from elastic_client import fetch_logs
from anomaly.anomaly import (
    detect_rare_logs,
    detect_error_rate_anomaly,
    detect_traffic_drop,
    detect_critical_errors,
    detect_spike_with_baseline
)
from rca.rca_engine import perform_rca
from alert.alert_engine import create_alert


def monitor():

    logs = fetch_logs(size=1000, minutes=2)

    anomalies = {
        "trafficDrop": detect_traffic_drop(logs),
        "errorRate": detect_error_rate_anomaly(logs),
        "critical": detect_critical_errors(logs),
        "rare": detect_rare_logs(logs),
        "spike": detect_spike_with_baseline(logs)
    }

    active_anomalies = {k: v for k, v in anomalies.items() if v}

    if not active_anomalies:
        return

    # Traffic drop (no RCA)
    if "trafficDrop" in active_anomalies:
        create_alert(
            anomalies={"trafficDrop": active_anomalies["trafficDrop"]},
            rca=None
        )
        return

    # Error-based anomalies → run RCA
    rca_result = perform_rca(logs)

    create_alert(
        anomalies=active_anomalies,
        rca=rca_result
    )


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor, "interval", seconds=30)
    scheduler.start()