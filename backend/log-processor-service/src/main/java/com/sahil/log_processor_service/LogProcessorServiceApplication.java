package com.sahil.log_processor_service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

@SpringBootApplication
@EnableKafka
public class LogProcessorServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(LogProcessorServiceApplication.class, args);
	}

}
