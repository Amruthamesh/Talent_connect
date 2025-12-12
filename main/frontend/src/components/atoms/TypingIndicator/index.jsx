import React from 'react'
import chatIcon from '@assets/icons/chat.png'
import './style.scss'

export default function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-content">
        <div className="typing-avatar">
          <img src={chatIcon} alt="AI Assistant" />
        </div>
        <div className="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  )
}
