package com.sahil.log_ingestion_service.Controller;



import com.sahil.log_ingestion_service.dto.LoginRequest;
import com.sahil.log_ingestion_service.dto.RegisterRequest;
import com.sahil.log_ingestion_service.model.User;
import com.sahil.log_ingestion_service.Repository.UserRepository;
import com.sahil.log_ingestion_service.Security.JwtService;
import com.sahil.log_ingestion_service.Services.AuthService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.security.crypto.password.PasswordEncoder;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService authService;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthController(
            AuthService authService,
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService
    ) {
        this.authService = authService;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(
            @Valid @RequestBody RegisterRequest request
    ) {

        if (
                userRepository.existsByUsername(
                        request.username()
                )
        ) {

            return ResponseEntity
                    .status(HttpStatus.CONFLICT)
                    .body(
                            Map.of(
                                    "message",
                                    "Username already exists"
                            )
                    );
        }

        User user = authService.register(
                request.username(),
                request.password()
        );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        Map.of(
                                "message",
                                "User registered successfully",
                                "username",
                                user.getUsername()
                        )
                );
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(
            @Valid @RequestBody LoginRequest request
    ) {

        User user =
                userRepository
                        .findByUsername(
                                request.username()
                        )
                        .orElse(null);

        if (
                user == null
                || !passwordEncoder.matches(
                        request.password(),
                        user.getPassword()
                )
        ) {

            return ResponseEntity
                    .status(HttpStatus.UNAUTHORIZED)
                    .body(
                            Map.of(
                                    "message",
                                    "Invalid username or password"
                            )
                    );
        }

        String token =
                jwtService.generateToken(
                        user.getUsername()
                );

        return ResponseEntity.ok(
                Map.of(
                        "message",
                        "Login successful",
                        "token",
                        token,
                        "username",
                        user.getUsername()
                )
        );
    }
}