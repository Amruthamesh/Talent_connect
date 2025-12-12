import React, { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@components/guards/ProtectedRoute'

// Lazy load pages
const Login = lazy(() => import('@pages/Login'))
const Dashboard = lazy(() => import('@pages/Dashboard'))
const JobCreationChoice = lazy(() => import('@pages/Jobs/JobCreationChoice'))
const JobChatBuilder = lazy(() => import('@pages/Jobs/JobChatBuilder'))
const JobFormReview = lazy(() => import('@pages/Jobs/JobFormReview'))
const JobDescriptionGenerator = lazy(() => import('@pages/Jobs/JobDescriptionGenerator'))
const JobDescriptionResult = lazy(() => import('@pages/Jobs/JobDescriptionGenerator').then(module => ({ default: module.JobDescriptionResultPage })))
const ProfileMatcher = lazy(() => import('@pages/Jobs/ProfileMatcher'))
const DocumentsDashboard = lazy(() => import('@pages/Documents'))
const DocumentTemplates = lazy(() => import('@pages/Documents/Templates'))
const DocumentQuery = lazy(() => import('@pages/Documents/Query'))
const DocumentAgent = lazy(() => import('@pages/Documents/Agent'))
const DocumentGenerate = lazy(() => import('@pages/Documents/Generate'))
const DocumentLibrary = lazy(() => import('@pages/Documents/Library'))
const InterviewDashboard = lazy(() => import('@pages/Interviews/Dashboard'))
const InterviewSchedule = lazy(() => import('@pages/Interviews/Schedule'))
const InterviewerPanel = lazy(() => import('@pages/Interviews/InterviewerPanel'))
const CandidatePanel = lazy(() => import('@pages/Interviews/CandidatePanel'))
const InterviewJoinRouter = lazy(() => import('@pages/Interviews/JoinRouter'))
const InterviewerLobby = lazy(() => import('@pages/Interviews/Lobby/InterviewerLobby'))
const CandidateLobby = lazy(() => import('@pages/Interviews/Lobby/CandidateLobby'))
const InterviewFeedback = lazy(() => import('@pages/Interviews/Feedback'))
const InterviewSummary = lazy(() => import('@pages/Interviews/Summary'))

// Loading component
const PageLoader = () => (
  <div className="page-loading">
    <div className="spinner"></div>
    <p>Loading...</p>
  </div>
)

export default function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes - Dashboard */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Protected Routes - Jobs Module */}
        <Route 
          path="/jobs/generator" 
          element={
            <ProtectedRoute>
              <JobCreationChoice />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/jobs/create/chat" 
          element={
            <ProtectedRoute>
              <JobChatBuilder />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/jobs/create/form" 
          element={
            <ProtectedRoute>
              <JobFormReview />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/jobs/generator/legacy" 
          element={
            <ProtectedRoute>
              <JobDescriptionGenerator />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/jobs/results" 
          element={
            <ProtectedRoute>
              <JobDescriptionResult />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/jobs/matcher" 
          element={
            <ProtectedRoute>
              <ProfileMatcher />
            </ProtectedRoute>
          } 
        />
        
        {/* Protected Routes - Documents Module */}
        <Route 
          path="/documents" 
          element={
            <ProtectedRoute>
              <DocumentsDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/documents/agent" 
          element={
            <ProtectedRoute>
              <DocumentAgent />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/documents/generate" 
          element={
            <ProtectedRoute>
              <DocumentGenerate />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/documents/library" 
          element={
            <ProtectedRoute>
              <DocumentLibrary />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/documents/templates" 
          element={
            <ProtectedRoute>
              <DocumentTemplates />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/documents/query" 
          element={
            <ProtectedRoute>
              <DocumentQuery />
            </ProtectedRoute>
          } 
        />
        
        {/* Protected Routes - Interviews Module */}
        <Route 
          path="/interviews/dashboard" 
          element={
            <ProtectedRoute>
              <InterviewDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/interviews/schedule" 
          element={
            <ProtectedRoute>
              <InterviewSchedule />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/interview/:interviewId/summary" 
          element={
            <ProtectedRoute>
              <InterviewSummary />
            </ProtectedRoute>
          } 
        />
        
        {/* Guest Routes - Interview (with token) */}
        <Route 
          path="/interview/join" 
          element={<InterviewJoinRouter />} 
        />
        <Route path="/interview/lobby/interviewer/:interviewId" element={<InterviewerLobby />} />
        <Route path="/interview/lobby/candidate/:interviewId" element={<CandidateLobby />} />
        <Route path="/interview/session/interviewer/:interviewId" element={<InterviewerPanel />} />
        <Route path="/interview/session/candidate/:interviewId" element={<CandidatePanel />} />
        <Route path="/interview/:interviewId/feedback" element={<InterviewFeedback />} />
        {/* Backwards compatibility for existing route */}
        <Route 
          path="/interviews/panel/:interviewId" 
          element={<InterviewerPanel />} 
        />
        
        {/* Redirect root to dashboard or login */}
        <Route 
          path="/" 
          element={
            localStorage.getItem('user') 
              ? <Navigate to="/dashboard" replace />
              : <Navigate to="/login" replace />
          } 
        />
        
        {/* 404 - Redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  )
}
