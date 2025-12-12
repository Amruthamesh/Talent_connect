import React, { useMemo, useState } from 'react'
import { FiClipboard, FiCheck, FiUpload } from 'react-icons/fi'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import FormInput from '@components/molecules/FormInput'
import Button from '@components/atoms/Button'
import { useInterviewStore } from '@store/interviewStore'
import content from './content.json'
import './style.scss'

const roundTypes = [
  { value: 'Behavioral', label: 'Behavioral' },
  { value: 'Technical', label: 'Technical' },
  { value: 'Hybrid', label: 'Hybrid' }
]

export default function InterviewSchedule() {
  const scheduleInterview = useInterviewStore((state) => state.scheduleInterview)
  const [formData, setFormData] = useState({
    candidateName: '',
    candidateEmail: '',
    role: '',
    company: 'Your Company',
    roundType: 'Behavioral',
    date: '',
    time: '',
    notes: '',
    jobDescriptionText: ''
  })
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescriptionFile, setJobDescriptionFile] = useState(null)
  const [confirmation, setConfirmation] = useState(null)
  const [copied, setCopied] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const links = useMemo(() => {
    if (!confirmation) return null
    const origin = window.location.origin
    return {
      interviewer: `${origin}/interview/join?key=${confirmation.interviewer_key}`,
      candidate: `${origin}/interview/join?key=${confirmation.candidate_key}`
    }
  }, [confirmation])

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.candidateName || !formData.role || !formData.date || !formData.time) return
    setSubmitting(true)
    setError(null)

    try {
      const interview = await scheduleInterview(formData, {
        resume: resumeFile,
        jobDescription: jobDescriptionFile
      })
      setConfirmation(interview)
      setCopied(null)
    } catch (err) {
      setError(err.message || 'Failed to schedule interview')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCopy = async (value, key) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(key)
      setTimeout(() => setCopied(null), 1800)
    } catch (err) {
      console.error('Failed to copy link', err)
    }
  }

  return (
    <AppLayout>
      <div className="interview-schedule">
        <header className="interview-schedule__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle}</p>
          </div>
          <span className="interview-schedule__hint">
            Fill the form to generate interviewer and candidate links.
          </span>
        </header>

        <div className="interview-schedule__grid">
          <Card title="Schedule New Interview" padding="large" className="interview-schedule__form-card">
            <form className="interview-schedule__form" onSubmit={handleSubmit}>
              <div className="interview-schedule__row">
                <FormInput
                  label="Candidate Name"
                  placeholder="Enter candidate name"
                  required
                  value={formData.candidateName}
                  onChange={(e) => handleChange('candidateName', e.target.value)}
                />
                <FormInput
                  label="Candidate Email"
                  type="email"
                  placeholder="candidate@example.com"
                  required
                  value={formData.candidateEmail}
                  onChange={(e) => handleChange('candidateEmail', e.target.value)}
                />
              </div>

              <div className="interview-schedule__row">
                <FormInput
                  label="Role"
                  placeholder="e.g., Senior Frontend Engineer"
                  required
                  value={formData.role}
                  onChange={(e) => handleChange('role', e.target.value)}
                />
                <FormInput
                  label="Company (optional)"
                  placeholder="Your Company"
                  value={formData.company}
                  onChange={(e) => handleChange('company', e.target.value)}
                />
              </div>

              <div className="interview-schedule__row">
                <div className="interview-schedule__field">
                  <label>Round Type</label>
                  <div className="interview-schedule__chips">
                    {roundTypes.map((type) => (
                      <button
                        key={type.value}
                        type="button"
                        className={`interview-schedule__chip ${formData.roundType === type.value ? 'is-active' : ''}`}
                        onClick={() => handleChange('roundType', type.value)}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="interview-schedule__row">
                <FormInput
                  label="Interview Date"
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                />
                <FormInput
                  label="Interview Time"
                  type="time"
                  required
                  value={formData.time}
                  onChange={(e) => handleChange('time', e.target.value)}
                />
              </div>

              <div className="interview-schedule__row">
                <div className="interview-schedule__field">
                  <label>Upload Resume</label>
                  <label className="interview-schedule__upload">
                    <FiUpload />
                    <span>{resumeFile ? resumeFile.name : 'Attach resume (PDF/DOC)'}</span>
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={(e) => setResumeFile(e.target.files?.[0])}
                    />
                  </label>
                </div>
                <div className="interview-schedule__field">
                  <label>Job Description (file or text)</label>
                  <label className="interview-schedule__upload">
                    <FiUpload />
                    <span>{jobDescriptionFile ? jobDescriptionFile.name : 'Attach JD (optional)'}</span>
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={(e) => setJobDescriptionFile(e.target.files?.[0])}
                    />
                  </label>
                </div>
              </div>

              <div className="interview-schedule__field">
                <label>Job Description (paste text)</label>
                <textarea
                  rows={4}
                  placeholder="Paste the JD or key requirements"
                  value={formData.jobDescriptionText}
                  onChange={(e) => handleChange('jobDescriptionText', e.target.value)}
                />
              </div>

              <div className="interview-schedule__field">
                <label>Notes (optional)</label>
                <textarea
                  rows={3}
                  placeholder="Share any notes for interviewer or candidate"
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                />
              </div>

              <Button variant="primary" fullWidth size="large" type="submit">
                {submitting ? 'Generating...' : 'Generate Interview Links'}
              </Button>
              {error && <p className="interview-schedule__error">{error}</p>}
            </form>
          </Card>

          <Card title="Share Links" padding="large" className="interview-schedule__confirmation">
            {confirmation ? (
              <>
                <div className="interview-schedule__summary">
                  <div>
                    <h3>{confirmation.candidate_name} — {confirmation.role}</h3>
                    <p>{confirmation.round_type} | {new Date(confirmation.scheduled_at).toLocaleString()}</p>
                    {confirmation.notes && <p className="interview-schedule__notes">Notes: {confirmation.notes}</p>}
                  </div>
                  <div className="interview-schedule__badge">Interview ID: {confirmation.id}</div>
                </div>

                <div className="interview-schedule__links">
                  <div className="interview-schedule__link">
                    <div>
                      <p>Interviewer Link</p>
                      <span>{links?.interviewer}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="small"
                      icon={copied === 'interviewer' ? <FiCheck /> : <FiClipboard />}
                      onClick={() => handleCopy(links?.interviewer, 'interviewer')}
                    >
                      {copied === 'interviewer' ? 'Copied' : 'Copy'}
                    </Button>
                  </div>
                  <div className="interview-schedule__link">
                    <div>
                      <p>Candidate Link</p>
                      <span>{links?.candidate}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="small"
                      icon={copied === 'candidate' ? <FiCheck /> : <FiClipboard />}
                      onClick={() => handleCopy(links?.candidate, 'candidate')}
                    >
                      {copied === 'candidate' ? 'Copied' : 'Copy'}
                    </Button>
                  </div>
                </div>

                <div className="interview-schedule__hint">
                  Share these links via email or WhatsApp with the interviewer and candidate.
                </div>
              </>
            ) : (
              <div className="interview-schedule__empty">
                <p>Fill in the schedule form to generate secure join links.</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
