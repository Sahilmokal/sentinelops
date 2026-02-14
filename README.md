SentinelOps

AI-Based Log Monitoring & Root Cause Analysis Platform

🚀 Problem Statement

Modern distributed systems generate massive volumes of logs, and engineers often manually inspect them during production failures. SentinelOps automates log pattern discovery, anomaly detection, and probable root cause identification to reduce downtime and speed up incident resolution.

🧠 What This Project Does

SentinelOps:

Collects structured logs from multiple services

Processes logs asynchronously using a message queue

Stores logs in a searchable system

Detects abnormal behavior using unsupervised machine learning

Identifies likely root causes of incidents

Exposes alerts and RCA insights through a dashboard

🏗️ System Architecture

High-Level Flow
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
AI Analysis Service (Clustering + Anomaly Detection + RCA)
        ↓
Alert API
        ↓
Frontend Dashboard

🛠️ Tech Stack
Backend

Java 17

Spring Boot 3.x

Spring Kafka

Messaging

Apache Kafka

Storage

Elasticsearch (Time-based indexing)

AI / ML

Python 3.10

scikit-learn

TF-IDF Vectorization

Unsupervised Anomaly Detection (Isolation Forest / DBSCAN)

Frontend

React

Infrastructure

Docker

Docker Compose

Nginx

Cloud

AWS EC2