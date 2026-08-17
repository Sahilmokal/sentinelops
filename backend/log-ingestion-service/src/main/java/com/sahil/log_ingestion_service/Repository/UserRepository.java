package com.sahil.log_ingestion_service.Repository;



import com.sahil.log_ingestion_service.model.User;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;

import java.util.Optional;

public interface UserRepository
        extends ElasticsearchRepository<User, String> {

    Optional<User> findByUsername(String username);

    boolean existsByUsername(String username);
}