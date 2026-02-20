package com.sahil.log_processor_service.repository;

import com.sahil.log_processor_service.model.LogDocument;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;

public interface LogRepository extends ElasticsearchRepository<LogDocument, String> {
}