import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { FiPause, FiPlay, FiSend, FiStopCircle, FiZap, FiRefreshCw } from 'react-icons/fi'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { interviewsAPI } from '@utils/api'
import './style.scss'

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const wsBase = apiBase.replace(/^http/, 'ws')

const upsertQuestion = (list = [], incoming) => {
  if (!incoming) return list

  // If an optimistic question with the same text exists, replace it
  const sameTextIdx = list.findIndex(
    (q) => q.question?.trim() === incoming.question?.trim() && !q.answer
  )
  if (sameTextIdx !== -1) {
    const next = [...list]
    const prev = next[sameTextIdx]
    next[sameTextIdx] = { ...prev, ...incoming, answer: prev.answer ?? incoming.answer }
    return next
  }

  // If we already have this id, merge while keeping existing answer
  const idIdx = list.findIndex((q) => q.id === incoming.id)
  if (idIdx !== -1) {
    const next = [...list]
    const prev = next[idIdx]
    next[idIdx] = { ...prev, ...incoming, answer: prev.answer ?? incoming.answer }
    return next
  }

  return [...list, incoming]
}

export default function InterviewerPanel() {
  const { interviewId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [interview, setInterview] = useState(null)
  const [transcript, setTranscript] = useState([])
  const [message, setMessage] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const [socketReady, setSocketReady] = useState(false)
  const [socketStatus, setSocketStatus] = useState('disconnected')
  const [socketDetail, setSocketDetail] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const keyRef = useRef(null)
  const reconnectRef = useRef(null)

  const lastUnanswered = useMemo(() => transcript.find((q) => !q.answer), [transcript])
  const suggestedQuestions = useMemo(() => buildSuggestions(interview), [interview])

  const loadKey = () => {
    return (
      searchParams.get('key') ||
      sessionStorage.getItem(`interview-key-interviewer-${interviewId}`)
    )
  }

  const storeKey = (key) => {
    if (key) {
      keyRef.current = key
      sessionStorage.setItem(`interview-key-interviewer-${interviewId}`, key)
    }
  }

  // Resolve key/interview
  useEffect(() => {
    const init = async () => {
      const key = loadKey()
      if (!key) {
        setError('Missing interviewer key. Open the invite link with ?key=<interviewer_key>.')
        setLoading(false)
        return
      }
      storeKey(key)
      try {
        const resolved = await interviewsAPI.resolveKey(key)
        setInterview(resolved.interview)
        setTranscript(resolved.interview.transcript || [])
      } catch (err) {
        setError(err.message || 'Could not resolve interview key.')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [interviewId, searchParams])

  const connectSocket = () => {
    if (!interview || !keyRef.current) return
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
      reconnectRef.current = setTimeout(connectSocket, 1000)
    }
    ws.onerror = (err) => {
      console.error('Interviewer WS error', err)
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
        navigate(`/interview/${interview.id}/feedback`)
      }
    }
  }

  useEffect(() => {
    connectSocket()
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [interview, navigate])
  const handleRetryResolve = () => {
    setLoading(true)
    setError(null)
    setInterview(null)
    setTranscript([])
    keyRef.current = null
    sessionStorage.removeItem(`interview-key-interviewer-${interviewId}`)
    // re-run init effect
    const params = new URLSearchParams(window.location.search)
    params.delete('key')
    window.history.replaceState({}, '', `${window.location.pathname}`)
    // trigger effect by manually calling init-like path
    const key = loadKey()
    if (!key) {
      setError('Missing interviewer key. Use the invite link with ?key=<interviewer_key>.')
      setLoading(false)
    }
  }

  const handleSendQuestion = () => {
    const text = message.trim()
    if (!text || !wsRef.current) return
    if (lastUnanswered) {
      alert('Please wait for the previous question to be answered before sending a new one.')
      return
    }
    // Prefer websocket; if not ready, fall back to REST
    if (socketReady) {
      wsRef.current.send(
        JSON.stringify({
          type: 'question',
          key: keyRef.current,
          question: text
        })
      )
      const temp = { id: `temp-${Date.now()}`, question: text, answer: null }
      setTranscript((prev) => upsertQuestion(prev, temp))
      setMessage('')
    } else {
      // REST fallback
      interviewsAPI
        .sendQuestion(interview.id, text, keyRef.current)
        .then((updated) => {
          setTranscript(updated.transcript || [])
          setMessage('')
        })
        .catch((err) => {
          alert(err.message || 'Failed to send question')
        })
    }
  }

  const handleStop = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'status', status: 'completed', key: keyRef.current }))
    }
    navigate(`/interview/${interview.id}/feedback`)
  }

  return (
    <GuestLayout>
      <div className="interviewer-panel">
        {loading && <p>Loading interview...</p>}
        {error && (
          <Card>
            <p>{error}</p>
            <Button variant="primary" icon={<FiRefreshCw />} onClick={handleRetryResolve}>
              Retry
            </Button>
          </Card>
        )}
        {interview && (
          <>
            <div className="interviewer-panel__header">
              <div>
                <h1>Interview Session</h1>
                <p className="interviewer-panel__sub">
                  {interview.candidate_name} | {interview.role} | {interview.round_type} round
                </p>
              </div>
              <div className="interviewer-panel__controls">
                <Button
                  variant="ghost"
                  icon={isPaused ? <FiPlay /> : <FiPause />}
                  onClick={() => setIsPaused((prev) => !prev)}
                >
                  {isPaused ? 'Resume Interview' : 'Pause Interview'}
                </Button>
                <Button variant="danger" icon={<FiStopCircle />} onClick={handleStop}>
                  Stop Interview
                </Button>
              </div>
            </div>

            <div className="interviewer-panel__layout">
              <div className="interviewer-panel__column interviewer-panel__column--video">
                <Card padding="large" title="Video/Call area (placeholder)">
                  <div className="interviewer-panel__video-placeholder">
                    <div className="interviewer-panel__video-box">Live video area</div>
                    <p>Integrate Zoom/Meet SDK here later.</p>
                  </div>
                </Card>
              </div>

              <div className="interviewer-panel__column interviewer-panel__column--copilot">
                <Card padding="large" title="Ask the candidate" subtitle="Type or click a suggested question">
                  {suggestedQuestions.length > 0 && (
                    <div className="interviewer-panel__suggestions">
                      {suggestedQuestions.map((q) => (
                        <Button
                          key={q}
                          variant="ghost"
                          size="small"
                          icon={<FiZap />}
                          onClick={() => setMessage(q)}
                        >
                          {q}
                        </Button>
                      ))}
                    </div>
                  )}
                  <div className="interviewer-panel__copilot">
                    <textarea
                      rows={4}
                      placeholder="Type your question or note for the candidate"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                    />
                <div className="interviewer-panel__actions">
                  <Button
                    variant="primary"
                    icon={<FiSend />}
                    onClick={handleSendQuestion}
                    disabled={!message.trim() || !socketReady}
                  >
                    Send to Candidate
                  </Button>
                  <span className="interviewer-panel__socket-status">
                    WS: {socketStatus}{socketDetail ? ` (${socketDetail})` : ''}
                  </span>
                </div>
                    {lastUnanswered && (
                      <p className="interviewer-panel__hint">
                        Awaiting response to: "{lastUnanswered.question}"
                      </p>
                    )}
                  </div>
                </Card>

                <Card padding="large" title="Transcript">
                  <div className="interviewer-panel__transcript">
                    {transcript.length === 0 && (
                      <p className="interviewer-panel__empty">No messages yet.</p>
                    )}
                    {transcript.map((item) => (
                      <div key={item.id} className="interviewer-panel__transcript-item">
                        <p className="interviewer-panel__question">{item.question}</p>
                        <p className="interviewer-panel__answer">
                          {item.answer || 'Waiting for candidate response...'}
                        </p>
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

function buildSuggestions(interview) {
  if (!interview) return []
  const base = []
  const role = interview.role || ''
  const round = interview.round_type || ''
  if (role) {
    base.push(`Can you walk me through your most relevant experience for a ${role} role?`)
    base.push(`What was a challenging project related to ${role} and how did you handle it?`)
  }
  if (round?.toLowerCase().includes('behavior')) {
    base.push('Tell me about a time you received tough feedback and how you responded.')
  }
  if (round?.toLowerCase().includes('technical')) {
    base.push('Describe a recent technical problem you solved end-to-end. What tradeoffs did you make?')
  }
  if (interview.jd_text) {
    base.push('Looking at the job description, which responsibility do you feel most confident about?')
  }
  return Array.from(new Set(base)).slice(0, 6)
}
