import React, { Suspense } from 'react'
import { Toaster } from 'react-hot-toast'
import AppRoutes from './router/routes'

function App() {
  return (
    <>
      <Suspense fallback={
        <div className="app-loading">
          <div className="spinner"></div>
          <p>Loading Talent Connect...</p>
        </div>
      }>
        <AppRoutes />
      </Suspense>
      <Toaster position="top-right" />
    </>
  )
}

export default App
