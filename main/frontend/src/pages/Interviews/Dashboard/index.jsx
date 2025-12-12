import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiClipboard, FiExternalLink, FiPlus } from 'react-icons/fi'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Badge from '@components/atoms/Badge'
import Button from '@components/atoms/Button'
import { useInterviewStore } from '@store/interviewStore'
import content from './content.json'
import './style.scss'

const statusVariant = {
  scheduled: 'primary',
  ongoing: 'warning',
  completed: 'success'
}

export default function InterviewDashboard() {
  const navigate = useNavigate()
  const interviews = useInterviewStore((state) => state.interviews)
  const fetchInterviews = useInterviewStore((state) => state.fetchInterviews)
  const [copied, setCopied] = useState(null)

  const buildLink = (key) => `${window.location.origin}/interview/join?key=${key}`

  useEffect(() => {
    fetchInterviews().catch(() => null)
  }, [fetchInterviews])

  const handleCopy = async (key, label) => {
    try {
      await navigator.clipboard.writeText(buildLink(key))
      setCopied(label)
      setTimeout(() => setCopied(null), 1500)
    } catch (err) {
      console.error('Failed to copy', err)
    }
  }

  const rows = useMemo(
    () =>
      interviews.map((item) => ({
        id: item.id,
        candidate: item.candidate_name,
        role: item.role,
        roundType: item.round_type,
        dateTime: new Date(item.scheduled_at).toLocaleString(),
        status: item.status,
        interviewerKey: item.interviewer_key,
        candidateKey: item.candidate_key
      })),
    [interviews]
  )

  return (
    <AppLayout>
      <div className="interview-dashboard">
        <div className="interview-dashboard__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle}</p>
          </div>
          <Button variant="primary" icon={<FiPlus />} onClick={() => navigate('/interviews/schedule')}>
            Schedule Interview
          </Button>
        </div>

        <Card padding="none">
          <div className="interview-dashboard__table">
            <div className="interview-dashboard__table-header">
              <span>Candidate</span>
              <span>Role</span>
              <span>Round Type</span>
              <span>Date/Time</span>
              <span>Status</span>
              <span>Actions</span>
            </div>

            {rows.map((row) => (
              <div key={row.id} className="interview-dashboard__table-row">
                <span className="medium">{row.candidate}</span>
                <span>{row.role}</span>
                <span>{row.roundType}</span>
                <span>{row.dateTime}</span>
                <span>
                  <Badge variant={statusVariant[row.status] || 'primary'} size="medium">
                    {row.status}
                  </Badge>
                </span>
                <div className="interview-dashboard__actions">
                  <Button
                    variant="ghost"
                    size="small"
                    icon={<FiExternalLink />}
                    onClick={() => navigate(`/interview/${row.id}/summary`)}
                  >
                    View Details
                  </Button>
                  <Button
                    variant="ghost"
                    size="small"
                    icon={<FiClipboard />}
                    onClick={() => handleCopy(row.interviewerKey, `interviewer-${row.id}`)}
                  >
                    {copied === `interviewer-${row.id}` ? 'Copied' : 'Copy Interviewer Link'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="small"
                    icon={<FiClipboard />}
                    onClick={() => handleCopy(row.candidateKey, `candidate-${row.id}`)}
                  >
                    {copied === `candidate-${row.id}` ? 'Copied' : 'Copy Candidate Link'}
                  </Button>
                  <Button
                    variant="primary"
                    size="small"
                    disabled={row.status !== 'completed'}
                    onClick={() => navigate(`/interview/${row.id}/summary`)}
                  >
                    View Results
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}
