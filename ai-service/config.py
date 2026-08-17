# config.py
# config.py
import os

ELASTIC_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
TIME_PROPAGATION_WINDOW_SECONDS = int(os.getenv("TIME_PROPAGATION_WINDOW_SECONDS", 30))
ERROR_BURST_THRESHOLD = 5              # minimum errors to consider burs