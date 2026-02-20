from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

def cluster_logs(logs):
    messages = [log["message"] for log in logs if "message" in log]

    if len(messages) < 2:
        return []

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(messages)

    clustering = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
    labels = clustering.fit_predict(X)

    clusters = {}

    for idx, label in enumerate(labels):
        if label == -1:
            continue

        if label not in clusters:
            clusters[label] = {
                "clusterId": int(label),
                "count": 0,
                "representativeMessage": messages[idx]
            }

        clusters[label]["count"] += 1

    return list(clusters.values())