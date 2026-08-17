from collections import Counter

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

DBSCAN_EPS = 0.40
DBSCAN_MIN_SAMPLES = 2


# ============================================================
# MODEL
# ============================================================

_model = None


def get_model():

    global _model

    if _model is None:

        print(
            "[Semantic Clustering] "
            f"Loading model: {MODEL_NAME}"
        )

        _model = SentenceTransformer(
            MODEL_NAME
        )

        print(
            "[Semantic Clustering] "
            "Model loaded."
        )

    return _model


# ============================================================
# MESSAGE EXTRACTION
# ============================================================

def extract_messages(logs):

    messages = []

    for log in logs:

        message = log.get("message")

        if not message:
            continue

        message = str(message).strip()

        if message:
            messages.append(message)

    return messages


# ============================================================
# CLUSTER LOGS
# ============================================================

def cluster_logs(logs):

    messages = extract_messages(logs)

    if not messages:

        return {
            "totalMessages": 0,
            "uniqueMessages": 0,
            "clusterCount": 0,
            "noiseCount": 0,
            "noiseMessages": [],
            "clusters": [],
        }

    # --------------------------------------------------------
    # Unique messages for clustering
    # --------------------------------------------------------

    unique_messages = list(
        set(messages)
    )

    # --------------------------------------------------------
    # Not enough unique messages for DBSCAN
    # --------------------------------------------------------

    if len(unique_messages) < DBSCAN_MIN_SAMPLES:

        return {
            "totalMessages": len(messages),
            "uniqueMessages": len(unique_messages),
            "clusterCount": 0,
            "noiseCount": len(unique_messages),
            "noiseMessages": unique_messages,
            "clusters": [],
        }

    # --------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------

    model = get_model()

    embeddings = model.encode(
        unique_messages,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(
        embeddings
    )

    # --------------------------------------------------------
    # DBSCAN
    # --------------------------------------------------------

    dbscan = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="cosine",
    )

    labels = dbscan.fit_predict(
        embeddings
    )

    # --------------------------------------------------------
    # Message frequency
    # --------------------------------------------------------

    message_frequency = Counter(
        messages
    )

    # --------------------------------------------------------
    # Organize clusters
    # --------------------------------------------------------

    cluster_messages = {}

    for message, label in zip(
        unique_messages,
        labels
    ):

        if label == -1:
            continue

        cluster_messages.setdefault(
            int(label),
            []
        ).append(message)

    # --------------------------------------------------------
    # Build cluster metadata
    # --------------------------------------------------------

    clusters = []

    for cluster_id, messages_in_cluster in cluster_messages.items():

        occurrences = sum(
            message_frequency[message]
            for message in messages_in_cluster
        )

        representative_message = max(
            messages_in_cluster,
            key=lambda message:
                message_frequency[message]
        )

        clusters.append({
            "clusterId": cluster_id,
            "messageCount": len(
                messages_in_cluster
            ),
            "occurrences": occurrences,
            "representativeMessage":
                representative_message,
            "messages":
                messages_in_cluster,
        })

    # --------------------------------------------------------
    # Sort clusters by frequency
    # --------------------------------------------------------

    clusters.sort(
        key=lambda cluster:
            cluster["occurrences"],
        reverse=True
    )

    # --------------------------------------------------------
    # Noise messages
    # --------------------------------------------------------

    noise_messages = [
        message
        for message, label in zip(
            unique_messages,
            labels
        )
        if label == -1
    ]

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "totalMessages": len(messages),
        "uniqueMessages": len(unique_messages),
        "clusterCount": len(clusters),
        "noiseCount": len(noise_messages),
        "noiseMessages": noise_messages,
        "clusters": clusters,
    }