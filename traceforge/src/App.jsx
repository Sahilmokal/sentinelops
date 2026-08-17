import React, {
  useCallback,
  useEffect,
  useState,
} from 'react'

import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'

import LogsPage from './pages/LogsPage'
import AlertsPage from './pages/AlertsPage'
import ClustersPage from './pages/ClustersPage'
import AnomaliesPage from './pages/AnomaliesPage'
import RCAPage from './pages/RCAPage'
import LoginPage from './pages/LoginPage'


// ============================================================
// BACKEND / MOCK MODE
// ============================================================

const USING_MOCK =
  !import.meta.env.VITE_AI_API_URL


export default function App() {

  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [
    authenticated,
    setAuthenticated,
  ] = useState(
    () =>
      !!localStorage.getItem(
        'token'
      )
  )


  // ============================================================
  // NAVIGATION
  // ============================================================

  const [
    page,
    setPage,
  ] = useState('logs')


  // ============================================================
  // EXACT RCA ALERT ID
  //
  // IMPORTANT:
  //
  // This is the ONLY alert identity used by RCA.
  //
  // It must come directly from:
  //
  // alert.alertId
  //
  // from the backend /alerts response.
  //
  // RCA must NEVER:
  //
  // - choose the latest alert
  // - search by service
  // - search by timestamp
  // - search by severity
  // - search by anomaly type
  // - guess an incident
  // ============================================================

  const [
    selectedAlertId,
    setSelectedAlertId,
  ] = useState(null)


  // ============================================================
  // GLOBAL REFRESH
  // ============================================================

  const [
    refreshKey,
    setRefresh,
  ] = useState(0)


  // ============================================================
  // MOBILE SIDEBAR
  // ============================================================

  const [
    sidebarOpen,
    setSidebar,
  ] = useState(false)


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin =
    useCallback(() => {

      setAuthenticated(true)

    }, [])


  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout =
    useCallback(() => {

      localStorage.removeItem(
        'token'
      )

      localStorage.removeItem(
        'username'
      )

      setAuthenticated(false)

      setPage('logs')

      // Clear RCA selection on logout.
      setSelectedAlertId(null)

      setSidebar(false)

    }, [])


  // ============================================================
  // NORMAL NAVIGATION
  // ============================================================

  const handleNavigate =
    useCallback(
      nextPage => {

        setPage(nextPage)

        setSidebar(false)

      },
      []
    )


  // ============================================================
  // OPEN EXACT RCA
  //
  // This function receives the canonical backend alertId.
  //
  // Example:
  //
  // handleOpenRCA('ALERT-12345')
  //
  // Then:
  //
  // selectedAlertId = 'ALERT-12345'
  //
  // and RCAPage receives exactly that value.
  // ============================================================

  const handleOpenRCA =
    useCallback(
      alertId => {

        // Never allow undefined/null/empty IDs.

        if (
          alertId ===
            undefined ||
          alertId ===
            null ||
          String(alertId).trim() === ''
        ) {

          console.error(
            '[App] Cannot open RCA: missing alertId.'
          )

          return
        }


        const normalizedAlertId =
          String(
            alertId
          ).trim()


        console.log(
          '[App] Opening RCA for exact alertId:',
          normalizedAlertId
        )


        setSelectedAlertId(
          normalizedAlertId
        )

        setPage('rca')

        setSidebar(false)

      },
      []
    )


  // ============================================================
  // KEYBOARD
  // ============================================================

  useEffect(() => {

    const handler =
      event => {

        if (
          event.key ===
          'Escape'
        ) {

          setSidebar(false)

        }

      }


    window.addEventListener(
      'keydown',
      handler
    )


    return () => {

      window.removeEventListener(
        'keydown',
        handler
      )

    }

  }, [])


  // ============================================================
  // LOGIN SCREEN
  // ============================================================

  if (!authenticated) {

    return (

      <LoginPage
        onLogin={
          handleLogin
        }
      />

    )
  }


  // ============================================================
  // COMMON PAGE PROPS
  // ============================================================

  const pageProps = {

    usingMock:
      USING_MOCK,

    key:
      refreshKey,

    onNavigate:
      handleNavigate,

  }


  // ============================================================
  // APPLICATION
  // ============================================================

  return (

    <>

      <div
        className="scan-overlay"
      />


      <div
        className="app-shell"
      >

        {/* ====================================================
            SIDEBAR OVERLAY
        ==================================================== */}

        <div
          className={
            `sidebar-overlay${
              sidebarOpen
                ? ' visible'
                : ''
            }`
          }
          onClick={() =>
            setSidebar(false)
          }
        />


        {/* ====================================================
            SIDEBAR
        ==================================================== */}

        <div
          className={
            `sidebar${
              sidebarOpen
                ? ' open'
                : ''
            }`
          }
        >

          <Sidebar
            activePage={
              page
            }
            onNavigate={
              handleNavigate
            }
            onLogout={
              handleLogout
            }
          />

        </div>


        {/* ====================================================
            MAIN AREA
        ==================================================== */}

        <div
          className="main-area"
        >

          <Topbar
            page={
              page
            }

            onRefresh={() =>
              setRefresh(
                current =>
                  current + 1
              )
            }

            onMenuToggle={() =>
              setSidebar(
                open =>
                  !open
              )
            }
          />


          <main
            className="page-content"
            style={{
              backgroundImage: `
                radial-gradient(
                  ellipse at 20% 0%,
                  rgba(0,212,255,0.035) 0%,
                  transparent 55%
                ),
                radial-gradient(
                  ellipse at 80% 100%,
                  rgba(176,106,255,0.025) 0%,
                  transparent 55%
                )
              `,
            }}
          >

            {/* ==================================================
                LOGS
            ================================================== */}

            {page === 'logs' && (

              <LogsPage
                {...pageProps}
              />

            )}


            {/* ==================================================
                ALERTS
            ================================================== */}

            {page === 'alerts' && (

              <AlertsPage
                {...pageProps}

                onOpenRCA={
                  handleOpenRCA
                }
              />

            )}


            {/* ==================================================
                CLUSTERS
            ================================================== */}

            {page === 'clusters' && (

              <ClustersPage
                {...pageProps}
              />

            )}


            {/* ==================================================
                ANOMALIES
            ================================================== */}

            {page === 'anomalies' && (

              <AnomaliesPage
                {...pageProps}
              />

            )}


            {/* ==================================================
                RCA
            ================================================== */}

            {page === 'rca' && (

              <RCAPage
                {...pageProps}

                alertId={
                  selectedAlertId
                }
              />

            )}

          </main>

        </div>

      </div>

    </>

  )
}