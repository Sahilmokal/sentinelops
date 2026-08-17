from collections import defaultdict, Counter
from datetime import datetime

from config import TIME_PROPAGATION_WINDOW_SECONDS


# ============================================================
# TIMESTAMP
# ============================================================

def parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


# ============================================================
# MAIN RCA
# ============================================================

def perform_rca(
    logs,
    cluster_result=None,
    ml_result=None,
):
    """
    RCA engine.

    Base RCA:
        - traceId grouping
        - temporal ordering
        - first-error service
        - downstream propagation

    Optional enhanced evidence:
        - semantic clustering
        - Isolation Forest anomaly context

    The base RCA works even when cluster_result
    and ml_result are not provided.
    """

    if not logs:
        return None

    # ========================================================
    # FILTER ERROR LOGS
    # ========================================================

    error_logs = [
        log
        for log in logs
        if str(
            log.get("logLevel", "")
        ).upper() == "ERROR"
    ]

    if not error_logs:
        return None

    # ========================================================
    # PARSE TIMESTAMPS
    # ========================================================

    parsed_logs = []

    for log in error_logs:

        parsed_time = parse_timestamp(
            log.get("timestamp")
        )

        if parsed_time is None:
            continue

        parsed_log = dict(log)

        parsed_log["_parsed_time"] = parsed_time

        parsed_logs.append(parsed_log)

    error_logs = parsed_logs

    if not error_logs:
        return None

    # ========================================================
    # GROUP BY TRACE ID
    # ========================================================

    trace_groups = defaultdict(list)

    for log in error_logs:

        trace_id = log.get("traceId")

        if trace_id:
            trace_groups[trace_id].append(log)

    # ========================================================
    # TRACE-BASED ROOT ANALYSIS
    # ========================================================

    trace_roots = []

    impacted_by_root = defaultdict(Counter)

    for trace_id, trace_logs in trace_groups.items():

        trace_logs.sort(
            key=lambda x: x["_parsed_time"]
        )

        first_error = trace_logs[0]

        root_service = first_error.get(
            "serviceName",
            "unknown-service"
        )

        trace_roots.append(
            root_service
        )

        root_time = first_error[
            "_parsed_time"
        ]

        # ----------------------------------------------------
        # Find downstream services
        # ----------------------------------------------------

        for log in trace_logs[1:]:

            service = log.get(
                "serviceName",
                "unknown-service"
            )

            time_diff = (
                log["_parsed_time"]
                - root_time
            ).total_seconds()

            if (
                0 <= time_diff
                <= TIME_PROPAGATION_WINDOW_SECONDS
                and service != root_service
            ):

                impacted_by_root[
                    root_service
                ][service] += 1

    # ========================================================
    # TRACE DOMINANCE
    # ========================================================

    root_counter = Counter(
        trace_roots
    )

    total_traces = len(
        trace_groups
    )

    trace_dominance = {}

    if total_traces:

        trace_dominance = {
            service: count / total_traces
            for service, count
            in root_counter.items()
        }

    # ========================================================
    # SERVICE FIRST-ERROR TIMES
    # ========================================================

    service_first_times = {}

    for log in error_logs:

        service = log.get(
            "serviceName",
            "unknown-service"
        )

        timestamp = log[
            "_parsed_time"
        ]

        if (
            service not in service_first_times
            or timestamp < service_first_times[service]
        ):
            service_first_times[
                service
            ] = timestamp

    temporal_scores = {}

    if service_first_times:

        earliest_time = min(
            service_first_times.values()
        )

        for service, timestamp in (
            service_first_times.items()
        ):

            delay = (
                timestamp
                - earliest_time
            ).total_seconds()

            temporal_scores[
                service
            ] = max(
                0.0,
                1.0 - (
                    delay
                    / max(
                        TIME_PROPAGATION_WINDOW_SECONDS,
                        1
                    )
                )
            )

    # ========================================================
    # SEMANTIC CLUSTER EVIDENCE
    # ========================================================

    cluster_evidence = build_cluster_evidence(
        error_logs,
        cluster_result
    )

    # ========================================================
    # CANDIDATE SERVICES
    # ========================================================

    candidate_services = {
        log.get(
            "serviceName",
            "unknown-service"
        )
        for log in error_logs
    }

    # ========================================================
    # SCORE ROOT CANDIDATES
    # ========================================================

    root_scores = {}

    for service in candidate_services:

        temporal = temporal_scores.get(
            service,
            0.0
        )

        dominance = trace_dominance.get(
            service,
            0.0
        )

        propagation = calculate_propagation_score(
            service,
            impacted_by_root,
            total_traces
        )

        semantic = cluster_evidence[
            "service_scores"
        ].get(
            service,
            0.0
        )

        # ----------------------------------------------------
        # ML is supporting evidence only.
        # It does NOT identify the root service.
        # ----------------------------------------------------

        ml_context = calculate_ml_context(
            ml_result
        )

        # ----------------------------------------------------
        # Weighted score
        # ----------------------------------------------------

        score = (
            temporal * 0.25
            + dominance * 0.30
            + propagation * 0.15
            + semantic * 0.25
            + ml_context * 0.05
        )

        root_scores[
            service
        ] = round(
            score,
            4
        )

    # ========================================================
    # FALLBACK IF TRACE IDS ARE MISSING
    # ========================================================

    if not root_scores:

        service_counter = Counter(
            log.get(
                "serviceName",
                "unknown-service"
            )
            for log in error_logs
        )

        if not service_counter:
            return None

        global_root = (
            service_counter
            .most_common(1)[0][0]
        )

        confidence = 0.0

    else:

        global_root = max(
            root_scores,
            key=root_scores.get
        )

        confidence = root_scores[
            global_root
        ]

    # ========================================================
    # IMPACTED SERVICES
    # ========================================================

    impacted_services = set(
        impacted_by_root[
            global_root
        ].keys()
    )

    impacted_services.discard(
        global_root
    )

    # ========================================================
    # DETERMINE REASON
    # ========================================================

    reason = determine_root_reason(
        error_logs,
        global_root,
        cluster_evidence
    )

    # ========================================================
    # ROOT CLUSTER INFORMATION
    # ========================================================

    root_clusters = cluster_evidence[
        "service_clusters"
    ].get(
        global_root,
        []
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence = {
        "temporal": round(
            temporal_scores.get(
                global_root,
                0.0
            ),
            4
        ),

        "traceDominance": round(
            trace_dominance.get(
                global_root,
                0.0
            ),
            4
        ),

        "propagation": round(
            calculate_propagation_score(
                global_root,
                impacted_by_root,
                total_traces
            ),
            4
        ),

        "semanticCluster": round(
            cluster_evidence[
                "service_scores"
            ].get(
                global_root,
                0.0
            ),
            4
        ),

        "mlContext": round(
            calculate_ml_context(
                ml_result
            ),
            4
        ),
    }

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = generate_summary(
        root=global_root,
        impacted=impacted_services,
        reason=reason,
        confidence=confidence,
        root_clusters=root_clusters,
        ml_result=ml_result,
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "rootService": global_root,

        "impactedServices": sorted(
            impacted_services
        ),

        "reason": reason,

        "confidence": round(
            confidence,
            2
        ),

        "rootScore": round(
            confidence,
            4
        ),

        "evidence": evidence,

        "clusters": root_clusters,

        "summary": summary,
    }


# ============================================================
# SEMANTIC CLUSTER EVIDENCE
# ============================================================

def build_cluster_evidence(
    error_logs,
    cluster_result,
):
    """
    Connect semantic clusters to services
    using the original logs.

    No cluster result means zero semantic evidence.
    """

    service_cluster_counts = defaultdict(
        Counter
    )

    service_clusters = defaultdict(
        list
    )

    if not cluster_result:

        return {
            "service_scores": {},
            "service_clusters": {},
        }

    clusters = cluster_result.get(
        "clusters",
        []
    )

    # ========================================================
    # MESSAGE → LOGS
    # ========================================================

    logs_by_message = defaultdict(
        list
    )

    for log in error_logs:

        message = str(
            log.get(
                "message",
                ""
            )
        ).strip()

        if message:

            logs_by_message[
                message
            ].append(log)

    # ========================================================
    # PROCESS CLUSTERS
    # ========================================================

    for cluster in clusters:

        messages = set(
            cluster.get(
                "messages",
                []
            )
        )

        if not messages:
            continue

        cluster_id = cluster.get(
            "clusterId"
        )

        representative = cluster.get(
            "representativeMessage"
        )

        occurrences = cluster.get(
            "occurrences",
            0
        )

        affected_services = Counter()

        for message in messages:

            for log in logs_by_message.get(
                message,
                []
            ):

                service = log.get(
                    "serviceName",
                    "unknown-service"
                )

                affected_services[
                    service
                ] += 1

        # ----------------------------------------------------
        # Associate cluster with services
        # ----------------------------------------------------

        for service, count in (
            affected_services.items()
        ):

            service_cluster_counts[
                service
            ][cluster_id] += count

            service_clusters[
                service
            ].append({

                "clusterId": cluster_id,

                "representativeMessage":
                    representative,

                "occurrences":
                    occurrences,

                "serviceOccurrences":
                    count,

                "messages":
                    list(messages),
            })

    # ========================================================
    # NORMALIZE SERVICE SCORES
    # ========================================================

    raw_scores = {}

    for service, cluster_counts in (
        service_cluster_counts.items()
    ):

        raw_scores[
            service
        ] = sum(
            cluster_counts.values()
        )

    max_score = max(
        raw_scores.values(),
        default=1
    )

    service_scores = {
        service: count / max_score
        for service, count
        in raw_scores.items()
    }

    return {
        "service_scores": service_scores,
        "service_clusters": dict(
            service_clusters
        ),
    }


# ============================================================
# PROPAGATION SCORE
# ============================================================

def calculate_propagation_score(
    service,
    impacted_by_root,
    total_traces,
):
    """
    Measure how strongly this service is followed
    by downstream service failures.
    """

    if total_traces <= 0:
        return 0.0

    downstream_count = sum(
        impacted_by_root[
            service
        ].values()
    )

    if downstream_count <= 0:
        return 0.0

    return min(
        downstream_count / total_traces,
        1.0
    )


# ============================================================
# ISOLATION FOREST CONTEXT
# ============================================================

def calculate_ml_context(
    ml_result
):
    """
    Isolation Forest is supporting evidence only.

    It tells RCA that the window is anomalous.
    It does NOT identify which service caused it.
    """

    if not ml_result:
        return 0.0

    if ml_result.get(
        "anomaly"
    ) is True:

        return 1.0

    return 0.0


# ============================================================
# ROOT REASON
# ============================================================

def determine_root_reason(
    error_logs,
    root_service,
    cluster_evidence,
):
    """
    Prefer semantic cluster evidence.

    Fall back to the most common error message
    from the root service.
    """

    root_clusters = cluster_evidence[
        "service_clusters"
    ].get(
        root_service,
        []
    )

    if root_clusters:

        root_clusters.sort(
            key=lambda cluster:
                cluster.get(
                    "serviceOccurrences",
                    0
                ),
            reverse=True
        )

        representative = (
            root_clusters[0].get(
                "representativeMessage"
            )
        )

        if representative:
            return representative

    root_messages = [
        log.get(
            "message",
            ""
        )
        for log in error_logs
        if log.get(
            "serviceName"
        ) == root_service
    ]

    if not root_messages:
        return "Unknown error"

    return Counter(
        root_messages
    ).most_common(1)[0][0]


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(
    root,
    impacted,
    reason,
    confidence,
    root_clusters,
    ml_result,
):
    impacted_text = (
        ", ".join(
            sorted(impacted)
        )
        if impacted
        else "no downstream services"
    )

    cluster_text = ""

    if root_clusters:

        cluster_text = (
            " The dominant semantic error pattern "
            f"was '{root_clusters[0].get('representativeMessage')}'."
        )

    ml_text = ""

    if (
        ml_result
        and ml_result.get("anomaly") is True
    ):

        ml_text = (
            " Isolation Forest also classified "
            "the analysis window as anomalous."
        )

    return (
        f"{root} is identified as the probable root cause "
        f"due to '{reason}'. "
        f"It impacted {impacted_text}."
        f"{cluster_text}"
        f"{ml_text} "
        f"RCA confidence score: "
        f"{round(confidence, 2)}."
    )