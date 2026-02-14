1️⃣ Problem Statement

Software systems generate thousands of logs. Engineers manually inspect logs during failures. This project automates log pattern discovery, anomaly detection, and root cause identification.

2️⃣ High-Level Flow
Application Services
        ↓
Log Ingestion Service (Spring Boot)
        ↓
Kafka (raw-logs topic)
        ↓
Log Processor Service
        ↓
Elasticsearch
        ↓
AI Service (Clustering + Anomaly Detection)
        ↓
Alert API
        ↓
Frontend Dashboard

3️⃣ Why Asynchronous Pipeline?

Explain:

Prevent system overload during spikes

Decouple ingestion from processing

Improve reliability

4️⃣ Why Elasticsearch Instead of SQL?

Explain:

Full-text search

Fast log filtering

Time-based indexing