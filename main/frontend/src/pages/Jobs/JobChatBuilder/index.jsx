import React from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Badge from '@components/atoms/Badge'
import JobBuilderChat from '@components/organisms/JobBuilderChat'
import './style.scss'

export default function JobChatBuilder() {
  const navigate = useNavigate()

  // Handle completion - directly generate JD and navigate to results
  const handleChatComplete = async (formData, options = {}) => {
    // Always generate JD directly from chat
    navigate('/jobs/generator', {
      state: {
        fromChat: true,
        formData,
        autoGenerate: true
      }
    })
  }

  const handleCancel = () => {
    // Optional: Navigate back or to dashboard
    navigate('/dashboard')
  }

  return (
    <AppLayout>
      <div className="job-chat-builder">
        <div className="job-chat-builder__header">
          <div>
            <h1>Create Job Description</h1>
            <p>Tell me about the role you're hiring for, and I'll help you create a comprehensive job description</p>
          </div>
          <Badge variant="primary" size="medium">💬 Chat Mode</Badge>
        </div>

        <Card 
          padding="none"
          className="job-chat-builder__card"
        >
          <JobBuilderChat 
            onComplete={handleChatComplete}
            onCancel={handleCancel}
            autoGeneratePrompt
          />
        </Card>

        <div className="job-chat-builder__footer">
          <p className="hint">
            <strong>Tip:</strong> Just describe the role naturally. I'll ask follow-up questions to gather all the details we need.
          </p>
        </div>
      </div>
    </AppLayout>
  )
}
