// ─── Mock Logs ────────────────────────────────────────────────────────────────
export const MOCK_LOGS = {
  page: 1,
  size: 20,
  total: 324,
  data: [
    {
      id: '1',
      timestamp: '2025-03-07T10:42:31Z',
      serviceName: 'inventory-service',
      logLevel: 'ERROR',
      message: 'NullPointerException in InventoryController.getStock() at line 84',
      traceId: 'abc-123-xyz-001',
    },
    {
      id: '2',
      timestamp: '2025-03-07T10:42:29Z',
      serviceName: 'order-service',
      logLevel: 'WARN',
      message: 'Slow DB query detected: 4200ms — SELECT * FROM orders WHERE status=PENDING',
      traceId: 'def-456-uvw-002',
    },
    {
      id: '3',
      timestamp: '2025-03-07T10:42:27Z',
      serviceName: 'auth-service',
      logLevel: 'INFO',
      message: 'User session created for uid:8821 from IP 10.0.1.44',
      traceId: 'ghi-789-rst-003',
    },
    {
      id: '4',
      timestamp: '2025-03-07T10:42:25Z',
      serviceName: 'payment-service',
      logLevel: 'ERROR',
      message: 'Connection timeout to payment gateway after 5000ms',
      traceId: 'jkl-012-opq-004',
    },
    {
      id: '5',
      timestamp: '2025-03-07T10:42:23Z',
      serviceName: 'gateway-service',
      logLevel: 'INFO',
      message: 'Request routed to inventory-service — latency 12ms',
      traceId: 'mno-345-lmn-005',
    },
    {
      id: '6',
      timestamp: '2025-03-07T10:42:20Z',
      serviceName: 'inventory-service',
      logLevel: 'ERROR',
      message: 'Database connection pool exhausted (50/50 active connections)',
      traceId: 'pqr-678-ijk-006',
    },
    {
      id: '7',
      timestamp: '2025-03-07T10:42:18Z',
      serviceName: 'notification-service',
      logLevel: 'DEBUG',
      message: 'Queuing email notification for order #9981 — recipient: user@example.com',
      traceId: 'stu-901-fgh-007',
    },
    {
      id: '8',
      timestamp: '2025-03-07T10:42:15Z',
      serviceName: 'order-service',
      logLevel: 'ERROR',
      message: 'Failed to reserve inventory: inventory-service returned 503 Service Unavailable',
      traceId: 'vwx-234-cde-008',
    },
    {
      id: '9',
      timestamp: '2025-03-07T10:42:12Z',
      serviceName: 'auth-service',
      logLevel: 'WARN',
      message: 'Rate limit approaching for IP 192.168.1.44 — 950/1000 requests used',
      traceId: 'yza-567-bcd-009',
    },
    {
      id: '10',
      timestamp: '2025-03-07T10:42:10Z',
      serviceName: 'payment-service',
      logLevel: 'INFO',
      message: 'Payment processed successfully: $149.99 for order #9980',
      traceId: 'bcd-890-abc-010',
    },
    {
      id: '11',
      timestamp: '2025-03-07T10:42:08Z',
      serviceName: 'inventory-service',
      logLevel: 'ERROR',
      message: 'Stock check failed for SKU:88821 — concurrent modification exception',
      traceId: 'efg-123-hij-011',
    },
    {
      id: '12',
      timestamp: '2025-03-07T10:42:05Z',
      serviceName: 'gateway-service',
      logLevel: 'WARN',
      message: 'Circuit breaker OPEN for inventory-service after 5 consecutive failures',
      traceId: 'klm-456-nop-012',
    },
    {
      id: '13',
      timestamp: '2025-03-07T10:42:02Z',
      serviceName: 'order-service',
      logLevel: 'INFO',
      message: 'Order #9982 created for customer uid:7712',
      traceId: 'qrs-789-tuv-013',
    },
    {
      id: '14',
      timestamp: '2025-03-07T10:41:59Z',
      serviceName: 'notification-service',
      logLevel: 'INFO',
      message: 'SMS sent successfully to +1-555-0142',
      traceId: 'wxy-012-zab-014',
    },
    {
      id: '15',
      timestamp: '2025-03-07T10:41:55Z',
      serviceName: 'auth-service',
      logLevel: 'DEBUG',
      message: 'JWT token validated for uid:8821 — expires in 3540s',
      traceId: 'cde-345-fgh-015',
    },
  ],
}


// ─── Mock Alerts ──────────────────────────────────────────────────────────────
export const MOCK_ALERTS = {
  page: 1,
  size: 20,
  total: 5,
  data: [
    {
      id: 'a1',
      severity: 'CRITICAL',
      anomalyType: 'HIGH_ERROR_RATE',
      rootService: 'inventory-service',
      status: 'NEW',
      confidence: 0.91,
      firstDetectedAt: '2025-03-07T10:40:00Z',

      // Stage 1
      lifecycleStage: 'RULE_DETECTED',
      stage1: {
        detectedBy: 'RULE_ENGINE',
        detectionType: 'HIGH_ERROR_RATE',
        threshold: 'ERROR ratio > 60%',
        evidence: {
          errorRatio: 0.69,
          errorCount: 138,
          totalCount: 200,
        },
      },

      // Stage 2
      stage2: {
        status: 'ENRICHED',
        enrichedAt: '2025-03-07T10:40:30Z',
        mlModel: 'ISOLATION_FOREST',
        mlScore: 0.94,
        anomaly: true,
      },
    },

    {
      id: 'a2',
      severity: 'HIGH',
      anomalyType: 'SPIKE',
      rootService: 'order-service',
      status: 'NEW',
      confidence: 0.78,
      firstDetectedAt: '2025-03-07T10:35:00Z',

      lifecycleStage: 'RULE_DETECTED',

      stage1: {
        detectedBy: 'RULE_ENGINE',
        detectionType: 'TRAFFIC_SPIKE',
        threshold: 'Traffic > 2.5x baseline',
        evidence: {
          baseline: 45,
          current: 144,
          multiplier: 3.2,
        },
      },

      stage2: {
        status: 'PENDING',
        enrichedAt: null,
        mlModel: 'ISOLATION_FOREST',
        mlScore: null,
        anomaly: null,
      },
    },

    {
      id: 'a3',
      severity: 'MEDIUM',
      anomalyType: 'TRAFFIC_DROP',
      rootService: 'payment-service',
      status: 'ACKNOWLEDGED',
      confidence: 0.62,
      firstDetectedAt: '2025-03-07T10:20:00Z',

      lifecycleStage: 'ENRICHED',

      stage1: {
        detectedBy: 'RULE_ENGINE',
        detectionType: 'TRAFFIC_DROP',
        threshold: 'Traffic below baseline',
        evidence: {
          baseline: 80,
          current: 42,
          dropPercent: 47.5,
        },
      },

      stage2: {
        status: 'ENRICHED',
        enrichedAt: '2025-03-07T10:20:30Z',
        mlModel: 'ISOLATION_FOREST',
        mlScore: 0.71,
        anomaly: true,
      },
    },

    {
      id: 'a4',
      severity: 'LOW',
      anomalyType: 'RARE_LOG',
      rootService: 'auth-service',
      status: 'RESOLVED',
      confidence: 0.45,
      firstDetectedAt: '2025-03-07T09:55:00Z',

      lifecycleStage: 'ENRICHED',

      stage1: {
        detectedBy: 'RULE_ENGINE',
        detectionType: 'RARE_PATTERN',
        threshold: 'Pattern occurrence < 3',
        evidence: {
          occurrences: 2,
        },
      },

      stage2: {
        status: 'ENRICHED',
        enrichedAt: '2025-03-07T09:55:30Z',
        mlModel: 'ISOLATION_FOREST',
        mlScore: 0.39,
        anomaly: false,
      },
    },

    {
      id: 'a5',
      severity: 'HIGH',
      anomalyType: 'CRITICAL_ERROR',
      rootService: 'gateway-service',
      status: 'NEW',
      confidence: 0.84,
      firstDetectedAt: '2025-03-07T10:38:00Z',

      lifecycleStage: 'ENRICHED',

      stage1: {
        detectedBy: 'RULE_ENGINE',
        detectionType: 'CRITICAL_ERROR',
        threshold: 'Repeated critical errors',
        evidence: {
          count: 14,
          windowSeconds: 60,
        },
      },

      stage2: {
        status: 'ENRICHED',
        enrichedAt: '2025-03-07T10:38:30Z',
        mlModel: 'ISOLATION_FOREST',
        mlScore: 0.88,
        anomaly: true,
      },
    },
  ],
}


// ─── Mock Anomalies ───────────────────────────────────────────────────────────
export const MOCK_ANOMALIES = {
  mode: 'realtime',

  trafficDrop: null,

  errorRate: {
    type: 'HIGH_ERROR_RATE',
    errorRatio: 0.69,
    message: 'High percentage of ERROR logs detected across services',
  },

  critical: [
    {
      service: 'inventory-service',
      message: 'NullPointerException spike — 14 occurrences in 60s',
      count: 14,
    },
  ],

  rare: [
    {
      pattern: 'JDBC connection reset by peer',
      occurrences: 2,
    },
  ],

  spike: [
    {
      service: 'order-service',
      multiplier: 3.2,
      baseline: 45,
      current: 144,
    },
  ],

  isolationForest: {
    status: 'ENRICHED',
    model: 'ISOLATION_FOREST',
    anomaly: true,
    score: 0.94,
    affectedServices: [
      'inventory-service',
      'order-service',
      'gateway-service',
    ],
  },
}


// ─── Mock Clusters ────────────────────────────────────────────────────────────
export const MOCK_CLUSTERS = {
  mode: 'realtime',

  totalLogsFetched: 500,

  totalMessages: 500,

  uniqueMessages: 15,

  totalClusters: 4,

  noiseCount: 3,

  noiseMessages: [
    'JDBC connection reset by peer',
    'Unexpected request timeout',
    'Unknown downstream response',
  ],

  clusters: [
    {
      clusterId: 0,
      size: 138,

      label: 'Inventory database / connection failures',

      representativeMessage:
        'Database connection pool exhausted (50/50 active connections)',

      services: [
        'inventory-service',
        'order-service',
      ],

      logLevels: [
        'ERROR',
        'WARN',
      ],

      messages: [
        'NullPointerException in InventoryController.getStock() at line 84',
        'Database connection pool exhausted (50/50 active connections)',
        'Stock check failed for SKU:88821 — concurrent modification exception',
        'Failed to reserve inventory: inventory-service returned 503 Service Unavailable',
      ],

      firstSeen: '2025-03-07T10:38:42Z',
      lastSeen: '2025-03-07T10:42:31Z',

      anomaly: true,

      confidence: 0.94,
    },

    {
      clusterId: 1,
      size: 96,

      label: 'Order traffic / latency degradation',

      representativeMessage:
        'Slow DB query detected: 4200ms — SELECT * FROM orders WHERE status=PENDING',

      services: [
        'order-service',
      ],

      logLevels: [
        'WARN',
        'ERROR',
      ],

      messages: [
        'Slow DB query detected: 4200ms — SELECT * FROM orders WHERE status=PENDING',
        'Order processing latency exceeded threshold',
        'Order retry triggered after downstream timeout',
      ],

      firstSeen: '2025-03-07T10:35:00Z',
      lastSeen: '2025-03-07T10:42:29Z',

      anomaly: true,

      confidence: 0.81,
    },

    {
      clusterId: 2,
      size: 72,

      label: 'Gateway circuit-breaker activity',

      representativeMessage:
        'Circuit breaker OPEN for inventory-service after 5 consecutive failures',

      services: [
        'gateway-service',
      ],

      logLevels: [
        'WARN',
        'ERROR',
      ],

      messages: [
        'Circuit breaker OPEN for inventory-service after 5 consecutive failures',
        'Request routed to inventory-service — latency 12ms',
        'Gateway fallback triggered',
      ],

      firstSeen: '2025-03-07T10:38:00Z',
      lastSeen: '2025-03-07T10:42:05Z',

      anomaly: true,

      confidence: 0.87,
    },

    {
      clusterId: 3,
      size: 41,

      label: 'Authentication activity',

      representativeMessage:
        'JWT token validated for uid:8821 — expires in 3540s',

      services: [
        'auth-service',
      ],

      logLevels: [
        'INFO',
        'DEBUG',
        'WARN',
      ],

      messages: [
        'JWT token validated for uid:8821 — expires in 3540s',
        'User session created',
        'Rate limit approaching',
      ],

      firstSeen: '2025-03-07T09:55:00Z',
      lastSeen: '2025-03-07T10:42:27Z',

      anomaly: false,

      confidence: 0.32,
    },
  ],
}


// ─── Mock RCA ─────────────────────────────────────────────────────────────────
export const MOCK_RCA = {
  mode: 'realtime',

  totalLogsAnalyzed: 1000,

  // The alert that initiated RCA
  alert: {
    id: 'a1',
    severity: 'CRITICAL',
    anomalyType: 'HIGH_ERROR_RATE',
    status: 'NEW',
    firstDetectedAt: '2025-03-07T10:40:00Z',
  },

  // ───────────────────────────────────────────────────────────────────────────
  // STAGE 1 — RULE / REALTIME DETECTION
  // ───────────────────────────────────────────────────────────────────────────
  stage1: {
    status: 'DETECTED',

    detectedAt: '2025-03-07T10:40:00Z',

    detectionMethod: 'RULE_ENGINE',

    detectionType: 'HIGH_ERROR_RATE',

    severity: 'CRITICAL',

    rootService: 'inventory-service',

    impactedServices: [
      'order-service',
      'payment-service',
      'gateway-service',
    ],

    confidence: 0.87,

    reason:
      'High error rate detected in inventory-service. Error activity increased sharply and preceded failures observed in downstream services.',

    evidence: {
      errorRatio: 0.69,
      errorCount: 138,
      totalLogs: 200,
      windowSeconds: 300,

      criticalErrors: 14,

      trafficMultiplier: 3.2,

      downstreamFailures: [
        {
          service: 'order-service',
          error: '503 Service Unavailable',
        },
        {
          service: 'payment-service',
          error: 'gateway timeout after 5000ms',
        },
        {
          service: 'gateway-service',
          error: 'circuit breaker OPEN',
        },
      ],
    },
  },

  // ───────────────────────────────────────────────────────────────────────────
  // STAGE 2 — ML ENRICHMENT
  // ───────────────────────────────────────────────────────────────────────────
  stage2: {
    status: 'ENRICHED',

    enrichedAt: '2025-03-07T10:40:30Z',

    detectionMethod: 'ML_ENRICHMENT',

    models: [
      {
        name: 'Isolation Forest',
        type: 'ISOLATION_FOREST',
        status: 'ANOMALY',
        score: 0.94,
        threshold: 0.65,
        confidence: 0.94,
      },
      {
        name: 'Semantic Clustering',
        type: 'SEMANTIC_CLUSTERING',
        status: 'MATCHED',
        clusterId: 0,
        similarity: 0.91,
        confidence: 0.91,
      },
    ],

    mlScore: 0.94,

    mlConfidence: 0.94,

    anomalyConfirmed: true,

    rootCauseConfirmed: true,

    rootService: 'inventory-service',

    impactedServices: [
      'order-service',
      'payment-service',
      'gateway-service',
    ],

    cluster: {
      clusterId: 0,

      label: 'Inventory database / connection failures',

      size: 138,

      representativeMessage:
        'Database connection pool exhausted (50/50 active connections)',

      confidence: 0.94,

      services: [
        'inventory-service',
        'order-service',
      ],
    },

    isolationForest: {
      anomaly: true,

      score: 0.94,

      threshold: 0.65,

      reason:
        'The observed error-rate, service concentration and temporal burst significantly deviate from the learned baseline.',
    },

    evidence: [
      'Inventory-service generated the earliest concentrated error burst.',
      'Database connection pool reached 50/50 active connections.',
      'Order-service subsequently produced repeated 503 failures.',
      'Gateway circuit breaker opened after repeated inventory-service failures.',
      'Semantic cluster strongly matches historical inventory/database failure patterns.',
      'Isolation Forest classified the current behavior as anomalous.',
    ],

    enrichedReason:
      'ML enrichment confirms that inventory-service is the most probable root service. Isolation Forest detected a strong behavioral deviation while semantic clustering grouped the failures into the known inventory/database failure pattern.',

    mlRca:
      'The evidence supports inventory-service as the originating failure. Database connection exhaustion appears to be the immediate technical cause, with downstream 503 responses and gateway circuit-breaker activation representing propagated effects.',
  },

  // ───────────────────────────────────────────────────────────────────────────
  // FINAL RCA
  // ───────────────────────────────────────────────────────────────────────────
  rca: {
    rootService: 'inventory-service',

    impactedServices: [
      'order-service',
      'payment-service',
      'gateway-service',
    ],

    reason:
      'Null pointer exception in InventoryController caused database connection pool exhaustion, cascading failures to downstream services.',

    confidence: 0.94,

    summary:
      'inventory-service is identified as the probable root cause with 94% confidence. A NullPointerException in InventoryController.getStock() triggered repeated failures and database connection pool exhaustion (50/50 connections). This propagated as 503 errors to order-service and gateway timeout failures in payment-service. The gateway circuit breaker subsequently entered OPEN state. Stage 2 ML enrichment independently confirmed the anomaly using Isolation Forest and semantic clustering, with the strongest matching cluster corresponding to inventory/database connection failures. Temporal analysis indicates that the inventory-service failure preceded the downstream degradation.',

    timeline: [
      {
        timestamp: '2025-03-07T10:38:42Z',
        service: 'inventory-service',
        event: 'Initial error burst detected',
        stage: 'STAGE_1',
      },
      {
        timestamp: '2025-03-07T10:39:10Z',
        service: 'inventory-service',
        event: 'Database connection pool reached capacity',
        stage: 'STAGE_1',
      },
      {
        timestamp: '2025-03-07T10:39:28Z',
        service: 'order-service',
        event: '503 responses increased',
        stage: 'STAGE_1',
      },
      {
        timestamp: '2025-03-07T10:39:44Z',
        service: 'gateway-service',
        event: 'Circuit breaker opened',
        stage: 'STAGE_1',
      },
      {
        timestamp: '2025-03-07T10:40:30Z',
        service: 'AI Service',
        event: 'Isolation Forest confirmed anomalous behavior',
        stage: 'STAGE_2',
      },
      {
        timestamp: '2025-03-07T10:40:30Z',
        service: 'AI Service',
        event: 'Semantic cluster matched inventory/database failure pattern',
        stage: 'STAGE_2',
      },
    ],

    recommendations: [
      'Investigate the InventoryController.getStock() null reference.',
      'Inspect database connection pool exhaustion and connection leaks.',
      'Review inventory-service deployment v2.4.1.',
      'Check downstream retry behavior in order-service.',
      'Verify gateway circuit-breaker configuration.',
    ],
  },
}