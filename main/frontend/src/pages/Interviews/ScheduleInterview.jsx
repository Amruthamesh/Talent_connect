import React, { useState } from 'react';
import './ScheduleInterview.scss';

// AI Detection Alert Component
function AIDetectionAlert({ result }) {
  if (!result) return null;

  const riskConfig = {
    high: {
      icon: '🚨',
      color: 'red',
      bgClass: 'alert-danger',
      message: 'This resume is likely AI-generated'
    },
    medium: {
      icon: '⚠️',
      color: 'orange',
      bgClass: 'alert-warning',
      message: 'This resume shows signs of AI generation'
    },
    low: {
      icon: '✅',
      color: 'green',
      bgClass: 'alert-success',
      message: 'This resume appears to be human-written'
    }
  };

  const config = riskConfig[result.risk_level] || riskConfig.low;

  return (
    <div className={`ai-alert ${config.bgClass}`}>
      <div className="ai-alert-header">
        <span className="ai-icon">{config.icon}</span>
        <div className="ai-info">
          <h4>AI Generation Detection</h4>
          <span className="risk-badge">{result.risk_level.toUpperCase()}</span>
        </div>
      </div>

      <div className="ai-alert-body">
        <p className="ai-message">{config.message}</p>
        
        <div className="confidence-bar">
          <label>Confidence Score</label>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${result.risk_level}`}
              style={{ width: `${result.confidence_score}%` }}
            />
          </div>
          <span className="score-value">{result.confidence_score}%</span>
        </div>

        {result.indicators && result.indicators.length > 0 && (
          <div className="indicators-section">
            <h5>Detected Issues:</h5>
            <ul className="indicators-list">
              {result.indicators.map((indicator, idx) => (
                <li key={idx} className="indicator-item">
                  <strong>{indicator.type.replace(/_/g, ' ')}:</strong> {indicator.message}
                  <span className="indicator-score">{indicator.score}%</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <details className="detailed-analysis">
          <summary>View Detailed Analysis</summary>
          <div className="analysis-grid">
            {Object.entries(result.detailed_analysis).map(([key, value]) => (
              <div key={key} className="analysis-item">
                <span className="label">{key.replace(/_score/g, '').replace(/_/g, ' ')}</span>
                <span className="value">{value}%</span>
              </div>
            ))}
          </div>
        </details>

        <p className="explanation">{result.explanation}</p>
      </div>
    </div>
  );
}

// Resume Upload Component with AI Detection
function ResumeUpload({ onFileSelect, onAIDetection }) {
  const [checking, setChecking] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setChecking(true);
    setDetectionResult(null);

    try {
      const formData = new FormData();
      formData.append('resume', file);

      const response = await fetch('/api/v1/interviews/check-resume-ai', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Detection failed');
      }

      const result = await response.json();
      setDetectionResult(result);
      onAIDetection?.(result);
    } catch (error) {
      console.error('Error checking resume:', error);
      setDetectionResult({
        error: 'Failed to analyze resume. Please try again.'
      });
    } finally {
      setChecking(false);
    }

    onFileSelect?.(file);
  };

  return (
    <div className="resume-upload-section">
      <label className="upload-label">Resume Upload</label>
      
      <div className="upload-input-wrapper">
        <input
          type="file"
          id="resume-input"
          accept=".pdf,.doc,.docx"
          onChange={handleFileChange}
          disabled={checking}
          className="resume-input"
        />
        <label htmlFor="resume-input" className="upload-button">
          {checking ? '🔍 Analyzing...' : '📎 Choose Resume'}
        </label>
      </div>

      {selectedFile && (
        <div className="selected-file">
          <span className="file-icon">📄</span>
          <span className="file-name">{selectedFile.name}</span>
        </div>
      )}

      {checking && (
        <div className="checking-status">
          <div className="spinner"></div>
          <p>Analyzing resume for AI generation...</p>
        </div>
      )}

      {detectionResult && !detectionResult.error && (
        <AIDetectionAlert result={detectionResult} />
      )}

      {detectionResult?.error && (
        <div className="alert alert-error">{detectionResult.error}</div>
      )}
    </div>
  );
}

// Main Schedule Interview Form
function ScheduleInterviewPage() {
  const [formData, setFormData] = useState({
    candidate_name: '',
    candidate_email: '',
    role: '',
    company: '',
    round_type: 'round_1',
    date: '',
    time: '',
    notes: '',
    resume: null,
  });

  const [aiDetection, setAiDetection] = useState(null);
  const [submitWarning, setSubmitWarning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleResumeSelect = (file) => {
    setFormData(prev => ({ ...prev, resume: file }));
  };

  const handleAIDetection = (result) => {
    setAiDetection(result);
    if (result.risk_level === 'high') {
      setSubmitWarning(true);
    } else {
      setSubmitWarning(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // Warn if high-risk AI detected
    if (aiDetection?.risk_level === 'high' && submitWarning) {
      if (!window.confirm(
        '⚠️ This resume shows HIGH RISK of AI generation. Are you sure you want to schedule this interview?'
      )) {
        return;
      }
    }

    setLoading(true);

    try {
      const submitFormData = new FormData();
      submitFormData.append('candidate_name', formData.candidate_name);
      submitFormData.append('candidate_email', formData.candidate_email);
      submitFormData.append('role', formData.role);
      submitFormData.append('company', formData.company);
      submitFormData.append('round_type', formData.round_type);
      submitFormData.append('date', formData.date);
      submitFormData.append('time', formData.time);
      submitFormData.append('notes', formData.notes);
      if (formData.resume) {
        submitFormData.append('resume', formData.resume);
      }

      const response = await fetch('/api/v1/interviews/schedule', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: submitFormData
      });

      if (!response.ok) {
        throw new Error('Failed to schedule interview');
      }

      const interview = await response.json();
      setSuccess(true);
      
      // Show AI detection in success message
      if (interview.ai_detection) {
        console.log('Interview scheduled with AI detection:', interview.ai_detection);
      }

      // Reset form
      setFormData({
        candidate_name: '',
        candidate_email: '',
        role: '',
        company: '',
        round_type: 'round_1',
        date: '',
        time: '',
        notes: '',
        resume: null,
      });
      setAiDetection(null);
      setSubmitWarning(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="schedule-interview-container">
      <div className="page-header">
        <h1>Schedule Interview</h1>
        <p>Create a new interview session with AI-powered resume screening</p>
      </div>

      {success && (
        <div className="alert alert-success">
          ✅ Interview scheduled successfully!
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="interview-form">
        <div className="form-section">
          <h3>Candidate Information</h3>
          
          <div className="form-group">
            <label htmlFor="candidate_name">Candidate Name *</label>
            <input
              id="candidate_name"
              type="text"
              name="candidate_name"
              value={formData.candidate_name}
              onChange={handleInputChange}
              placeholder="Enter candidate full name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="candidate_email">Email Address</label>
            <input
              id="candidate_email"
              type="email"
              name="candidate_email"
              value={formData.candidate_email}
              onChange={handleInputChange}
              placeholder="candidate@example.com"
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Position Details</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="role">Role *</label>
              <input
                id="role"
                type="text"
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                placeholder="e.g., Senior Software Engineer"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="company">Company</label>
              <input
                id="company"
                type="text"
                name="company"
                value={formData.company}
                onChange={handleInputChange}
                placeholder="Company name"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="round_type">Interview Round</label>
            <select
              id="round_type"
              name="round_type"
              value={formData.round_type}
              onChange={handleInputChange}
            >
              <option value="round_1">Round 1 - Initial Screening</option>
              <option value="round_2">Round 2 - Technical</option>
              <option value="round_3">Round 3 - Managerial</option>
              <option value="round_4">Round 4 - Final</option>
            </select>
          </div>
        </div>

        <div className="form-section">
          <h3>Resume & AI Detection</h3>
          <ResumeUpload 
            onFileSelect={handleResumeSelect}
            onAIDetection={handleAIDetection}
          />
        </div>

        <div className="form-section">
          <h3>Schedule Details</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="date">Date *</label>
              <input
                id="date"
                type="date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="time">Time *</label>
              <input
                id="time"
                type="time"
                name="time"
                value={formData.time}
                onChange={handleInputChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              placeholder="Add any additional notes..."
              rows={4}
            />
          </div>
        </div>

        {submitWarning && aiDetection?.risk_level === 'high' && (
          <div className="warning-banner">
            <span className="warning-icon">⚠️</span>
            <div className="warning-text">
              <strong>High Risk AI Detection</strong>
              <p>This resume shows strong indicators of AI generation. Proceed with caution.</p>
            </div>
          </div>
        )}

        <div className="form-actions">
          <button 
            type="submit" 
            disabled={loading || !formData.candidate_name || !formData.role}
            className={`btn btn-primary ${loading ? 'loading' : ''}`}
          >
            {loading ? '⏳ Scheduling...' : '📅 Schedule Interview'}
          </button>
          <button type="reset" className="btn btn-secondary">
            Clear Form
          </button>
        </div>
      </form>
    </div>
  );
}

export default ScheduleInterviewPage;
