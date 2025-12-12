import React, { useState, useEffect, useRef } from 'react'
import Button from '@components/atoms/Button'
import TypingIndicator from '@components/atoms/TypingIndicator'
import ChatMessage from '@components/molecules/ChatMessage'
import { FiSend, FiEye, FiDownload, FiX, FiUpload } from 'react-icons/fi'
import axios from 'axios'
import './style.scss'

export default function DocumentBuilderChat({ sessionId, templateName, requiredFields = [], optionalFields = [], onComplete }) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const [collectedData, setCollectedData] = useState({})
  const [validationStatus, setValidationStatus] = useState({})
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0)
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [previewHtml, setPreviewHtml] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('pdf')
  const [isGenerating, setIsGenerating] = useState(false)
  const [signatureFile, setSignatureFile] = useState(null)
  const [showTextInput, setShowTextInput] = useState(false)
  const [inputType, setInputType] = useState('text') // 'text', 'date', 'select'
  const [selectOptions, setSelectOptions] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

  const allFields = [...requiredFields, ...optionalFields]
  const currentField = allFields[currentFieldIndex]
  const completionPercentage = allFields.length > 0 
    ? Math.round((Object.keys(collectedData).length / allFields.length) * 100) 
    : 0

  // Get hint/example for a field
  const getFieldHint = (fieldName) => {
    const hints = {
      'employee_name': '💡 Example: John Michael Doe',
      'candidate_name': '💡 Example: Sarah Jane Smith',
      'signatory_name': '💡 Example: Robert Williams',
      'designation': '💡 Example: Senior Software Engineer',
      'current_designation': '💡 Example: Software Engineer',
      'new_designation': '💡 Example: Senior Software Engineer',
      'company_name': '💡 Example: DHL Supply Chain India Pvt Ltd',
      'company_address': '💡 Example: 123 Tech Park, Whitefield, Bangalore 560066',
      'contact_info': '💡 Example: +91-80-12345678 | hr@company.com',
      'salary': '💡 Example: 1200000 (for ₹12 LPA) or 85000 (for $85k)',
      'ctc': '💡 Example: 1500000 (annual package)',
      'new_salary': '💡 Example: 1500000',
      'joining_date': '💡 Example: 01/12/2024 or 2024-12-01',
      'date_of_joining': '💡 Example: 15/01/2025',
      'offer_acceptance_date': '💡 Example: 30/11/2024',
      'last_working_date': '💡 Example: 31/12/2024',
      // Locations
      'current_location': '💡 Example: Chennai (city) or Bengaluru, Karnataka',
      'new_location': '💡 Example: Hyderabad (city) or Pune, Maharashtra',
      'location': '💡 Example: Mumbai',
      'email': '💡 Example: john.doe@company.com',
      'phone_number': '💡 Example: +91-9876543210',
      'employee_code': '💡 Example: EMP2024001',
      'department': '💡 Example: Information Technology',
      'signatory_designation': '💡 Example: Vice President - Human Resources',
    }
    return hints[fieldName] || '💡 Enter the value'
  }

  // Determine if field should use select options
  const getFieldOptions = (fieldName) => {
    const options = {
      'department': [
        'Information Technology',
        'Human Resources',
        'Finance',
        'Operations',
        'Sales',
        'Marketing',
        'Engineering',
        'Customer Service'
      ],
      'location': [
        'Bangalore',
        'Chennai',
        'Mumbai',
        'Delhi',
        'Hyderabad',
        'Pune',
        'Remote'
      ],
      'current_location': [
        'Bangalore',
        'Chennai',
        'Mumbai',
        'Delhi',
        'Hyderabad',
        'Pune'
      ],
      'new_location': [
        'Bangalore',
        'Chennai',
        'Mumbai',
        'Delhi',
        'Hyderabad',
        'Pune'
      ]
    }
    return options[fieldName] || null
  }

  // Check if field is a date field
  const isDateField = (fieldName) => {
    const dateFields = [
      'date', 'joining_date', 'date_of_joining', 'start_date', 'end_date',
      'last_working_date', 'last_working_day', 'effective_date', 'offer_acceptance_date',
      'probation_end_date', 'confirmation_date', 'transfer_date', 'incident_date',
      'issue_date', 'termination_date', 'relieving_date'
    ]
    return dateFields.includes(fieldName?.toLowerCase())
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    inputRef.current?.focus()
  }, [currentField])

  // Start with first field
  useEffect(() => {
    if (currentField && messages.length === 0) {
      const isRequired = requiredFields.includes(currentField)
      const hint = getFieldHint(currentField)
      const options = getFieldOptions(currentField)
      
      // Check field type and set appropriate input mode
      if (options) {
        setSelectOptions(options)
        setShowTextInput(false)
      } else if (isDateField(currentField)) {
        setInputType('date')
        setShowTextInput(true)
      } else {
        setInputType('text')
        setShowTextInput(true)
      }
      
      setMessages([{
        role: 'assistant',
        content: `Perfect! Let's fill this **${templateName}** step by step.\n\nFirst, please provide **${currentField.replace('_', ' ')}**${isRequired ? ' (required)' : ' (optional)'}:\n\n<span class="field-hint">${hint}</span>`,
        timestamp: new Date(),
        fieldOptions: options
      }])
    }
  }, [currentField, templateName, requiredFields, messages.length])

  const handleSignatureUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Validate file type
    if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Please upload a PNG, JPG, or JPEG image file.',
        timestamp: new Date()
      }])
      return
    }

    setSignatureFile(file)
    setIsTyping(true)

    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token

      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)

      const response = await axios.post(
        `${API_BASE}/documents/agent/upload-signature`,
        formData,
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      // Update collected data
      const newData = { ...collectedData, signatory_signature: file.name }
      setCollectedData(newData)
      setValidationStatus(prev => ({ ...prev, signatory_signature: true }))

      // If signature uploaded, auto-skip name and designation fields
      const sigNameIndex = allFields.indexOf('signatory_name')
      const sigDesigIndex = allFields.indexOf('signatory_designation')
      
      if (sigNameIndex !== -1) {
        newData.signatory_name = 'skip'
        setValidationStatus(prev => ({ ...prev, signatory_name: true }))
      }
      if (sigDesigIndex !== -1) {
        newData.signatory_designation = 'skip'
        setValidationStatus(prev => ({ ...prev, signatory_designation: true }))
      }
      
      setCollectedData(newData)

      // Move to next field after signature/name/designation
      let nextIndex = currentFieldIndex + 1
      while (nextIndex < allFields.length && 
             (allFields[nextIndex] === 'signatory_name' || 
              allFields[nextIndex] === 'signatory_designation')) {
        nextIndex++
      }
      setCurrentFieldIndex(nextIndex)

      // Add bot response
      setMessages(prev => [...prev, {
        role: 'user',
        content: `📎 Uploaded: ${file.name}`,
        timestamp: new Date()
      }, {
        role: 'assistant',
        content: '✅ E-signature uploaded successfully! (This will replace signatory name and designation)\n\n' + 
                 (nextIndex < allFields.length 
                   ? `Next, please provide **${allFields[nextIndex].replace('_', ' ')}**:` 
                   : 'All fields completed!'),
        timestamp: new Date()
      }])

      // Check if complete
      if (nextIndex >= allFields.length) {
        setAwaitingConfirmation(true)
      }
    } catch (error) {
      console.error('Failed to upload signature:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error uploading the signature. Please try again.',
        timestamp: new Date()
      }])
    }

    setIsTyping(false)
  }

  // Handle option button click
  const handleOptionClick = async (value) => {
    if (isTyping) return
    
    // Use the same send logic with the value
    await processFieldSubmission(value)
  }

  const handleSend = async () => {
    if (!input.trim() || isTyping) return
    
    const trimmed = input.trim()
    
    await processFieldSubmission(trimmed)
  }

  const processFieldSubmission = async (value) => {
    // Easter egg: autofill command
    if (value.toLowerCase() === 'autofill') {
      const testData = {
        'company_logo': 'skip',
        'company_name': 'DHL Supply Chain India Pvt Ltd',
        'company_address': '123 Tech Park, Whitefield, Bangalore 560066',
        'contact_info': '+91-80-12345678 | hr@dhl.com',
        'employee_name': 'Rajesh Kumar',
        'candidate_name': 'Priya Sharma',
        'designation': 'Senior Software Engineer',
        'current_designation': 'Software Engineer',
        'new_designation': 'Lead Software Engineer',
        'salary': '1500000',
        'ctc': '1500000',
        'new_salary': '1800000',
        'joining_date': '01/12/2024',
        'date_of_joining': '01/12/2024',
        'offer_acceptance_date': '25/11/2024',
        'last_working_date': '30/11/2024',
        'relieving_date': '30/11/2024',
        'confirmation_date': '01/06/2025',
        'email': 'rajesh.kumar@dhl.com',
        'phone_number': '+91-9876543210',
        'employee_code': 'DHL2024001',
        'department': 'Information Technology',
        'signatory_name': 'Amit Verma',
        'signatory_designation': 'Vice President - Human Resources',
        'signatory_signature': 'skip',
        'bonus_amount': '50000',
        'month': 'November 2024',
        'reason_for_termination': 'Performance Issues',
        'termination_date': '31/12/2024',
        'pronoun_subject': 'he',
        'pronoun_possessive': 'his'
      }
      
      // Fill all available fields
      const filledData = {}
      const validationState = {}
      allFields.forEach(field => {
        if (testData[field]) {
          filledData[field] = testData[field]
          validationState[field] = true
        }
      })
      
      setCollectedData(filledData)
      setValidationStatus(validationState)
      setCurrentFieldIndex(allFields.length)
      setAwaitingConfirmation(true)
      
      setMessages(prev => [...prev, {
        role: 'user',
        content: '🎉 autofill',
        timestamp: new Date()
      }, {
        role: 'assistant',
        content: '✨ **Magic!** All fields have been auto-filled with test data.\n\nPlease review the information on the right and confirm when ready.',
        timestamp: new Date()
      }])
      
      setInput('')
      return
    }
    
    // If we're waiting for confirmation, handle it separately
    if (awaitingConfirmation) {
      handleConfirmation(value)
      setInput('')
      return
    }
    
    const fieldName = currentField
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: value,
      timestamp: new Date()
    }])
    
    setInput('')
    setIsTyping(true)

    try {
      // Call backend to submit this field
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token
      
      const response = await axios.post(
        `${API_BASE}/documents/agent/manual-field`,
        {
        session_id: sessionId,
        field_name: fieldName,
        field_value: value
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    )      // Check for validation errors
      if (response.data.validation_error) {
        // Field is invalid - show error and stay on same field
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `❌ ${response.data.error}\n\n${response.data.hint ? `**Hint:** ${response.data.hint}` : ''}\n\nPlease try again:`,
          timestamp: new Date()
        }])
        
        // Mark field as invalid
        setValidationStatus(prev => ({ ...prev, [fieldName]: false }))
        setIsTyping(false)
        return
      }

      // Field is valid - store value and mark as valid
      const newData = { ...collectedData, [fieldName]: value }
      setCollectedData(newData)
      setValidationStatus(prev => ({ ...prev, [fieldName]: true }))

      // Check if we have more fields
      const nextIndex = currentFieldIndex + 1
      setCurrentFieldIndex(nextIndex)

      if (nextIndex < allFields.length) {
        // Ask for next field
        const nextField = allFields[nextIndex]
        const isRequired = requiredFields.includes(nextField)
        const hint = getFieldHint(nextField)
        const nextOptions = getFieldOptions(nextField)
        
        // Set input type for next field
        if (nextOptions) {
          setSelectOptions(nextOptions)
          setShowTextInput(false)
        } else if (isDateField(nextField)) {
          setInputType('date')
          setShowTextInput(true)
        } else {
          setInputType('text')
          setShowTextInput(true)
        }
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✓ **${fieldName.replace('_', ' ')}**: ${value}\n\nNext, please provide **${nextField.replace('_', ' ')}**${isRequired ? ' (required)' : ' (optional)'}:\n\n<span class="field-hint">${hint}</span>`,
          timestamp: new Date(),
          fieldOptions: nextOptions
        }])
      } else {
        // All fields collected - show summary with validation status
        const summary = allFields
          .map(f => {
            const isValid = validationStatus[f] !== false
            const icon = isValid ? '✓' : '❌'
            return `${icon} **${f.replace('_', ' ')}**: ${newData[f] || '(not provided)'}`
          })
          .join('\n')
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✓ Perfect! I've collected all the information:\n\n${summary}\n\nAll fields validated successfully! You can now:\n1. **Preview** the document before generating\n2. **Edit** a field (type the field name to edit)`,
          timestamp: new Date()
        }])
        
        // Set awaiting confirmation flag
        setAwaitingConfirmation(true)
      }
    } catch (error) {
      console.error('Failed to submit field:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error. Please try again.',
        timestamp: new Date()
      }])
    }

    setIsTyping(false)
  }
  
  // Handle preview request
  const handlePreview = async () => {
    setIsTyping(true)
    
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token
      
      const response = await axios.post(
        `${API_BASE}/documents/agent/preview`,
        {
          session_id: sessionId
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      if (response.data.validation_errors && Object.keys(response.data.validation_errors).length > 0) {
        // Show validation errors
        const errors = Object.entries(response.data.validation_errors)
          .map(([field, error]) => `❌ **${field.replace('_', ' ')}**: ${error}`)
          .join('\n')
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Some fields have validation errors:\n\n${errors}\n\nPlease fix these fields before generating.`,
          timestamp: new Date()
        }])
      } else {
        // Show preview
        setPreviewHtml(response.data.preview_html)
        setShowPreview(true)
      }
    } catch (error) {
      console.error('Failed to generate preview:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error generating the preview. Please try again.',
        timestamp: new Date()
      }])
    }
    
    setIsTyping(false)
  }

  // Handle document generation
  const handleGenerate = async () => {
    setIsGenerating(true)
    setShowPreview(false)
    
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: `Generating your ${templateName} as ${selectedFormat.toUpperCase()}...`,
      timestamp: new Date()
    }])
    
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const token = user.token
      
      const response = await axios.post(
        `${API_BASE}/documents/agent/generate`,
        {
          session_id: sessionId,
          format: selectedFormat
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.message || `Document generated successfully! Your ${selectedFormat.toUpperCase()} is ready in the library.`,
        timestamp: new Date()
      }])

      // Call onComplete callback with document IDs
      setTimeout(() => {
        if (onComplete && response.data.document_ids) {
          onComplete(response.data.document_ids)
        }
      }, 1500)
    } catch (error) {
      console.error('Failed to generate document:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error generating the document. Please try again.',
        timestamp: new Date()
      }])
    }
    
    setIsGenerating(false)
  }
  
  // Handle confirmation after all fields collected
  const handleConfirmation = async (userInput) => {
    const input = userInput.trim().toLowerCase()
    
    if (input === 'preview') {
      await handlePreview()
      return
    }
    
    // Check if user wants to edit a field
    const fieldToEdit = allFields.find(f => f.toLowerCase() === input.replace(' ', '_').toLowerCase())
    if (fieldToEdit) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sure! Please provide the new value for **${fieldToEdit.replace('_', ' ')}**:`,
        timestamp: new Date()
      }])
      // Set that field as current to collect again
      const fieldIndex = allFields.indexOf(fieldToEdit)
      setCurrentFieldIndex(fieldIndex)
      setAwaitingConfirmation(false)  // Back to field collection mode
      
      // Set up input for the field being edited
      const options = getFieldOptions(fieldToEdit)
      if (options) {
        setSelectOptions(options)
        setShowTextInput(false)
      } else if (isDateField(fieldToEdit)) {
        setInputType('date')
        setShowTextInput(true)
      } else {
        setInputType('text')
        setShowTextInput(true)
      }
    } else {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `I didn't understand that. Please use the "Preview Document" button to review, or type a field name to edit it.`,
        timestamp: new Date()
      }])
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const hasValue = (value) => {
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== undefined && value !== ''
  }

  return (
    <div className="document-builder-chat">
      <div className="document-builder-chat__container">
        {/* Chat Messages */}
        <div className="document-builder-chat__messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message--${msg.role}`}>
              <div className="message__content">
                <div className="message__avatar">
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>
                <div className="message__bubble">
                  <div 
                    dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }}
                  />
                  {/* Show option buttons in message if it's the last assistant message and has options */}
                  {msg.role === 'assistant' && msg.fieldOptions && idx === messages.length - 1 && !isTyping && !awaitingConfirmation && (
                    <div className="message-options" style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {msg.fieldOptions.map((option, optIdx) => (
                        <Button
                          key={optIdx}
                          onClick={() => handleOptionClick(option)}
                          disabled={isTyping}
                          variant="secondary"
                          size="small"
                        >
                          {option}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="message message--assistant">
              <div className="message__content">
                <div className="message__avatar">🤖</div>
                <div className="message__bubble">
                  <TypingIndicator />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="document-builder-chat__input-area">
          {awaitingConfirmation ? (
            <div className="action-buttons">
              <Button
                onClick={handlePreview}
                disabled={isTyping || isGenerating}
                variant="primary"
              >
                <FiEye size={18} />
                Preview Document
              </Button>
            </div>
          ) : (
            <>
              {/* Show option buttons if field has predefined options */}
              {!showTextInput && selectOptions.length > 0 && (
                <div className="option-buttons">
                  {selectOptions.map((option, idx) => (
                    <Button
                      key={idx}
                      onClick={() => handleOptionClick(option)}
                      disabled={isTyping}
                      variant="secondary"
                      className="option-button"
                    >
                      {option}
                    </Button>
                  ))}
                  {!requiredFields.includes(currentField) && (
                    <Button
                      onClick={() => handleOptionClick('skip')}
                      disabled={isTyping}
                      variant="ghost"
                      className="option-button"
                    >
                      Skip (Optional)
                    </Button>
                  )}
                </div>
              )}
              
              {/* Show text input for signature fields */}
              {(currentField === 'signatory_signature' || currentField === 'signature' || currentField === 'e_signature' || currentField === 'signatory_name') ? (
                <>
                  {currentField === 'signatory_name' ? (
                    <>
                      <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Enter signatory name..."
                        disabled={isTyping}
                        className="chat-input"
                      />
                      <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        variant="primary"
                      >
                        <FiSend size={18} />
                        Send
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg"
                        onChange={handleSignatureUpload}
                        style={{ display: 'none' }}
                      />
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isTyping}
                        variant="secondary"
                        title="Upload signature image that includes name and designation"
                      >
                        <FiUpload size={18} />
                        Or Upload Signature
                      </Button>
                    </>
                  ) : (
                    <>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg"
                        onChange={handleSignatureUpload}
                        style={{ display: 'none' }}
                      />
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isTyping}
                        variant="secondary"
                        style={{ flex: 1 }}
                      >
                        <FiUpload size={18} />
                        {signatureFile ? `Change Signature (${signatureFile.name})` : 'Upload E-Signature Image'}
                      </Button>
                      <Button
                        onClick={() => {
                          handleOptionClick('skip')
                        }}
                        disabled={isTyping}
                        variant="ghost"
                      >
                        Skip
                      </Button>
                    </>
                  )}
                </>
              ) : showTextInput && (
                /* Show text input for fields that need manual entry */
                <>
                  <input
                    ref={inputRef}
                    type={inputType}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={
                      currentField 
                        ? `Enter ${currentField.replace('_', ' ')}...` 
                        : 'Type your response...'
                    }
                    disabled={isTyping}
                    className="chat-input"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isTyping}
                    variant="primary"
                  >
                    <FiSend size={18} />
                    Send
                  </Button>
                  {!requiredFields.includes(currentField) && (
                    <Button
                      onClick={() => handleOptionClick('skip')}
                      disabled={isTyping}
                      variant="ghost"
                    >
                      Skip
                    </Button>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Side Panel - Field Progress */}
      <div className="document-builder-chat__sidebar">
        <div className="data-summary">
          <div className="data-summary__header">
            <h4>📋 Required Information</h4>
            <div className="data-summary__progress">
              <div className="progress-bar">
                <div 
                  className="progress-bar__fill" 
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>
              <span className="progress-text">{completionPercentage}%</span>
            </div>
          </div>

          <div className="data-summary__fields">
            <h5>Required Fields</h5>
            {requiredFields.map((field, idx) => {
              const isFilled = hasValue(collectedData[field])
              const isValid = validationStatus[field] !== false
              const isCurrent = currentFieldIndex === allFields.indexOf(field)
              
              return (
                <div 
                  key={field}
                  className={`data-summary__field ${isFilled ? 'data-summary__field--filled' : ''} ${isCurrent ? 'data-summary__field--active' : ''} ${!isValid ? 'data-summary__field--invalid' : ''}`}
                >
                  <div className="field-label">
                    {isFilled ? (
                      isValid ? (
                        <span className="icon-success">✓</span>
                      ) : (
                        <span className="icon-error">❌</span>
                      )
                    ) : isCurrent ? (
                      <span className="icon-current">→</span>
                    ) : (
                      <span className="icon-missing">○</span>
                    )}
                    <span>{field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  </div>
                </div>
              )
            })}

            {optionalFields.length > 0 && (
              <>
                <h5 style={{ marginTop: '1rem' }}>Optional Fields</h5>
                {optionalFields.map((field, idx) => {
                  const absoluteIdx = requiredFields.length + idx
                  const isFilled = hasValue(collectedData[field])
                  const isValid = validationStatus[field] !== false
                  const isCurrent = currentFieldIndex === allFields.indexOf(field)
                  
                  return (
                    <div 
                      key={field}
                      className={`data-summary__field data-summary__field--optional ${isFilled ? 'data-summary__field--filled' : ''} ${isCurrent ? 'data-summary__field--active' : ''} ${!isValid ? 'data-summary__field--invalid' : ''}`}
                    >
                      <div className="field-label">
                        {isFilled ? (
                          isValid ? (
                            <span className="icon-success">✓</span>
                          ) : (
                            <span className="icon-error">❌</span>
                          )
                        ) : isCurrent ? (
                          <span className="icon-current">→</span>
                        ) : (
                          <span className="icon-missing">○</span>
                        )}
                        <span>{field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                      </div>
                    </div>
                  )
                })}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div className="preview-modal">
          <div className="preview-modal__overlay" onClick={() => setShowPreview(false)} />
          <div className="preview-modal__content">
            <div className="preview-modal__header">
              <h3>📄 Document Preview</h3>
              <button 
                className="preview-modal__close"
                onClick={() => setShowPreview(false)}
              >
                <FiX size={24} />
              </button>
            </div>
            
            <div className="preview-modal__body">
              <div 
                className="preview-html"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            </div>
            
            <div className="preview-modal__footer">
              <div className="format-selector">
                <label>Output Format:</label>
                <div className="format-options">
                  <label className={`format-option ${selectedFormat === 'pdf' ? 'format-option--active' : ''}`}>
                    <input
                      type="radio"
                      name="format"
                      value="pdf"
                      checked={selectedFormat === 'pdf'}
                      onChange={(e) => setSelectedFormat(e.target.value)}
                    />
                    <span>📄 PDF</span>
                  </label>
                  <label className={`format-option ${selectedFormat === 'docx' ? 'format-option--active' : ''}`}>
                    <input
                      type="radio"
                      name="format"
                      value="docx"
                      checked={selectedFormat === 'docx'}
                      onChange={(e) => setSelectedFormat(e.target.value)}
                    />
                    <span>📝 Word (DOCX)</span>
                  </label>
                </div>
              </div>
              
              <div className="preview-modal__actions">
                <Button
                  onClick={() => setShowPreview(false)}
                  variant="secondary"
                >
                  Edit Fields
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  variant="primary"
                >
                  <FiDownload size={18} />
                  {isGenerating ? 'Generating...' : `Generate ${selectedFormat.toUpperCase()}`}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
