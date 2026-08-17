import axios from 'axios'

// ============================================================
// BASE URL
// ============================================================

const BASE_URL =
  import.meta.env.VITE_API_URL || ''

console.log(
  '=================================================='
)

console.log(
  '[TraceForge API] Initializing API client'
)

console.log(
  '[TraceForge API] VITE_API_URL =',
  import.meta.env.VITE_API_URL
)

console.log(
  '[TraceForge API] BASE_URL =',
  BASE_URL || '(same-origin)'
)

console.log(
  '=================================================='
)


// ============================================================
// AXIOS CLIENT
// ============================================================

const api = axios.create({

  baseURL: BASE_URL,

  timeout: 50000,

  headers: {
    'Content-Type': 'application/json',
  },

})


// ============================================================
// REQUEST INTERCEPTOR
//
// Automatically attach JWT to every authenticated request.
// ============================================================

api.interceptors.request.use(

  config => {

    const token =
      localStorage.getItem('token')

    if (token) {

      config.headers.Authorization =
        `Bearer ${token}`

    }

    console.groupCollapsed(
      `[TraceForge API] REQUEST ${
        config.method?.toUpperCase()
      } ${
        config.baseURL || ''
      }${config.url}`
    )

    console.log(
      'Method:',
      config.method?.toUpperCase()
    )

    console.log(
      'Base URL:',
      config.baseURL
    )

    console.log(
      'URL:',
      config.url
    )

    console.log(
      'Params:',
      config.params
    )

    console.log(
      'Data:',
      config.data
    )

    console.log(
      'JWT:',
      token ? 'ATTACHED' : 'NOT ATTACHED'
    )

    console.log(
      'Full URL:',
      buildDebugUrl(config)
    )

    console.groupEnd()

    return config
  },

  error => {

    console.error(
      '[TraceForge API] REQUEST SETUP ERROR',
      error
    )

    return Promise.reject(error)
  }

)


// ============================================================
// RESPONSE INTERCEPTOR
// ============================================================

api.interceptors.response.use(

  response => {

    console.groupCollapsed(
      `[TraceForge API] RESPONSE ${
        response.status
      } ${
        response.config.method?.toUpperCase()
      } ${
        response.config.url
      }`
    )

    console.log(
      'HTTP status:',
      response.status
    )

    console.log(
      'URL:',
      response.config.url
    )

    console.log(
      'Response:',
      response.data
    )

    console.groupEnd()

    return response.data
  },

  error => {

    console.groupCollapsed(
      '[TraceForge API] RESPONSE ERROR'
    )

    console.error(
      'HTTP status:',
      error?.response?.status
    )

    console.error(
      'Method:',
      error?.config?.method?.toUpperCase()
    )

    console.error(
      'URL:',
      error?.config?.url
    )

    console.error(
      'Params:',
      error?.config?.params
    )

    console.error(
      'Response data:',
      error?.response?.data
    )

    console.error(
      'Message:',
      error?.message
    )

    console.groupEnd()

    return Promise.reject(error)
  }

)


// ============================================================
// LOGS
// ============================================================

export const fetchLogs = (
  params = {}
) => {

  return api.get(
    '/logs',
    {
      params,
    }
  )
}


// ============================================================
// ALERTS
// ============================================================

export const fetchAlerts = (
  params = {}
) => {

  console.log(
    '[TraceForge ALERTS] GET /alerts',
    params
  )

  return api.get(
    '/alerts',
    {
      params,
    }
  )
}


// ============================================================
// EXACT ALERT
// ============================================================

export const fetchAlertById =
  async (
    alertId
  ) => {

    const id =
      requireAlertId(
        alertId,
        'fetchAlertById'
      )

    console.log(
      '[TraceForge ALERTS] GET EXACT ALERT:',
      id
    )

    return api.get(
      `/alerts/${encodeURIComponent(id)}`
    )
  }


// ============================================================
// ACKNOWLEDGE
// ============================================================

export const acknowledgeAlert =
  async (
    alertId
  ) => {

    const id =
      requireAlertId(
        alertId,
        'acknowledgeAlert'
      )

    console.log(
      '[TraceForge ALERTS] ACK:',
      id
    )

    return api.post(
      `/alerts/${encodeURIComponent(id)}/ack`
    )
  }


// ============================================================
// RESOLVE
// ============================================================

export const resolveAlert =
  async (
    alertId
  ) => {

    const id =
      requireAlertId(
        alertId,
        'resolveAlert'
      )

    console.log(
      '[TraceForge ALERTS] RESOLVE:',
      id
    )

    return api.post(
      `/alerts/${encodeURIComponent(id)}/resolve`
    )
  }


// ============================================================
// RCA — EXACT INCIDENT
// ============================================================

export const fetchRCAIncident =
  async (
    alertId
  ) => {

    const id =
      requireAlertId(
        alertId,
        'fetchRCAIncident'
      )

    const encodedId =
      encodeURIComponent(id)

    console.log(
      '=================================================='
    )

    console.log(
      '[TraceForge RCA] EXACT INCIDENT REQUEST'
    )

    console.log(
      '[TraceForge RCA] alertId:',
      id
    )

    console.log(
      '[TraceForge RCA] endpoint:',
      `/rca/incident/${encodedId}`
    )

    console.log(
      '=================================================='
    )

    return api.get(
      `/rca/incident/${encodedId}`
    )
  }


// ============================================================
// RCA REALTIME
// ============================================================

export const fetchRCARealtme =
  async (
    alertId
  ) => {

    return fetchRCAIncident(
      alertId
    )
  }


// ============================================================
// RCA HISTORICAL
// ============================================================

export const fetchRCAHistorical =
  async () => {

    throw new Error(
      'Historical RCA is not implemented by the backend. Use fetchRCAIncident(alertId).'
    )
  }


// ============================================================
// ANOMALIES
// ============================================================

export const fetchAnomalies = (
  params = {}
) => {

  return api.get(
    '/anomalies',
    {
      params,
    }
  )
}


// ============================================================
// CLUSTERS
// ============================================================

export const fetchClusters = (
  params = {}
) => {

  return api.get(
    '/clusters',
    {
      params,
    }
  )
}


// ============================================================
// CLUSTER DETAILS
// ============================================================

export const fetchClusterDetails =
  async (
    clusterId
  ) => {

    console.warn(
      '[TraceForge CLUSTERS] Cluster details API not implemented:',
      clusterId
    )

    throw new Error(
      'Cluster details API is not implemented in the AI service.'
    )
  }


// ============================================================
// RCA HISTORY
// ============================================================

export const fetchRCAHistory =
  async (
    params = {}
  ) => {

    console.log(
      '[TraceForge RCA] GET RCA HISTORY',
      params
    )

    return api.get(
      '/rca/history',
      {
        params,
      }
    )
  }


// ============================================================
// ALERT ID VALIDATION
// ============================================================

function requireAlertId(
  alertId,
  functionName
) {

  if (
    alertId === undefined ||
    alertId === null
  ) {

    throw new Error(
      `${functionName}: alertId is required.`
    )
  }

  const normalized =
    String(
      alertId
    ).trim()

  if (!normalized) {

    throw new Error(
      `${functionName}: alertId cannot be empty.`
    )
  }

  return normalized
}


// ============================================================
// DEBUG URL
// ============================================================

function buildDebugUrl(
  config
) {

  try {

    const base =
      config.baseURL ||
      window.location.origin

    const url =
      new URL(
        config.url,
        base.endsWith('/')
          ? base
          : `${base}/`
      )

    if (
      config.params &&
      typeof config.params === 'object'
    ) {

      Object.entries(
        config.params
      ).forEach(
        ([key, value]) => {

          if (
            value !== undefined &&
            value !== null &&
            value !== ''
          ) {

            url.searchParams.set(
              key,
              String(value)
            )

          }

        }
      )

    }

    return url.toString()

  } catch {

    return `${
      config.baseURL || ''
    }${
      config.url || ''
    }`
  }
}


// ============================================================
// EXPORT
// ============================================================

export default api