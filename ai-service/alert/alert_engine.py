import uuid
import hashlib

from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from elastic_client import (
    es,
    ALERT_INDEX,
    create_alert_index,
)


IST = ZoneInfo(
    "Asia/Kolkata"
)


# ============================================================
# CONFIGURATION
# ============================================================

# A NEW alert that receives no further detections for this
# amount of time is automatically resolved.
AUTO_RESOLVE_MINUTES = 5


ACTIVE_STATUSES = [
    "NEW",
    "ACKNOWLEDGED",
]


# ============================================================
# INCIDENT FAMILY
# ============================================================

def determine_incident_family(
    anomalies
):
    """
    Convert the current anomaly set into a stable incident
    family.

    RCA/root service is NEVER part of incident identity.

    Example:

        errorRate + rare + spike
        errorRate + rare

    both resolve to:

        errorRate

    Therefore changing RCA results do not create a new alert.
    """

    if not anomalies:

        return "anomaly_detected"


    priority = [

        "trafficDrop",

        "critical",

        "errorRate",

        "spike",

        "rare",

    ]


    for anomaly_type in priority:

        if anomaly_type in anomalies:

            return anomaly_type


    return sorted(
        anomalies.keys()
    )[0]


# ============================================================
# DEDUPLICATION KEY
# ============================================================

def generate_dedup_key(
    anomalies
):
    """
    Stable incident identity.

    NEVER depends on:

        - RCA reason
        - root service
        - confidence
        - ML result
        - cluster result
        - anomaly values
    """

    return determine_incident_family(
        anomalies
    )


def generate_signature(
    dedup_key
):
    """
    Hash the stable deduplication key.
    """

    return hashlib.sha256(
        dedup_key.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# SEVERITY
# ============================================================

SEVERITY_RANK = {

    "LOW": 1,

    "MEDIUM": 2,

    "HIGH": 3,

    "CRITICAL": 4,

}


def classify_severity(
    anomalies
):

    if "trafficDrop" in anomalies:

        return "CRITICAL"


    if "critical" in anomalies:

        return "HIGH"


    if "errorRate" in anomalies:

        return "HIGH"


    if "spike" in anomalies:

        return "MEDIUM"


    if "rare" in anomalies:

        return "LOW"


    return "LOW"


def max_severity(
    current,
    new
):
    """
    Never downgrade an existing incident's severity.
    """

    if not current:

        return new


    if not new:

        return current


    if (
        SEVERITY_RANK.get(
            new,
            1
        )
        >
        SEVERITY_RANK.get(
            current,
            1
        )
    ):

        return new


    return current


# ============================================================
# RCA EXTRACTION
# ============================================================

def extract_rca_fields(
    rca
):

    root_service = (
        "unknown-service"
    )

    impacted_services = []

    confidence = 0.0


    if isinstance(
        rca,
        dict
    ):

        root_service = rca.get(
            "rootService",
            "unknown-service"
        )

        impacted_services = rca.get(
            "impactedServices",
            []
        )

        confidence = rca.get(
            "confidence",
            0.0
        )


    return (
        root_service,
        impacted_services,
        confidence,
    )


# ============================================================
# FIND ACTIVE INCIDENT
# ============================================================

def find_active_alert(
    dedup_key
):

    create_alert_index()


    query = {

        "bool": {

            "must": [

                {
                    "term": {
                        "dedupKey":
                            dedup_key
                    }
                },

                {
                    "terms": {
                        "status":
                            ACTIVE_STATUSES
                    }
                },

            ]

        }

    }


    response = es.search(

        index=
            ALERT_INDEX,

        query=
            query,

        size=
            1,

        sort=[

            {
                "lastUpdatedAt": {
                    "order":
                        "desc"
                }
            }

        ],

    )


    hits = response[
        "hits"
    ][
        "hits"
    ]


    if not hits:

        return None


    return hits[0]


# ============================================================
# FIND MOST RECENT ACTIVE INCIDENT
# ============================================================

def find_recent_active_alert():

    create_alert_index()


    cutoff = (

        datetime.now(
            IST
        )

        - timedelta(
            minutes=
                AUTO_RESOLVE_MINUTES
        )

    ).isoformat()


    query = {

        "bool": {

            "must": [

                {
                    "terms": {
                        "status":
                            ACTIVE_STATUSES
                    }
                },

                {
                    "range": {

                        "lastUpdatedAt": {

                            "gte":
                                cutoff

                        }

                    }

                },

            ]

        }

    }


    response = es.search(

        index=
            ALERT_INDEX,

        query=
            query,

        size=
            1,

        sort=[

            {
                "lastUpdatedAt": {

                    "order":
                        "desc"

                }

            }

        ],

    )


    hits = response[
        "hits"
    ][
        "hits"
    ]


    if not hits:

        return None


    return hits[0]


# ============================================================
# AUTO RESOLVE STALE NEW ALERTS
# ============================================================

def auto_resolve_stale_alerts():

    create_alert_index()


    cutoff = (

        datetime.now(
            IST
        )

        - timedelta(
            minutes=
                AUTO_RESOLVE_MINUTES
        )

    ).isoformat()


    query = {

        "bool": {

            "must": [

                {
                    "term": {
                        "status":
                            "NEW"
                    }
                },

                {
                    "range": {

                        "lastUpdatedAt": {

                            "lt":
                                cutoff

                        }

                    }

                },

            ]

        }

    }


    response = es.search(

        index=
            ALERT_INDEX,

        query=
            query,

        size=
            100,

    )


    resolved_count = 0


    for hit in response[
        "hits"
    ][
        "hits"
    ]:

        alert_id = hit[
            "_id"
        ]


        now = datetime.now(
            IST
        ).isoformat()


        es.update(

            index=
                ALERT_INDEX,

            id=
                alert_id,

            doc={

                "status":
                    "RESOLVED",

                "resolvedAt":
                    now,

                "lastUpdatedAt":
                    now,

            },

        )


        resolved_count += 1


        print(

            "[ALERT ENGINE] "

            f"Auto-resolved stale alert: "
            f"{alert_id}"

        )


    return resolved_count


# ============================================================
# CREATE OR UPDATE RULE INCIDENT
# ============================================================

def create_alert(

    anomalies,

    rca=None,

    source="RULE",

):

    if not anomalies:

        return None


    create_alert_index()


    # --------------------------------------------------------
    # Resolve stale NEW incidents first.
    # --------------------------------------------------------

    auto_resolve_stale_alerts()


    # --------------------------------------------------------
    # Stable incident identity
    # --------------------------------------------------------

    incident_family = (
        determine_incident_family(
            anomalies
        )
    )


    dedup_key = (
        incident_family
    )


    signature = (
        generate_signature(
            dedup_key
        )
    )


    # --------------------------------------------------------
    # Stage 1 RCA
    # --------------------------------------------------------

    (
        root_service,
        impacted_services,
        confidence,
    ) = extract_rca_fields(
        rca
    )


    severity = (
        classify_severity(
            anomalies
        )
    )


    now = datetime.now(
        IST
    ).isoformat()


    # --------------------------------------------------------
    # Find existing active incident
    # --------------------------------------------------------

    existing = (
        find_active_alert(
            dedup_key
        )
    )


    # ========================================================
    # EXISTING INCIDENT
    # ========================================================

    if existing:

        existing_id = (
            existing["_id"]
        )


        existing_doc = (
            existing["_source"]
        )


        # ----------------------------------------------------
        # Existing anomaly information
        # ----------------------------------------------------

        existing_anomalies = (
            existing_doc.get(
                "anomalies",
                {}
            )
        )


        merged_anomalies = {

            **existing_anomalies,

            **anomalies,

        }


        # ----------------------------------------------------
        # Sources
        # ----------------------------------------------------

        existing_sources = list(

            existing_doc.get(
                "sources",
                []
            )

        )


        if source not in existing_sources:

            existing_sources.append(
                source
            )


        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        current_severity = (
            existing_doc.get(
                "severity",
                "LOW"
            )
        )


        final_severity = (
            max_severity(

                current_severity,

                severity

            )
        )


        # ----------------------------------------------------
        # Impacted services
        # ----------------------------------------------------

        existing_impacted = set(

            existing_doc.get(
                "impactedServices",
                []
            )

        )


        existing_impacted.update(
            impacted_services
        )


        # ----------------------------------------------------
        # Occurrence count
        # ----------------------------------------------------

        occurrence_count = (

            existing_doc.get(
                "occurrenceCount",
                0
            )

            + 1

        )


        # ----------------------------------------------------
        # Current RCA stage
        # ----------------------------------------------------

        current_rca_stage = (
            existing_doc.get(
                "rcaStage",
                1
            )
        )


        # ----------------------------------------------------
        # Stage 2 existence
        #
        # Stage 2 is considered present only when the alert
        # actually contains Stage 2 RCA.
        # ----------------------------------------------------

        stage2_exists = (

            current_rca_stage >= 2

            and isinstance(
                existing_doc.get(
                    "stage2Rca"
                ),
                dict
            )

        )


        # ----------------------------------------------------
        # Preserve / update Stage 1 RCA
        # ----------------------------------------------------

        rule_rca = (
            existing_doc.get(
                "ruleRca"
            )
        )


        if isinstance(
            rca,
            dict
        ):

            rule_rca = rca


        # ----------------------------------------------------
        # Build base update
        # ----------------------------------------------------

        update_fields = {

            "anomalies":
                merged_anomalies,

            "severity":
                final_severity,

            "impactedServices":
                list(
                    existing_impacted
                ),

            "sources":
                existing_sources,

            "lastUpdatedAt":
                now,

            "occurrenceCount":
                occurrence_count,

            "status":
                existing_doc.get(
                    "status",
                    "NEW"
                ),

            "ruleRca":
                rule_rca,

        }


        # ====================================================
        # NO STAGE 2 YET
        #
        # Stage 1 remains authoritative.
        # ====================================================

        if not stage2_exists:

            update_fields[
                "rootService"
            ] = root_service


            update_fields[
                "confidence"
            ] = confidence


            update_fields[
                "rca"
            ] = rca


            update_fields[
                "rcaStage"
            ] = 1


            update_fields[
                "rcaSource"
            ] = "RULE"


        # ====================================================
        # STAGE 2 ALREADY EXISTS
        #
        # NEVER overwrite Stage 2 with a later Stage 1 run.
        # ====================================================

        else:

            print(

                "[ALERT ENGINE] "

                "Stage 2 RCA already exists. "

                "Preserving authoritative RCA."

            )


        # ----------------------------------------------------
        # Update SAME Elasticsearch document
        # ----------------------------------------------------

        es.update(

            index=
                ALERT_INDEX,

            id=
                existing_id,

            doc=
                update_fields,

            refresh=
                "wait_for",

        )


        print(

            "[ALERT ENGINE] "

            f"Existing incident updated | "

            f"id={existing_id} | "

            f"type={incident_family} | "

            f"occurrences={occurrence_count} | "

            f"source={source} | "

            f"rcaStage="
            f"{2 if stage2_exists else 1}"

        )


        return {

            **existing_doc,

            **update_fields,

            "alertId":
                existing_id,

        }


    # ========================================================
    # NEW INCIDENT
    #
    # STAGE 1
    # ========================================================

    alert_id = str(
        uuid.uuid4()
    )


    alert = {

        # ----------------------------------------------------
        # INCIDENT ID
        # ----------------------------------------------------

        "alertId":
            alert_id,


        # ----------------------------------------------------
        # INCIDENT IDENTITY
        # ----------------------------------------------------

        "signature":
            signature,


        "dedupKey":
            dedup_key,


        "incidentFamily":
            incident_family,


        "anomalyType":
            incident_family,


        # ----------------------------------------------------
        # ALERT
        # ----------------------------------------------------

        "severity":
            severity,


        "status":
            "NEW",


        "sources":
            [source],


        "anomalies":
            anomalies,


        # ----------------------------------------------------
        # STAGE 1 RCA
        # ----------------------------------------------------

        "ruleRca":
            rca,


        # ----------------------------------------------------
        # CURRENT AUTHORITATIVE RCA
        #
        # Initially Stage 1.
        # Stage 2 replaces this later.
        # ----------------------------------------------------

        "rca":
            rca,


        "rcaStage":
            1,


        "rcaSource":
            "RULE",


        # ----------------------------------------------------
        # CURRENT RCA SUMMARY
        # ----------------------------------------------------

        "rootService":
            root_service,


        "impactedServices":
            impacted_services,


        "confidence":
            confidence,


        # ----------------------------------------------------
        # TIMESTAMPS
        # ----------------------------------------------------

        "firstDetectedAt":
            now,


        "lastUpdatedAt":
            now,


        "resolvedAt":
            None,


        # ----------------------------------------------------
        # COUNTERS
        # ----------------------------------------------------

        "occurrenceCount":
            1,


        "mlEnrichmentCount":
            0,


        # ----------------------------------------------------
        # STAGE 2 / ML
        #
        # These are intentionally empty until the exact
        # 5-minute ML window enriches this incident.
        # ----------------------------------------------------

        "stage2Rca":
            None,


        "mlRca":
            None,


        "mlEvidence":
            None,


        "mlAnomaly":
            None,


        "mlScore":
            None,


        "mlWindowId":
            None,


        "mlWindowStart":
            None,


        "mlWindowEnd":
            None,

    }


    # --------------------------------------------------------
    # CREATE INCIDENT
    # --------------------------------------------------------

    es.index(

        index=
            ALERT_INDEX,

        id=
            alert_id,

        document=
            alert,

        refresh=
            "wait_for",

    )


    print(

        "[ALERT ENGINE] "

        f"NEW INCIDENT CREATED | "

        f"type={incident_family} | "

        f"severity={severity} | "

        f"root={root_service} | "

        f"rcaStage=1 | "

        f"alertId={alert_id}"

    )


    return alert


# ============================================================
# STAGE 2 — EXACT INCIDENT ML ENRICHMENT
# ============================================================

def enrich_active_alert_with_ml(

    alert_id,

    window_id=None,

    window_start=None,

    window_end=None,

    cluster_result=None,

    ml_result=None,

    rca_result=None,

):
    """
    STAGE 2 RCA.

    The exact alertId MUST be supplied by the scheduler.

    Stage 2 combines:

        1. Stage 1 rule / trace evidence
        2. Isolation Forest context
        3. Semantic clustering

    Stage 1 remains preserved as:

        ruleRca

    Stage 2 becomes authoritative as:

        rca
        stage2Rca
        mlRca

    Stage 2 summary fields:

        rootService
        impactedServices
        confidence

    ML window identity:

        mlWindowId
        mlWindowStart
        mlWindowEnd

    IMPORTANT:

    This function NEVER searches for the latest active alert.

    It updates exactly:

        /alerts/{alert_id}

    Therefore multiple incidents can be enriched safely.
    """


    # ========================================================
    # VALIDATE ALERT ID
    # ========================================================

    if not alert_id:

        print(

            "[ALERT ENGINE] "

            "Stage 2 enrichment rejected: "

            "alert_id is required."

        )

        return None


    # ========================================================
    # VALIDATE ML DATA
    # ========================================================

    if (

        cluster_result is None

        and ml_result is None

        and rca_result is None

    ):

        print(

            "[ALERT ENGINE] "

            f"Stage 2 skipped: no ML/RCA data | "

            f"id={alert_id}"

        )

        return None


    create_alert_index()


    # ========================================================
    # GET EXACT INCIDENT
    # ========================================================

    try:

        existing = es.get(

            index=
                ALERT_INDEX,

            id=
                alert_id,

        )

    except Exception as e:

        print(

            "[ALERT ENGINE] "

            f"Stage 2 alert lookup failed | "

            f"id={alert_id} | "

            f"error={e}"

        )

        return None


    existing_doc = existing.get(

        "_source",

        {}

    )


    # ========================================================
    # VERIFY CANONICAL ALERT ID
    # ========================================================

    stored_alert_id = (
        existing_doc.get(
            "alertId"
        )
    )


    if (

        stored_alert_id

        and str(
            stored_alert_id
        ) != str(
            alert_id
        )

    ):

        print(

            "[ALERT ENGINE] "

            "CRITICAL IDENTITY MISMATCH | "

            f"requested={alert_id} | "

            f"stored={stored_alert_id}"

        )

        return None


    # ========================================================
    # ONLY ACTIVE INCIDENTS
    # ========================================================

    current_status = (
        existing_doc.get(
            "status",
            "NEW"
        )
    )


    if current_status not in ACTIVE_STATUSES:

        print(

            "[ALERT ENGINE] "

            f"Stage 2 skipped because incident "

            f"is not active | "

            f"id={alert_id} | "

            f"status={current_status}"

        )

        return None


    # ========================================================
    # PREVENT DUPLICATE 5-MINUTE ENRICHMENT
    #
    # The same completed ML window must not be applied twice
    # to the same incident.
    # ========================================================

    previous_window_id = (
        existing_doc.get(
            "mlWindowId"
        )
    )


    if (

        window_id

        and previous_window_id

        and str(
            previous_window_id
        ) == str(
            window_id
        )

    ):

        print(

            "[ALERT ENGINE] "

            "Stage 2 already applied for this exact ML window | "

            f"id={alert_id} | "

            f"window={window_id}"

        )

        return {

            **existing_doc,

            "alertId":
                alert_id,

        }


    # ========================================================
    # TIME
    # ========================================================

    now = datetime.now(
        IST
    ).isoformat()


    # ========================================================
    # SOURCES
    # ========================================================

    sources = list(

        existing_doc.get(
            "sources",
            []
        )

    )


    if "ML" not in sources:

        sources.append(
            "ML"
        )


    # ========================================================
    # ML ENRICHMENT COUNT
    # ========================================================

    ml_count = (

        existing_doc.get(
            "mlEnrichmentCount",
            0
        )

        + 1

    )


    # ========================================================
    # BASE STAGE 2 UPDATE
    # ========================================================

    update_fields = {

        "sources":
            sources,


        "mlEnrichmentCount":
            ml_count,


        "lastUpdatedAt":
            now,


        # ----------------------------------------------------
        # EXACT ML WINDOW
        # ----------------------------------------------------

        "mlWindowId":
            window_id,


        "mlWindowStart":
            window_start,


        "mlWindowEnd":
            window_end,


        # ----------------------------------------------------
        # COMPLETE ML EVIDENCE
        # ----------------------------------------------------

        "mlEvidence": {

            "windowId":
                window_id,

            "windowStart":
                window_start,

            "windowEnd":
                window_end,

            "clusterResult":
                cluster_result,

            "isolationForest":
                ml_result,

            "rca":
                rca_result,

        },

    }


    # ========================================================
    # ISOLATION FOREST
    # ========================================================

    if isinstance(

        ml_result,

        dict

    ):

        update_fields[
            "mlAnomaly"
        ] = ml_result.get(

            "anomaly",

            False

        )


        update_fields[
            "mlScore"
        ] = ml_result.get(

            "score"

        )


    # ========================================================
    # STAGE 2 RCA
    # ========================================================

    if isinstance(

        rca_result,

        dict

    ):

        # ----------------------------------------------------
        # PRESERVE STAGE 1 PERMANENTLY
        # ----------------------------------------------------

        existing_rule_rca = (
            existing_doc.get(
                "ruleRca"
            )
        )


        if not isinstance(

            existing_rule_rca,

            dict

        ):

            existing_rule_rca = (
                existing_doc.get(
                    "rca"
                )
            )


        update_fields[
            "ruleRca"
        ] = existing_rule_rca


        # ----------------------------------------------------
        # STORE STAGE 2 RCA
        # ----------------------------------------------------

        update_fields[
            "stage2Rca"
        ] = rca_result


        update_fields[
            "mlRca"
        ] = rca_result


        # ----------------------------------------------------
        # STAGE 2 BECOMES AUTHORITATIVE
        # ----------------------------------------------------

        update_fields[
            "rca"
        ] = rca_result


        update_fields[
            "rcaStage"
        ] = 2


        update_fields[
            "rcaSource"
        ] = (
            "RULE+ISOLATION_FOREST+CLUSTERING"
        )


        # ----------------------------------------------------
        # ROOT SERVICE
        # ----------------------------------------------------

        update_fields[
            "rootService"
        ] = rca_result.get(

            "rootService",

            existing_doc.get(

                "rootService",

                "unknown-service"

            )

        )


        # ----------------------------------------------------
        # IMPACTED SERVICES
        # ----------------------------------------------------

        update_fields[
            "impactedServices"
        ] = rca_result.get(

            "impactedServices",

            existing_doc.get(

                "impactedServices",

                []

            )

        )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        update_fields[
            "confidence"
        ] = rca_result.get(

            "confidence",

            existing_doc.get(

                "confidence",

                0.0

            )

        )


    # ========================================================
    # UPDATE EXACT SAME INCIDENT
    # ========================================================

    try:

        result = es.update(

            index=
                ALERT_INDEX,

            id=
                alert_id,

            doc=
                update_fields,

            refresh=
                "wait_for",

        )

    except Exception as e:

        print(

            "[ALERT ENGINE] "

            f"Stage 2 update FAILED | "

            f"id={alert_id} | "

            f"window={window_id} | "

            f"error={e}"

        )

        return None


    # ========================================================
    # FINAL STAGE
    # ========================================================

    final_rca_stage = (

        2

        if isinstance(
            rca_result,
            dict
        )

        else existing_doc.get(
            "rcaStage",
            1
        )

    )


    final_root_service = (
        update_fields.get(

            "rootService",

            existing_doc.get(
                "rootService"
            )

        )
    )


    # ========================================================
    # LOG
    # ========================================================

    print(

        "[ALERT ENGINE] "

        "=================================================="

    )


    print(

        "[ALERT ENGINE] "

        "Stage 2 updated SAME incident"

    )


    print(

        "[ALERT ENGINE] "

        f"alertId={alert_id}"

    )


    print(

        "[ALERT ENGINE] "

        f"windowId={window_id}"

    )


    print(

        "[ALERT ENGINE] "

        f"windowStart={window_start}"

    )


    print(

        "[ALERT ENGINE] "

        f"windowEnd={window_end}"

    )


    print(

        "[ALERT ENGINE] "

        f"mlEnrichmentCount={ml_count}"

    )


    print(

        "[ALERT ENGINE] "

        f"rcaStage={final_rca_stage}"

    )


    print(

        "[ALERT ENGINE] "

        f"rootService={final_root_service}"

    )


    print(

        "[ALERT ENGINE] "

        "=================================================="

    )


    # ========================================================
    # RETURN UPDATED INCIDENT
    # ========================================================

    return {

        **existing_doc,

        **update_fields,

        "alertId":
            alert_id,

    }