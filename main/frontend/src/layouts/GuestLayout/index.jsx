import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './style.scss'

export default function GuestLayout({ children, showBranding = true }) {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState('fadeIn')

  useEffect(() => {
    if (location !== displayLocation) {
      setTransitionStage('fadeOut')
    }
  }, [location, displayLocation])

  return (
    <div className="guest-layout">
      {showBranding && (
        <header className="guest-layout__header">
          <div className="guest-layout__branding">
            <h2>Talent Connect</h2>
            <span className="guest-layout__badge">Interview Portal</span>
          </div>
        </header>
      )}
      
      <main 
        className={`guest-layout__main guest-layout__main--${transitionStage}`}
        onAnimationEnd={() => {
          if (transitionStage === 'fadeOut') {
            setTransitionStage('fadeIn')
            setDisplayLocation(location)
          }
        }}
      >
        {children}
      </main>
      
      <footer className="guest-layout__footer">
        <p>Powered by Talent Connect AI | Secure Interview Environment</p>
      </footer>
    </div>
  )
}
