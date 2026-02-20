package com.sahil.log_processor_service.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sahil.log_processor_service.model.LogDocument;
import com.sahil.log_processor_service.repository.LogRepository;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class KafkaConsumerService {

    private final LogRepository logRepository;
    private final ObjectMapper objectMapper;

    public KafkaConsumerService(LogRepository logRepository) {
        this.logRepository = logRepository;
        this.objectMapper = new ObjectMapper();
    }

    @KafkaListener(topics = "raw-logs", groupId = "log-processor-group")
    public void consume(String message) {
        try {
            LogDocument logDocument = objectMapper.readValue(message, LogDocument.class);

            logRepository.save(logDocument);

            System.out.println("Saved log to Elasticsearch: " + logDocument.getTraceId());

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}