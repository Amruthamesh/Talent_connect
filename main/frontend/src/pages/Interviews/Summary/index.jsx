import React from 'react'
import { useParams } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Badge from '@components/atoms/Badge'
import { useInterviewStore } from '@store/interviewStore'
import './style.scss'

const statusVariant = {
  scheduled: 'primary',
  ongoing: 'warning',
  completed: 'success'
}

export default function InterviewSummary() {
  const { interviewId } = useParams()
  const interview = useInterviewStore((state) =>
    state.interviews.find((item) => String(item.id) === String(interviewId))
  )

  if (!interview) {
    return (
      <AppLayout>
        <p>Interview not found.</p>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="interview-summary">
        <div className="interview-summary__header">
          <div>
            <h1>{interview.candidate_name}</h1>
            <p>{interview.role} — {interview.round_type}</p>
            <p className="interview-summary__muted">{new Date(interview.scheduled_at).toLocaleString()}</p>
          </div>
          <Badge variant={statusVariant[interview.status] || 'primary'} size="medium">
            {interview.status}
          </Badge>
        </div>

        <div className="interview-summary__grid">
          <Card title="Feedback" padding="large">
            {interview.feedback ? (
              <div className="interview-summary__feedback">
                <div className="interview-summary__feedback-row">
                  <span>Rating</span>
                  <strong>{interview.feedback.rating}/5</strong>
                </div>
                <div className="interview-summary__feedback-row">
                  <span>Decision</span>
                  <strong>{interview.feedback.decision}</strong>
                </div>
                <div className="interview-summary__feedback-block">
                  <p className="label">Feedback</p>
                  <p>{interview.feedback.comments}</p>
                </div>
                {interview.feedback.notes && (
                  <div className="interview-summary__feedback-block">
                    <p className="label">Notes</p>
                    <p>{interview.feedback.notes}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="interview-summary__muted">Feedback not submitted yet.</p>
            )}
          </Card>

          <Card title="Transcript" padding="large">
            <div className="interview-summary__transcript">
              {interview.transcript.length === 0 && (
                <p className="interview-summary__muted">No transcript available.</p>
              )}
              {interview.transcript.map((item) => (
                <div key={item.id} className="interview-summary__transcript-item">
                  <p className="interview-summary__question">{item.question}</p>
                  <p className="interview-summary__answer">{item.answer || 'No response logged.'}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
