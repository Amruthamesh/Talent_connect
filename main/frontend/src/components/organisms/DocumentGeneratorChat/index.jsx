import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '@components/atoms/Button'
import { FiSend, FiX } from 'react-icons/fi'
import toast from 'react-hot-toast'
import api from '@utils/api'
import './style.scss'

export default function DocumentGeneratorChat({ onComplete, onCancel }) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const [templates, setTemplates] = useState([])
  const messagesEndRef = useRef(null)
  const promptRef = useRef(null)
  const navigate = useNavigate()

  // Fetch available templates on mount
  useEffect(() => {
    fetchTemplates()
    // Initial greeting
    setMessages([{
      role: 'assistant',
      content: "Hello! I'm here to help you create employment documents.\n\n**What type of document would you like to create?**",
      timestamp: new Date()
    }])
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    promptRef.current?.focus()
  }, [messages, isTyping])

  const fetchTemplates = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const response = await api.get('/documents/templates', {
        headers: { Authorization: `Bearer ${user.token}` }
      })
      setTemplates(response.templates || [])
    } catch (error) {
      console.error('Failed to fetch templates:', error)
      // Fallback templates
      setTemplates([
        { id: 'offer_letter', name: 'Offer Letter' },
        { id: 'appointment_letter', name: 'Appointment Letter' },
        { id: 'increment_letter', name: 'Increment Letter' },
        { id: 'transfer_letter', name: 'Transfer Letter' },
        { id: 'confirmation_letter', name: 'Confirmation Letter' },
        { id: 'relieving_letter', name: 'Relieving Letter' }
      ])
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isTyping) return
    
    const trimmed = input.trim()
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: trimmed,
      timestamp: new Date()
    }])
    
    setInput('')
    setIsTyping(true)

    try {
      // Simple document type detection
      const lowerInput = trimmed.toLowerCase()
      let detectedTemplate = null
      
      for (const template of templates) {
        const templateName = template.name.toLowerCase()
        if (lowerInput.includes(templateName) || lowerInput.includes(template.id)) {
          detectedTemplate = template
          break
        }
      }

      if (detectedTemplate) {
        // Template detected - navigate to document agent
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Great! I'll help you create a **${detectedTemplate.name}**.\n\nRedirecting you to the document builder...`,
          timestamp: new Date()
        }])
        
        setTimeout(() => {
          navigate('/documents/agent', {
            state: { selectedTemplate: detectedTemplate.id }
          })
        }, 1500)
      } else {
        // Show template options
        const templateList = templates.map(t => `• ${t.name}`).join('\n')
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `I can help you create the following documents:\n\n${templateList}\n\nWhich one would you like to create?`,
          timestamp: new Date()
        }])
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error. Please try again.',
        timestamp: new Date()
      }])
    }

    setIsTyping(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="job-builder-chat">
      <div className="job-builder-chat__container">
        <div className="job-builder-chat__messages">
          <div className="messages-list">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message chat-message--${msg.role}`}>
                <div className="chat-message__content">
                  <div className="chat-message__avatar">
                    {msg.role === 'assistant' ? '🤖' : '👤'}
                  </div>
                  <div className="chat-message__bubble">
                    <div 
                      className="message-text"
                      dangerouslySetInnerHTML={{ 
                        __html: msg.content
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br/>') 
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="typing-indicator">
                <div className="typing-content">
                  <div className="typing-avatar">🤖</div>
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="job-builder-chat__input">
          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                ref={promptRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type your message..."
                disabled={isTyping}
                rows={1}
              />
            </div>
            <button 
              className="send-button"
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
            >
              <FiSend />
            </button>
          </div>
        </div>
      </div>

      <div className="job-builder-chat__sidebar">
        <div className="data-summary">
          <div className="data-summary__header">
            <h4>📋 Available Documents</h4>
          </div>
          <div className="data-summary__fields">
            {templates.map((template) => (
              <div 
                key={template.id}
                className="data-summary__field"
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setInput(template.name)
                  promptRef.current?.focus()
                }}
              >
                <div className="field-label">
                  <span className="icon-missing">📄</span>
                  <span>{template.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {onCancel && (
          <Button
            variant="ghost"
            size="small"
            onClick={onCancel}
            className="cancel-button"
            fullWidth
          >
            <FiX /> Cancel & Use Form
          </Button>
        )}
      </div>
    </div>
  )
}
