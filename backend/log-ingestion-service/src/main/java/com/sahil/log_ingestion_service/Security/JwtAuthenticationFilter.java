package com.sahil.log_ingestion_service.Security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;

    public JwtAuthenticationFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String method = request.getMethod();
        String uri = request.getRequestURI();

        System.out.println(
                "[JWT] " + method + " " + uri
        );

        if ("OPTIONS".equalsIgnoreCase(method)) {

            System.out.println(
                    "[JWT] OPTIONS request - skipping JWT"
            );

            filterChain.doFilter(request, response);
            return;
        }

        String authorizationHeader =
                request.getHeader("Authorization");

        if (authorizationHeader == null) {

            System.out.println(
                    "[JWT] NO Authorization header"
            );

            filterChain.doFilter(request, response);
            return;
        }

        if (!authorizationHeader.startsWith("Bearer ")) {

            System.out.println(
                    "[JWT] Authorization header exists but is not Bearer"
            );

            filterChain.doFilter(request, response);
            return;
        }

        String token =
                authorizationHeader.substring(7);

        System.out.println(
                "[JWT] Bearer token received. Length="
                        + token.length()
        );

        try {

            boolean valid =
                    jwtService.isTokenValid(token);

            System.out.println(
                    "[JWT] Token valid=" + valid
            );

            if (valid) {

                String username =
                        jwtService.extractUsername(token);

                System.out.println(
                        "[JWT] Username=" + username
                );

                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                                username,
                                null,
                                Collections.singletonList(
                                        new SimpleGrantedAuthority(
                                                "ROLE_USER"
                                        )
                                )
                        );

                SecurityContextHolder
                        .getContext()
                        .setAuthentication(authentication);

                System.out.println(
                        "[JWT] Authentication SUCCESS"
                );

            } else {

                System.out.println(
                        "[JWT] Authentication FAILED - invalid/expired token"
                );
            }

        } catch (Exception e) {

            System.out.println(
                    "[JWT] EXCEPTION validating token: "
                            + e.getClass().getName()
                            + " - "
                            + e.getMessage()
            );

            SecurityContextHolder
                    .clearContext();
        }

        filterChain.doFilter(request, response);
    }
}