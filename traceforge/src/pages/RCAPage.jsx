import React, {
  useCallback,
  useMemo,
} from 'react'

import {
  fetchRCAIncident,
} from '../services/api'

import {
  useAsync,
} from '../hooks/useAsync'

import {
  confidenceColor,
  confidenceLabel,
  formatTimestamp,
} from '../utils/helpers'

import {
  SeverityBadge,
  StatusBadge,
} from '../components/Badges'

import {
  Card,
  CardHeader,
} from '../components/Card'

import {
  LoadingState,
  EmptyState,
} from '../components/States'

import {
  IconButton,
} from '../components/Controls'


// ============================================================
// CONFIDENCE METER
// ============================================================

function ConfidenceMeter({
  value,
}) {

  const numericValue =
    Number(
      value ?? 0
    )

  const safeValue =
    Math.max(
      0,
      Math.min(
        1,
        Number.isFinite(
          numericValue
        )
          ? numericValue
          : 0
      )
    )

  const pct =
    Math.round(
      safeValue * 100
    )

  const color =
    confidenceColor(
      safeValue
    )

  const label =
    confidenceLabel(
      safeValue
    )

  const r = 48
  const cx = 62
  const cy = 62

  const startAngle = -210
  const totalArc = 240

  const filled =
    (
      pct / 100
    ) *
    totalArc

  const toRad =
    degrees =>
      (
        degrees *
        Math.PI
      ) / 180

  const arc =
    (
      start,
      sweep
    ) => {

      const s =
        toRad(
          start
        )

      const e =
        toRad(
          start + sweep
        )

      const x1 =
        cx +
        r *
        Math.cos(s)

      const y1 =
        cy +
        r *
        Math.sin(s)

      const x2 =
        cx +
        r *
        Math.cos(e)

      const y2 =
        cy +
        r *
        Math.sin(e)

      return `
        M ${x1} ${y1}
        A ${r} ${r} 0
        ${sweep > 180 ? 1 : 0}
        1 ${x2} ${y2}
      `
    }

  return (

    <div
      style={{
        display:
          'flex',
        flexDirection:
          'column',
        alignItems:
          'center',
        flexShrink: 0,
      }}
    >

      <svg
        width={124}
        height={88}
        viewBox="0 0 124 88"
      >

        <path
          d={
            arc(
              startAngle,
              totalArc
            )
          }
          fill="none"
          stroke="var(--border)"
          strokeWidth={7}
          strokeLinecap="round"
        />

        {pct > 0 && (

          <path
            d={
              arc(
                startAngle,
                filled
              )
            }
            fill="none"
            stroke={color}
            strokeWidth={7}
            strokeLinecap="round"
            style={{
              filter:
                `drop-shadow(0 0 4px ${color}60)`,
            }}
          />

        )}

        <text
          x={cx}
          y={cy + 7}
          textAnchor="middle"
          fill={color}
          style={{
            fontSize: 20,
            fontFamily:
              'var(--font-display)',
            fontWeight: 800,
          }}
        >
          {pct}%
        </text>

        <text
          x={cx}
          y={cy + 20}
          textAnchor="middle"
          fill="var(--text-muted)"
          style={{
            fontSize: 8,
            fontFamily:
              'var(--font-mono)',
            letterSpacing:
              '1px',
          }}
        >
          {String(
            label || ''
          ).toUpperCase()}
        </text>

      </svg>

      <div
        style={{
          fontSize: 9,
          color:
            'var(--text-muted)',
          letterSpacing:
            '1px',
          textTransform:
            'uppercase',
        }}
      >
        Confidence
      </div>

    </div>
  )
}


// ============================================================
// EVIDENCE BAR
// ============================================================

function EvidenceBar({
  label,
  value,
}) {

  const numericValue =
    Number(
      value ?? 0
    )

  const safeValue =
    Number.isFinite(
      numericValue
    )
      ? Math.max(
          0,
          Math.min(
            1,
            numericValue
          )
        )
      : 0

  const pct =
    Math.round(
      safeValue * 100
    )

  return (

    <div
      style={{
        marginBottom: 10,
      }}
    >

      <div
        style={{
          display:
            'flex',
          justifyContent:
            'space-between',
          marginBottom: 4,
        }}
      >

        <span
          style={{
            fontSize: 9,
            color:
              'var(--text-muted)',
            textTransform:
              'uppercase',
            letterSpacing:
              '1px',
          }}
        >
          {label}
        </span>

        <span
          style={{
            fontSize: 10,
            color:
              'var(--text-secondary)',
            fontFamily:
              'var(--font-mono)',
          }}
        >
          {pct}%
        </span>

      </div>

      <div
        style={{
          height: 4,
          background:
            'var(--border)',
          borderRadius: 3,
          overflow:
            'hidden',
        }}
      >

        <div
          style={{
            height: '100%',
            width:
              `${pct}%`,
            background:
              pct >= 70
                ? 'var(--green)'
                : pct >= 40
                  ? 'var(--amber)'
                  : 'var(--red)',
            borderRadius: 3,
            transition:
              'width 0.5s ease',
          }}
        />

      </div>

    </div>
  )
}


// ============================================================
// DETAIL ROW
// ============================================================

function DetailRow({
  label,
  value,
  valueColor,
}) {

  return (

    <div
      style={{
        display:
          'flex',
        justifyContent:
          'space-between',
        alignItems:
          'flex-start',
        gap: 20,
        padding:
          '7px 0',
        borderBottom:
          '1px solid rgba(26,45,64,0.45)',
      }}
    >

      <span
        style={{
          fontSize: 9,
          color:
            'var(--text-muted)',
          letterSpacing:
            '1px',
          textTransform:
            'uppercase',
          flexShrink: 0,
        }}
      >
        {label}
      </span>

      <span
        style={{
          fontSize: 10,
          color:
            valueColor ||
            'var(--text-secondary)',
          fontFamily:
            'var(--font-mono)',
          textAlign:
            'right',
          wordBreak:
            'break-word',
        }}
      >
        {value ?? '—'}
      </span>

    </div>
  )
}


// ============================================================
// SERVICE FLOW
// ============================================================

function ServiceFlow({
  rootService,
  impactedServices = [],
}) {

  const services = [
    rootService,
    ...(
      Array.isArray(
        impactedServices
      )
        ? impactedServices
        : []
    ),
  ].filter(
    Boolean
  )

  if (
    !services.length
  ) {

    return (

      <div
        style={{
          fontSize: 11,
          color:
            'var(--text-muted)',
        }}
      >
        No service propagation detected.
      </div>

    )
  }

  return (

    <div
      style={{
        display:
          'flex',
        alignItems:
          'center',
        flexWrap:
          'wrap',
        gap: 4,
      }}
    >

      {services.map(
        (
          service,
          index
        ) => (

          <React.Fragment
            key={
              `${service}-${index}`
            }
          >

            <div
              style={{
                padding:
                  '6px 10px',
                borderRadius:
                  4,
                background:
                  index === 0
                    ? 'rgba(255,61,90,0.10)'
                    : 'rgba(255,184,0,0.07)',
                border:
                  `1px solid ${
                    index === 0
                      ? 'rgba(255,61,90,0.28)'
                      : 'rgba(255,184,0,0.20)'
                  }`,
                color:
                  index === 0
                    ? 'var(--red)'
                    : 'var(--amber)',
                fontSize: 10,
                fontFamily:
                  'var(--font-mono)',
              }}
            >

              {index === 0
                ? 'ROOT · '
                : `IMPACT +${index} · `}

              {service}

            </div>

            {index <
              services.length - 1 && (

              <span
                style={{
                  color:
                    'var(--text-dim)',
                  fontSize: 12,
                  padding:
                    '0 3px',
                }}
              >
                →
              </span>

            )}

          </React.Fragment>

        )
      )}

    </div>
  )
}


// ============================================================
// CLUSTER DETAILS
// ============================================================

function ClusterDetails({
  clusters = [],
}) {

  const safeClusters =
    Array.isArray(
      clusters
    )
      ? clusters
      : []

  if (
    !safeClusters.length
  ) {

    return (

      <div
        style={{
          padding: 12,
          border:
            '1px solid var(--border)',
          borderRadius:
            'var(--radius-sm)',
          color:
            'var(--text-muted)',
          fontSize: 11,
        }}
      >
        No semantic clusters were attached
        to this RCA.
      </div>

    )
  }

  return (

    <div
      style={{
        display:
          'flex',
        flexDirection:
          'column',
        gap: 8,
      }}
    >

      {safeClusters.map(
        (
          cluster,
          index
        ) => {

          const messages =
            Array.isArray(
              cluster?.messages
            )
              ? cluster.messages
              : []

          return (

            <div
              key={
                cluster?.clusterId ??
                index
              }
              style={{
                padding: 12,
                background:
                  'var(--bg-elevated)',
                border:
                  '1px solid var(--border)',
                borderRadius:
                  'var(--radius-sm)',
              }}
            >

              <div
                style={{
                  display:
                    'flex',
                  alignItems:
                    'center',
                  justifyContent:
                    'space-between',
                  gap: 10,
                  marginBottom: 8,
                }}
              >

                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color:
                      'var(--cyan)',
                    fontFamily:
                      'var(--font-mono)',
                  }}
                >
                  CLUSTER #
                  {
                    cluster?.clusterId ??
                    index + 1
                  }
                </span>

                <span
                  style={{
                    fontSize: 9,
                    color:
                      'var(--text-muted)',
                  }}
                >
                  {
                    cluster?.occurrences ??
                    0
                  } occurrences
                </span>

              </div>

              <div
                style={{
                  fontSize: 12,
                  color:
                    'var(--text-primary)',
                  marginBottom: 8,
                  lineHeight: 1.5,
                }}
              >
                {
                  cluster?.representativeMessage ||
                  'No representative message'
                }
              </div>

              {cluster?.serviceOccurrences != null && (

                <div
                  style={{
                    fontSize: 9,
                    color:
                      'var(--text-muted)',
                    marginBottom: 8,
                  }}
                >
                  Service occurrences:{' '}

                  <span
                    style={{
                      color:
                        'var(--cyan)',
                    }}
                  >
                    {
                      cluster.serviceOccurrences
                    }
                  </span>

                </div>

              )}

              {messages.length > 0 && (

                <div
                  style={{
                    display:
                      'flex',
                    flexWrap:
                      'wrap',
                    gap: 5,
                  }}
                >

                  {messages.map(
                    (
                      message,
                      i
                    ) => (

                      <span
                        key={
                          `${message}-${i}`
                        }
                        style={{
                          padding:
                            '3px 6px',
                          borderRadius:
                            3,
                          background:
                            'rgba(0,212,255,0.04)',
                          border:
                            '1px solid rgba(0,212,255,0.12)',
                          color:
                            'var(--text-muted)',
                          fontSize: 9,
                          fontFamily:
                            'var(--font-mono)',
                        }}
                      >
                        {message}
                      </span>

                    )
                  )}

                </div>

              )}

            </div>

          )
        }
      )}

    </div>
  )
}


// ============================================================
// RCA EVIDENCE
// ============================================================

function RCAEvidence({
  rca,
  mlEvidence,
}) {

  const evidence =
    rca?.evidence ||
    mlEvidence?.evidence ||
    {}

  return (

    <Card>

      <CardHeader
        title="RCA Evidence"
        icon="◌"
      />

      <div
        style={{
          padding: 16,
        }}
      >

        <EvidenceBar
          label="Temporal"
          value={
            evidence.temporal
          }
        />

        <EvidenceBar
          label="Trace Dominance"
          value={
            evidence.traceDominance
          }
        />

        <EvidenceBar
          label="Propagation"
          value={
            evidence.propagation
          }
        />

        <EvidenceBar
          label="Semantic Cluster"
          value={
            evidence.semanticCluster
          }
        />

        <EvidenceBar
          label="ML Context"
          value={
            evidence.mlContext
          }
        />

      </div>

    </Card>
  )
}


// ============================================================
// STAGE 1 — STORED RCA
// ============================================================

function RuleStage({
  alert,
  rca,
  alertId,
}) {

  if (
    !alert &&
    !rca
  ) {
    return null
  }

  return (

    <div
      className="rca-full"
    >

      <Card>

        <div
          style={{
            height: 2,
            background:
              'linear-gradient(90deg,var(--amber),transparent)',
          }}
        />

        <CardHeader
          title="Incident RCA"
          icon="◷"
          right={

            <span
              style={{
                fontSize: 9,
                color:
                  'var(--amber)',
                fontFamily:
                  'var(--font-mono)',
              }}
            >
              BACKEND RCA
            </span>

          }
        />

        <div
          style={{
            padding: 18,
          }}
        >

          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'repeat(auto-fit,minmax(180px,1fr))',
              gap: 10,
              marginBottom: 16,
            }}
          >

            <DetailRow
              label="Alert ID"
              value={
                alertId
              }
              valueColor={
                'var(--cyan)'
              }
            />

            <DetailRow
              label="Anomaly"
              value={
                alert?.anomalyType ||
                alert?.incidentFamily
              }
            />

            <DetailRow
              label="Severity"
              value={
                alert?.severity
              }
              valueColor={
                'var(--red)'
              }
            />

            <DetailRow
              label="Status"
              value={
                alert?.status
              }
            />

            <DetailRow
              label="First Detected"
              value={
                alert?.firstDetectedAt
                  ? formatTimestamp(
                      alert.firstDetectedAt
                    )
                  : '—'
              }
            />

            <DetailRow
              label="Last Updated"
              value={
                alert?.lastUpdatedAt
                  ? formatTimestamp(
                      alert.lastUpdatedAt
                    )
                  : '—'
              }
            />

            <DetailRow
              label="Occurrences"
              value={
                alert?.occurrenceCount ??
                1
              }
            />

          </div>


          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'minmax(0,1fr) 150px',
              gap: 20,
              alignItems:
                'center',
            }}
          >

            <div>

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                  letterSpacing:
                    '1.5px',
                  textTransform:
                    'uppercase',
                  marginBottom: 7,
                }}
              >
                Root Cause
              </div>

              <div
                style={{
                  fontFamily:
                    'var(--font-display)',
                  fontSize: 22,
                  fontWeight: 800,
                  color:
                    'var(--amber)',
                  marginBottom: 8,
                }}
              >
                {
                  rca?.rootService ||
                  alert?.rootService ||
                  'Unknown'
                }
              </div>

              <div
                style={{
                  padding:
                    '10px 12px',
                  background:
                    'rgba(255,184,0,0.04)',
                  border:
                    '1px solid rgba(255,184,0,0.15)',
                  borderLeft:
                    '3px solid var(--amber)',
                  borderRadius:
                    '0 3px 3px 0',
                  fontSize: 11,
                  color:
                    'var(--text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                {
                  rca?.reason ||
                  rca?.summary ||
                  'No RCA reason available.'
                }
              </div>

              <div
                style={{
                  marginTop: 12,
                }}
              >

                <div
                  style={{
                    fontSize: 9,
                    color:
                      'var(--text-muted)',
                    textTransform:
                      'uppercase',
                    letterSpacing:
                      '1px',
                    marginBottom: 7,
                  }}
                >
                  Service Flow
                </div>

                <ServiceFlow
                  rootService={
                    rca?.rootService ||
                    alert?.rootService
                  }
                  impactedServices={
                    rca?.impactedServices ||
                    alert?.impactedServices ||
                    []
                  }
                />

              </div>

            </div>

            <ConfidenceMeter
              value={
                rca?.confidence ??
                alert?.confidence ??
                0
              }
            />

          </div>

        </div>

      </Card>

    </div>
  )
}


// ============================================================
// STAGE 2 — ML ENRICHMENT
//
// IMPORTANT:
//
// Backend response:
//
// {
//   "mlRca": ...,
//   "mlEvidence": ...,
//   "mlAnomaly": ...,
//   "mlScore": ...
// }
//
// These are TOP-LEVEL response fields.
// ============================================================

function MLEnrichmentStage({
  alert,
  mlRca,
  mlEvidence,
  mlAnomaly,
  mlScore,
}) {

  const hasML =
    !!(
      mlRca ||
      mlEvidence ||
      mlAnomaly != null ||
      mlScore != null
    )

  if (
    !hasML
  ) {

    return (

      <div
        className="rca-full"
      >

        <Card>

          <CardHeader
            title="Stage 2 · ML Enrichment"
            icon="⬡"
            right={

              <span
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                }}
              >
                NOT AVAILABLE
              </span>

            }
          />

          <div
            style={{
              padding: 22,
              textAlign:
                'center',
              color:
                'var(--text-muted)',
              fontSize: 11,
            }}
          >
            This exact incident does not have
            ML enrichment stored yet.
          </div>

        </Card>

      </div>

    )
  }

  const isolationForest =
    mlEvidence?.isolationForest ||
    {}

  const clusterResult =
    mlEvidence?.clusterResult ||
    {}

  return (

    <div
      className="rca-full"
    >

      <Card>

        <div
          style={{
            height: 2,
            background:
              'linear-gradient(90deg,var(--cyan),var(--purple),transparent)',
          }}
        />

        <CardHeader
          title="Stage 2 · ML Enrichment"
          icon="⬡"
          right={

            <span
              style={{
                fontSize: 9,
                color:
                  'var(--cyan)',
                fontFamily:
                  'var(--font-mono)',
              }}
            >
              INCIDENT ENRICHMENT
            </span>

          }
        />

        <div
          style={{
            padding: 18,
          }}
        >

          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'repeat(auto-fit,minmax(180px,1fr))',
              gap: 10,
              marginBottom: 16,
            }}
          >

            <DetailRow
              label="ML Enrichments"
              value={
                alert?.mlEnrichmentCount ??
                0
              }
            />

            <DetailRow
              label="ML Anomaly"
              value={
                mlAnomaly === true
                  ? 'ANOMALOUS'
                  : mlAnomaly === false
                    ? 'NORMAL'
                    : '—'
              }
              valueColor={
                mlAnomaly === true
                  ? 'var(--red)'
                  : mlAnomaly === false
                    ? 'var(--green)'
                    : undefined
              }
            />

            <DetailRow
              label="ML Score"
              value={
                mlScore != null
                  ? Number(
                      mlScore
                    ).toFixed(4)
                  : '—'
              }
            />

            <DetailRow
              label="Sources"
              value={
                Array.isArray(
                  alert?.sources
                )
                  ? alert.sources.join(
                      ' + '
                    )
                  : '—'
              }
            />

          </div>


          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'minmax(0,1fr) 150px',
              gap: 20,
              alignItems:
                'center',
              marginBottom: 18,
            }}
          >

            <div>

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                  letterSpacing:
                    '1.5px',
                  textTransform:
                    'uppercase',
                  marginBottom: 7,
                }}
              >
                ML Root Cause
              </div>

              <div
                style={{
                  fontFamily:
                    'var(--font-display)',
                  fontSize: 22,
                  fontWeight: 800,
                  color:
                    'var(--cyan)',
                  marginBottom: 8,
                }}
              >
                {
                  mlRca?.rootService ||
                  'Not available'
                }
              </div>

              <div
                style={{
                  padding:
                    '10px 12px',
                  background:
                    'rgba(0,212,255,0.035)',
                  border:
                    '1px solid rgba(0,212,255,0.14)',
                  borderLeft:
                    '3px solid var(--cyan)',
                  borderRadius:
                    '0 3px 3px 0',
                  fontSize: 11,
                  color:
                    'var(--text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                {
                  mlRca?.reason ||
                  mlRca?.summary ||
                  'ML did not provide a root-cause explanation.'
                }
              </div>

            </div>

            <ConfidenceMeter
              value={
                mlRca?.confidence ??
                0
              }
            />

          </div>


          <div
            style={{
              marginBottom: 18,
            }}
          >

            <div
              style={{
                fontSize: 9,
                color:
                  'var(--text-muted)',
                textTransform:
                  'uppercase',
                letterSpacing:
                  '1px',
                marginBottom: 7,
              }}
            >
              Enriched Service Flow
            </div>

            <ServiceFlow
              rootService={
                mlRca?.rootService
              }
              impactedServices={
                mlRca?.impactedServices ||
                []
              }
            />

          </div>


          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'repeat(auto-fit,minmax(260px,1fr))',
              gap: 12,
            }}
          >

            <div>

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                  textTransform:
                    'uppercase',
                  letterSpacing:
                    '1px',
                  marginBottom: 7,
                }}
              >
                Semantic Clustering
              </div>

              <ClusterDetails
                clusters={
                  mlRca?.clusters ||
                  clusterResult?.clusters ||
                  []
                }
              />

            </div>


            <div>

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                  textTransform:
                    'uppercase',
                  letterSpacing:
                    '1px',
                  marginBottom: 7,
                }}
              >
                Isolation Forest
              </div>

              <div
                style={{
                  padding: 12,
                  background:
                    'var(--bg-elevated)',
                  border:
                    '1px solid var(--border)',
                  borderRadius:
                    'var(--radius-sm)',
                }}
              >

                <DetailRow
                  label="Anomaly"
                  value={
                    mlAnomaly === true
                      ? 'YES'
                      : mlAnomaly === false
                        ? 'NO'
                        : isolationForest?.anomaly != null
                          ? isolationForest.anomaly
                            ? 'YES'
                            : 'NO'
                          : '—'
                  }
                  valueColor={
                    mlAnomaly === true ||
                    isolationForest?.anomaly === true
                      ? 'var(--red)'
                      : mlAnomaly === false ||
                        isolationForest?.anomaly === false
                        ? 'var(--green)'
                        : undefined
                  }
                />

                <DetailRow
                  label="Score"
                  value={
                    mlScore != null
                      ? Number(
                          mlScore
                        ).toFixed(4)
                      : isolationForest?.score != null
                        ? Number(
                            isolationForest.score
                          ).toFixed(4)
                        : '—'
                  }
                />

              </div>

            </div>

          </div>


          {mlRca?.summary && (

            <div
              style={{
                marginTop: 14,
                padding: 12,
                background:
                  'rgba(176,106,255,0.035)',
                border:
                  '1px solid rgba(176,106,255,0.14)',
                borderLeft:
                  '3px solid var(--purple)',
                borderRadius:
                  '0 3px 3px 0',
                fontSize: 11,
                color:
                  'var(--text-secondary)',
                lineHeight: 1.7,
              }}
            >

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--purple)',
                  letterSpacing:
                    '1px',
                  textTransform:
                    'uppercase',
                  marginBottom: 5,
                }}
              >
                ML Analysis Summary
              </div>

              {
                mlRca.summary
              }

            </div>

          )}

        </div>

      </Card>

    </div>
  )
}


// ============================================================
// RCA COMPARISON
// ============================================================

function StageComparison({
  ruleRca,
  mlRca,
}) {

  if (
    !ruleRca &&
    !mlRca
  ) {
    return null
  }

  const ruleConfidence =
    ruleRca?.confidence

  const mlConfidence =
    mlRca?.confidence

  const delta =
    ruleConfidence != null &&
    mlConfidence != null
      ? Math.round(
          (
            mlConfidence -
            ruleConfidence
          ) * 100
        )
      : null

  return (

    <div
      className="rca-full"
    >

      <Card>

        <CardHeader
          title="RCA Evolution"
          icon="↗"
        />

        <div
          style={{
            padding: 16,
          }}
        >

          <div
            style={{
              display:
                'grid',
              gridTemplateColumns:
                'repeat(auto-fit,minmax(220px,1fr))',
              gap: 10,
            }}
          >

            <div
              style={{
                padding: 14,
                background:
                  'rgba(255,184,0,0.035)',
                border:
                  '1px solid rgba(255,184,0,0.14)',
                borderRadius:
                  'var(--radius-sm)',
              }}
            >

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--amber)',
                  letterSpacing:
                    '1px',
                  textTransform:
                    'uppercase',
                  marginBottom: 8,
                }}
              >
                Stored RCA
              </div>

              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  color:
                    'var(--text-primary)',
                  fontFamily:
                    'var(--font-display)',
                }}
              >
                {
                  ruleRca?.rootService ||
                  '—'
                }
              </div>

              <div
                style={{
                  fontSize: 10,
                  color:
                    'var(--text-muted)',
                  marginTop: 4,
                }}
              >
                {
                  ruleConfidence != null
                    ? `${Math.round(
                        ruleConfidence * 100
                      )}% confidence`
                    : 'No confidence'
                }
              </div>

            </div>


            <div
              style={{
                padding: 14,
                background:
                  'rgba(0,212,255,0.035)',
                border:
                  '1px solid rgba(0,212,255,0.14)',
                borderRadius:
                  'var(--radius-sm)',
              }}
            >

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--cyan)',
                  letterSpacing:
                    '1px',
                  textTransform:
                    'uppercase',
                  marginBottom: 8,
                }}
              >
                ML Enrichment
              </div>

              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  color:
                    'var(--text-primary)',
                  fontFamily:
                    'var(--font-display)',
                }}
              >
                {
                  mlRca?.rootService ||
                  'Not enriched'
                }
              </div>

              <div
                style={{
                  fontSize: 10,
                  color:
                    'var(--text-muted)',
                  marginTop: 4,
                }}
              >
                {
                  mlConfidence != null
                    ? `${Math.round(
                        mlConfidence * 100
                      )}% confidence`
                    : 'Not enriched yet'
                }
              </div>

            </div>

          </div>


          {delta != null && (

            <div
              style={{
                marginTop: 12,
                padding:
                  '8px 10px',
                border:
                  '1px solid var(--border)',
                borderRadius:
                  'var(--radius-sm)',
                fontSize: 10,
                color:
                  delta >= 0
                    ? 'var(--green)'
                    : 'var(--amber)',
                fontFamily:
                  'var(--font-mono)',
              }}
            >
              ML confidence change:{' '}

              {delta >= 0
                ? '+'
                : ''}

              {delta}{' '}
              percentage points
            </div>

          )}

        </div>

      </Card>

    </div>
  )
}


// ============================================================
// MISSING ALERT ID
// ============================================================

function MissingAlertIdState() {

  return (

    <Card>

      <div
        style={{
          padding: 30,
          textAlign:
            'center',
        }}
      >

        <div
          style={{
            fontSize: 28,
            marginBottom: 10,
            color:
              'var(--red)',
          }}
        >
          ⚠
        </div>

        <div
          style={{
            fontSize: 14,
            fontWeight: 700,
            color:
              'var(--text-primary)',
            marginBottom: 8,
          }}
        >
          Alert ID Required
        </div>

        <div
          style={{
            fontSize: 11,
            color:
              'var(--text-muted)',
            lineHeight: 1.7,
            maxWidth: 500,
            margin:
              '0 auto',
          }}
        >
          RCA cannot run because no canonical
          backend alertId was provided.
          Select RCA from an alert in the
          Alerts page so the exact alertId is
          passed to this page.
        </div>

      </div>

    </Card>
  )
}


// ============================================================
// NO RCA AVAILABLE
// ============================================================

function NoRCAState({
  alertId,
  message,
}) {

  return (

    <Card>

      <div
        style={{
          padding: 30,
          textAlign:
            'center',
        }}
      >

        <div
          style={{
            fontSize: 28,
            marginBottom: 10,
            color:
              'var(--amber)',
          }}
        >
          ◌
        </div>

        <div
          style={{
            fontSize: 14,
            fontWeight: 700,
            color:
              'var(--text-primary)',
            marginBottom: 8,
          }}
        >
          RCA Not Available Yet
        </div>

        <div
          style={{
            fontSize: 11,
            color:
              'var(--text-muted)',
            lineHeight: 1.7,
            maxWidth: 600,
            margin:
              '0 auto',
          }}
        >
          {
            message ||
            `The backend has no stored RCA for alert ${alertId}.`
          }
        </div>

      </div>

    </Card>
  )
}


// ============================================================
// API ERROR MESSAGE
// ============================================================

function getApiErrorMessage(
  error,
  fallback
) {

  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    (
      typeof error?.response?.data ===
      'string'
        ? error.response.data
        : null
    ) ||
    error?.message ||
    fallback
  )
}


// ============================================================
// MAIN RCA PAGE
//
// FLOW:
//
// AlertsPage
//    ↓
// alert.alertId
//    ↓
// App.handleOpenRCA(alertId)
//    ↓
// RCAPage({ alertId })
//    ↓
// fetchRCAIncident(alertId)
//    ↓
// GET /rca/incident/{alertId}
//
// NO GUESSING.
// NO SEARCHING.
// NO HISTORICAL FALLBACK.
// NO MOCK RCA.
// ============================================================

export default function RCAPage({
  alertId,
}) {

  // ==========================================================
  // CANONICAL ID
  // ==========================================================

  const canonicalAlertId =
    useMemo(
      () => {

        if (
          alertId === undefined ||
          alertId === null
        ) {
          return null
        }

        const normalized =
          String(
            alertId
          ).trim()

        return normalized
          ? normalized
          : null

      },
      [
        alertId,
      ]
    )


  // ==========================================================
  // FETCH EXACT INCIDENT
  // ==========================================================

  const fetcher =
    useCallback(
      async () => {

        if (
          !canonicalAlertId
        ) {

          throw new Error(
            'Cannot run RCA: alertId is missing.'
          )
        }

        console.log(
          '=================================================='
        )

        console.log(
          '[RCA] EXACT INCIDENT REQUEST'
        )

        console.log(
          '[RCA] alertId:',
          canonicalAlertId
        )

        console.log(
          '[RCA] endpoint:',
          `/rca/incident/${canonicalAlertId}`
        )

        console.log(
          '=================================================='
        )

        try {

          const response =
            await fetchRCAIncident(
              canonicalAlertId
            )

          console.log(
            '=================================================='
          )

          console.log(
            '[RCA] BACKEND RESPONSE'
          )

          console.log(
            '[RCA] requested alertId:',
            canonicalAlertId
          )

          console.log(
            '[RCA] response:',
            response
          )

          console.log(
            '=================================================='
          )

          return response

        } catch (
          error
        ) {

          console.error(
            '[RCA] BACKEND REQUEST FAILED',
            {
              alertId:
                canonicalAlertId,
              error,
            }
          )

          throw error
        }

      },
      [
        canonicalAlertId,
      ]
    )


  const {
    data,
    loading,
    error,
    refetch,
  } = useAsync(
    fetcher,
    [
      canonicalAlertId,
    ]
  )


  // ==========================================================
  // MISSING ID
  // ==========================================================

  if (
    !canonicalAlertId
  ) {

    return (

      <div
        className="animate-fade-in"
        style={{
          display:
            'flex',
          flexDirection:
            'column',
          gap: 14,
          width: '100%',
        }}
      >

        <MissingAlertIdState />

      </div>

    )
  }


  // ==========================================================
  // BACKEND RESPONSE
  // ==========================================================

  const backendAlert =
    data?.alert ||
    null

  /*
   * IMPORTANT:
   *
   * When RCA exists, backend returns:
   *
   * data.rca
   * data.mlRca
   * data.mlEvidence
   * data.mlAnomaly
   * data.mlScore
   *
   * These are NOT necessarily nested inside data.rca.
   */

  const rca =
    data?.rca ||
    null

  const mlRca =
    data?.mlRca ||
    null

  const mlEvidence =
    data?.mlEvidence ||
    null

  const mlAnomaly =
    data?.mlAnomaly

  const mlScore =
    data?.mlScore


  // ==========================================================
  // RESPONSE ID VALIDATION
  //
  // Never render another alert's RCA.
  // ==========================================================

  const responseAlertId =
    data?.alertId ||
    backendAlert?.alertId ||
    null

  const responseIdMismatch =
    responseAlertId &&
    String(
      responseAlertId
    ) !==
      String(
        canonicalAlertId
      )


  // ==========================================================
  // RESPONSE ID MISMATCH
  // ==========================================================

  if (
    responseIdMismatch
  ) {

    return (

      <div
        className="animate-fade-in"
        style={{
          display:
            'flex',
          flexDirection:
            'column',
          gap: 14,
          width: '100%',
        }}
      >

        <Card>

          <div
            style={{
              padding: 30,
              textAlign:
                'center',
            }}
          >

            <div
              style={{
                fontSize: 28,
                marginBottom: 10,
                color:
                  'var(--red)',
              }}
            >
              ⚠
            </div>

            <div
              style={{
                fontSize: 14,
                fontWeight: 700,
                color:
                  'var(--text-primary)',
                marginBottom: 10,
              }}
            >
              RCA Identity Mismatch
            </div>

            <div
              style={{
                fontSize: 10,
                color:
                  'var(--text-muted)',
                fontFamily:
                  'var(--font-mono)',
                lineHeight: 1.8,
              }}
            >
              Requested alertId:

              <br />

              <span
                style={{
                  color:
                    'var(--cyan)',
                }}
              >
                {canonicalAlertId}
              </span>

              <br />
              <br />

              Backend returned:

              <br />

              <span
                style={{
                  color:
                    'var(--red)',
                }}
              >
                {responseAlertId}
              </span>

            </div>

            <div
              style={{
                marginTop: 14,
                fontSize: 11,
                color:
                  'var(--text-secondary)',
              }}
            >
              RCA was blocked because the backend
              response does not belong to the
              requested alert.
            </div>

          </div>

        </Card>

      </div>

    )
  }


  // ==========================================================
  // MAIN RENDER
  // ==========================================================

  return (

    <div
      className="animate-fade-in"
      style={{
        display:
          'flex',
        flexDirection:
          'column',
        gap: 14,
        width: '100%',
      }}
    >

      {/* ======================================================
          TARGET
      ====================================================== */}

      <Card>

        <div
          style={{
            padding:
              '12px 16px',
            display:
              'flex',
            alignItems:
              'center',
            justifyContent:
              'space-between',
            gap: 12,
            flexWrap:
              'wrap',
          }}
        >

          <div>

            <div
              style={{
                fontSize: 9,
                color:
                  'var(--text-muted)',
                letterSpacing:
                  '1.5px',
                textTransform:
                  'uppercase',
                marginBottom: 5,
              }}
            >
              RCA Target
            </div>

            <div
              style={{
                fontSize: 12,
                color:
                  'var(--cyan)',
                fontFamily:
                  'var(--font-mono)',
                fontWeight: 700,
              }}
            >
              ALERT · {canonicalAlertId}
            </div>

          </div>


          {backendAlert && (

            <div
              style={{
                display:
                  'flex',
                alignItems:
                  'center',
                gap: 8,
              }}
            >

              {backendAlert.severity && (

                <SeverityBadge
                  severity={
                    backendAlert.severity
                  }
                />

              )}

              {backendAlert.status && (

                <StatusBadge
                  status={
                    backendAlert.status
                  }
                />

              )}

            </div>

          )}

        </div>

      </Card>


      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (

        <div
          style={{
            padding:
              '9px 12px',
            background:
              'rgba(255,61,90,0.06)',
            border:
              '1px solid rgba(255,61,90,0.25)',
            borderLeft:
              '3px solid var(--red)',
            borderRadius:
              'var(--radius-sm)',
            color:
              'var(--red)',
            fontSize: 11,
            fontFamily:
              'var(--font-mono)',
          }}
        >
          ⚠{' '}
          {
            getApiErrorMessage(
              error,
              'Failed to load RCA.'
            )
          }
        </div>

      )}


      {/* ======================================================
          RE-ANALYZE
      ====================================================== */}

      <div
        style={{
          display:
            'flex',
          justifyContent:
            'flex-end',
        }}
      >

        <IconButton
          onClick={
            refetch
          }
          disabled={
            loading
          }
        >
          {loading
            ? 'Loading...'
            : '↻ Re-analyze'}
        </IconButton>

      </div>


      {/* ======================================================
          LOADING
      ====================================================== */}

      {loading && (

        <LoadingState
          message={
            `Loading exact RCA for ${canonicalAlertId}...`
          }
        />

      )}


      {/* ======================================================
          NO RCA
      //
      // Backend explicitly returns:
      //
      // rca: null
      // message: "RCA is not available..."
      // ====================================================== */}

      {!loading &&
        !error &&
        !rca && (

          <NoRCAState
            alertId={
              canonicalAlertId
            }
            message={
              data?.message
            }
          />

        )}


      {/* ======================================================
          RCA CONTENT
      ====================================================== */}

      {!loading &&
        !error &&
        rca && (

          <div
            className="rca-grid"
          >

            {/* ==================================================
                HERO
            ================================================== */}

            <div
              className="rca-full"
            >

              <Card>

                <div
                  style={{
                    height: 2,
                    background:
                      'linear-gradient(90deg,var(--red),var(--amber),var(--cyan),transparent)',
                  }}
                />

                <div
                  style={{
                    padding: 20,
                  }}
                >

                  <div
                    style={{
                      display:
                        'flex',
                      alignItems:
                        'flex-start',
                      justifyContent:
                        'space-between',
                      gap: 16,
                      flexWrap:
                        'wrap',
                    }}
                  >

                    <div
                      style={{
                        flex: 1,
                        minWidth: 0,
                      }}
                    >

                      <div
                        style={{
                          fontSize: 10,
                          letterSpacing:
                            '2px',
                          textTransform:
                            'uppercase',
                          color:
                            'var(--text-muted)',
                          marginBottom: 6,
                        }}
                      >
                        Probable Root Cause
                      </div>

                      <div
                        style={{
                          fontFamily:
                            'var(--font-display)',
                          fontSize:
                            'clamp(22px,3.5vw,32px)',
                          fontWeight: 800,
                          color:
                            'var(--red)',
                          lineHeight: 1,
                          marginBottom: 12,
                        }}
                      >
                        {
                          rca?.rootService ||
                          backendAlert?.rootService ||
                          mlRca?.rootService ||
                          'Unknown'
                        }
                      </div>

                      <div
                        style={{
                          padding:
                            '10px 12px',
                          background:
                            'rgba(255,61,90,0.04)',
                          border:
                            '1px solid rgba(255,61,90,0.15)',
                          borderLeft:
                            '3px solid var(--red)',
                          borderRadius:
                            '0 3px 3px 0',
                          fontSize: 12,
                          color:
                            'var(--text-primary)',
                          lineHeight: 1.65,
                        }}
                      >
                        {
                          rca?.reason ||
                          rca?.summary ||
                          mlRca?.reason ||
                          mlRca?.summary ||
                          'No RCA explanation available.'
                        }
                      </div>

                    </div>

                    <ConfidenceMeter
                      value={
                        rca?.confidence ??
                        backendAlert?.confidence ??
                        mlRca?.confidence ??
                        0
                      }
                    />

                  </div>

                </div>

              </Card>

            </div>


            {/* ==================================================
                INCIDENT DETAILS
            ================================================== */}

            <RuleStage
              alert={
                backendAlert ||
                data
              }
              rca={
                rca
              }
              alertId={
                canonicalAlertId
              }
            />


            {/* ==================================================
                ML
            ================================================== */}

            <MLEnrichmentStage
              alert={
                backendAlert ||
                data
              }
              mlRca={
                mlRca
              }
              mlEvidence={
                mlEvidence
              }
              mlAnomaly={
                mlAnomaly
              }
              mlScore={
                mlScore
              }
            />


            {/* ==================================================
                RCA EVOLUTION
            ================================================== */}

            {(rca ||
              mlRca) && (

              <StageComparison
                ruleRca={
                  rca
                }
                mlRca={
                  mlRca
                }
              />

            )}


            {/* ==================================================
                EVIDENCE
            ================================================== */}

            <div
              className="rca-full"
            >

              <RCAEvidence
                rca={
                  rca
                }
                mlEvidence={
                  mlEvidence
                }
              />

            </div>


            {/* ==================================================
                SUMMARY
            ================================================== */}

            {(rca?.summary ||
              mlRca?.summary) && (

              <div
                className="rca-full"
              >

                <Card>

                  <CardHeader
                    title="Analysis Summary"
                    icon="⬡"
                  />

                  <div
                    style={{
                      padding: 18,
                      fontSize: 12,
                      color:
                        'var(--text-secondary)',
                      lineHeight: 1.85,
                      fontFamily:
                        'var(--font-mono)',
                    }}
                  >
                    {
                      rca?.summary ||
                      mlRca?.summary
                    }
                  </div>

                </Card>

              </div>

            )}


            {/* ==================================================
                SERVICE IMPACT
            ================================================== */}

            <div
              className="rca-full"
            >

              <Card>

                <CardHeader
                  title="Service Impact Map"
                  icon="◈"
                />

                <div
                  style={{
                    padding: 14,
                  }}
                >

                  <ServiceFlow
                    rootService={
                      rca?.rootService ||
                      mlRca?.rootService ||
                      backendAlert?.rootService
                    }
                    impactedServices={
                      rca?.impactedServices ||
                      mlRca?.impactedServices ||
                      backendAlert?.impactedServices ||
                      []
                    }
                  />

                </div>

              </Card>

            </div>


            {/* ==================================================
                INCIDENT METADATA
            ================================================== */}

            <div
              className="rca-full"
            >

              <Card>

                <CardHeader
                  title="Incident Metadata"
                  icon="◫"
                />

                <div
                  style={{
                    padding: 16,
                  }}
                >

                  <DetailRow
                    label="Alert ID"
                    value={
                      canonicalAlertId
                    }
                    valueColor={
                      'var(--cyan)'
                    }
                  />

                  <DetailRow
                    label="Incident Family"
                    value={
                      data?.incidentFamily ||
                      backendAlert?.incidentFamily
                    }
                  />

                  <DetailRow
                    label="Anomaly Type"
                    value={
                      data?.anomalyType ||
                      backendAlert?.anomalyType
                    }
                  />

                  <DetailRow
                    label="Severity"
                    value={
                      data?.severity ||
                      backendAlert?.severity
                    }
                    valueColor={
                      'var(--red)'
                    }
                  />

                  <DetailRow
                    label="Status"
                    value={
                      data?.status ||
                      backendAlert?.status
                    }
                  />

                  <DetailRow
                    label="Root Service"
                    value={
                      data?.rootService ||
                      backendAlert?.rootService
                    }
                    valueColor={
                      'var(--cyan)'
                    }
                  />

                  <DetailRow
                    label="Occurrence Count"
                    value={
                      data?.occurrenceCount ??
                      backendAlert?.occurrenceCount ??
                      0
                    }
                  />

                  <DetailRow
                    label="First Detected"
                    value={
                      data?.firstDetectedAt
                        ? formatTimestamp(
                            data.firstDetectedAt
                          )
                        : backendAlert?.firstDetectedAt
                          ? formatTimestamp(
                              backendAlert.firstDetectedAt
                            )
                          : '—'
                    }
                  />

                  <DetailRow
                    label="Last Updated"
                    value={
                      data?.lastUpdatedAt
                        ? formatTimestamp(
                            data.lastUpdatedAt
                          )
                        : backendAlert?.lastUpdatedAt
                          ? formatTimestamp(
                              backendAlert.lastUpdatedAt
                            )
                          : '—'
                    }
                  />

                </div>

              </Card>

            </div>


            {/* ==================================================
                RAW BACKEND RESPONSE
            ================================================== */}

            <div
              className="rca-full"
            >

              <Card>

                <CardHeader
                  title="Backend RCA Response"
                  icon="{}"
                  right={

                    <span
                      style={{
                        fontSize: 9,
                        color:
                          'var(--cyan)',
                        fontFamily:
                          'var(--font-mono)',
                      }}
                    >
                      {canonicalAlertId}
                    </span>

                  }
                />

                <details
                  style={{
                    padding: 14,
                  }}
                >

                  <summary
                    style={{
                      cursor:
                        'pointer',
                      fontSize: 10,
                      color:
                        'var(--text-muted)',
                      fontFamily:
                        'var(--font-mono)',
                    }}
                  >
                    Inspect backend response
                  </summary>

                  <pre
                    style={{
                      marginTop: 12,
                      padding: 12,
                      background:
                        'var(--bg-elevated)',
                      border:
                        '1px solid var(--border)',
                      borderRadius:
                        'var(--radius-sm)',
                      overflow:
                        'auto',
                      maxHeight: 400,
                      fontSize: 9,
                      color:
                        'var(--text-secondary)',
                      fontFamily:
                        'var(--font-mono)',
                    }}
                  >
                    {
                      JSON.stringify(
                        data,
                        null,
                        2
                      )
                    }
                  </pre>

                </details>

              </Card>

            </div>

          </div>

        )}

    </div>
  )
}