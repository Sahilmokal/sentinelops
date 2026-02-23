from collections import defaultdict, Counter
from datetime import datetime
from config import TIME_PROPAGATION_WINDOW_SECONDS


def parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts)
    except:
        return None


def perform_rca(logs):

    # Filter ERROR logs
    error_logs = [
        log for log in logs
        if log.get("logLevel") == "ERROR"
    ]

    if not error_logs:
        return None

    # Parse timestamps
    for log in error_logs:
        log["_parsed_time"] = parse_timestamp(log.get("timestamp"))

    error_logs = [l for l in error_logs if l["_parsed_time"]]

    if not error_logs:
        return None

    # ---------------------------
    # Step 1 — Group by traceId
    # ---------------------------
    trace_groups = defaultdict(list)

    for log in error_logs:
        trace_id = log.get("traceId")
        if trace_id:
            trace_groups[trace_id].append(log)

    if not trace_groups:
        return None

    # ----------------------------------------
    # Step 2 — Determine trace-level root
    # ----------------------------------------
    trace_roots = []

    for trace_id, logs_list in trace_groups.items():
        logs_list.sort(key=lambda x: x["_parsed_time"])
        first_error = logs_list[0]
        trace_roots.append(first_error["serviceName"])

    # ----------------------------------------
    # Step 3 — Aggregate across traces
    # ----------------------------------------
    root_counter = Counter(trace_roots)

    global_root, root_occurrences = root_counter.most_common(1)[0]

    # ----------------------------------------
    # Step 4 — Determine impacted services
    # ----------------------------------------
    impacted_services = set()

    for trace_id, logs_list in trace_groups.items():
        logs_list.sort(key=lambda x: x["_parsed_time"])

        first_error = logs_list[0]

        if first_error["serviceName"] == global_root:
            root_time = first_error["_parsed_time"]

            for log in logs_list[1:]:
                time_diff = (log["_parsed_time"] - root_time).total_seconds()

                if 0 <= time_diff <= TIME_PROPAGATION_WINDOW_SECONDS:
                    impacted_services.add(log["serviceName"])

    impacted_services.discard(global_root)

    # ----------------------------------------
    # Determine dominant reason
    # ----------------------------------------
    root_messages = [
        log["message"]
        for log in error_logs
        if log["serviceName"] == global_root
    ]

    reason = Counter(root_messages).most_common(1)[0][0]

    confidence = calculate_confidence(
        root_counter,
        global_root,
        len(trace_groups)
    )

    return {
        "rootService": global_root,
        "impactedServices": list(impacted_services),
        "reason": reason,
        "confidence": confidence,
        "summary": generate_summary(
            global_root,
            impacted_services,
            reason,
            confidence
        )
    }


def calculate_confidence(root_counter, root_service, total_traces):

    dominance = root_counter[root_service] / total_traces

    return round(min(dominance + 0.2, 1.0), 2)


def generate_summary(root, impacted, reason, confidence):

    impacted_text = ", ".join(impacted) if impacted else "no downstream services"

    return (
        f"{root} is identified as the probable root cause "
        f"due to '{reason}'. It impacted {impacted_text}. "
        f"RCA confidence score: {confidence}."
    )