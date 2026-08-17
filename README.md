# TraceForge

TraceForge is an observability and incident-analysis platform that detects anomalies from application logs, creates and deduplicates incidents, performs Root Cause Analysis (RCA), and enriches incidents with machine-learning evidence.

## Overview

TraceForge uses two complementary processing pipelines:

* **Rule-based pipeline:** runs every 30 seconds against a rolling 2-minute log window.
* **ML enrichment pipeline:** runs every 5 minutes against a completed 5-minute window.

The two pipelines operate on the **same incident identity**. ML processing enriches an existing incident rather than creating a duplicate incident.

```text
                         Application Logs
                                |
                                v
                         Elasticsearch
                                |
                +---------------+---------------+
                |                               |
                v                               v
        Rule Monitoring                  ML Enrichment
          every 30s                       every 5m
         2-minute window                 5-minute window
                |                               |
                v                               v
       Anomaly Detection              Semantic Clustering
                |                     Isolation Forest
                v                               |
           Stage 1 RCA                           |
                |                               v
                +-----------> Incident <--------+
                                |
                                v
                           Stage 2 RCA
                                |
                                v
                         React Dashboard
```

## Features

* Real-time log analysis
* Traffic-drop detection
* Error-rate anomaly detection
* Critical-error detection
* Rare-log detection
* Spike detection
* Isolation Forest anomaly detection
* Semantic log clustering
* Automatic incident creation
* Incident deduplication
* Progressive RCA
* Alert acknowledgement and resolution
* Automatic stale-incident resolution
* Exact incident RCA lookup
* Elasticsearch-backed incident history
* React-based operational dashboard

## Architecture

### Rule Pipeline

The rule pipeline executes every 30 seconds.

It retrieves the latest two minutes of logs and runs the configured anomaly detectors.

```text
Logs
  |
  v
Rule Detectors
  |
  v
Active Anomalies
  |
  v
Incident Family
  |
  +---- Existing Incident ----> Update
  |
  +---- New Incident ----------> Create
                                  |
                                  v
                               Stage 1 RCA
```

### ML Pipeline

The ML pipeline executes every five minutes against a completed five-minute window.

```text
Completed 5-Minute Window
            |
            +--------------------+
            |                    |
            v                    v
      Semantic Clustering   Isolation Forest
            |                    |
            +---------+----------+
                      |
                      v
                Enhanced RCA
                      |
                      v
             Existing Incident
                      |
                      v
                 Stage 2 RCA
```

## Incident Lifecycle

```text
NEW
 |
 | ACK
 v
ACKNOWLEDGED
 |
 | RESOLVE
 v
RESOLVED
```

The backend enforces the lifecycle transitions:

* `NEW → ACKNOWLEDGED`
* `ACKNOWLEDGED → RESOLVED`

Stale `NEW` incidents can be automatically resolved after the configured timeout.

## Incident Identity

Every incident receives a unique `alertId`.

The `alertId` remains constant throughout the incident lifecycle and is used to associate:

* Alert data
* RCA
* ML enrichment
* Acknowledgement
* Resolution
* Frontend RCA navigation

Incident identity is based on the anomaly family, not on RCA output.

For example:

```text
errorRate + rare + spike
```

is associated with the `errorRate` incident family according to the configured priority.

RCA results, root service, confidence, clustering, and ML results do not create a new incident identity.

## Progressive RCA

TraceForge uses two RCA stages.

### Stage 1

Stage 1 RCA is generated during rule processing using the rolling 2-minute window:

```python
rca_result = perform_rca(
    logs=logs
)
```

The initial incident stores:

```text
rcaStage = 1
rcaSource = RULE
```

The original RCA is preserved as:

```text
ruleRca
```

### Stage 2

The ML pipeline processes the completed 5-minute window using:

* Semantic clustering
* Isolation Forest
* Enhanced RCA

The enhanced result is stored against the **same `alertId`**.

The incident then contains:

```text
ruleRca
stage2Rca
mlRca
rca
```

`rca` represents the current authoritative RCA.

```text
Initial:
rca = Stage 1 RCA

After ML enrichment:
rca = Stage 2 RCA
```

The Stage 1 RCA remains available for comparison and investigation.

## Alert Management

Alerts are automatically created when active anomalies are detected.

The system deduplicates active incidents using a stable incident family.

Supported operations:

```http
GET  /alerts
GET  /alerts/{alertId}

POST /alerts/{alertId}/ack
POST /alerts/{alertId}/resolve
```

The frontend passes the exact `alertId` selected from the alert table to the RCA page.

RCA lookup therefore does not attempt to infer an incident from timestamps, services, anomaly types, or other fields.

## RCA API

### Exact Incident RCA

```http
GET /rca/incident/{alertId}
```

Returns the stored RCA for the specified incident.

No RCA is recalculated by this endpoint.

### RCA History

```http
GET /rca/history
```

Supported filters:

```text
start_time
end_time
status
severity
page
size
```

Historical RCA is retrieved from previously stored incidents. The endpoint does not recalculate RCA for historical records.

## Anomaly API

```http
GET /anomalies
```

Parameters:

```text
minutes
size
```

The endpoint exposes the latest rule-based anomaly results and persisted ML results.

## Cluster API

```http
GET /clusters
```

Parameters:

```text
minutes
size
```

## Logs API

```http
GET /logs
```

Supported parameters include:

```text
service
level
start_time
end_time
minutes
page
size
sort_field
sort_order
```

## Elasticsearch

TraceForge uses Elasticsearch for log and incident storage.

### Log index

```text
logs
```

### Alert index

```text
alerts
```

Alert documents contain fields including:

```text
alertId
signature
dedupKey
incidentFamily
anomalyType
severity
status
sources
rootService
impactedServices
confidence
firstDetectedAt
lastUpdatedAt
resolvedAt
occurrenceCount
mlEnrichmentCount
anomalies
ruleRca
stage2Rca
mlRca
rca
mlEvidence
mlAnomaly
mlScore
```

## Project Structure

```text
TraceForge/
├── backend/
│   ├── main.py
│   ├── scheduler.py
│   ├── elastic_client.py
│   │
│   ├── alert/
│   │   └── alert_engine.py
│   │
│   ├── anomaly/
│   │   ├── anomaly.py
│   │   ├── isolation_forest.py
│   │   └── ml_result_store.py
│   │
│   ├── clustering/
│   │   ├── cluster_service.py
│   │   ├── semantic_cluster.py
│   │   └── cluster_store.py
│   │
│   ├── rca/
│   │   └── rca_engine.py
│   │
│   └── storage/
│       └── ml_storage.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── pages/
│   │   │   ├── LogsPage.jsx
│   │   │   ├── AlertsPage.jsx
│   │   │   ├── RCAPage.jsx
│   │   │   ├── AnomaliesPage.jsx
│   │   │   └── ClustersPage.jsx
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   │   └── api.js
│   │   └── utils/
│   └── package.json
│
└── README.md
```

## Technology Stack

| Component            | Technology          |
| -------------------- | ------------------- |
| Frontend             | React               |
| Build Tool           | Vite                |
| Backend              | FastAPI             |
| Language             | Python              |
| HTTP Client          | Axios               |
| Log Storage          | Elasticsearch       |
| Scheduling           | APScheduler         |
| ML Anomaly Detection | Isolation Forest    |
| Clustering           | Semantic Clustering |
| RCA                  | Custom RCA Engine   |

## Configuration

### Frontend

Create:

```text
frontend/.env
```

```env
VITE_API_URL=http://localhost:8000
```

### Backend

Example configuration:

```env
ELASTIC_HOST=http://elasticsearch:9200
ALLOWED_ORIGINS=http://localhost:5173
```

## Running Locally

### Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

The backend runs on:

```text
http://localhost:8000
```

## Core Design Principle

TraceForge separates **incident identity** from **incident diagnosis**.

```text
Incident Identity
      |
      +-- alertId
      |
      +-- incident lifecycle
      |
      +-- anomaly family
      |
      v
Incident Diagnosis
      |
      +-- Stage 1 RCA
      |
      +-- Stage 2 RCA
      |
      +-- ML evidence
      |
      +-- root service
      |
      +-- confidence
```

This allows the system to detect an incident quickly, provide an initial RCA immediately, and progressively improve that RCA as additional five-minute ML evidence becomes available.
