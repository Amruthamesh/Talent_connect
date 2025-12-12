import React from 'react'
import chatIcon from '@assets/icons/chat.png'
import manIcon from '@assets/icons/man.png'
import boyIcon from '@assets/icons/boy.png'
import girlIcon from '@assets/icons/girl.png'
import './style.scss'

// Randomly select a user profile icon (consistent per session)
const getUserProfileIcon = () => {
  const icons = [manIcon, boyIcon, girlIcon]
  if (!window.__userProfileIcon) {
    window.__userProfileIcon = icons[Math.floor(Math.random() * icons.length)]
  }
  return window.__userProfileIcon
}

// Format timestamp to relative time
const getRelativeTime = (timestamp) => {
  if (!timestamp) return ''
  
  const now = new Date()
  const messageTime = new Date(timestamp)
  const diffMs = now - messageTime
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffSecs < 10) return 'Just now'
  if (diffSecs < 60) return `${diffSecs}s ago`
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  // For older messages, show the date
  return messageTime.toLocaleDateString()
}

// Split message into parts (statements and questions)
const parseMessage = (message) => {
  if (!message) return []
  
  // Split by sentences, keeping the delimiter
  const sentences = message.match(/[^.!?]+[.!?]+/g) || [message]
  const parts = []
  let currentStatement = ''
  
  sentences.forEach(sentence => {
    const trimmed = sentence.trim()
    if (trimmed.endsWith('?')) {
      // If we have accumulated statements, add them first
      if (currentStatement) {
        parts.push({ type: 'statement', text: currentStatement.trim() })
        currentStatement = ''
      }
      // Add the question
      parts.push({ type: 'question', text: trimmed })
    } else {
      // Accumulate non-question sentences
      currentStatement += (currentStatement ? ' ' : '') + trimmed
    }
  })
  
  // Add any remaining statements
  if (currentStatement) {
    parts.push({ type: 'statement', text: currentStatement.trim() })
  }
  
  return parts.length > 0 ? parts : [{ type: 'statement', text: message }]
}

export default function ChatMessage({ 
  message, 
  sender = 'user', // 'user' or 'assistant'
  timestamp,
  avatar,
  className = ''
}) {
  const isUser = sender === 'user'
  const displayAvatar = avatar || (isUser ? <img src={getUserProfileIcon()} alt="User" /> : <img src={chatIcon} alt="AI Assistant" />)
  const relativeTime = getRelativeTime(timestamp)
  const messageParts = !isUser ? parseMessage(message) : [{ type: 'statement', text: message }]
  
  const formatText = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')
  }
  
  return (
    <div className={`chat-message chat-message--${sender} ${className}`}>
      <div className="chat-message__content">
        <div className="chat-message__avatar">
          {displayAvatar}
        </div>
        
        <div className="chat-message__bubbles">
          {messageParts.map((part, index) => (
            <div 
              key={index}
              className={`chat-message__bubble ${part.type === 'question' ? 'chat-message__bubble--question' : ''}`}
            >
              <div 
                className="message-text"
                dangerouslySetInnerHTML={{ __html: formatText(part.text) }} 
              />
              {index === messageParts.length - 1 && relativeTime && (
                <span className="chat-message__timestamp">{relativeTime}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
