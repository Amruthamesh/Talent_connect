import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import GuestLayout from '@layouts/GuestLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { useInterviewStore } from '@store/interviewStore'
import './style.scss'

export default function InterviewJoinRouter() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const key = searchParams.get('key')
  const resolveKey = useInterviewStore((state) => state.resolveKey)
  const syncInterview = useInterviewStore((state) => state.syncInterview)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const run = async () => {
      if (!key) {
        setError('Missing interview key. Please use the link shared with you.')
        setLoading(false)
        return
      }
      try {
        const result = await resolveKey(key)
        syncInterview(result.interview)
        const destination =
          result.role === 'interviewer'
            ? `/interview/lobby/interviewer/${result.interview.id}`
            : `/interview/lobby/candidate/${result.interview.id}`
        // Persist key for downstream pages (lobby → session)
        const storageKey =
          result.role === 'interviewer'
            ? `interview-key-interviewer-${result.interview.id}`
            : `interview-key-candidate-${result.interview.id}`
        sessionStorage.setItem(storageKey, key)
        navigate(destination, { replace: true, state: { key } })
      } catch (err) {
        setError(err.message || 'Invalid or expired link. Ask the HR team for a fresh invite.')
        setLoading(false)
      }
    }
    run()
  }, [key, resolveKey, navigate, syncInterview])

  return (
    <GuestLayout>
      <div className="join-router">
        <Card title="Checking your invite">
          {error ? (
            <>
              <p className="join-router__message join-router__message--error">{error}</p>
              <Button variant="primary" onClick={() => navigate('/login')}>
                Go to login
              </Button>
            </>
          ) : (
            <p className="join-router__message">
              {loading ? 'Verifying your link and redirecting...' : 'Redirecting...'}
            </p>
          )}
        </Card>
      </div>
    </GuestLayout>
  )
}
