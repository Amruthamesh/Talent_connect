import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from '@components/organisms/Navbar'
import Sidebar from '@components/organisms/Sidebar'
import './style.scss'

export default function AppLayout({ children }) {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState('fadeIn')

  useEffect(() => {
    if (location !== displayLocation) {
      setTransitionStage('fadeOut')
    }
  }, [location, displayLocation])

  return (
    <div className="app-layout">
      <Navbar />
      <div className="app-layout__container">        
        <main className="app-layout__main">
          <div 
            className={`app-layout__content app-layout__content--${transitionStage}`}
            onAnimationEnd={() => {
              if (transitionStage === 'fadeOut') {
                setTransitionStage('fadeIn')
                setDisplayLocation(location)
              }
            }}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
