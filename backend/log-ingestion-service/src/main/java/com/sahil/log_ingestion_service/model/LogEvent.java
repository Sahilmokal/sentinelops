package com.sahil.log_ingestion_service.model;

import lombok.Data;

@Data
public class LogEvent {
    private String timestamp;
    private String serviceName;
    private String logLevel;
    private String message;
    private String traceId;
    private String host;
}
