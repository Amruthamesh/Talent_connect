import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import Button from '@components/atoms/Button'
import ChatMessage from '@components/molecules/ChatMessage'
import TypingIndicator from '@components/atoms/TypingIndicator'
import { FiSend } from 'react-icons/fi'
import './style.scss'

export default function DocumentChatAdapter({ onComplete }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [currentStep, setCurrentStep] = useState('template_selection')
  const [collectedData, setCollectedData] = useState({})
  const [requiredFields, setRequiredFields] = useState([])
  const messagesEndRef = useRef(null)
  const promptRef = useRef(null)
  
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

  // Start conversation on mount
  useEffect(() => {
    startConversation()
  }, [])

  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    promptRef.current?.focus()
  }, [messages, loading])

  const startConversation = async () => {
    try {
      setLoading(true)
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token
      
      const response = await axios.post(
        `${API_BASE}/documents/agent/start`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      console.log('Start conversation response:', response.data)
      
      setSessionId(response.data.session_id)
      const availableTemplates = response.data.options || response.data.templates || []
      setTemplates(availableTemplates)
      
      // Build message with template list (avoid question marks to prevent bubble splitting)
      let messageContent = response.data.message.replace(/\?$/, ':')
      if (availableTemplates.length > 0) {
        const templateList = availableTemplates.map(t => `• ${t.name}`).join('\n')
        messageContent = `${response.data.message.replace(/\?$/, ':')}\n\n${templateList}\n\nWhich document would you like to create`
      }
      
      setMessages([{
        id: 'start-1',
        role: 'assistant',
        content: messageContent,
        timestamp: new Date()
      }])
    } catch (error) {
      console.error('Failed to start conversation:', error)
      setMessages([{
        id: 'error-1',
        role: 'assistant',
        content: 'Sorry, I encountered an error starting the conversation. Please refresh and try again.',
        timestamp: new Date()
      }])
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { id: `u-${Date.now()}`, role: 'user', content: text, timestamp: new Date() }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token
      
      // Try AI chat endpoint first
      try {
        const chatResponse = await axios.post(
          `${API_BASE}/documents/chat`,
          {
            message: text,
            session_id: sessionId,
            conversation_history: messages.map(m => ({
              role: m.role,
              content: m.content
            })),
            available_templates: templates
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )

        const assistantMsg = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: chatResponse.data.reply,
          timestamp: new Date()
        }
        setMessages((m) => [...m, assistantMsg])

        // Handle actions from AI
        if (chatResponse.data.action === 'template_selected' && chatResponse.data.action_data) {
          setSelectedTemplate(chatResponse.data.action_data)
          setCurrentStep('ask_method')
        } else if (chatResponse.data.action === 'method_selected' && chatResponse.data.action_data) {
          if (chatResponse.data.action_data.method === 'manual_entry') {
            setCurrentStep('collecting_fields')
          }
        } else if (chatResponse.data.action === 'generate_document') {
          // AI detected user wants to generate - trigger generation
          setCurrentStep('confirm_generation')
        }

        // If AI marks conversation as complete, trigger document generation
        if (chatResponse.data.is_complete) {
          try {
            const generateResponse = await axios.post(
              `${API_BASE}/documents/agent/generate`,
              {
                session_id: sessionId,
                format: 'pdf'
              },
              { headers: { Authorization: `Bearer ${token}` } }
            )

            const successMsg = {
              id: `a-${Date.now() + 1}`,
              role: 'assistant',
              content: `✅ Document generated successfully!\n\n${generateResponse.data.generated_count} ${selectedTemplate?.name || 'document'}(s) created.\n\nDownloading now...`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, successMsg])
            
            // Trigger download for generated documents
            const documentIds = generateResponse.data.document_ids || []
            if (documentIds.length > 0) {
              for (const docId of documentIds) {
                try {
                  const downloadResponse = await axios.get(
                    `${API_BASE}/documents/${docId}/download?format=pdf`,
                    { 
                      headers: { Authorization: `Bearer ${token}` },
                      responseType: 'blob'
                    }
                  )
                  
                  const blob = new Blob([downloadResponse.data], { type: 'application/pdf' })
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.setAttribute('download', `${selectedTemplate?.name?.replace(/\s+/g, '_') || 'document'}_${docId}.pdf`)
                  document.body.appendChild(link)
                  link.click()
                  link.remove()
                  window.URL.revokeObjectURL(url)
                } catch (downloadErr) {
                  console.error(`Failed to download document ${docId}:`, downloadErr)
                }
              }
              
              setTimeout(() => {
                const doneMsg = {
                  id: `a-${Date.now() + 2}`,
                  role: 'assistant',
                  content: `📥 Download complete! Check your downloads folder.`,
                  timestamp: new Date()
                }
                setMessages((m) => [...m, doneMsg])
              }, 1000)
            }
            
            // Navigate to document library
            setTimeout(() => {
              if (typeof onComplete === 'function') {
                onComplete(generateResponse.data)
              }
            }, 3000)
          } catch (genErr) {
            console.error('Auto-generation error:', genErr)
            const errorMsg = {
              id: `e-${Date.now() + 1}`,
              role: 'assistant',
              content: `I have all the information, but encountered an error generating the document. Please try again.`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, errorMsg])
          }
        }
        
        return // Exit early if chat endpoint succeeded
      } catch (chatErr) {
        console.log('Chat endpoint failed, using fallback:', chatErr.message)
      }

      // Fallback: Use conversational flow with context
      if (currentStep === 'template_selection') {
        const matchedTemplate = templates.find(t => 
          t.name.toLowerCase().includes(text.toLowerCase()) || 
          text.toLowerCase().includes(t.name.toLowerCase())
        )

        if (matchedTemplate) {
          const response = await axios.post(
            `${API_BASE}/documents/agent/select-template`,
            {
              session_id: sessionId,
              template_id: matchedTemplate.id
            },
            { headers: { Authorization: `Bearer ${token}` } }
          )

          setSelectedTemplate(matchedTemplate)
          setRequiredFields(response.data.required_fields || [])
          setCurrentStep('ask_method')

          const assistantMsg = {
            id: `a-${Date.now()}`,
            role: 'assistant',
            content: `Perfect! I'll help you create a ${matchedTemplate.name}.\n\nHow would you like to provide the information:\n• Type the details manually (I'll guide you)\n• Upload a CSV file with multiple entries\n• Download a CSV template to fill offline`,
            timestamp: new Date()
          }
          setMessages((m) => [...m, assistantMsg])
        } else {
          // Provide helpful suggestions based on what they typed
          const suggestions = templates.filter(t => {
            const keywords = text.toLowerCase().split(' ')
            return keywords.some(kw => t.name.toLowerCase().includes(kw))
          })

          let content
          if (suggestions.length > 0) {
            const suggestionList = suggestions.map(t => `• ${t.name}`).join('\n')
            content = `Did you mean one of these:\n\n${suggestionList}\n\nOr you can ask me about any of our document types`
          } else {
            const templateList = templates.map(t => `• ${t.name}`).join('\n')
            content = `I didn't quite catch that. Here are the documents I can create:\n\n${templateList}\n\nWhich one do you need`
          }

          const assistantMsg = {
            id: `a-${Date.now()}`,
            role: 'assistant',
            content,
            timestamp: new Date()
          }
          setMessages((m) => [...m, assistantMsg])
        }
      } else if (currentStep === 'ask_method') {
        const lowerText = text.toLowerCase()
        let content

        if (lowerText.includes('manual') || lowerText.includes('type') || lowerText.includes('guide')) {
          content = `Great! I'll guide you through each field.\n\nFor a ${selectedTemplate.name}, I need:\n${requiredFields.map(f => `• ${f.replace(/_/g, ' ')}`).join('\n')}\n\nLet's start - what is the employee name`
          setCurrentStep('collecting_fields')
        } else if (lowerText.includes('csv') || lowerText.includes('upload')) {
          content = `Perfect! Please upload your CSV file with the required columns:\n${requiredFields.map(f => `• ${f}`).join('\n')}\n\nMake sure your CSV includes these fields with the exact column names`
          setCurrentStep('awaiting_csv')
        } else if (lowerText.includes('download') || lowerText.includes('template')) {
          content = `I'll prepare a CSV template for you. Once downloaded, fill it with your data and upload it back.\n\nThe template includes:\n${requiredFields.map(f => `• ${f}`).join('\n')}\n\nClick the download button that appears below`
          setCurrentStep('template_download')
        } else {
          content = `I can help you in three ways:\n\n1. **Manual entry** - I'll ask you for each detail step by step\n2. **CSV upload** - Upload a file with multiple employee records\n3. **Download template** - Get a CSV template to fill offline\n\nWhich method works best for you`
        }

        const assistantMsg = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content,
          timestamp: new Date()
        }
        setMessages((m) => [...m, assistantMsg])
      } else if (currentStep === 'collecting_fields') {
        // Collect field values one by one
        const currentFieldIndex = Object.keys(collectedData).length
        const currentField = requiredFields[currentFieldIndex]
        
        if (currentField) {
          setCollectedData(prev => ({ ...prev, [currentField]: text }))
          
          const nextFieldIndex = currentFieldIndex + 1
          if (nextFieldIndex < requiredFields.length) {
            const nextField = requiredFields[nextFieldIndex]
            const assistantMsg = {
              id: `a-${Date.now()}`,
              role: 'assistant',
              content: `Got it! Next, what is the ${nextField.replace(/_/g, ' ')}`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, assistantMsg])
          } else {
            const assistantMsg = {
              id: `a-${Date.now()}`,
              role: 'assistant',
              content: `Perfect! I have all the information I need:\n\n${Object.entries({ ...collectedData, [currentField]: text }).map(([k, v]) => `• ${k.replace(/_/g, ' ')}: ${v}`).join('\n')}\n\nShall I generate the document now`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, assistantMsg])
            setCurrentStep('confirm_generation')
          }
        }
      } else if (currentStep === 'confirm_generation') {
        if (text.toLowerCase().includes('yes') || text.toLowerCase().includes('generate') || text.toLowerCase().includes('proceed')) {
          const assistantMsg = {
            id: `a-${Date.now()}`,
            role: 'assistant',
            content: `Generating your ${selectedTemplate.name} now...`,
            timestamp: new Date()
          }
          setMessages((m) => [...m, assistantMsg])
          
          // Call the generate endpoint
          try {
            const generateResponse = await axios.post(
              `${API_BASE}/documents/agent/generate`,
              {
                session_id: sessionId,
                format: 'pdf'
              },
              { headers: { Authorization: `Bearer ${token}` } }
            )

            const successMsg = {
              id: `a-${Date.now()}`,
              role: 'assistant',
              content: `✅ Success! Your ${selectedTemplate.name} has been generated.\n\nGenerated ${generateResponse.data.generated_count} document(s).\n\nDownloading now...`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, successMsg])
            
            // Trigger download for generated documents
            const documentIds = generateResponse.data.document_ids || []
            if (documentIds.length > 0) {
              // Download all generated documents
              for (const docId of documentIds) {
                try {
                  const downloadResponse = await axios.get(
                    `${API_BASE}/documents/${docId}/download?format=pdf`,
                    { 
                      headers: { Authorization: `Bearer ${token}` },
                      responseType: 'blob'
                    }
                  )
                  
                  // Create download link
                  const blob = new Blob([downloadResponse.data], { type: 'application/pdf' })
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.setAttribute('download', `${selectedTemplate.name.replace(/\s+/g, '_')}_${docId}.pdf`)
                  document.body.appendChild(link)
                  link.click()
                  link.remove()
                  window.URL.revokeObjectURL(url)
                } catch (downloadErr) {
                  console.error(`Failed to download document ${docId}:`, downloadErr)
                }
              }
              
              // Show completion message
              setTimeout(() => {
                const doneMsg = {
                  id: `a-${Date.now()}`,
                  role: 'assistant',
                  content: `📥 Download complete! Your document${documentIds.length > 1 ? 's have' : ' has'} been saved.\n\nYou can also view ${documentIds.length > 1 ? 'them' : 'it'} in the Document Library.`,
                  timestamp: new Date()
                }
                setMessages((m) => [...m, doneMsg])
              }, 1000)
            }
            
            // Navigate to document library after downloads
            setTimeout(() => {
              if (typeof onComplete === 'function') {
                onComplete(generateResponse.data)
              }
            }, 3000)
          } catch (genErr) {
            console.error('Generation error:', genErr)
            const errorMsg = {
              id: `e-${Date.now()}`,
              role: 'assistant',
              content: `❌ Sorry, there was an error generating the document. Please try again or contact support.`,
              timestamp: new Date()
            }
            setMessages((m) => [...m, errorMsg])
          }
        } else {
          const assistantMsg = {
            id: `a-${Date.now()}`,
            role: 'assistant',
            content: `No problem! What would you like to change`,
            timestamp: new Date()
          }
          setMessages((m) => [...m, assistantMsg])
        }
      } else {
        const templateList = templates.map(t => `• ${t.name}`).join('\n')
        const assistantMsg = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: `I can help you with:\n\n${templateList}\n\nJust tell me which type of document you need`,
          timestamp: new Date()
        }
        setMessages((m) => [...m, assistantMsg])
      }
    } catch (err) {
      console.error('Message error:', err)
      const errorMsg = {
        id: `e-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I had trouble processing that. Please try selecting a document type from the list above.',
        timestamp: new Date()
      }
      setMessages((m) => [...m, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="job-builder-chat">
      <div className="job-builder-chat__container">
        <div className="job-builder-chat__messages">
          <div className="messages-list">
            {messages.map((msg, index) => (
              <ChatMessage
                key={index}
                sender={msg.role}
                message={msg.content}
                timestamp={msg.timestamp}
              />
            ))}
            
            {loading && <TypingIndicator />}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      <div className="job-builder-chat__input">
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={promptRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe the document you need and key details (recipient, dates, role, salary, etc.)."
              disabled={loading}
              rows={1}
            />
          </div>
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            aria-label="Send message"
          >
            <FiSend />
          </button>
        </div>
      </div>
    </div>
  )
}
