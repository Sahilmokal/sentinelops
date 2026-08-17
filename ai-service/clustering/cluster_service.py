from clustering.semantic_cluster import cluster_logs

from clustering.cluster_store import (
    save_cluster_result,
)


def process_cluster_window(
    logs,
    window_id,
    window_start,
    window_end,
):
    """
    Cluster one canonical time window and persist
    the resulting cluster metadata.
    """

    print(
        "[Semantic Clustering] "
        f"Processing window: "
        f"{window_start} → {window_end}"
    )

    # --------------------------------------------------------
    # Run Sentence Transformer + DBSCAN
    # --------------------------------------------------------

    result = cluster_logs(logs)

    print(
        "[Semantic Clustering] "
        f"Clusters found: "
        f"{result['clusterCount']}"
    )

    # --------------------------------------------------------
    # Persist metadata
    # --------------------------------------------------------

    save_cluster_result(
        window_id=window_id,
        window_start=window_start,
        window_end=window_end,
        result=result,
    )

    return result
