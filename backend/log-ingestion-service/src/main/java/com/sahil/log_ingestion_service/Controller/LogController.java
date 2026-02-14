package com.sahil.log_ingestion_service.Controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sahil.log_ingestion_service.Services.KafkaProducerService;
import com.sahil.log_ingestion_service.model.LogEvent;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/logs")
public class LogController {

    private final KafkaProducerService producerService;
    private final ObjectMapper objectMapper;

    public LogController(KafkaProducerService producerService) {
        this.producerService = producerService;
        this.objectMapper = new ObjectMapper();
    }

    @PostMapping
    public ResponseEntity<String> ingestLog(@RequestBody LogEvent logEvent) throws JsonProcessingException {

        String json = objectMapper.writeValueAsString(logEvent);
        producerService.sendLog(json);

        return ResponseEntity.ok("Log sent to Kafka");
    }
}
