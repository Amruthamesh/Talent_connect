import React, { useEffect, useMemo } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { FiCalendar, FiClock, FiUser } from 'react-icons/fi'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { useInterviewStore } from '@store/interviewStore'
import './style.scss'

export default function InterviewerLobby() {
  const { interviewId } = useParams()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const interview = useInterviewStore((state) =>
    state.interviews.find((item) => String(item.id) === String(interviewId))
  )
  const updateStatus = useInterviewStore((state) => state.updateStatus)

  // Derive interviewer key from state, query, or existing sessionStorage
  const interviewerKey = useMemo(() => {
    const fromState = location.state && location.state.key
    const fromQuery = searchParams.get('key')
    const fromStorage = sessionStorage.getItem(`interview-key-interviewer-${interviewId}`)
    return fromState || fromQuery || fromStorage || null
  }, [location.state, searchParams, interviewId])

  // Persist the key for the session page if provided
  useEffect(() => {
    if (interviewerKey) {
      sessionStorage.setItem(`interview-key-interviewer-${interviewId}`, interviewerKey)
    }
  }, [interviewerKey, interviewId])

  if (!interview) {
    return (
      <GuestLayout>
        <div className="lobby">
          <Card title="Interview not found">
            <p>Please check your invite link or ask the HR team for a new one.</p>
          </Card>
        </div>
      </GuestLayout>
    )
  }

  const handleJoin = () => {
    updateStatus(interview.id, 'ongoing')
    const keyParam = interviewerKey ? `?key=${interviewerKey}` : ''
    navigate(`/interview/session/interviewer/${interview.id}${keyParam}`)
  }

  return (
    <GuestLayout>
      <div className="lobby">
        <Card title="Interviewer Lobby">
          <div className="lobby__header">
            <div>
              <p className="lobby__eyebrow">Interview ready</p>
              <h2>{interview.role} – {interview.round_type} Round</h2>
              <p className="lobby__status">Waiting for candidate to join...</p>
            </div>
            <div className="lobby__meta">
              <span><FiUser /> {interview.candidate_name}</span>
              <span><FiCalendar /> {new Date(interview.scheduled_at).toLocaleDateString()}</span>
              <span><FiClock /> {new Date(interview.scheduled_at).toLocaleTimeString()}</span>
            </div>
          </div>

          <div className="lobby__body">
            <div className="lobby__card">
              <h4>Your next steps</h4>
              <ul>
                <li>Review the candidate name and round focus.</li>
                <li>Keep your mic/camera ready.</li>
                <li>Use the Join button to enter the live interview.</li>
              </ul>
            </div>
            <div className="lobby__card lobby__card--cta">
              <p>When you are ready, start the session.</p>
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
