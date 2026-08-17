import React, {
  useState,
  useCallback,
} from 'react'

import {
  fetchAlerts,
  acknowledgeAlert,
  resolveAlert,
} from '../services/api'

import { useAsync } from '../hooks/useAsync'
import { timeAgo } from '../utils/helpers'

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
  FilterSelect,
  Pagination,
  ActionButton,
  ConfidenceBar,
} from '../components/Controls'


// ============================================================
// FILTER OPTIONS
// ============================================================

const SEVERITY_OPTIONS = [
  {
    value: 'CRITICAL',
    label: 'CRITICAL',
  },
  {
    value: 'HIGH',
    label: 'HIGH',
  },
  {
    value: 'MEDIUM',
    label: 'MEDIUM',
  },
  {
    value: 'LOW',
    label: 'LOW',
  },
]

const STATUS_OPTIONS = [
  {
    value: 'NEW',
    label: 'NEW',
  },
  {
    value: 'ACKNOWLEDGED',
    label: 'ACKNOWLEDGED',
  },
  {
    value: 'RESOLVED',
    label: 'RESOLVED',
  },
]


// ============================================================
// PAGE
//
// IMPORTANT:
//
// `onOpenRCA` must receive the exact backend alertId.
//
// Example:
//
// <AlertsPage
//   onOpenRCA={alertId => {
//     setSelectedAlertId(alertId)
//     setPage('rca')
//   }}
// />
//
// There is NO ID GUESSING here.
// ============================================================

export default function AlertsPage({
  onOpenRCA,
}) {

  const [page, setPage] =
    useState(1)

  const [status, setStatus] =
    useState('')

  const [severity, setSeverity] =
    useState('')

  const [actionLoading, setActionLoading] =
    useState({})

  const [actionError, setActionError] =
    useState('')

  const [successMessage, setSuccessMessage] =
    useState('')


  // ============================================================
  // FETCH ALERTS
  //
  // Backend is the source of truth.
  //
  // IMPORTANT:
  // This page only displays the alerts returned by /alerts.
  // It does NOT search other alerts to determine identity.
  // ============================================================

  const fetcher = useCallback(
    async () => {

      const params = {
        page,
        size: 20,
      }

      if (status) {
        params.status = status
      }

      if (severity) {
        params.severity = severity
      }

      console.log(
        '=================================================='
      )

      console.log(
        '[Alerts] GET /alerts'
      )

      console.log(
        '[Alerts] params:',
        params
      )

      const response =
        await fetchAlerts(
          params
        )

      console.log(
        '[Alerts] backend response:',
        response
      )

      console.log(
        '=================================================='
      )

      return response
    },
    [
      page,
      status,
      severity,
    ]
  )


  const {
    data,
    loading,
    refetch,
  } = useAsync(
    fetcher,
    [
      page,
      status,
      severity,
    ]
  )


  // ============================================================
  // DATA
  // ============================================================

  const alerts =
    Array.isArray(data?.data)
      ? data.data
      : []


  // ============================================================
  // CANONICAL ALERT ID
  //
  // DO NOT FALL BACK TO:
  //   alert.id
  //   alert._id
  //
  // The backend contract is alert.alertId.
  // ============================================================

  const getAlertId = useCallback(
    alert => {

      const alertId =
        alert?.alertId

      if (
        alertId === undefined ||
        alertId === null ||
        String(alertId).trim() === ''
      ) {

        console.error(
          '[Alerts] INVALID ALERT: backend alertId is missing.',
          alert
        )

        return null
      }

      return String(
        alertId
      )
    },
    []
  )


  // ============================================================
  // COUNTS
  //
  // These counts represent the currently loaded page.
  //
  // We do NOT calculate fake global counts from pagination.
  // If the backend later supplies aggregate counts, use those
  // backend values directly.
  // ============================================================

  const newCount =
    alerts.filter(
      alert =>
        alert.status === 'NEW'
    ).length

  const ackCount =
    alerts.filter(
      alert =>
        alert.status === 'ACKNOWLEDGED'
    ).length

  const critCount =
    alerts.filter(
      alert =>
        alert.severity === 'CRITICAL'
    ).length

  const totalAlerts =
    Number(
      data?.total ?? 0
    )

  const pageSize =
    Number(
      data?.size ?? 20
    )

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        totalAlerts /
        pageSize
      )
    )


  // ============================================================
  // OPEN RCA
  //
  // THIS IS THE IMPORTANT PART.
  //
  // RCA receives the exact alertId from the exact alert row.
  //
  // No:
  //   - matching by service
  //   - matching by timestamp
  //   - matching by anomaly type
  //   - searching another alert
  //   - guessing an ID
  // ============================================================

  const handleOpenRCA = useCallback(
    alert => {

      const alertId =
        getAlertId(
          alert
        )

      console.log(
        '=================================================='
      )

      console.log(
        '[Alerts] RCA CLICKED'
      )

      console.log(
        '[Alerts] exact alert object:',
        alert
      )

      console.log(
        '[Alerts] exact backend alertId:',
        alertId
      )

      console.log(
        '=================================================='
      )


      if (!alertId) {

        setActionError(
          'RCA cannot be opened because this alert has no backend alertId.'
        )

        return
      }


      setActionError('')
      setSuccessMessage('')


      if (
        typeof onOpenRCA !==
        'function'
      ) {

        console.error(
          '[Alerts] onOpenRCA callback is not configured.'
        )

        setActionError(
          'RCA navigation is not configured.'
        )

        return
      }


      /*
       * Pass ONLY the canonical alertId.
       */

      onOpenRCA(
        alertId
      )

    },
    [
      getAlertId,
      onOpenRCA,
    ]
  )


  // ============================================================
  // ACKNOWLEDGE
  // ============================================================

  const handleAcknowledge =
    async alert => {

      const alertId =
        getAlertId(
          alert
        )


      console.log(
        '=================================================='
      )

      console.log(
        '[Alerts] ACK CLICKED'
      )

      console.log(
        '[Alerts] alert:',
        alert
      )

      console.log(
        '[Alerts] canonical alertId:',
        alertId
      )

      console.log(
        '[Alerts] current status:',
        alert?.status
      )

      console.log(
        '=================================================='
      )


      if (!alertId) {

        setActionError(
          'ACK failed: backend alertId is missing.'
        )

        return
      }


      // --------------------------------------------------------
      // Backend lifecycle:
      //
      // NEW -> ACKNOWLEDGED
      // --------------------------------------------------------

      if (
        alert.status !== 'NEW'
      ) {

        setActionError(
          `ACK is not allowed for alert ${alertId} because its current status is ${alert.status}.`
        )

        return
      }


      if (
        actionLoading[alertId]
      ) {

        console.warn(
          '[Alerts] ACK already in progress:',
          alertId
        )

        return
      }


      setActionError('')
      setSuccessMessage('')


      setActionLoading(
        current => ({
          ...current,
          [alertId]: 'ack',
        })
      )


      try {

        console.log(
          `[Alerts] POST /alerts/${alertId}/ack`
        )


        const response =
          await acknowledgeAlert(
            alertId
          )


        console.log(
          '[Alerts] ACK response:',
          response
        )


        if (
          response?.updated === false ||
          response?.status === 'NOT_FOUND'
        ) {

          throw new Error(
            response?.message ||
            'Backend rejected ACK.'
          )
        }


        if (
          response?.status !==
          'ACKNOWLEDGED'
        ) {

          throw new Error(
            response?.message ||
            `Unexpected ACK response status: ${response?.status}`
          )
        }


        setSuccessMessage(
          `Alert ${alertId} acknowledged.`
        )


        /*
         * Backend remains source of truth.
         * Never mutate the row locally and assume success.
         */

        await refetch()

      } catch (error) {

        console.error(
          '[Alerts] ACK FAILED:',
          error
        )

        setActionError(
          getApiErrorMessage(
            error,
            'Failed to acknowledge alert.'
          )
        )

      } finally {

        setActionLoading(
          current => {

            const next = {
              ...current,
            }

            delete next[alertId]

            return next
          }
        )
      }
    }


  // ============================================================
  // RESOLVE
  // ============================================================

  const handleResolve =
    async alert => {

      const alertId =
        getAlertId(
          alert
        )


      console.log(
        '=================================================='
      )

      console.log(
        '[Alerts] RESOLVE CLICKED'
      )

      console.log(
        '[Alerts] alert:',
        alert
      )

      console.log(
        '[Alerts] canonical alertId:',
        alertId
      )

      console.log(
        '[Alerts] current status:',
        alert?.status
      )

      console.log(
        '=================================================='
      )


      if (!alertId) {

        setActionError(
          'RESOLVE failed: backend alertId is missing.'
        )

        return
      }


      // --------------------------------------------------------
      // Backend lifecycle:
      //
      // ACKNOWLEDGED -> RESOLVED
      //
      // NEW -> RESOLVED is not allowed.
      // --------------------------------------------------------

      if (
        alert.status !==
        'ACKNOWLEDGED'
      ) {

        setActionError(
          `RESOLVE is not allowed for alert ${alertId} because its current status is ${alert.status}.`
        )

        return
      }


      if (
        actionLoading[alertId]
      ) {

        console.warn(
          '[Alerts] RESOLVE already in progress:',
          alertId
        )

        return
      }


      setActionError('')
      setSuccessMessage('')


      setActionLoading(
        current => ({
          ...current,
          [alertId]: 'resolve',
        })
      )


      try {

        console.log(
          `[Alerts] POST /alerts/${alertId}/resolve`
        )


        const response =
          await resolveAlert(
            alertId
          )


        console.log(
          '[Alerts] RESOLVE response:',
          response
        )


        if (
          response?.updated === false ||
          response?.status === 'NOT_FOUND'
        ) {

          throw new Error(
            response?.message ||
            'Backend rejected RESOLVE.'
          )
        }


        if (
          response?.status !==
          'RESOLVED'
        ) {

          throw new Error(
            response?.message ||
            `Unexpected RESOLVE response status: ${response?.status}`
          )
        }


        setSuccessMessage(
          `Alert ${alertId} resolved.`
        )


        /*
         * Again, backend is source of truth.
         */

        await refetch()

      } catch (error) {

        console.error(
          '[Alerts] RESOLVE FAILED:',
          error
        )

        setActionError(
          getApiErrorMessage(
            error,
            'Failed to resolve alert.'
          )
        )

      } finally {

        setActionLoading(
          current => {

            const next = {
              ...current,
            }

            delete next[alertId]

            return next
          }
        )
      }
    }


  // ============================================================
  // STATUS FILTER
  // ============================================================

  const changeStatus =
    value => {

      console.log(
        '[Alerts] Status filter:',
        value
      )

      setStatus(
        value
      )

      setPage(1)

      setActionError('')
      setSuccessMessage('')
    }


  // ============================================================
  // SEVERITY FILTER
  // ============================================================

  const changeSeverity =
    value => {

      console.log(
        '[Alerts] Severity filter:',
        value
      )

      setSeverity(
        value
      )

      setPage(1)

      setActionError('')
      setSuccessMessage('')
    }


  // ============================================================
  // REFRESH
  // ============================================================

  const handleRefresh =
    async () => {

      setActionError('')
      setSuccessMessage('')

      console.log(
        '[Alerts] Manual refresh'
      )

      await refetch()
    }


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        width: '100%',
      }}
    >

      {/* ======================================================
          ERROR
      ====================================================== */}

      {actionError && (

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
          ⚠ {actionError}
        </div>

      )}


      {/* ======================================================
          SUCCESS
      ====================================================== */}

      {successMessage && (

        <div
          style={{
            padding:
              '9px 12px',
            background:
              'rgba(0,255,153,0.05)',
            border:
              '1px solid rgba(0,255,153,0.20)',
            borderLeft:
              '3px solid var(--green)',
            borderRadius:
              'var(--radius-sm)',
            color:
              'var(--green)',
            fontSize: 11,
            fontFamily:
              'var(--font-mono)',
          }}
        >
          ✓ {successMessage}
        </div>

      )}


      {/* ======================================================
          STATS
      ====================================================== */}

      <div className="stat-grid-4">

        {[
          {
            label:
              'Active Alerts',
            value:
              newCount,
            color:
              'var(--red)',
          },
          {
            label:
              'Acknowledged',
            value:
              ackCount,
            color:
              'var(--amber)',
          },
          {
            label:
              'Critical',
            value:
              critCount,
            color:
              'var(--red)',
          },
          {
            label:
              'Total Alerts',
            value:
              totalAlerts,
            color:
              'var(--text-primary)',
          },
        ].map(
          stat => (

            <div
              key={
                stat.label
              }
              style={{
                background:
                  'var(--bg-card)',
                border:
                  '1px solid var(--border)',
                borderRadius:
                  'var(--radius-md)',
                padding:
                  '12px 16px',
              }}
            >

              <div
                style={{
                  fontFamily:
                    'var(--font-display)',
                  fontSize: 22,
                  fontWeight: 800,
                  color:
                    stat.color,
                  lineHeight: 1,
                }}
              >
                {stat.value}
              </div>

              <div
                style={{
                  fontSize: 9,
                  color:
                    'var(--text-muted)',
                  letterSpacing:
                    '1px',
                  textTransform:
                    'uppercase',
                  marginTop: 4,
                }}
              >
                {stat.label}
              </div>

            </div>

          )
        )}

      </div>


      {/* ======================================================
          FILTERS
      ====================================================== */}

      <div
        className="filter-bar"
      >

        <FilterSelect
          value={
            status
          }
          onChange={
            changeStatus
          }
          options={
            STATUS_OPTIONS
          }
          placeholder="All Statuses"
        />

        <FilterSelect
          value={
            severity
          }
          onChange={
            changeSeverity
          }
          options={
            SEVERITY_OPTIONS
          }
          placeholder="All Severities"
        />

        <div
          style={{
            marginLeft:
              'auto',
          }}
        >

          <ActionButton
            onClick={
              handleRefresh
            }
            variant="default"
            disabled={
              loading
            }
          >
            {loading
              ? 'Refreshing...'
              : '↻ Refresh'}
          </ActionButton>

        </div>

      </div>


      {/* ======================================================
          ALERT TABLE
      ====================================================== */}

      <Card>

        <CardHeader
          title="Alert Feed"
          icon="⚡"
          right={

            <span
              style={{
                fontSize: 10,
                color:
                  'var(--text-muted)',
              }}
            >

              {newCount > 0 && (

                <span
                  style={{
                    color:
                      'var(--red)',
                    marginRight: 8,
                  }}
                >
                  ● {newCount} new
                </span>

              )}

              {totalAlerts}
              {' '}
              total

            </span>

          }
        />


        {/* ====================================================
            LOADING
        ==================================================== */}

        {loading && (

          <LoadingState
            message="Loading alerts..."
          />

        )}


        {/* ====================================================
            EMPTY
        ==================================================== */}

        {!loading &&
          alerts.length === 0 && (

            <EmptyState
              icon="⚡"
              message="No alerts found"
              sub={
                status ||
                severity
                  ? 'Try changing the filters.'
                  : 'All clear!'
              }
            />

          )}


        {/* ====================================================
            TABLE
        ==================================================== */}

        {!loading &&
          alerts.length > 0 && (

            <div
              className="table-scroll"
            >

              <table
                style={{
                  width:
                    '100%',
                  borderCollapse:
                    'collapse',
                }}
              >

                <thead>

                  <tr>

                    {[
                      'Severity',
                      'Type',
                      'Root Service',
                      'Status',
                      'Confidence',
                      'Detected',
                      'Actions',
                    ].map(
                      (
                        heading,
                        index
                      ) => (

                        <th
                          key={
                            heading
                          }
                          className={
                            index === 1 ||
                            index === 4 ||
                            index === 5
                              ? 'col-hide-xs'
                              : ''
                          }
                          style={{
                            fontSize: 9,
                            fontWeight: 700,
                            letterSpacing:
                              '1.5px',
                            textTransform:
                              'uppercase',
                            color:
                              'var(--text-muted)',
                            padding:
                              '9px 12px',
                            textAlign:
                              'left',
                            borderBottom:
                              '1px solid var(--border)',
                            background:
                              'rgba(255,255,255,0.012)',
                            whiteSpace:
                              'nowrap',
                          }}
                        >
                          {
                            heading
                          }
                        </th>

                      )
                    )}

                  </tr>

                </thead>


                <tbody>

                  {alerts.map(
                    (
                      alert,
                      index
                    ) => {

                      /*
                       * CANONICAL ID.
                       *
                       * If this is null, RCA/ACK/RESOLVE
                       * will refuse to operate.
                       */
                      const alertId =
                        getAlertId(
                          alert
                        )


                      const loadingAction =
                        alertId
                          ? actionLoading[
                              alertId
                            ]
                          : null


                      const isNew =
                        alert.status ===
                        'NEW'

                      const isAcknowledged =
                        alert.status ===
                        'ACKNOWLEDGED'

                      const isResolved =
                        alert.status ===
                        'RESOLVED'

                      const isLoading =
                        !!loadingAction


                      /*
                       * An alert without a backend ID
                       * is invalid data.
                       *
                       * We still render it so the operator
                       * can see the backend problem, but we
                       * disable operations against it.
                       */

                      const invalidIdentity =
                        !alertId


                      return (

                        <tr
                          key={
                            alertId ||
                            `invalid-alert-${index}`
                          }

                          onMouseEnter={
                            e => {
                              e.currentTarget.style.background =
                                'var(--bg-hover)'
                            }
                          }

                          onMouseLeave={
                            e => {
                              e.currentTarget.style.background =
                                'transparent'
                            }
                          }
                        >

                          {/* =================================================
                              SEVERITY
                          ================================================= */}

                          <td
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                            }}
                          >

                            <SeverityBadge
                              severity={
                                alert.severity
                              }
                            />

                          </td>


                          {/* =================================================
                              TYPE
                          ================================================= */}

                          <td
                            className="col-hide-xs"
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                              whiteSpace:
                                'nowrap',
                            }}
                          >

                            <span
                              style={{
                                fontSize: 11,
                                color:
                                  'var(--text-secondary)',
                              }}
                            >
                              {(
                                alert.anomalyType ||
                                alert.incidentFamily ||
                                'ANOMALY'
                              ).replace(
                                /_/g,
                                ' '
                              )}
                            </span>

                          </td>


                          {/* =================================================
                              ROOT SERVICE
                          ================================================= */}

                          <td
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                              whiteSpace:
                                'nowrap',
                            }}
                          >

                            <span
                              style={{
                                fontSize: 11,
                                color:
                                  'var(--cyan)',
                                fontFamily:
                                  'var(--font-mono)',
                              }}
                            >
                              {alert.rootService ||
                                'unknown-service'}
                            </span>

                          </td>


                          {/* =================================================
                              STATUS
                          ================================================= */}

                          <td
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                            }}
                          >

                            <StatusBadge
                              status={
                                alert.status
                              }
                            />

                          </td>


                          {/* =================================================
                              CONFIDENCE
                          ================================================= */}

                          <td
                            className="col-hide-xs"
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                            }}
                          >

                            <ConfidenceBar
                              value={
                                alert.confidence ??
                                0
                              }
                              width={60}
                            />

                          </td>


                          {/* =================================================
                              DETECTED
                          ================================================= */}

                          <td
                            className="col-hide-xs"
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                              whiteSpace:
                                'nowrap',
                            }}
                          >

                            <div
                              style={{
                                fontSize: 11,
                                color:
                                  'var(--text-muted)',
                              }}
                            >
                              {alert.firstDetectedAt
                                ? timeAgo(
                                    alert.firstDetectedAt
                                  )
                                : '—'}
                            </div>

                          </td>


                          {/* =================================================
                              ACTIONS
                          ================================================= */}

                          <td
                            style={{
                              padding:
                                '9px 12px',
                              borderBottom:
                                '1px solid rgba(26,45,64,0.5)',
                            }}
                          >

                            <div
                              style={{
                                display:
                                  'flex',
                                gap: 5,
                                alignItems:
                                  'center',
                                flexWrap:
                                  'wrap',
                              }}
                            >

                              {/* =============================================
                                  INVALID ID
                              ============================================= */}

                              {invalidIdentity && (

                                <span
                                  style={{
                                    fontSize: 9,
                                    color:
                                      'var(--red)',
                                    fontFamily:
                                      'var(--font-mono)',
                                  }}
                                >
                                  ⚠ INVALID ID
                                </span>

                              )}


                              {/* =============================================
                                  RCA
                              ============================================= */}

                              {!invalidIdentity && (

                                <ActionButton
                                  variant="default"
                                  disabled={
                                    isLoading
                                  }
                                  onClick={() =>
                                    handleOpenRCA(
                                      alert
                                    )
                                  }
                                >
                                  RCA
                                </ActionButton>

                              )}


                              {/* =============================================
                                  NEW -> ACK
                              ============================================= */}

                              {!invalidIdentity &&
                                isNew && (

                                  <ActionButton
                                    variant="ack"
                                    disabled={
                                      isLoading
                                    }
                                    onClick={() =>
                                      handleAcknowledge(
                                        alert
                                      )
                                    }
                                  >
                                    {loadingAction ===
                                    'ack'
                                      ? 'ACK...'
                                      : 'ACK'}
                                  </ActionButton>

                                )}


                              {/* =============================================
                                  ACKNOWLEDGED -> RESOLVE
                              ============================================= */}

                              {!invalidIdentity &&
                                isAcknowledged && (

                                  <ActionButton
                                    variant="resolve"
                                    disabled={
                                      isLoading
                                    }
                                    onClick={() =>
                                      handleResolve(
                                        alert
                                      )
                                    }
                                  >
                                    {loadingAction ===
                                    'resolve'
                                      ? 'RESOLVING...'
                                      : 'RESOLVE'}
                                  </ActionButton>

                                )}


                              {/* =============================================
                                  RESOLVED
                              ============================================= */}

                              {isResolved && (

                                <span
                                  style={{
                                    fontSize: 10,
                                    color:
                                      'var(--green)',
                                    fontFamily:
                                      'var(--font-mono)',
                                    opacity:
                                      0.75,
                                  }}
                                >
                                  ✓ RESOLVED
                                </span>

                              )}

                            </div>

                          </td>

                        </tr>

                      )
                    }
                  )}

                </tbody>

              </table>

            </div>

          )}


        {/* ====================================================
            PAGINATION
        ==================================================== */}

        <Pagination
          page={
            page
          }
          totalPages={
            totalPages
          }
          total={
            totalAlerts
          }
          size={
            pageSize
          }
          onChange={
            nextPage => {

              console.log(
                '[Alerts] Page:',
                nextPage
              )

              setPage(
                nextPage
              )

              setActionError('')
              setSuccessMessage('')

            }
          }
        />

      </Card>

    </div>
  )
}


// ============================================================
// API ERROR
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