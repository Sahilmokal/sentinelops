import requests
import random
import time
import uuid
import argparse

from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor


# ============================================================
# TRACE FORGE
# HARSH SYSTEM TESTER
# ============================================================

# ============================================================
# CONFIGURATION
# ============================================================

INGESTION_URL = "http://100.57.251.173:8080/api/logs"

IST = ZoneInfo("Asia/Kolkata")

SERVICES = [
    "auth-service",
    "order-service",
    "payment-service",
    "inventory-service",
]


# ============================================================
# NORMAL LOGS
# ============================================================

NORMAL_MESSAGES = [
    "User login successful",
    "Order created successfully",
    "Payment processed successfully",
    "Cache hit for user profile",
    "Inventory lookup completed",
    "User profile loaded successfully",
    "Order retrieved successfully",
    "Payment status updated",
]


# ============================================================
# GENERIC ERRORS
# ============================================================

ERROR_MESSAGES = [
    "Database connection timeout",
    "Payment gateway timeout",
    "Token validation failed",
    "Null pointer exception occurred",
    "Request processing failed",
    "Service dependency unavailable",
]


# ============================================================
# DATABASE SEMANTIC GROUP
# ============================================================

DATABASE_MESSAGES = [
    "Database connection failed",
    "Unable to connect to database",
    "Database connection refused",
    "Could not establish database connection",
    "Database server is unreachable",
    "Failed to connect to PostgreSQL database",
]


# ============================================================
# PAYMENT SEMANTIC GROUP
# ============================================================

PAYMENT_MESSAGES = [
    "Payment processing failed",
    "Unable to process payment",
    "Payment transaction was rejected",
    "Payment request could not be completed",
    "Transaction processing failed",
    "Payment gateway rejected the transaction",
]


# ============================================================
# AUTH SEMANTIC GROUP
# ============================================================

AUTH_MESSAGES = [
    "User authentication failed",
    "Unable to authenticate user",
    "User login was rejected",
    "Authentication request failed",
    "Invalid user credentials",
    "User could not be authenticated",
]


# ============================================================
# CACHE / REDIS SEMANTIC GROUP
# ============================================================

CACHE_MESSAGES = [
    "Redis connection timeout",
    "Unable to connect to Redis",
    "Cache server connection failed",
    "Redis server is unreachable",
    "Cache connection was refused",
    "Failed to connect to cache server",
]


# ============================================================
# SEMANTIC NOISE
# ============================================================

NOISE_MESSAGES = [
    "User profile updated successfully",
    "Order notification sent",
    "Inventory synchronization completed",
    "Health check completed successfully",
    "Background cleanup task finished",
    "Configuration refreshed successfully",
    "Health check passed",
    "Metrics exported successfully",
    "Scheduled job completed",
]


# ============================================================
# CRITICAL
# ============================================================

CRITICAL_MESSAGES = [
    "CRITICAL: Memory leak detected in JVM",
    "FATAL: Service process crashed",
    "PANIC: Database corruption detected",
    "CRITICAL: Out of memory condition",
]


# ============================================================
# TIMESTAMP
# ============================================================

def current_timestamp():
    return datetime.now(IST).isoformat()


# ============================================================
# SEND ONE LOG
# ============================================================

def send_log(
    service,
    level,
    message,
    trace_id=None,
):
    """
    Send one log to the ingestion service.

    trace_id can intentionally be None for testing
    missing-trace scenarios.
    """

    payload = {
        "serviceName": service,
        "logLevel": level,
        "message": message,
        "timestamp": current_timestamp(),
        "traceId": trace_id,
        "host": "trace-forge",
    }

    try:

        response = requests.post(
            INGESTION_URL,
            json=payload,
            timeout=5,
        )

        if not response.ok:

            print(
                f"[FAILED] "
                f"HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

            return False

        return True

    except requests.RequestException as e:

        print(
            f"[HTTP ERROR] {e}"
        )

        return False


# ============================================================
# HELPER
# ============================================================

def print_progress(
    name,
    sent,
    failed,
    total=None,
):

    if total:

        print(
            f"[{name}] "
            f"{sent}/{total} sent | "
            f"failed={failed}"
        )

    else:

        print(
            f"[{name}] "
            f"sent={sent} | "
            f"failed={failed}"
        )


# ============================================================
# MODE 1
# NORMAL TRAFFIC
# ============================================================

def normal_mode(
    duration=600,
    rate=0.5,
):

    print("\n================================================")
    print("TRACE FORGE | NORMAL TRAFFIC")
    print("================================================")

    print(
        f"Duration={duration}s | "
        f"Rate={rate}/sec"
    )

    end_time = time.time() + duration

    sent = 0
    failed = 0

    interval = 1.0 / rate

    while time.time() < end_time:

        service = random.choice(
            SERVICES
        )

        success = send_log(
            service=service,
            level="INFO",
            message=random.choice(
                NORMAL_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        if success:
            sent += 1
        else:
            failed += 1

        if sent % 50 == 0:

            print_progress(
                "NORMAL",
                sent,
                failed,
            )

        time.sleep(interval)

    print_progress(
        "NORMAL COMPLETE",
        sent,
        failed,
    )


# ============================================================
# MODE 2
# ERROR SPIKE
# ============================================================

def error_spike_mode(
    duration=120,
    rate=10,
    error_ratio=0.90,
):

    print("\n================================================")
    print("TRACE FORGE | EXTREME ERROR SPIKE")
    print("================================================")

    print(
        f"Duration={duration}s | "
        f"Rate={rate}/sec | "
        f"Error ratio={error_ratio}"
    )

    end_time = time.time() + duration

    sent = 0
    failed = 0

    interval = 1.0 / rate

    while time.time() < end_time:

        trace_id = str(uuid.uuid4())

        if random.random() < error_ratio:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                ERROR_MESSAGES
            )

            level = "ERROR"

        else:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                NORMAL_MESSAGES
            )

            level = "INFO"

        success = send_log(
            service=service,
            level=level,
            message=message,
            trace_id=trace_id,
        )

        if success:
            sent += 1
        else:
            failed += 1

        if sent % 100 == 0:

            print_progress(
                "ERROR SPIKE",
                sent,
                failed,
            )

        time.sleep(interval)

    print_progress(
        "ERROR SPIKE COMPLETE",
        sent,
        failed,
    )


# ============================================================
# MODE 3
# RARE ERROR
# ============================================================

def rare_error_mode(
    duration=120,
    rate=5,
):

    print("\n================================================")
    print("TRACE FORGE | RARE ERROR")
    print("================================================")

    end_time = time.time() + duration

    sent = 0
    failed = 0

    while time.time() < end_time:

        service = random.choice(
            SERVICES
        )

        if random.random() < 0.05:

            level = "ERROR"

            message = (
                "Unexpected certificate "
                "validation failure"
            )

        else:

            level = "INFO"

            message = random.choice(
                NORMAL_MESSAGES
            )

        success = send_log(
            service=service,
            level=level,
            message=message,
            trace_id=str(uuid.uuid4()),
        )

        if success:
            sent += 1
        else:
            failed += 1

        time.sleep(
            1.0 / rate
        )

    print_progress(
        "RARE ERROR COMPLETE",
        sent,
        failed,
    )


# ============================================================
# MODE 4
# CASCADING FAILURE
# ============================================================

def cascading_failure_mode(
    duration=120,
):

    print("\n================================================")
    print("TRACE FORGE | CASCADING FAILURE / RCA TEST")
    print("================================================")

    print(
        "Same traceId will travel through:"
    )

    print(
        "auth-service"
        " -> order-service"
        " -> payment-service"
    )

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        trace_id = str(uuid.uuid4())

        # ----------------------------------------------------
        # ROOT
        # ----------------------------------------------------

        send_log(
            service="auth-service",
            level="ERROR",
            message=(
                "Database connection timeout"
            ),
            trace_id=trace_id,
        )

        time.sleep(0.2)

        # ----------------------------------------------------
        # DOWNSTREAM 1
        # ----------------------------------------------------

        send_log(
            service="order-service",
            level="ERROR",
            message=(
                "Downstream auth failure"
            ),
            trace_id=trace_id,
        )

        time.sleep(0.2)

        # ----------------------------------------------------
        # DOWNSTREAM 2
        # ----------------------------------------------------

        send_log(
            service="payment-service",
            level="ERROR",
            message=(
                "Auth dependency failed"
            ),
            trace_id=trace_id,
        )

        count += 1

        print(
            f"[CASCADE] "
            f"Trace #{count} | "
            f"traceId={trace_id}"
        )

        time.sleep(1)

    print(
        "\n[Cascade] Test completed."
    )


# ============================================================
# MODE 5
# TRAFFIC DROP
# ============================================================

def traffic_drop_mode(
    baseline_duration=30,
):

    print("\n================================================")
    print("TRACE FORGE | TRAFFIC DROP")
    print("================================================")

    print(
        "Generating baseline traffic..."
    )

    end_time = (
        time.time()
        + baseline_duration
    )

    count = 0

    while time.time() < end_time:

        send_log(
            service=random.choice(
                SERVICES
            ),
            level="INFO",
            message=random.choice(
                NORMAL_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        count += 1

        time.sleep(0.1)

    print(
        f"Baseline generated: {count} logs"
    )

    print(
        "\nSTOPPING TRAFFIC."
    )

    print(
        "Leave generator stopped for "
        "at least 60 seconds."
    )

    print(
        "This allows the traffic-drop "
        "detector to react."
    )


# ============================================================
# MODE 6
# CRITICAL ERRORS
# ============================================================

def critical_mode(
    duration=120,
    rate=5,
):

    print("\n================================================")
    print("TRACE FORGE | CRITICAL ERROR STORM")
    print("================================================")

    end_time = time.time() + duration

    sent = 0

    while time.time() < end_time:

        success = send_log(
            service=random.choice(
                SERVICES
            ),
            level="ERROR",
            message=random.choice(
                CRITICAL_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        if success:
            sent += 1

        if sent % 25 == 0:

            print(
                f"[CRITICAL] "
                f"Sent {sent}"
            )

        time.sleep(
            1.0 / rate
        )

    print(
        f"[CRITICAL] Complete. "
        f"Sent={sent}"
    )


# ============================================================
# MODE 7
# SEMANTIC CLUSTERING
# ============================================================

def semantic_clustering_mode(
    duration=120,
    rate=10,
    noise_ratio=0.10,
):

    print("\n================================================")
    print("TRACE FORGE | SEMANTIC CLUSTERING")
    print("================================================")

    print(
        "Expected semantic groups:"
    )

    print(
        "  DATABASE"
    )

    print(
        "  PAYMENT"
    )

    print(
        "  AUTH"
    )

    print(
        "  CACHE / REDIS"
    )

    print(
        f"Noise ratio={noise_ratio}"
    )

    cluster_groups = [

        (
            "DATABASE",
            DATABASE_MESSAGES,
            "order-service",
        ),

        (
            "PAYMENT",
            PAYMENT_MESSAGES,
            "payment-service",
        ),

        (
            "AUTH",
            AUTH_MESSAGES,
            "auth-service",
        ),

        (
            "CACHE",
            CACHE_MESSAGES,
            "inventory-service",
        ),

    ]

    end_time = time.time() + duration

    sent = 0
    failed = 0

    interval = 1.0 / rate

    while time.time() < end_time:

        trace_id = str(uuid.uuid4())

        if random.random() < noise_ratio:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                NOISE_MESSAGES
            )

            level = "INFO"

            group = "NOISE"

        else:

            group, messages, service = random.choice(
                cluster_groups
            )

            message = random.choice(
                messages
            )

            level = "ERROR"

        success = send_log(
            service=service,
            level=level,
            message=message,
            trace_id=trace_id,
        )

        if success:
            sent += 1
        else:
            failed += 1

        if sent % 100 == 0:

            print(
                f"[CLUSTERING] "
                f"group={group} "
                f"sent={sent}"
            )

        time.sleep(interval)

    print_progress(
        "CLUSTERING COMPLETE",
        sent,
        failed,
    )


# ============================================================
# MODE 8
# DATABASE OUTAGE
# ============================================================

def database_outage_mode(
    duration=120,
    rate=10,
):

    print("\n================================================")
    print("TRACE FORGE | DATABASE OUTAGE")
    print("================================================")

    end_time = time.time() + duration

    messages = DATABASE_MESSAGES

    count = 0

    while time.time() < end_time:

        service = random.choice([
            "order-service",
            "inventory-service",
        ])

        send_log(
            service=service,
            level="ERROR",
            message=random.choice(messages),
            trace_id=str(uuid.uuid4()),
        )

        count += 1

        if count % 100 == 0:

            print(
                f"[DATABASE] "
                f"Sent {count}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 9
# REDIS / CACHE OUTAGE
# ============================================================

def redis_outage_mode(
    duration=120,
    rate=10,
):

    print("\n================================================")
    print("TRACE FORGE | REDIS / CACHE OUTAGE")
    print("================================================")

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        send_log(
            service="inventory-service",
            level="ERROR",
            message=random.choice(
                CACHE_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        count += 1

        if count % 100 == 0:

            print(
                f"[REDIS] "
                f"Sent {count}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 10
# AUTHENTICATION OUTAGE
# ============================================================

def authentication_outage_mode(
    duration=120,
    rate=10,
):

    print("\n================================================")
    print("TRACE FORGE | AUTHENTICATION OUTAGE")
    print("================================================")

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        send_log(
            service="auth-service",
            level="ERROR",
            message=random.choice(
                AUTH_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        count += 1

        if count % 100 == 0:

            print(
                f"[AUTH] "
                f"Sent {count}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 11
# PAYMENT OUTAGE
# ============================================================

def payment_outage_mode(
    duration=120,
    rate=10,
):

    print("\n================================================")
    print("TRACE FORGE | PAYMENT OUTAGE")
    print("================================================")

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        send_log(
            service="payment-service",
            level="ERROR",
            message=random.choice(
                PAYMENT_MESSAGES
            ),
            trace_id=str(uuid.uuid4()),
        )

        count += 1

        if count % 100 == 0:

            print(
                f"[PAYMENT] "
                f"Sent {count}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 12
# MIXED SIMULTANEOUS FAILURE
# ============================================================

def mixed_failure_mode(
    duration=120,
    rate=20,
):

    print("\n================================================")
    print("TRACE FORGE | MIXED SIMULTANEOUS FAILURE")
    print("================================================")

    print(
        "Multiple independent failure domains "
        "will occur simultaneously."
    )

    end_time = time.time() + duration

    groups = [

        (
            "DATABASE",
            DATABASE_MESSAGES,
            "order-service",
        ),

        (
            "REDIS",
            CACHE_MESSAGES,
            "inventory-service",
        ),

        (
            "AUTH",
            AUTH_MESSAGES,
            "auth-service",
        ),

        (
            "PAYMENT",
            PAYMENT_MESSAGES,
            "payment-service",
        ),

    ]

    sent = 0

    while time.time() < end_time:

        group, messages, service = random.choice(
            groups
        )

        send_log(
            service=service,
            level="ERROR",
            message=random.choice(
                messages
            ),
            trace_id=str(uuid.uuid4()),
        )

        sent += 1

        if sent % 100 == 0:

            print(
                f"[MIXED] "
                f"Sent {sent}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 13
# SLOW DEGRADATION
# ============================================================

def slow_degradation_mode(
    duration=180,
    start_rate=2,
    end_rate=20,
):

    print("\n================================================")
    print("TRACE FORGE | SLOW ERROR-RATE DEGRADATION")
    print("================================================")

    print(
        f"Rate grows from "
        f"{start_rate}/sec "
        f"to {end_rate}/sec"
    )

    start_time = time.time()

    sent = 0

    while True:

        elapsed = (
            time.time()
            - start_time
        )

        if elapsed >= duration:
            break

        progress = elapsed / duration

        rate = (
            start_rate
            + (
                end_rate
                - start_rate
            ) * progress
        )

        error_probability = (
            0.05
            + (
                0.85
                * progress
            )
        )

        trace_id = str(uuid.uuid4())

        if random.random() < error_probability:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                ERROR_MESSAGES
            )

            level = "ERROR"

        else:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                NORMAL_MESSAGES
            )

            level = "INFO"

        send_log(
            service=service,
            level=level,
            message=message,
            trace_id=trace_id,
        )

        sent += 1

        if sent % 100 == 0:

            print(
                f"[DEGRADATION] "
                f"rate={rate:.1f}/s "
                f"errorProbability="
                f"{error_probability:.2f} "
                f"sent={sent}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 14
# FLAPPING INCIDENT
# ============================================================

def flapping_incident_mode(
    cycles=6,
):

    print("\n================================================")
    print("TRACE FORGE | FLAPPING INCIDENT")
    print("================================================")

    print(
        "Failure starts, recovers, "
        "then returns repeatedly."
    )

    for cycle in range(1, cycles + 1):

        print(
            f"\n[FLAP {cycle}/{cycles}] "
            f"FAILURE"
        )

        failure_end = (
            time.time() + 15
        )

        while time.time() < failure_end:

            send_log(
                service="order-service",
                level="ERROR",
                message=random.choice(
                    DATABASE_MESSAGES
                ),
                trace_id=str(uuid.uuid4()),
            )

            time.sleep(0.1)

        print(
            f"[FLAP {cycle}/{cycles}] "
            f"RECOVERY"
        )

        recovery_end = (
            time.time() + 15
        )

        while time.time() < recovery_end:

            send_log(
                service="order-service",
                level="INFO",
                message=random.choice(
                    NORMAL_MESSAGES
                ),
                trace_id=str(uuid.uuid4()),
            )

            time.sleep(0.2)

    print(
        "\n[FLAPPING] Complete."
    )


# ============================================================
# MODE 15
# MISSING TRACE IDS
# ============================================================

def missing_trace_mode(
    duration=120,
    rate=10,
):

    print("\n================================================")
    print("TRACE FORGE | MISSING TRACE IDS")
    print("================================================")

    print(
        "Tests RCA behavior when traceId is missing."
    )

    end_time = time.time() + duration

    sent = 0

    while time.time() < end_time:

        service = random.choice(
            SERVICES
        )

        message = random.choice(
            DATABASE_MESSAGES
        )

        send_log(
            service=service,
            level="ERROR",
            message=message,
            trace_id=None,
        )

        sent += 1

        if sent % 100 == 0:

            print(
                f"[NO TRACE] "
                f"Sent {sent}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 16
# BROKEN TRACE CHAIN
# ============================================================

def broken_trace_chain_mode(
    duration=120,
):

    print("\n================================================")
    print("TRACE FORGE | BROKEN TRACE CHAIN")
    print("================================================")

    print(
        "Some downstream events intentionally "
        "use different trace IDs."
    )

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        root_trace = str(uuid.uuid4())

        send_log(
            service="auth-service",
            level="ERROR",
            message=(
                "Database connection timeout"
            ),
            trace_id=root_trace,
        )

        time.sleep(0.2)

        # Wrong trace ID
        send_log(
            service="order-service",
            level="ERROR",
            message=(
                "Downstream auth failure"
            ),
            trace_id=str(uuid.uuid4()),
        )

        time.sleep(0.2)

        # Missing trace ID
        send_log(
            service="payment-service",
            level="ERROR",
            message=(
                "Auth dependency failed"
            ),
            trace_id=None,
        )

        count += 1

        print(
            f"[BROKEN TRACE] "
            f"Test #{count}"
        )

        time.sleep(1)


# ============================================================
# MODE 17
# HIGH NOISE SEMANTIC TEST
# ============================================================

def noisy_semantic_mode(
    duration=120,
    rate=20,
    noise_ratio=0.50,
):

    print("\n================================================")
    print("TRACE FORGE | HIGH-NOISE SEMANTIC TEST")
    print("================================================")

    print(
        f"Noise ratio={noise_ratio}"
    )

    cluster_groups = [

        (
            "DATABASE",
            DATABASE_MESSAGES,
            "order-service",
        ),

        (
            "PAYMENT",
            PAYMENT_MESSAGES,
            "payment-service",
        ),

        (
            "AUTH",
            AUTH_MESSAGES,
            "auth-service",
        ),

        (
            "CACHE",
            CACHE_MESSAGES,
            "inventory-service",
        ),

    ]

    end_time = time.time() + duration

    sent = 0

    while time.time() < end_time:

        if random.random() < noise_ratio:

            service = random.choice(
                SERVICES
            )

            message = random.choice(
                NOISE_MESSAGES
            )

            level = "INFO"

        else:

            _, messages, service = random.choice(
                cluster_groups
            )

            message = random.choice(
                messages
            )

            level = "ERROR"

        send_log(
            service=service,
            level=level,
            message=message,
            trace_id=str(uuid.uuid4()),
        )

        sent += 1

        if sent % 100 == 0:

            print(
                f"[NOISY CLUSTER] "
                f"Sent {sent}"
            )

        time.sleep(
            1.0 / rate
        )


# ============================================================
# MODE 18
# 10K+ LOG STRESS TEST
# ============================================================

def high_volume_stress_mode(
    total_logs=12000,
    workers=20,
):

    print("\n================================================")
    print("TRACE FORGE | HIGH-VOLUME 10K+ STRESS TEST")
    print("================================================")

    print(
        f"Generating {total_logs} logs."
    )

    print(
        f"HTTP workers={workers}"
    )

    print(
        "IMPORTANT:"
    )

    print(
        "Your ML pipeline currently processes "
        "at most 10,000 logs from a 5-minute window."
    )

    print(
        "This test intentionally exceeds that limit."
    )

    start = time.time()

    sent = 0
    failed = 0

    def generate_one(index):

        service = random.choice(
            SERVICES
        )

        roll = random.random()

        if roll < 0.75:

            level = "ERROR"

            group = random.choice([
                DATABASE_MESSAGES,
                PAYMENT_MESSAGES,
                AUTH_MESSAGES,
                CACHE_MESSAGES,
            ])

            message = random.choice(
                group
            )

        else:

            level = "INFO"

            message = random.choice(
                NORMAL_MESSAGES
            )

        trace_id = str(uuid.uuid4())

        return send_log(
            service=service,
            level=level,
            message=message,
            trace_id=trace_id,
        )

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        results = executor.map(
            generate_one,
            range(total_logs)
        )

        for result in results:

            if result:
                sent += 1
            else:
                failed += 1

            processed = (
                sent + failed
            )

            if processed % 500 == 0:

                elapsed = (
                    time.time()
                    - start
                )

                rate = (
                    processed / elapsed
                    if elapsed > 0
                    else 0
                )

                print(
                    f"[10K STRESS] "
                    f"{processed}/{total_logs} "
                    f"| sent={sent} "
                    f"| failed={failed} "
                    f"| rate={rate:.1f}/s"
                )

    elapsed = (
        time.time()
        - start
    )

    print("\n================================================")
    print("TRACE FORGE | STRESS TEST COMPLETE")
    print("================================================")

    print(
        f"Requested: {total_logs}"
    )

    print(
        f"Sent: {sent}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Elapsed: {elapsed:.2f}s"
    )

    print(
        f"Actual rate: "
        f"{total_logs / elapsed:.1f}/sec"
    )


# ============================================================
# MODE 19
# EXTREME 50K STRESS
# ============================================================

def extreme_stress_mode():

    print("\n================================================")
    print("TRACE FORGE | EXTREME 50K STRESS TEST")
    print("================================================")

    print(
        "WARNING:"
    )

    print(
        "This will generate 50,000 HTTP requests."
    )

    print(
        "Run this only after the 12K test succeeds."
    )

    confirmation = input(
        "Type YES to continue: "
    ).strip()

    if confirmation != "YES":

        print(
            "Extreme test cancelled."
        )

        return

    high_volume_stress_mode(
        total_logs=50000,
        workers=30,
    )


# ============================================================
# MODE MENU
# ============================================================

def print_menu():

    print("""
============================================================
                      TRACE FORGE
                 HARSH SYSTEM TESTER
============================================================

Choose a test mode:

 1  - Normal traffic
 2  - Extreme error spike
 3  - Rare errors
 4  - Cascading failure / RCA
 5  - Traffic drop
 6  - Critical error storm
 7  - Semantic clustering
 8  - Database outage
 9  - Redis / Cache outage
10  - Authentication outage
11  - Payment outage
12  - Mixed simultaneous failures
13  - Slow degradation
14  - Flapping incident
15  - Missing trace IDs
16  - Broken trace chain
17  - High-noise semantic clustering
18  - 12K log stress test
19  - 50K log stress test

============================================================
""")


# ============================================================
# MODE SELECTION
# ============================================================

def get_mode():

    while True:

        user_input = input(
            "Trace Forge | Enter mode number (1-19): "
        ).strip()

        try:

            mode = int(
                user_input
            )

        except ValueError:

            print(
                "Invalid input. "
                "Enter a number from 1 to 19."
            )

            continue

        if 1 <= mode <= 19:

            return mode

        print(
            "Invalid mode. "
            "Choose a number from 1 to 19."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Trace Forge - harsh log testing framework"
        )
    )

    parser.add_argument(
        "--mode",
        type=int,
        help="Test mode number. If omitted, interactive mode is used."
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="Duration in seconds"
    )

    parser.add_argument(
        "--rate",
        type=float,
        default=10,
        help="Logs per second"
    )

    parser.add_argument(
        "--total",
        type=int,
        default=12000,
        help="Total logs for stress mode"
    )

    args = parser.parse_args()

    # ========================================================
    # MODE SELECTION
    # ========================================================

    mode = args.mode

    if mode is None:

        print_menu()

        mode = get_mode()

    elif not 1 <= mode <= 19:

        print(
            "Invalid mode. "
            "Choose a number from 1 to 19."
        )

        return

    # ========================================================
    # RUN SELECTED MODE
    # ========================================================

    try:

        if mode == 1:

            normal_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 2:

            error_spike_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 3:

            rare_error_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 4:

            cascading_failure_mode(
                duration=args.duration,
            )

        elif mode == 5:

            traffic_drop_mode(
                baseline_duration=30
            )

        elif mode == 6:

            critical_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 7:

            semantic_clustering_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 8:

            database_outage_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 9:

            redis_outage_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 10:

            authentication_outage_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 11:

            payment_outage_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 12:

            mixed_failure_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 13:

            slow_degradation_mode(
                duration=args.duration
            )

        elif mode == 14:

            flapping_incident_mode()

        elif mode == 15:

            missing_trace_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 16:

            broken_trace_chain_mode(
                duration=args.duration
            )

        elif mode == 17:

            noisy_semantic_mode(
                duration=args.duration,
                rate=args.rate,
            )

        elif mode == 18:

            high_volume_stress_mode(
                total_logs=args.total
            )

        elif mode == 19:

            extreme_stress_mode()

    except KeyboardInterrupt:

        print(
            "\n\nTrace Forge stopped by user."
        )

    except Exception as e:

        print(
            f"\nTrace Forge error: {e}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()