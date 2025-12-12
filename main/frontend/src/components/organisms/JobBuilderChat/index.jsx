import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '@components/atoms/Button'
import Input from '@components/atoms/Input'
import TypingIndicator from '@components/atoms/TypingIndicator'
import Badge from '@components/atoms/Badge'
import ChatMessage from '@components/molecules/ChatMessage'
import DataSummary from '@components/molecules/DataSummary'
import { FiSend, FiCheck, FiFileText, FiX } from 'react-icons/fi'
import toast from 'react-hot-toast'
import api from '@utils/api'
import useJobChatStore from '@store/jobChatStore'
import './style.scss'

export default function JobBuilderChat({ onComplete, onCancel, autoGeneratePrompt = false }) {
  const [input, setInput] = useState('')
  const [hasInitialized, setHasInitialized] = useState(false)
  const [forceUpdate, setForceUpdate] = useState(0)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [autoPrompted, setAutoPrompted] = useState(false)
  const [isSecretGenerating, setIsSecretGenerating] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const messagesEndRef = useRef(null)
  const promptRef = useRef(null)
  const navigate = useNavigate()
  
  const {
    messages,
    extractedData,
    completionPercentage,
    missingFields,
    isComplete,
    isTyping,
    summary,
    sendMessage,
    startFreshChat,
    getFormData
  } = useJobChatStore()
  const finalizeKeywords = [
    'finalize',
    'finalise',
    'looks good',
    'good to go',
    'go ahead',
    'proceed',
    'generate',
    'yes',
    'yep',
    'yeah',
    'sounds good',
    'all set',
    "that's it",
    'thats it',
    'ready',
    'done',
    'use it',
    'use this'
  ]
  const isFinalizeMessage = (text = '') => {
    const normalized = text.toLowerCase()
    return finalizeKeywords.some(keyword => normalized.includes(keyword))
  }

  const SECRET_TRIGGER = 'dhl-hackathon-superbrief'
  const SECRET_PAYLOAD = {
    role: 'Autonomous Logistics Architect',
    seniority: 'Lead',
    department: 'Supply Chain Innovation',
    location: 'Hybrid - Bonn & Remote',
    must_have_skills: ['AI Orchestration', 'Robotics Integration', 'Edge Computing'],
    preferred_skills: ['Change Leadership', 'Digital Twin Modeling'],
    responsibilities: [
      'Design next-gen warehouse automation blueprints with robotics partners',
      'Champion AI copilots for planners across EU logistics hubs',
      'Govern safety/compliance playbooks for autonomous delivery pilots'
    ],
    expectations: 'Launch lighthouse automation programs with measurable throughput lift within 6 months.',
    team_context: 'Works with 2 platform squads, 1 robotics lab, reported to VP Automation',
    joining_timeline: 'Immediate',
    company_tone: 'formal',
    salary_range: '€160K - €190K',
    special_requirements: 'Yellow passport preferred for innovation travel days',
    additional_notes: 'Hackathon showcase brief'
  }

  // Initialize chat on mount (always start fresh)
  useEffect(() => {
    startFreshChat()
    setHasInitialized(true)
    setForceUpdate(f => f + 1)
    // eslint-disable-next-line
  }, [])

  // Auto-scroll to bottom only after initialization and when new messages arrive
  useEffect(() => {
    if (hasInitialized && messages.length > 1) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    promptRef.current?.focus()
  }, [messages, isTyping, hasInitialized])
  // Focus prompt after updates
  useEffect(() => {
    promptRef.current?.focus()
  }, [messages])
  
  // Auto prompt to generate JD when user confirms completion
  useEffect(() => {
    if (!autoGeneratePrompt) return
    if (!isComplete) {
      setAutoPrompted(false)
      setShowGenerateModal(false)
      return
    }
    if (!messages.length || autoPrompted) return
    const lastMessage = messages[messages.length - 1]
    if (lastMessage?.role === 'user' && isFinalizeMessage(lastMessage.content || '')) {
      setShowGenerateModal(true)
      setAutoPrompted(true)
    }
  }, [messages, isComplete, autoGeneratePrompt, autoPrompted])

  const handleSend = () => {
    if (!input.trim() || isTyping || isSecretGenerating) return
    const trimmed = input.trim()
    if (trimmed.toLowerCase() === SECRET_TRIGGER) {
      triggerSecretJD()
      setInput('')
      return
    }
    
    sendMessage(trimmed)
    setInput('')
    promptRef.current?.focus()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleUseData = async (source = 'button') => {
    const formData = getFormData()
    
    // Generate JD directly
    if (source === 'modal' || source === 'button') {
      await handleGenerateJD(formData)
    } else if (onComplete) {
      onComplete(formData, { source })
    }
    setShowGenerateModal(false)
  }
  
  const handleGenerateJD = async (formData) => {
    setIsGenerating(true)
    toast.loading('Generating your job description...', { id: 'jd-generation' })
    
    try {
      const payload = {
        role: formData.role || '',
        seniority: formData.seniority || 'Mid',
        location: formData.location || '',
        must_have_skills: formData.must_have_skills || [],
        company_tone: 'formal',
        // Optional fields - send only if provided
        ...(formData.expectations && { expectations: formData.expectations }),
        ...(formData.department && { department: formData.department }),
        ...(formData.preferred_skills?.length > 0 && { preferred_skills: formData.preferred_skills }),
      }
      
      console.log('Sending JD generation payload:', payload)
      const response = await api.post('/jobs/generate-jd', payload)
      toast.success('Job description generated successfully!', { id: 'jd-generation' })
      
      navigate('/jobs/results', {
        state: {
          generatedJD: response,
          formData: payload
        }
      })
    } catch (error) {
      console.error('Generation failed', error)
      toast.error(error.message || 'Failed to generate JD. Please try again.', { id: 'jd-generation' })
    } finally {
      setIsGenerating(false)
    }
  }
  
  const handleOpenGenerateModal = () => {
    setShowGenerateModal(true)
    setAutoPrompted(true)
  }
  
  const handleCloseGenerateModal = () => {
    setShowGenerateModal(false)
  }

  const triggerSecretJD = async () => {
    if (isSecretGenerating) return
    setIsSecretGenerating(true)
    toast.loading('🔥 Hackathon brief unlocked! Generating showcase JD...', { icon: '🚀', id: 'secret-jd-generation' })
    try {
      const response = await api.post('/jobs/generate-jd', SECRET_PAYLOAD)
      toast.success('Showcase JD generated successfully!', { id: 'secret-jd-generation' })
      navigate('/jobs/results', {
        state: {
          generatedJD: response,
          formData: SECRET_PAYLOAD,
          secretUnlocked: true
        }
      })
    } catch (error) {
      console.error('Secret generation failed', error)
      toast.error('Secret generator is busy. Try again!', { id: 'secret-jd-generation' })
    } finally {
      setIsSecretGenerating(false)
    }
  }

  return (
    <div className="job-builder-chat">
      {/* Loading Overlay for JD Generation */}
      {isGenerating && (
        <div className="job-builder-chat__loading-overlay">
          <div className="loading-content">
            <div className="spinner"></div>
            <h2>Generating Your Job Description</h2>
            <p>Our AI is crafting a comprehensive, market-aligned job description...</p>
            <div className="loading-steps">
              <div className="step">✓ Analyzing role requirements</div>
              <div className="step">✓ Benchmarking skills & salary</div>
              <div className="step active">⟳ Generating detailed content</div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay for Secret JD */}
      {isSecretGenerating && (
        <div className="job-builder-chat__loading-overlay">
          <div className="loading-content">
            <div className="spinner"></div>
            <h2>🔥 Hackathon Mode Activated!</h2>
            <p>Generating showcase job description with premium features...</p>
            <div className="loading-steps">
              <div className="step">✓ Secret payload unlocked</div>
              <div className="step">✓ Premium AI model activated</div>
              <div className="step active">⟳ Crafting showcase JD</div>
            </div>
          </div>
        </div>
      )}

      <div className="job-builder-chat__container">
        {/* Chat Messages */}
        <div className="job-builder-chat__messages">
          <div className="messages-list">
            {messages.map((msg, index) => (
              <ChatMessage
                key={index}
                sender={msg.role}
                message={msg.content}
                timestamp={msg.timestamp}
                className={msg.isError ? 'message-error' : ''}
              />
            ))}
            
            {isTyping && <TypingIndicator />}

            {isComplete && summary && (
              <div className="completion-card">
                <div className="completion-card__header">
                  <FiCheck size={24} className="icon-success" />
                  <h3>All information collected!</h3>
                </div>
                <div className="completion-card__content">
                  <p>I've gathered all the details we need. Here's a summary:</p>
                  <div className="summary-text">
                    {summary.split('\n\n').map((section, i) => (
                      <p key={i}>{section}</p>
                    ))}
                  </div>
                </div>
                <div className="completion-card__actions">
                  <Button 
                    variant="primary" 
                    icon={autoGeneratePrompt ? <FiFileText /> : <FiCheck />}
                    onClick={autoGeneratePrompt ? handleOpenGenerateModal : () => handleUseData('button')}
                    size="large"
                  >
                    {autoGeneratePrompt ? 'Generate Detailed JD' : 'Use This Data'}
                  </Button>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Data Summary Sidebar */}
        <div className="job-builder-chat__sidebar">
          <DataSummary 
            data={extractedData}
            missingFields={missingFields}
            completionPercentage={completionPercentage}
          />
          
          {onCancel && (
            <Button 
              variant="ghost" 
              onClick={onCancel}
              fullWidth
              className="cancel-button"
            >
              Cancel & Use Form
            </Button>
          )}
        </div>
      </div>

      {/* Chat Input */}
      {!isComplete && (
        <div className="job-builder-chat__input">
          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                ref={promptRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type your message..."
                disabled={isTyping || isSecretGenerating}
                rows={1}
              />
            </div>
            <button
              className="send-button"
              onClick={handleSend}
              disabled={!input.trim() || isTyping || isSecretGenerating}
              aria-label="Send message"
            >
              <FiSend />
            </button>
          </div>
        </div>
      )}
      
      {autoGeneratePrompt && showGenerateModal && (
        <div className="job-builder-chat__modal-overlay">
          <div className="job-builder-chat__modal">
            <button className="modal-close" onClick={handleCloseGenerateModal} aria-label="Close">
              <FiX />
            </button>
            <div className="modal-body">
              <Badge variant="primary" size="small">Ready for next step</Badge>
              <h2>Generate a detailed job description?</h2>
              <p>We've captured everything the role needs. I can now craft a complete JD with responsibilities, salary benchmarks, and insights.</p>
              
              {summary ? (
                <div className="modal-summary-text">
                  {summary.split('\n\n').map((section, i) => (
                    <p key={i}>{section}</p>
                  ))}
                </div>
              ) : (
                <ul className="modal-details">
                  <li><span>Role</span><strong>{extractedData.role || 'Not provided yet'}</strong></li>
                  <li><span>Seniority</span><strong>{extractedData.seniority || 'Not provided yet'}</strong></li>
                  <li><span>Location</span><strong>{extractedData.location || 'Not provided yet'}</strong></li>
                  <li><span>Must-have skills</span><strong>{extractedData.must_have_skills?.join(', ') || 'Pending'}</strong></li>
                </ul>
              )}
            </div>
            <div className="modal-actions">
              <Button 
                variant="primary" 
                size="large" 
                icon={<FiFileText />} 
                fullWidth 
                onClick={() => handleUseData('modal')}
              >
                Generate Job Description
              </Button>
              <Button 
                variant="ghost" 
                size="large" 
                fullWidth 
                onClick={handleCloseGenerateModal}
              >
                Maybe Later
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
