from apscheduler.schedulers.background import BackgroundScheduler
from elastic_client import fetch_logs
from anomaly import (
    detect_rare_logs,
    detect_error_rate_anomaly,
    detect_traffic_drop,
    detect_critical_errors,
    detect_spike_with_baseline
)
from alert import send_alert


def monitor():

    logs = fetch_logs(size=1000, minutes=2)

    results = {
        "trafficDrop": detect_traffic_drop(logs),
        "errorRate": detect_error_rate_anomaly(logs),
        "critical": detect_critical_errors(logs),
        "rare": detect_rare_logs(logs),
        "spike": detect_spike_with_baseline(logs)
    }

    # If any anomaly exists → alert
    for key, value in results.items():
        if value:
            send_alert({
                "type": key,
                "details": value
            })


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor, "interval", seconds=30)
    scheduler.start()