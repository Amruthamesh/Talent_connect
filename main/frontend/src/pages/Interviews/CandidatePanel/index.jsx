import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { FiPause, FiPlay, FiSend, FiXCircle, FiRefreshCw } from 'react-icons/fi'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Badge from '@components/atoms/Badge'
import Button from '@components/atoms/Button'
import { interviewsAPI } from '@utils/api'
import './style.scss'

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const wsBase = apiBase.replace(/^http/, 'ws')

const upsertQuestion = (list = [], incoming) => {
  if (!incoming) return list

  const sameTextIdx = list.findIndex(
    (q) => q.question?.trim() === incoming.question?.trim() && !q.answer
  )
  if (sameTextIdx !== -1) {
    const next = [...list]
    const prev = next[sameTextIdx]
    next[sameTextIdx] = { ...prev, ...incoming, answer: prev.answer ?? incoming.answer }
    return next
  }

  const idIdx = list.findIndex((q) => q.id === incoming.id)
  if (idIdx !== -1) {
    const next = [...list]
    const prev = next[idIdx]
    next[idIdx] = { ...prev, ...incoming, answer: prev.answer ?? incoming.answer }
    return next
  }

  return [...list, incoming]
}

export default function CandidatePanel() {
  const { interviewId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [interview, setInterview] = useState(null)
  const [transcript, setTranscript] = useState([])
  const [response, setResponse] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const [socketReady, setSocketReady] = useState(false)
  const [socketStatus, setSocketStatus] = useState('disconnected')
  const [socketDetail, setSocketDetail] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [manualKey, setManualKey] = useState('')
  const wsRef = useRef(null)
  const keyRef = useRef(null)
  const reconnectRef = useRef(null)

  const activeQuestion = useMemo(
    () => transcript.find((q) => !q.answer),
    [transcript]
  )

  const loadKey = () =>
    searchParams.get('key') ||
    sessionStorage.getItem(`interview-key-candidate-${interviewId}`)

  const resolveWithKey = async (key) => {
    if (!key) {
      setError('Missing candidate key. Paste the key from your invite link.')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    storeKey(key)
    try {
      const resolved = await interviewsAPI.resolveKey(key)
      setInterview(resolved.interview)
      setTranscript(resolved.interview.transcript || [])
    } catch (err) {
      setError(err.message || 'Could not resolve candidate link.')
    } finally {
      setLoading(false)
    }
  }

  const storeKey = (key) => {
    if (key) {
      keyRef.current = key
      sessionStorage.setItem(`interview-key-candidate-${interviewId}`, key)
    }
  }

  // Resolve key/interview
  useEffect(() => {
    const init = async () => {
      const key = loadKey()
      await resolveWithKey(key)
    }
    init()
  }, [interviewId, searchParams])

  // Poll as a fallback if socket is not connected
  useEffect(() => {
    if (!interview || !keyRef.current) return undefined
    if (socketStatus === 'connected') return undefined
    const interval = setInterval(async () => {
      try {
        const resolved = await interviewsAPI.resolveKey(keyRef.current)
        setInterview(resolved.interview)
        setTranscript(resolved.interview.transcript || [])
      } catch (err) {
        console.warn('Poll failed', err)
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [interview, socketStatus])

  // Connect socket
  useEffect(() => {
    if (!interview || !keyRef.current) return
    const connect = () => {
      const url = `${wsBase}/interviews/${interview.id}/ws?key=${keyRef.current}`
      const ws = new WebSocket(url)
      wsRef.current = ws
      setSocketStatus('connecting')

      ws.onopen = () => {
        setSocketReady(true)
        setSocketStatus('connected')
        setSocketDetail('')
      }
      ws.onclose = (evt) => {
        setSocketReady(false)
        setSocketStatus('disconnected')
        setSocketDetail(`closed code=${evt?.code || ''} reason=${evt?.reason || ''}`)
        if (reconnectRef.current) clearTimeout(reconnectRef.current)
        reconnectRef.current = setTimeout(connect, 1000)
      }
      ws.onerror = (err) => {
        console.error('Candidate WS error', err)
        setSocketStatus('error')
        setSocketDetail(err?.message || 'socket error')
      }
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'question' && data.question) {
          setTranscript((prev) => upsertQuestion(prev, data.question))
        } else if (data.type === 'response') {
          setTranscript((prev) =>
            prev.map((q) => (q.id === data.question_id ? { ...q, answer: data.answer } : q))
          )
        } else if (data.type === 'status' && data.status === 'completed') {
          navigate(`/interview/${interview.id}/summary`)
        }
      }
    }

    connect()

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [interview, navigate])

  const handleSubmit = () => {
    if (!activeQuestion || !response.trim() || !wsRef.current) return
    wsRef.current.send(
      JSON.stringify({
        type: 'response',
        key: keyRef.current,
        question_id: activeQuestion.id,
        answer: response.trim()
      })
    )
    setResponse('')
  }

  const handleLeave = () => {
    navigate('/login')
  }

  const handleRetry = () => {
    setLoading(true)
    setError(null)
    setInterview(null)
    setTranscript([])
    keyRef.current = null
    sessionStorage.removeItem(`interview-key-candidate-${interviewId}`)
    const key = loadKey()
    if (!key) {
      setError('Missing candidate key. Use the invite link with ?key=<candidate_key>.')
      setLoading(false)
    }
  }

  return (
    <GuestLayout>
      <div className="candidate-panel">
        {loading && <p>Loading interview...</p>}
        {error && (
          <Card>
            <p>{error}</p>
            <Button icon={<FiRefreshCw />} onClick={handleRetry}>
              Retry
            </Button>
          </Card>
        )}
        {!interview && !loading && (
          <Card>
            <p>Enter your candidate key to join the session.</p>
            <input
              type="text"
              value={manualKey}
              onChange={(e) => setManualKey(e.target.value)}
              placeholder="candidate-xxxx"
            />
            <div style={{ marginTop: '0.5rem' }}>
              <Button
                variant="primary"
                onClick={() => resolveWithKey(manualKey.trim())}
                disabled={!manualKey.trim()}
              >
                Join with Key
              </Button>
            </div>
          </Card>
        )}
        {interview && (
          <>
            <div className="candidate-panel__header">
              <div>
                <h1>Interview Session</h1>
                <p>{interview.role} | {interview.company}</p>
              </div>
              <div className="candidate-panel__header-actions">
                <Badge variant="success" size="medium">Interview Active</Badge>
                <Button
                  variant="ghost"
                  icon={isPaused ? <FiPlay /> : <FiPause />}
                  onClick={() => setIsPaused((prev) => !prev)}
                >
                  {isPaused ? 'Resume' : 'Pause'}
                </Button>
                <Button variant="danger" icon={<FiXCircle />} onClick={handleLeave}>
                  Leave
                </Button>
              </div>
            </div>

            <div className="candidate-panel__layout">
              <div className="candidate-panel__column candidate-panel__column--video">
                <Card padding="large" title="Video/Call area (placeholder)">
                  <div className="candidate-panel__video-placeholder">
                    <div className="candidate-panel__video-box">Live video area</div>
                    <p>Mirrors interviewer view. Integrate call SDK later.</p>
                  </div>
                </Card>
              </div>

              <div className="candidate-panel__column candidate-panel__column--qa">
                <Card padding="large" title="Question">
                  <div className="candidate-panel__qa">
                    <p className="muted">Connection: {socketStatus}</p>
                    {!activeQuestion && (
                      <div className="candidate-panel__empty">
                        <p>Waiting for questions...</p>
                        <p className="muted">Questions will appear here when the interviewer sends them.</p>
                      </div>
                    )}

                    {activeQuestion && (
                      <div className="candidate-panel__question-card">
                        <p className="candidate-panel__question">{activeQuestion.question}</p>
                        <textarea
                          rows={3}
                          placeholder="Type your response"
                          value={response}
                          onChange={(e) => setResponse(e.target.value)}
                        />
                    <div className="candidate-panel__actions">
                      <Button
                        variant="primary"
                        size="small"
                        icon={<FiSend />}
                        onClick={handleSubmit}
                        disabled={!response.trim() || !socketReady}
                      >
                        Submit Response
                      </Button>
                    <span className="candidate-panel__socket-status">
                      WS: {socketStatus}{socketDetail ? ` (${socketDetail})` : ''}
                    </span>
                    </div>
                      </div>
                    )}
                  </div>
                </Card>

                <Card padding="large" title="Responses Logged">
                  <div className="candidate-panel__transcript">
                    {transcript.filter((item) => item.answer).length === 0 && (
                      <p className="muted">Your responses will appear here after submission.</p>
                    )}
                    {transcript
                      .filter((item) => item.answer)
                      .map((item) => (
                        <div key={item.id} className="candidate-panel__transcript-item">
                          <p className="candidate-panel__question">{item.question}</p>
                          <p className="candidate-panel__answer">{item.answer}</p>
                        </div>
                      ))}
                  </div>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </GuestLayout>
  )
}
