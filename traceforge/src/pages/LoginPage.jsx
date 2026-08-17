import React, { useState } from 'react'

const API_URL =
  import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8080'

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('login')

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const resetMessages = () => {
    setError('')
    setMessage('')
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    resetMessages()
    setPassword('')
    setConfirmPassword('')
  }

  const handleLogin = async () => {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Login failed')
    }

    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)

    onLogin(data)
  }

  const handleRegister = async () => {
    if (password !== confirmPassword) {
      throw new Error('Passwords do not match')
    }

    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Registration failed')
    }

    setMessage(
      'Registration successful. You can now sign in.'
    )

    setPassword('')
    setConfirmPassword('')
    setMode('login')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    resetMessages()
    setLoading(true)

    try {
      if (mode === 'login') {
        await handleLogin()
      } else {
        await handleRegister()
      }
    } catch (err) {
      setError(
        err.message || 'Unable to connect to authentication service'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-header">
          <div className="login-brand">
            TRACEFORGE
          </div>

          <div className="login-subtitle">
            {mode === 'login'
              ? 'SYSTEM ACCESS'
              : 'CREATE OPERATOR ACCOUNT'}
          </div>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={mode === 'login' ? 'active' : ''}
            onClick={() => switchMode('login')}
          >
            LOGIN
          </button>

          <button
            type="button"
            className={mode === 'register' ? 'active' : ''}
            onClick={() => switchMode('register')}
          >
            REGISTER
          </button>
        </div>

        <form onSubmit={handleSubmit}>

          <div className="login-field">
            <label>USERNAME</label>

            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              autoComplete="username"
            />
          </div>

          <div className="login-field">
            <label>PASSWORD</label>

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              autoComplete={
                mode === 'login'
                  ? 'current-password'
                  : 'new-password'
              }
            />
          </div>

          {mode === 'register' && (
            <div className="login-field">
              <label>CONFIRM PASSWORD</label>

              <input
                type="password"
                value={confirmPassword}
                onChange={(e) =>
                  setConfirmPassword(e.target.value)
                }
                placeholder="Confirm password"
                required
                autoComplete="new-password"
              />
            </div>
          )}

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          {message && (
            <div className="login-success">
              {message}
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading
              ? mode === 'login'
                ? 'AUTHENTICATING...'
                : 'CREATING ACCOUNT...'
              : mode === 'login'
                ? 'AUTHENTICATE'
                : 'CREATE ACCOUNT'}
          </button>

        </form>

        <div className="login-footer">
          {mode === 'login'
            ? 'No operator account? Register above.'
            : 'Already have an account? Login above.'}
        </div>

      </div>
    </div>
  )
}