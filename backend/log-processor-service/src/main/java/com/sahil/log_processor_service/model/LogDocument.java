package com.sahil.log_processor_service.model;



import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;

@Data
@Document(indexName = "logs")
public class LogDocument {

    @Id
    private String id;

    private String timestamp;
    private String serviceName;
    private String logLevel;
    private String message;
    private String traceId;
    private String host;
}