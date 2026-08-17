package com.sahil.log_ingestion_service.Services;



import com.sahil.log_ingestion_service.model.User;
import com.sahil.log_ingestion_service.Repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
public class AuthService {

    private final UserRepository userRepository;

    private final BCryptPasswordEncoder passwordEncoder =
            new BCryptPasswordEncoder();

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User register(String username, String password) {

        if (userRepository.existsByUsername(username)) {
            throw new RuntimeException(
                    "Username already exists"
            );
        }

        User user = new User();

        user.setUsername(username);

        user.setPassword(
                passwordEncoder.encode(password)
        );

        user.setCreatedAt(
                Instant.now().toString()
        );

        return userRepository.save(user);
    }

    public boolean validatePassword(
            String rawPassword,
            String hashedPassword
    ) {

        return passwordEncoder.matches(
                rawPassword,
                hashedPassword
        );
    }
}