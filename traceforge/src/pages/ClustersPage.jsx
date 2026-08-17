import React, { useCallback, useMemo, useState } from 'react'

import { fetchClusters } from '../services/api'

import { useAsync } from '../hooks/useAsync'

import {
  Card,
  CardHeader,
  StatCard,
} from '../components/Card'

import {
  LoadingState,
  EmptyState,
} from '../components/States'

import {
  IconButton,
} from '../components/Controls'


// ============================================================
// PAGE
// ============================================================

export default function ClustersPage({
  onNavigate,
}) {

  const [
    selectedCluster,
    setSelectedCluster,
  ] = useState(null)

  const [
    error,
    setError,
  ] = useState('')


  // ==========================================================
  // FETCH REAL BACKEND DATA
  // ==========================================================

  const fetcher = useCallback(
    async () => {

      console.log(
        '[Clusters] Fetching clusters...'
      )

      const params = {
        size: 500,
        minutes: 5,
      }

      console.log(
        '[Clusters] GET /clusters',
        params
      )

      try {

        const response =
          await fetchClusters(params)

        console.log(
          '[Clusters] Backend response:',
          response
        )

        return response

      } catch (err) {

        console.error(
          '[Clusters] Fetch failed:',
          err
        )

        throw err
      }

    },
    []
  )


  const {
    data,
    loading,
    refetch,
  } = useAsync(
    fetcher,
    []
  )


  // ==========================================================
  // NORMALIZE BACKEND RESPONSE
  // ==========================================================

  const normalized = useMemo(
    () => normalizeClusters(data),
    [data]
  )


  const clusters =
    normalized.clusters


  // ==========================================================
  // REFRESH
  // ==========================================================

  const handleRefresh = async () => {

    setSelectedCluster(null)
    setError('')

    console.log(
      '[Clusters] Manual refresh'
    )

    try {

      await refetch()

    } catch (err) {

      console.error(
        '[Clusters] Refresh failed:',
        err
      )

      setError(
        err?.response?.data?.message ||
        err?.message ||
        'Unable to load clusters'
      )
    }
  }


  // ==========================================================
  // OPEN CLUSTER
  //
  // IMPORTANT:
  // There is currently NO /clusters/{id}
  // endpoint in the FastAPI backend.
  //
  // Therefore we use the cluster object already
  // returned by /clusters.
  // ==========================================================

  const handleOpenCluster = (
    cluster
  ) => {

    console.log(
      '[Clusters] Selected cluster:',
      cluster
    )

    setSelectedCluster(cluster)
  }


  // ==========================================================
  // RENDER
  // ==========================================================

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

      {error && (

        <div
          style={{
            padding: '9px 12px',
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
          ⚠ {error}
        </div>

      )}


      {/* ======================================================
          STATS
      ====================================================== */}

      <div className="stat-grid-4">

        <StatCard
          value={
            normalized.clusterCount
              .toLocaleString()
          }
          label="Clusters"
          color="var(--cyan)"
          accent="var(--cyan)"
          icon="◎"
        />

        <StatCard
          value={
            normalized.totalMessages
              .toLocaleString()
          }
          label="Clustered Logs"
          color="var(--red)"
          accent="var(--red)"
          icon="≋"
        />

        <StatCard
          value={
            normalized.uniqueMessages
              .toLocaleString()
          }
          label="Unique Messages"
          color="var(--amber)"
          accent="var(--amber)"
          icon="◇"
        />

        <StatCard
          value={
            normalized.noiseCount
              .toLocaleString()
          }
          label="Noise"
          color="var(--purple)"
          accent="var(--purple)"
          icon="∅"
        />

      </div>


      {/* ======================================================
          TOOLBAR
      ====================================================== */}

      <div
        className="filter-bar"
        style={{
          display: 'flex',
          alignItems: 'center',
        }}
      >

        <div
          style={{
            fontSize: 10,
            color:
              'var(--text-muted)',
            fontFamily:
              'var(--font-mono)',
          }}
        >
          Semantic clustering ·
          last 5 minutes
        </div>


        <div
          style={{
            marginLeft: 'auto',
          }}
        >

          <IconButton
            onClick={
              handleRefresh
            }
          >
            ↻ Refresh
          </IconButton>

        </div>

      </div>


      {/* ======================================================
          CONTENT
      ====================================================== */}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            selectedCluster
              ? 'minmax(0, 1.4fr) minmax(300px, 0.8fr)'
              : '1fr',
          gap: 14,
          alignItems: 'start',
        }}
      >

        {/* ====================================================
            CLUSTER FEED
        ==================================================== */}

        <Card>

          <CardHeader
            title="Cluster Feed"
            icon="◎"
            right={

              <span
                style={{
                  fontSize: 10,
                  color:
                    'var(--text-muted)',
                }}
              >
                {normalized.clusterCount}
                {' '}
                clusters
              </span>

            }
          />


          {loading && (

            <LoadingState
              message="Analyzing log clusters..."
            />

          )}


          {!loading &&
            !clusters.length && (

              <EmptyState
                icon="◎"
                message="No clusters found"
                sub={
                  normalized.noiseCount > 0
                    ? 'Logs were classified as noise.'
                    : 'No clusterable log messages found.'
                }
              />

            )}


          {!loading &&
            clusters.length > 0 && (

              <div className="table-scroll">

                <table
                  style={{
                    width: '100%',
                    borderCollapse:
                      'collapse',
                  }}
                >

                  <thead>

                    <tr>

                      {[
                        'Cluster',
                        'Pattern',
                        'Messages',
                        'Occurrences',
                      ].map(
                        heading => (

                          <th
                            key={heading}
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
                            {heading}
                          </th>

                        )
                      )}

                    </tr>

                  </thead>


                  <tbody>

                    {clusters.map(
                      cluster => {

                        const id =
                          cluster.clusterId

                        const selected =
                          selectedCluster &&
                          selectedCluster.clusterId ===
                            id


                        return (

                          <tr
                            key={id}
                            onClick={() =>
                              handleOpenCluster(
                                cluster
                              )
                            }
                            style={{
                              cursor:
                                'pointer',
                              background:
                                selected
                                  ? 'var(--cyan-dim)'
                                  : 'transparent',
                              transition:
                                'background 0.12s',
                            }}
                            onMouseEnter={e => {

                              if (!selected) {

                                e.currentTarget.style.background =
                                  'var(--bg-hover)'

                              }

                            }}
                            onMouseLeave={e => {

                              if (!selected) {

                                e.currentTarget.style.background =
                                  'transparent'

                              }

                            }}
                          >

                            {/* Cluster ID */}

                            <td
                              style={
                                cellStyle
                              }
                            >

                              <span
                                style={{
                                  fontFamily:
                                    'var(--font-mono)',
                                  fontSize: 10,
                                  color:
                                    'var(--cyan)',
                                }}
                              >
                                #{id}
                              </span>

                            </td>


                            {/* Representative message */}

                            <td
                              style={
                                cellStyle
                              }
                            >

                              <div
                                style={{
                                  fontSize: 11,
                                  color:
                                    'var(--text-primary)',
                                  maxWidth: 420,
                                  overflow:
                                    'hidden',
                                  textOverflow:
                                    'ellipsis',
                                  whiteSpace:
                                    'nowrap',
                                }}
                                title={
                                  cluster.representativeMessage
                                }
                              >
                                {
                                  cluster.representativeMessage ||
                                  'No representative message'
                                }
                              </div>

                            </td>


                            {/* Unique messages in cluster */}

                            <td
                              style={
                                cellStyle
                              }
                            >

                              <span
                                style={{
                                  fontFamily:
                                    'var(--font-display)',
                                  fontWeight: 700,
                                  color:
                                    'var(--text-primary)',
                                }}
                              >
                                {Number(
                                  cluster.messageCount ||
                                  0
                                ).toLocaleString()}
                              </span>

                            </td>


                            {/* Total occurrences */}

                            <td
                              style={
                                cellStyle
                              }
                            >

                              <span
                                style={{
                                  fontFamily:
                                    'var(--font-display)',
                                  fontWeight: 700,
                                  color:
                                    'var(--cyan)',
                                }}
                              >
                                {Number(
                                  cluster.occurrences ||
                                  0
                                ).toLocaleString()}
                              </span>

                            </td>

                          </tr>

                        )

                      }
                    )}

                  </tbody>

                </table>

              </div>

            )}

        </Card>


        {/* ====================================================
            DETAILS
        ==================================================== */}

        {selectedCluster && (

          <ClusterDetails
            cluster={
              selectedCluster
            }
            onClose={() =>
              setSelectedCluster(null)
            }
            onOpenAlerts={() =>
              onNavigate?.('alerts')
            }
            onOpenRCA={() =>
              onNavigate?.('rca')
            }
          />

        )}

      </div>

    </div>

  )
}


// ============================================================
// CLUSTER DETAILS
// ============================================================

function ClusterDetails({
  cluster,
  onClose,
  onOpenAlerts,
  onOpenRCA,
}) {

  const messages =
    Array.isArray(
      cluster.messages
    )
      ? cluster.messages
      : []


  return (

    <Card
      style={{
        position: 'sticky',
        top: 14,
      }}
    >

      <CardHeader
        title="Cluster Details"
        icon="◎"
        right={

          <IconButton
            onClick={onClose}
          >
            × Close
          </IconButton>

        }
      />


      <div
        style={{
          padding: 16,
        }}
      >

        {/* Header */}

        <div
          style={{
            marginBottom: 16,
          }}
        >

          <div
            style={{
              fontFamily:
                'var(--font-mono)',
              fontSize: 10,
              color:
                'var(--cyan)',
              marginBottom: 8,
            }}
          >
            CLUSTER #{cluster.clusterId}
          </div>


          <div
            style={{
              fontFamily:
                'var(--font-display)',
              fontSize: 19,
              fontWeight: 800,
              color:
                'var(--text-primary)',
              lineHeight: 1.3,
            }}
          >
            {
              cluster.representativeMessage ||
              'No representative message'
            }
          </div>

        </div>


        {/* Metrics */}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              '1fr 1fr',
            gap: 8,
            marginBottom: 14,
          }}
        >

          <MiniMetric
            label="Unique Messages"
            value={Number(
              cluster.messageCount || 0
            ).toLocaleString()}
            color="var(--cyan)"
          />

          <MiniMetric
            label="Occurrences"
            value={Number(
              cluster.occurrences || 0
            ).toLocaleString()}
            color="var(--green)"
          />

        </div>


        {/* Messages */}

        {messages.length > 0 && (

          <DetailSection
            title="Messages in Cluster"
          >

            <div
              style={{
                display: 'flex',
                flexDirection:
                  'column',
                gap: 5,
              }}
            >

              {messages
                .slice(0, 20)
                .map(
                  (message, index) => (

                    <div
                      key={index}
                      style={{
                        padding:
                          '7px 9px',
                        background:
                          'var(--bg-elevated)',
                        border:
                          '1px solid var(--border)',
                        borderRadius: 3,
                        fontSize: 9,
                        fontFamily:
                          'var(--font-mono)',
                        color:
                          'var(--text-secondary)',
                        overflow:
                          'hidden',
                      }}
                    >
                      {message}
                    </div>

                  )
                )}

            </div>

          </DetailSection>

        )}


        {/* Actions */}

        <div
          style={{
            display: 'flex',
            gap: 6,
            marginTop: 16,
            flexWrap: 'wrap',
          }}
        >

          <IconButton
            onClick={
              onOpenAlerts
            }
          >
            ⚡ View Alerts
          </IconButton>

          <IconButton
            onClick={
              onOpenRCA
            }
          >
            ⬡ Run RCA
          </IconButton>

        </div>

      </div>

    </Card>

  )
}


// ============================================================
// SMALL COMPONENTS
// ============================================================

function MiniMetric({
  label,
  value,
  color,
}) {

  return (

    <div
      style={{
        padding: '9px 10px',
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
          fontFamily:
            'var(--font-display)',
          fontSize: 18,
          fontWeight: 800,
          color,
        }}
      >
        {value}
      </div>


      <div
        style={{
          fontSize: 8,
          color:
            'var(--text-muted)',
          textTransform:
            'uppercase',
          letterSpacing:
            '1px',
          marginTop: 3,
        }}
      >
        {label}
      </div>

    </div>

  )
}


function DetailSection({
  title,
  children,
}) {

  return (

    <div
      style={{
        marginTop: 14,
      }}
    >

      <div
        style={{
          fontSize: 8,
          fontWeight: 700,
          letterSpacing:
            '1.5px',
          textTransform:
            'uppercase',
          color:
            'var(--text-muted)',
          marginBottom: 7,
        }}
      >
        {title}
      </div>

      {children}

    </div>

  )
}


// ============================================================
// RESPONSE NORMALIZATION
// ============================================================

function normalizeClusters(data) {

  if (!data) {

    return {
      totalMessages: 0,
      uniqueMessages: 0,
      clusterCount: 0,
      noiseCount: 0,
      noiseMessages: [],
      clusters: [],
    }

  }


  /*
   * This matches the FastAPI response exactly:
   *
   * {
   *   mode,
   *   totalLogsFetched,
   *   totalMessages,
   *   uniqueMessages,
   *   totalClusters,
   *   noiseCount,
   *   noiseMessages,
   *   clusters
   * }
   */

  return {

    totalMessages:
      Number(
        data.totalMessages ??
        0
      ),

    uniqueMessages:
      Number(
        data.uniqueMessages ??
        0
      ),

    clusterCount:
      Number(
        data.totalClusters ??
        data.clusterCount ??
        data.clusters?.length ??
        0
      ),

    noiseCount:
      Number(
        data.noiseCount ??
        0
      ),

    noiseMessages:
      Array.isArray(
        data.noiseMessages
      )
        ? data.noiseMessages
        : [],

    clusters:
      Array.isArray(
        data.clusters
      )
        ? data.clusters
        : [],

  }

}


// ============================================================
// TABLE CELL STYLE
// ============================================================

const cellStyle = {

  padding:
    '9px 12px',

  borderBottom:
    '1px solid rgba(26,45,64,0.5)',

  verticalAlign:
    'middle',

}