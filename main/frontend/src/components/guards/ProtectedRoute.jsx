import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { canAccessRoute } from '@utils/permissions'

export default function ProtectedRoute({ children }) {
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  // Check if user is authenticated
  if (!user || !user.role) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check if user has permission to access this route
  if (!canAccessRoute(user, location.pathname)) {
    // Redirect to dashboard if user doesn't have permission
    return <Navigate to="/dashboard" replace />
  }

  return children
}
