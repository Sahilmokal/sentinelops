import React from 'react'
import { useClock } from '../hooks/useAsync'
import { formatTime } from '../utils/helpers'

const NAV_ITEMS = [
  {
    id: 'logs',
    label: 'Logs Explorer',
    icon: '▤',
  },
  {
    id: 'alerts',
    label: 'Alerts',
    icon: '⚡',
  },
  {
    id: 'anomalies',
    label: 'Anomalies',
    icon: '◈',
  },
  {
    id: 'clusters',
    label: 'Clustering',
    icon: '◎',
  },
  {
    id: 'rca',
    label: 'Root Cause',
    icon: '⬡',
  },
]

const INFRASTRUCTURE = [
  {
    label: 'Kafka',
    detail: 'broker:9092',
  },
  {
    label: 'Elasticsearch',
    detail: 'logs',
  },
  {
    label: 'FastAPI AI',
    detail: 'port:8001',
  },
]

export default function Sidebar({
  activePage,
  onNavigate,
  onLogout,
}) {
  const clock = useClock()

  const username =
    localStorage.getItem('username') || 'operator'

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: 'var(--bg-panel)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >

      {/* ───────────────────────────────────────────────────── */}
      {/* EDGE GLOW */}
      {/* ───────────────────────────────────────────────────── */}

      <div
        style={{
          position: 'absolute',
          top: 0,
          right: -1,
          bottom: 0,
          width: 1,
          background:
            'linear-gradient(180deg, transparent 0%, var(--cyan) 30%, var(--cyan) 70%, transparent 100%)',
          opacity: 0.15,
          pointerEvents: 'none',
        }}
      />

      {/* ───────────────────────────────────────────────────── */}
      {/* BRAND */}
      {/* ───────────────────────────────────────────────────── */}

      <div
        style={{
          padding: '20px 18px 16px',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            marginBottom: 10,
          }}
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 32 32"
            fill="none"
            style={{ flexShrink: 0 }}
          >
            <rect
              width="32"
              height="32"
              rx="6"
              fill="var(--bg-elevated)"
            />

            <path
              d="M6 10L16 6L26 10L26 22L16 26L6 22Z"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.5"
            />

            <circle
              cx="16"
              cy="16"
              r="3"
              fill="var(--cyan)"
            />

            <line
              x1="16"
              y1="6"
              x2="16"
              y2="13"
              stroke="var(--cyan)"
              strokeWidth="1"
              opacity="0.5"
            />

            <line
              x1="16"
              y1="19"
              x2="16"
              y2="26"
              stroke="var(--cyan)"
              strokeWidth="1"
              opacity="0.5"
            />
          </svg>

          <div>
            <div
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 16,
                fontWeight: 800,
                letterSpacing: '-0.3px',
              }}
            >
              Trace
              <span style={{ color: 'var(--cyan)' }}>
                Forge
              </span>
            </div>

            <div
              style={{
                fontSize: 9,
                color: 'var(--text-muted)',
                letterSpacing: '1.8px',
                textTransform: 'uppercase',
              }}
            >
              AI OBSERVABILITY
            </div>
          </div>
        </div>

        {/* System status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '5px 10px',
            background: 'var(--green-dim)',
            border:
              '1px solid rgba(0,255,153,0.15)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--green)',
              flexShrink: 0,
              animation: 'pulse-dot 2s infinite',
            }}
          />

          <span
            style={{
              fontSize: 10,
              color: 'var(--green)',
              letterSpacing: '0.5px',
            }}
          >
            Systems Nominal
          </span>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────── */}
      {/* NAVIGATION */}
      {/* ───────────────────────────────────────────────────── */}

      <nav
        style={{
          padding: '10px 0',
          flex: 1,
          overflow: 'auto',
        }}
      >
        <div
          style={{
            fontSize: 9,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            padding: '6px 18px 8px',
          }}
        >
          Monitoring
        </div>

        {NAV_ITEMS.map((item) => {
          const active = activePage === item.id

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                width: '100%',
                padding: '9px 18px',
                background: active
                  ? 'var(--cyan-dim)'
                  : 'transparent',
                border: 'none',
                borderLeft:
                  `2px solid ${
                    active
                      ? 'var(--cyan)'
                      : 'transparent'
                  }`,
                color: active
                  ? 'var(--cyan)'
                  : 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s',
                textAlign: 'left',
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.background =
                    'var(--bg-hover)'

                  e.currentTarget.style.color =
                    'var(--text-primary)'
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.background =
                    'transparent'

                  e.currentTarget.style.color =
                    'var(--text-secondary)'
                }
              }}
            >
              <span
                style={{
                  fontSize: 14,
                  width: 18,
                  textAlign: 'center',
                  flexShrink: 0,
                }}
              >
                {item.icon}
              </span>

              <span style={{ flex: 1 }}>
                {item.label}
              </span>

              {item.id === 'alerts' && (
                <span
                  style={{
                    fontSize: 8,
                    padding: '1px 5px',
                    color: 'var(--text-muted)',
                    border:
                      '1px solid var(--border)',
                    borderRadius: 3,
                  }}
                >
                  LIVE
                </span>
              )}
            </button>
          )
        })}

        {/* ─────────────────────────────────────────────── */}
        {/* DETECTION PIPELINE */}
        {/* ─────────────────────────────────────────────── */}

        <div
          style={{
            height: 1,
            background: 'var(--border)',
            margin: '10px 0',
          }}
        />

        <div
          style={{
            fontSize: 9,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            padding: '6px 18px 8px',
          }}
        >
          Detection Pipeline
        </div>

        <PipelineItem
          number="01"
          label="Log Ingestion"
          detail="Kafka → ES"
        />

        <PipelineItem
          number="02"
          label="Anomaly Detection"
          detail="Isolation Forest"
        />

        <PipelineItem
          number="03"
          label="Log Clustering"
          detail="Pattern Groups"
        />

        <PipelineItem
          number="04"
          label="RCA"
          detail="Two Stage"
        />

        {/* ─────────────────────────────────────────────── */}
        {/* INFRASTRUCTURE */}
        {/* ─────────────────────────────────────────────── */}

        <div
          style={{
            height: 1,
            background: 'var(--border)',
            margin: '10px 0',
          }}
        />

        <div
          style={{
            fontSize: 9,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            padding: '6px 18px 8px',
          }}
        >
          Infrastructure
        </div>

        {INFRASTRUCTURE.map(
          ({ label, detail }) => (
            <div
              key={label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 18px',
                fontSize: 11,
              }}
            >
              <span
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: '50%',
                  flexShrink: 0,
                  background: 'var(--green)',
                  boxShadow:
                    '0 0 5px rgba(0,255,153,0.35)',
                }}
              />

              <span
                style={{
                  color: 'var(--text-secondary)',
                  flex: 1,
                }}
              >
                {label}
              </span>

              <span
                style={{
                  fontSize: 9,
                  color: 'var(--text-muted)',
                }}
              >
                {detail}
              </span>
            </div>
          )
        )}
      </nav>

      {/* ───────────────────────────────────────────────────── */}
      {/* USER / LOGOUT */}
      {/* ───────────────────────────────────────────────────── */}

      <div
        style={{
          padding: '10px 18px',
          borderTop: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 8,
          }}
        >
          <div
            style={{
              width: 25,
              height: 25,
              borderRadius: 5,
              background: 'var(--cyan-dim)',
              border:
                '1px solid rgba(0,212,255,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--cyan)',
              fontSize: 10,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            {username.charAt(0).toUpperCase()}
          </div>

          <div
            style={{
              minWidth: 0,
              flex: 1,
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: 'var(--text-primary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {username}
            </div>

            <div
              style={{
                fontSize: 8,
                color: 'var(--text-muted)',
                letterSpacing: '0.8px',
                textTransform: 'uppercase',
              }}
            >
              Operator
            </div>
          </div>

          <button
            type="button"
            onClick={onLogout}
            title="Logout"
            style={{
              padding: '4px 7px',
              background: 'transparent',
              border:
                '1px solid var(--border)',
              borderRadius: 3,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color =
                'var(--red)'
              e.currentTarget.style.borderColor =
                'rgba(255,61,90,0.3)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color =
                'var(--text-muted)'
              e.currentTarget.style.borderColor =
                'var(--border)'
            }}
          >
            EXIT
          </button>
        </div>

        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            color: 'var(--cyan)',
            opacity: 0.5,
            marginBottom: 2,
          }}
        >
          {formatTime(clock)}
        </div>

        <div
          style={{
            fontSize: 9,
            color: 'var(--text-muted)',
          }}
        >
          TraceForge AI v2.4.1
        </div>

        <div
          style={{
            fontSize: 8,
            color: 'var(--text-muted)',
            opacity: 0.5,
            marginTop: 1,
          }}
        >
          © 2025 TraceForge
        </div>
      </div>
    </div>
  )
}

function PipelineItem({
  number,
  label,
  detail,
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 18px',
      }}
    >
      <span
        style={{
          width: 20,
          height: 18,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border:
            '1px solid var(--border)',
          borderRadius: 3,
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: 8,
          flexShrink: 0,
        }}
      >
        {number}
      </span>

      <div
        style={{
          minWidth: 0,
          flex: 1,
        }}
      >
        <div
          style={{
            fontSize: 10,
            color: 'var(--text-secondary)',
          }}
        >
          {label}
        </div>

        <div
          style={{
            fontSize: 8,
            color: 'var(--text-muted)',
            marginTop: 1,
          }}
        >
          {detail}
        </div>
      </div>
    </div>
  )
}