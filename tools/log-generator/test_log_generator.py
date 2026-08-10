import requests
import random
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

INGESTION_URL = "http://localhost:8080/api/logs"

# All generated timestamps will use Indian Standard Time
IST = ZoneInfo("Asia/Kolkata")

services = [
    "auth-service",
    "order-service",
    "payment-service",
    "inventory-service"
]


# ============================================================
# LOG MESSAGES
# ============================================================

normal_messages = [
    "User login successful",
    "Order created successfully",
    "Payment processed successfully",
    "Cache hit for user profile"
]

error_messages = [
    "Database connection timeout",
    "Payment gateway timeout",
    "Token validation failed",
    "Null pointer exception occurred"
]

critical_message = "CRITICAL: Memory leak detected in JVM"


# ============================================================
# TIMESTAMP
# ============================================================

def get_current_timestamp():
    """
    Generate timezone-aware IST timestamp.

    Example:
    2026-08-06T16:45:21.123456+05:30
    """
    return datetime.now(IST).isoformat()


# ============================================================
# SEND LOG
# ============================================================

def send_log(service, level, message, trace_id):

    payload = {
        "serviceName": service,
        "logLevel": level,
        "message": message,
        "timestamp": get_current_timestamp(),
        "traceId": trace_id,
        "host": "test-log-generator"
    }

    try:
        response = requests.post(
            INGESTION_URL,
            json=payload,
            timeout=5
        )

        if not response.ok:
            print(
                f"[FAILED] "
                f"{response.status_code} "
                f"{response.text}"
            )

    except requests.RequestException as e:
        print(f"[ERROR] Could not send log: {e}")


# ============================================================
# MODE 1 — NORMAL TRAFFIC
# ============================================================

def normal_mode():

    print("\nRunning NORMAL TRAFFIC mode...")
    print("Press CTRL+C to stop.\n")

    count = 0

    while True:

        service = random.choice(services)
        message = random.choice(normal_messages)

        send_log(
            service=service,
            level="INFO",
            message=message,
            trace_id=str(uuid.uuid4())
        )

        count += 1

        if count % 50 == 0:
            print(f"[NORMAL] Sent {count} logs")

        time.sleep(0.1)


# ============================================================
# MODE 2 — ERROR SPIKE
# ============================================================

def spike_mode():

    print("\nRunning ERROR SPIKE mode...")
    print("Approximately 70% of generated logs will be ERROR.")
    print("This should trigger error-rate anomaly detection.")
    print("Press CTRL+C to stop.\n")

    count = 0
    error_count = 0

    while True:

        trace_id = str(uuid.uuid4())

        # 70% ERROR traffic
        if random.random() < 0.70:

            service = random.choice(services)
            message = random.choice(error_messages)

            send_log(
                service=service,
                level="ERROR",
                message=message,
                trace_id=trace_id
            )

            error_count += 1

        else:

            service = random.choice(services)
            message = random.choice(normal_messages)

            send_log(
                service=service,
                level="INFO",
                message=message,
                trace_id=trace_id
            )

        count += 1

        if count % 50 == 0:
            print(
                f"[SPIKE] Sent {count} logs | "
                f"Errors: {error_count}"
            )

        time.sleep(0.05)


# ============================================================
# MODE 3 — RARE ERROR
# ============================================================

def rare_mode():

    print("\nRunning RARE ERROR mode...")
    print("Approximately 5% of logs contain a rare error.")
    print("Press CTRL+C to stop.\n")

    count = 0
    rare_count = 0

    while True:

        trace_id = str(uuid.uuid4())

        if random.random() < 0.95:

            service = random.choice(services)
            message = random.choice(normal_messages)

            send_log(
                service=service,
                level="INFO",
                message=message,
                trace_id=trace_id
            )

        else:

            send_log(
                service="auth-service",
                level="ERROR",
                message="RARE: Kernel panic detected",
                trace_id=trace_id
            )

            rare_count += 1

        count += 1

        if count % 50 == 0:
            print(
                f"[RARE] Sent {count} logs | "
                f"Rare errors: {rare_count}"
            )

        time.sleep(0.1)


# ============================================================
# MODE 4 — CASCADING FAILURE / RCA
# ============================================================

def cascading_failure_mode():

    print("\nRunning CASCADING FAILURE mode...")
    print("Root service: auth-service")
    print("Expected impacted services: order-service, payment-service")
    print("Press CTRL+C to stop.\n")

    cascade_count = 0

    while True:

        # Same trace ID is deliberately shared across the
        # complete failure chain.
        trace_id = str(uuid.uuid4())

        # ----------------------------------------------------
        # ROOT FAILURE
        # ----------------------------------------------------

        send_log(
            service="auth-service",
            level="ERROR",
            message="Database connection timeout",
            trace_id=trace_id
        )

        time.sleep(0.3)

        # ----------------------------------------------------
        # FIRST DOWNSTREAM FAILURE
        # ----------------------------------------------------

        send_log(
            service="order-service",
            level="ERROR",
            message="Downstream auth failure",
            trace_id=trace_id
        )

        time.sleep(0.3)

        # ----------------------------------------------------
        # SECOND DOWNSTREAM FAILURE
        # ----------------------------------------------------

        send_log(
            service="payment-service",
            level="ERROR",
            message="Auth dependency failed",
            trace_id=trace_id
        )

        cascade_count += 1

        print(
            f"[RCA] Cascade #{cascade_count} | "
            f"traceId={trace_id}"
        )

        time.sleep(1)


# ============================================================
# MODE 5 — TRAFFIC DROP
# ============================================================

def traffic_drop_mode():

    print("\nRunning TRAFFIC DROP mode...")
    print("Generating baseline traffic first...\n")

    # --------------------------------------------------------
    # BASELINE TRAFFIC
    # --------------------------------------------------------

    for i in range(200):

        service = random.choice(services)

        send_log(
            service=service,
            level="INFO",
            message=random.choice(normal_messages),
            trace_id=str(uuid.uuid4())
        )

        if (i + 1) % 50 == 0:
            print(f"[BASELINE] Sent {i + 1}/200 logs")

        time.sleep(0.05)

    # --------------------------------------------------------
    # TRAFFIC DROP
    # --------------------------------------------------------

    print("\n[TRAFFIC DROP] Traffic stopped.")
    print("Waiting 30 seconds for detector...\n")

    time.sleep(30)

    print("Traffic drop simulation completed.")


# ============================================================
# MODE 6 — CRITICAL ERROR
# ============================================================

def critical_mode():

    print("\nRunning CRITICAL ERROR mode...")
    print("Generating critical JVM errors.")
    print("Press CTRL+C to stop.\n")

    count = 0

    while True:

        trace_id = str(uuid.uuid4())

        send_log(
            service="payment-service",
            level="ERROR",
            message=critical_message,
            trace_id=trace_id
        )

        count += 1

        print(f"[CRITICAL] Sent critical error #{count}")

        time.sleep(1)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("""
============================================================
              TRACEFORGE LOG GENERATOR
============================================================

Choose Test Mode:

1 - Normal Traffic
2 - Error Spike
3 - Rare Error
4 - Cascading Failure (RCA)
5 - Traffic Drop
6 - Critical Error

============================================================
""")

    choice = input("Enter mode number: ").strip()

    try:

        if choice == "1":
            normal_mode()

        elif choice == "2":
            spike_mode()

        elif choice == "3":
            rare_mode()

        elif choice == "4":
            cascading_failure_mode()

        elif choice == "5":
            traffic_drop_mode()

        elif choice == "6":
            critical_mode()

        else:
            print("Invalid choice.")

    except KeyboardInterrupt:
        print("\n\nLog generator stopped.")