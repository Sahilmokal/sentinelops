from clustering.semantic_cluster import cluster_logs


# ============================================================
# TEST LOGS
# ============================================================

logs = [

    # Database-related messages
    {
        "message": "Database connection failed",
        "serviceName": "order-service"
    },
    {
        "message": "Unable to connect to database",
        "serviceName": "payment-service"
    },
    {
        "message": "PostgreSQL connection refused",
        "serviceName": "order-service"
    },

    # Redis-related messages
    {
        "message": "Redis connection timeout",
        "serviceName": "cache-service"
    },
    {
        "message": "Cache server timed out",
        "serviceName": "cache-service"
    },

    # Authentication-related messages
    {
        "message": "User authentication failed",
        "serviceName": "auth-service"
    },
    {
        "message": "Invalid credentials provided",
        "serviceName": "auth-service"
    },

    # Normal unrelated message
    {
        "message": "Order processed successfully",
        "serviceName": "order-service"
    },
]


# ============================================================
# RUN CLUSTERING
# ============================================================

print("\nStarting semantic clustering...\n")

result = cluster_logs(logs)


# ============================================================
# DISPLAY RESULT
# ============================================================

print("\n========================================")
print("SEMANTIC CLUSTERING RESULT")
print("========================================")

print(
    f"Total messages: {result['totalMessages']}"
)

print(
    f"Unique messages: {result['uniqueMessages']}"
)

print(
    f"Clusters: {result['clusterCount']}"
)

print(
    f"Noise messages: {result['noiseCount']}"
)


for cluster in result["clusters"]:

    print("\n----------------------------------------")

    print(
        f"Cluster ID: "
        f"{cluster['clusterId']}"
    )

    print(
        f"Unique messages: "
        f"{cluster['messageCount']}"
    )

    print(
        f"Occurrences: "
        f"{cluster['occurrences']}"
    )

    print(
        f"Representative: "
        f"{cluster['representativeMessage']}"
    )

    print("Messages:")

    for message in cluster["messages"]:
        print(f"  - {message}")


print("\n========================================")
print("TEST COMPLETE")
print("========================================")