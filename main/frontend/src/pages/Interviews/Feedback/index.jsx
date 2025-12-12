import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import Badge from '@components/atoms/Badge'
import { useInterviewStore } from '@store/interviewStore'
import './style.scss'

const prompts = [
  'What stood out about this candidate?',
  'Any concerns about technical ability?',
  'Would you want to work with this person?'
]

export default function InterviewFeedback() {
  const { interviewId } = useParams()
  const navigate = useNavigate()
  const interview = useInterviewStore((state) =>
    state.interviews.find((item) => String(item.id) === String(interviewId))
  )
  const saveFeedback = useInterviewStore((state) => state.saveFeedback)
  const [form, setForm] = useState({
    rating: '4',
    decision: 'Move to next round',
    comments: '',
    notes: ''
  })

  if (!interview) {
    return (
      <GuestLayout>
        <p>Interview not found.</p>
      </GuestLayout>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await saveFeedback(interview.id, {
      rating: Number(form.rating),
      decision: form.decision,
      comments: form.comments,
      notes: form.notes
    })
    navigate(`/interview/${interview.id}/summary`)
  }

  const addPrompt = (text) => {
    setForm((prev) => ({
      ...prev,
      comments: prev.comments ? `${prev.comments}\n${text}: ` : `${text}: `
    }))
  }

  return (
    <GuestLayout>
      <div className="feedback">
        <Card title="Interview Feedback">
            <div className="feedback__header">
              <div>
                <h2>{interview.candidate_name}</h2>
                <p>{interview.role} | {interview.round_type}</p>
              </div>
              <Badge variant="primary" size="medium">Transcript attached</Badge>
            </div>

          <form className="feedback__form" onSubmit={handleSubmit}>
            <div className="feedback__row">
              <div className="feedback__field">
                <label>Overall rating (1-5)</label>
                <select
                  value={form.rating}
                  onChange={(e) => setForm((prev) => ({ ...prev, rating: e.target.value }))}
                >
                  {[1, 2, 3, 4, 5].map((value) => (
                    <option key={value} value={value}>{value}</option>
                  ))}
                </select>
              </div>

              <div className="feedback__field">
                <label>Recommended decision</label>
                <select
                  value={form.decision}
                  onChange={(e) => setForm((prev) => ({ ...prev, decision: e.target.value }))}
                >
                  <option>Hire</option>
                  <option>Move to next round</option>
                  <option>Hold</option>
                  <option>Reject</option>
                </select>
              </div>
            </div>

            <div className="feedback__field">
              <label>Feedback</label>
              <textarea
                rows={4}
                placeholder="Share signal from the conversation"
                value={form.comments}
                onChange={(e) => setForm((prev) => ({ ...prev, comments: e.target.value }))}
              />
              <div className="feedback__chips">
                {prompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="feedback__chip"
                    onClick={() => addPrompt(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div className="feedback__field">
              <label>Additional notes</label>
              <textarea
                rows={3}
                placeholder="Signals about culture fit, logistics, or follow-ups"
                value={form.notes}
                onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              />
            </div>

            <Button variant="primary" type="submit">
              Save Feedback
            </Button>
          </form>

          <div className="feedback__transcript">
            <h4>Transcript</h4>
            <p className="feedback__hint">Questions asked and candidate responses</p>
            <div className="feedback__transcript-list">
              {interview.transcript.length === 0 && (
                <p className="feedback__muted">No conversation captured yet.</p>
              )}
              {interview.transcript.map((item) => (
                <div key={item.id} className="feedback__transcript-item">
                  <p className="feedback__question">{item.question}</p>
                  <p className="feedback__answer">{item.answer || 'No response logged.'}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </GuestLayout>
  )
}
