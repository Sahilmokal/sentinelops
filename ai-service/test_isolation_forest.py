from anomaly.isolation_forest import detect_isolation_forest_anomaly


def create_logs(
    total,
    errors,
    warnings,
    service="payment-service"
):
    logs = []

    for i in range(total):

        if i < errors:
            level = "ERROR"
            message = "Database connection failed"

        elif i < errors + warnings:
            level = "WARN"
            message = "Slow database response"

        else:
            level = "INFO"
            message = "Request processed successfully"

        logs.append({
            "logLevel": level,
            "message": message,
            "serviceName": service,
            "traceId": f"trace-{i}"
        })

    return logs


# ============================================================
# NORMAL WINDOWS
# ============================================================

normal_windows = [
    (100, 5, 10),
    (105, 6, 11),
    (97, 4, 9),
    (110, 7, 12),
    (102, 5, 10),
    (95, 4, 8),
    (108, 6, 13),
    (101, 5, 9),
    (112, 7, 11),
    (98, 4, 10),
    (106, 5, 12),
    (103, 6, 10),
    (99, 5, 8),
    (109, 6, 11),
    (104, 5, 9),

    # Repeat similar normal behavior
    (101, 5, 10),
    (107, 6, 11),
    (96, 4, 9),
    (111, 7, 12),
    (103, 5, 10),
    (94, 4, 8),
    (109, 6, 13),
    (102, 5, 9),
    (113, 7, 11),
    (99, 4, 10),
    (107, 5, 12),
    (104, 6, 10),
    (100, 5, 8),
    (110, 6, 11),
    (105, 5, 9)
]


for i, (total, errors, warnings) in enumerate(
    normal_windows,
    start=1
):

    logs = create_logs(
        total=total,
        errors=errors,
        warnings=warnings
    )

    result = detect_isolation_forest_anomaly(logs)

    print(
        f"Window {i}: "
        f"prediction={result.get('prediction')}, "
        f"anomaly={result.get('anomaly')}, "
        f"score={result.get('score')}, "
        f"type={result.get('type')}"
    )


# ============================================================
# ANOMALOUS WINDOW
# ============================================================
normal_logs = create_logs(
    total=103,
    errors=5,
    warnings=10
)

result = detect_isolation_forest_anomaly(normal_logs)

print("\nBaseline validation:")
print(result)
print("\n========== ANOMALOUS WINDOW ==========\n")

anomalous_logs = create_logs(
    total=1000,
    errors=600,
    warnings=100
)

result = detect_isolation_forest_anomaly(
    anomalous_logs
)

print("Prediction:", result["prediction"])
print("Anomaly:", result["anomaly"])
print("Score:", result["score"])
print("Features:", result["features"])