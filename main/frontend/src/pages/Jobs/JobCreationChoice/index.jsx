import React from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { FiMessageSquare, FiEdit3, FiZap, FiClock } from 'react-icons/fi'
import './style.scss'

export default function JobCreationChoice() {
  const navigate = useNavigate()

  const handleChatChoice = () => {
    navigate('/jobs/create/chat')
  }

  const handleFormChoice = () => {
    navigate('/jobs/create/form')
  }

  return (
    <AppLayout>
      <div className="job-creation-choice">
        <div className="job-creation-choice__header">
          <h1>Create Job Description</h1>
          <p>Choose how you'd like to create your job description</p>
        </div>

        <div className="job-creation-choice__options">
          {/* Chat Option */}
          <Card className="choice-card chat-option" padding="large">
            <div className="choice-card__icon chat-icon">
              <FiMessageSquare size={48} />
            </div>
            
            <h2>Chat with AI Assistant</h2>
            <p className="description">
              Have a natural conversation with our AI assistant. Simply describe the role, 
              and we'll guide you through collecting all the necessary details.
            </p>

            <div className="features">
              <div className="feature">
                <FiZap size={20} />
                <span>Smart follow-up questions</span>
              </div>
              <div className="feature">
                <FiClock size={20} />
                <span>Quick & conversational</span>
              </div>
              <div className="feature">
                <FiMessageSquare size={20} />
                <span>No form to fill</span>
              </div>
            </div>

            <div className="best-for">
              <strong>Best for:</strong> Quick job postings, when you prefer talking over typing, 
              or when you want AI guidance
            </div>

            <Button
              variant="primary"
              size="large"
              fullWidth
              icon={<FiMessageSquare />}
              onClick={handleChatChoice}
              className="choice-button"
            >
              Start Conversation
            </Button>
          </Card>

          {/* Form Option */}
          <Card className="choice-card form-option" padding="large">
            <div className="choice-card__icon form-icon">
              <FiEdit3 size={48} />
            </div>
            
            <h2>Fill Form Manually</h2>
            <p className="description">
              Use our structured form to input all job details directly. 
              Perfect when you have all the information ready.
            </p>

            <div className="features">
              <div className="feature">
                <FiEdit3 size={20} />
                <span>Traditional form interface</span>
              </div>
              <div className="feature">
                <FiZap size={20} />
                <span>Full control over fields</span>
              </div>
              <div className="feature">
                <FiClock size={20} />
                <span>Direct & precise</span>
              </div>
            </div>

            <div className="best-for">
              <strong>Best for:</strong> Detailed job postings, when you have all details prepared, 
              or when you prefer structured forms
            </div>

            <Button
              variant="secondary"
              size="large"
              fullWidth
              icon={<FiEdit3 />}
              onClick={handleFormChoice}
              className="choice-button"
            >
              Open Form
            </Button>
          </Card>
        </div>

        <div className="job-creation-choice__footer">
          <p className="info-text">
            <strong>Tip:</strong> Both options lead to the same result – a comprehensive, 
            AI-generated job description. Choose whichever feels more comfortable for you.
          </p>
        </div>
      </div>
    </AppLayout>
  )
}
