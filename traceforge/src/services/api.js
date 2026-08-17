import axios from 'axios'


// ============================================================
// API URLS
// ============================================================
//
// Spring Boot:
//   Authentication + JWT
//
//   http://100.57.251.173:8080
//
// FastAPI AI service:
//   Logs, alerts, anomalies, clusters, RCA
//
//   http://100.57.251.173:8000
// ============================================================

const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8080'

const AI_API_URL =
  import.meta.env.VITE_AI_API_URL || 'http://localhost:8000'


console.log('==================================================')
console.log('[TraceForge API] Initializing API clients')
console.log('==================================================')

console.log(
  '[TraceForge API] AUTH_API_URL =',
  AUTH_API_URL
)

console.log(
  '[TraceForge API] AI_API_URL =',
  AI_API_URL
)

console.log('==================================================')


// ============================================================
// AUTH CLIENT
// ============================================================

export const authApi = axios.create({

  baseURL: AUTH_API_URL,

  timeout: 50000,

  headers: {
    'Content-Type': 'application/json',
  },

})


// ============================================================
// AI CLIENT
// ============================================================

const api = axios.create({

  baseURL: AI_API_URL,

  timeout: 50000,

  headers: {
    'Content-Type': 'application/json',
  },

})


// ============================================================
// JWT INTERCEPTOR
//
// Attach JWT to AI requests.
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
      `[TraceForge AI] REQUEST ${
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
      'JWT:',
      token ? 'ATTACHED' : 'NOT ATTACHED'
    )

    console.groupEnd()

    return config

  },

  error => {

    console.error(
      '[TraceForge AI] REQUEST SETUP ERROR',
      error
    )

    return Promise.reject(error)

  }

)


// ============================================================
// AI RESPONSE INTERCEPTOR
// ============================================================

api.interceptors.response.use(

  response => {

    console.groupCollapsed(
      `[TraceForge AI] RESPONSE ${
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
      '[TraceForge AI] RESPONSE ERROR'
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
//
// FastAPI:
// GET /logs
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
//
// FastAPI:
// GET /alerts
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
//
// FastAPI:
// GET /alerts/{alert_id}
// ============================================================

export const fetchAlertById = async (
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
// ACKNOWLEDGE ALERT
//
// FastAPI:
// POST /alerts/{alert_id}/ack
// ============================================================

export const acknowledgeAlert = async (
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
// RESOLVE ALERT
//
// FastAPI:
// POST /alerts/{alert_id}/resolve
// ============================================================

export const resolveAlert = async (
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
// RCA INCIDENT
//
// FastAPI:
// GET /rca/incident/{alert_id}
// ============================================================

export const fetchRCAIncident = async (
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
    '[TraceForge RCA] GET INCIDENT:',
    `/rca/incident/${encodedId}`
  )

  return api.get(
    `/rca/incident/${encodedId}`
  )

}


// ============================================================
// RCA REALTIME ALIAS
// ============================================================

export const fetchRCARealtme = async (
  alertId
) => {

  return fetchRCAIncident(
    alertId
  )

}


// ============================================================
// RCA HISTORICAL
// ============================================================

export const fetchRCAHistorical = async () => {

  throw new Error(
    'Historical RCA is not implemented by the backend. Use fetchRCAHistory().'
  )

}


// ============================================================
// RCA HISTORY
//
// FastAPI:
// GET /rca/history
// ============================================================

export const fetchRCAHistory = async (
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
// ANOMALIES
//
// FastAPI:
// GET /anomalies
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
//
// FastAPI:
// GET /clusters
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

export const fetchClusterDetails = async (
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
    String(alertId).trim()

  if (!normalized) {

    throw new Error(
      `${functionName}: alertId cannot be empty.`
    )

  }

  return normalized

}


// ============================================================
// AUTH HELPERS
//
// Use these for login/register if you want auth calls
// centralized in api.js.
// ============================================================

export const login = (
  username,
  password
) => {

  return authApi.post(
    '/auth/login',
    {
      username,
      password,
    }
  )

}


export const register = (
  username,
  password
) => {

  return authApi.post(
    '/auth/register',
    {
      username,
      password,
    }
  )

}


// ============================================================
// EXPORT AI CLIENT
// ============================================================

export default api