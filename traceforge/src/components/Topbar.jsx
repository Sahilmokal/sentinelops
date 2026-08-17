import React from 'react'
import { IconButton } from './Controls'

const PAGE_META = {
  logs: {
    title: 'Logs Explorer',
    subtitle: 'Search and browse application log streams',
    icon: '▤',
  },

  alerts: {
    title: 'Alerts Dashboard',
    subtitle: 'Investigate, acknowledge and resolve detected incidents',
    icon: '⚡',
  },

  anomalies: {
    title: 'Anomaly Monitor',
    subtitle: 'Isolation Forest and statistical anomaly detection',
    icon: '◈',
  },

  clusters: {
    title: 'Log Clustering',
    subtitle: 'Group related failures and behavioral patterns',
    icon: '◎',
  },

  rca: {
    title: 'Root Cause Analysis',
    subtitle: 'Two-stage AI failure attribution and propagation analysis',
    icon: '⬡',
  },
}

export default function Topbar({
  page,
  onRefresh,
  onMenuToggle,
}) {
  const meta = PAGE_META[page] || PAGE_META.logs

  return (
    <div className="topbar">

      {/* ─────────────────────────────────────────────── */}
      {/* LEFT */}
      {/* ─────────────────────────────────────────────── */}

      <div className="topbar-left">

        <button
          type="button"
          className="hamburger"
          onClick={onMenuToggle}
          aria-label="Open menu"
        >
          <span />
          <span />
          <span />
        </button>

        <span
          style={{
            fontSize: 15,
            opacity: 0.5,
            flexShrink: 0,
          }}
        >
          {meta.icon}
        </span>

        <div
          style={{
            minWidth: 0,
          }}
        >
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 15,
              fontWeight: 700,
              color: 'var(--text-primary)',
              letterSpacing: '-0.2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {meta.title}
          </div>

          <div
            style={{
              fontSize: 10,
              color: 'var(--text-muted)',
              marginTop: 1,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {meta.subtitle}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────── */}
      {/* RIGHT */}
      {/* ─────────────────────────────────────────────── */}

      <div className="topbar-right">

        <Chip
          color="var(--green)"
          bg="var(--green-dim)"
          border="rgba(0,255,153,0.2)"
          dot
          pulse
        >
          LIVE
        </Chip>

        <Chip
          color="var(--cyan)"
          bg="var(--cyan-dim)"
          border="rgba(0,212,255,0.2)"
          cls="topbar-chip-hide-sm"
        >
          KAFKA
        </Chip>

        <Chip
          color="var(--cyan)"
          bg="var(--cyan-dim)"
          border="rgba(0,212,255,0.2)"
          cls="topbar-chip-hide-sm"
        >
          ES
        </Chip>

        <Chip
          color="var(--purple)"
          bg="var(--purple-dim)"
          border="rgba(176,106,255,0.2)"
          cls="topbar-chip-hide-sm"
        >
          AI
        </Chip>

        <div
          style={{
            width: 1,
            height: 18,
            background: 'var(--border)',
            flexShrink: 0,
          }}
        />

        <IconButton
          onClick={onRefresh}
          title="Refresh current view"
        >
          ↻ Refresh
        </IconButton>

      </div>
    </div>
  )
}

function Chip({
  children,
  color,
  bg,
  border,
  dot = false,
  pulse = false,
  cls = '',
}) {
  return (
    <span
      className={cls}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: '1.2px',
        padding: '3px 8px',
        borderRadius: 3,
        background: bg,
        border: `1px solid ${border}`,
        color,
        fontFamily: 'var(--font-mono)',
        flexShrink: 0,
      }}
    >
      {dot && (
        <span
          style={{
            width: 5,
            height: 5,
            borderRadius: '50%',
            background: color,
            flexShrink: 0,
            ...(pulse
              ? {
                  animation:
                    'pulse-dot 2s infinite',
                }
              : {}),
          }}
        />
      )}

      {children}
    </span>
  )
}