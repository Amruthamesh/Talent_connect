import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './style.scss'
import authBg from '../../assets/images/auth-bg.jpg'

export default function AuthLayout({ children }) {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState('fadeIn')

  useEffect(() => {
    if (location !== displayLocation) {
      setTransitionStage('fadeOut')
    }
  }, [location, displayLocation])

  return (
    <div className="auth-layout">
      <div
        className="auth-layout__background"
        style={{ backgroundImage: `url(${authBg})` }}
      >
        <div className="auth-layout__gradient" />
      </div>
      
      <div 
        className={`auth-layout__content auth-layout__content--${transitionStage}`}
        onAnimationEnd={() => {
          if (transitionStage === 'fadeOut') {
            setTransitionStage('fadeIn')
            setDisplayLocation(location)
          }
        }}
      >
        <div className="auth-layout__branding">
          <h1 className="auth-layout__logo">Talent Connect</h1>
          <p className="auth-layout__tagline">AI-Powered HR Management Platform</p>
        </div>
        
        <div className="auth-layout__card">
          {children}
        </div>
        
        <div className="auth-layout__footer">
          <p>&copy; 2025 Talent Connect | DHL Hackathon Project</p>
        </div>
      </div>
    </div>
  )
}
