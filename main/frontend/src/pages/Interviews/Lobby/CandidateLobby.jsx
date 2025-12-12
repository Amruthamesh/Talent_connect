import React, { useEffect, useMemo } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { FiBriefcase, FiCalendar, FiClock } from 'react-icons/fi'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { useInterviewStore } from '@store/interviewStore'
import './style.scss'

export default function CandidateLobby() {
  const { interviewId } = useParams()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const interview = useInterviewStore((state) =>
    state.interviews.find((item) => String(item.id) === String(interviewId))
  )

  // Resolve candidate key from state, query, or storage
  const candidateKey = useMemo(() => {
    const fromState = location.state && location.state.key
    const fromQuery = searchParams.get('key')
    const fromStorage = sessionStorage.getItem(`interview-key-candidate-${interviewId}`)
    return fromState || fromQuery || fromStorage || null
  }, [location.state, searchParams, interviewId])

  useEffect(() => {
    if (candidateKey) {
      sessionStorage.setItem(`interview-key-candidate-${interviewId}`, candidateKey)
    }
  }, [candidateKey, interviewId])

  if (!interview) {
    return (
      <GuestLayout>
        <div className="lobby">
          <Card title="Interview not found">
            <p>Please check your invite link or ask the recruiter for a new one.</p>
          </Card>
        </div>
      </GuestLayout>
    )
  }

  const handleJoin = () => {
    const keyParam = candidateKey ? `?key=${candidateKey}` : ''
    navigate(`/interview/session/candidate/${interview.id}${keyParam}`)
  }

  return (
    <GuestLayout>
      <div className="lobby">
        <Card title="Candidate Lobby">
          <div className="lobby__header">
            <div>
              <p className="lobby__eyebrow">Welcome to your interview</p>
              <h2>{interview.role}</h2>
              <p className="lobby__status">
                Please keep your mic ready. You will enter when the interviewer starts the session.
              </p>
            </div>
            <div className="lobby__meta">
              <span><FiBriefcase /> {interview.company || 'Company'}</span>
              <span><FiCalendar /> {new Date(interview.scheduled_at).toLocaleDateString()}</span>
              <span><FiClock /> {new Date(interview.scheduled_at).toLocaleTimeString()}</span>
            </div>
          </div>

          <div className="lobby__body">
            <div className="lobby__card">
              <h4>What to expect</h4>
              <ul>
                <li>Round type: {interview.round_type}</li>
                <li>Keep stable internet and a quiet space.</li>
                <li>Questions will appear when the interviewer shares them.</li>
              </ul>
            </div>
            <div className="lobby__card lobby__card--cta">
              <p>Ready? Join the waiting room.</p>
              <Button variant="primary" size="large" onClick={handleJoin}>
                Join Interview
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </GuestLayout>
  )
}
