import React from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import { FiMessageSquare, FiFileText } from 'react-icons/fi'
import './style.scss'

export default function DocumentTemplates() {
  const navigate = useNavigate()

  return (
    <AppLayout>
      <div className="document-choice">
        <div className="document-choice__header">
          <h1>Generate HR Documents</h1>
          <p>Choose how you'd like to create your HR documents</p>
        </div>

        <div className="document-choice__options">
          <Card className="choice-card choice-card--highlighted">
            <div className="choice-card__icon choice-card__icon--chat">
              <FiMessageSquare />
            </div>
            <h2>Chat with AI Assistant</h2>
            <p className="choice-card__description">
              Have a natural conversation with our AI assistant. Simply describe the document type, and we'll guide you through collecting all the necessary details.
            </p>
            
            <ul className="choice-card__features">
              <li>
                <span className="feature-icon">✨</span>
                Smart follow-up questions
              </li>
              <li>
                <span className="feature-icon">💬</span>
                Quick & conversational
              </li>
              <li>
                <span className="feature-icon">📋</span>
                Bulk CSV upload support
              </li>
            </ul>

            <div className="choice-card__recommendation">
              <strong>Best for:</strong>
              <p>Quick document generation, when you prefer AI guidance, or bulk document creation via CSV upload</p>
            </div>

            <Button 
              variant="primary" 
              icon={<FiMessageSquare />}
              onClick={() => navigate('/documents/agent')}
              className="choice-card__button"
            >
              Start Conversation
            </Button>
          </Card>

          <Card className="choice-card">
            <div className="choice-card__icon choice-card__icon--form">
              <FiFileText />
            </div>
            <h2>Use Template Manually</h2>
            <p className="choice-card__description">
              Browse our pre-built letter templates for various HR needs. Select a template and fill in the details manually.
            </p>
            
            <ul className="choice-card__features">
              <li>
                <span className="feature-icon">📝</span>
                Traditional template interface
              </li>
              <li>
                <span className="feature-icon">🎯</span>
                Full control over fields
              </li>
              <li>
                <span className="feature-icon">🔍</span>
                Direct & precise
              </li>
            </ul>

            <div className="choice-card__recommendation">
              <strong>Best for:</strong>
              <p>Single document creation when you have all details prepared, or when you prefer manual template selection</p>
            </div>

            <Button 
              variant="outline" 
              icon={<FiFileText />}
              onClick={() => navigate('/documents/library')}
              className="choice-card__button"
            >
              Browse Templates
            </Button>
          </Card>
        </div>

        <div className="document-choice__tip">
          <strong>Tip:</strong> Both options lead to the same result – a comprehensive, AI-generated HR document. Choose whichever feels more comfortable for you.
        </div>
      </div>
    </AppLayout>
  )
}
