# AI Detection - Frontend Integration Examples

This document provides ready-to-use code examples for integrating AI detection results into the Talent Connect frontend.

## 1. Resume Upload Component with Real-Time Detection

```jsx
// frontend/src/components/atoms/ResumeUpload.jsx
import React, { useState } from 'react';
import { useAuthStore } from '@/store/authStore';

function ResumeUpload({ onDetectionResult }) {
  const [file, setFile] = useState(null);
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState(null);
  const { token } = useAuthStore();

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setChecking(true);

    try {
      const formData = new FormData();
      formData.append('resume', selectedFile);

      const response = await fetch('/api/v1/interviews/check-resume-ai', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) throw new Error('Detection failed');

      const detectionResult = await response.json();
      setResult(detectionResult);
      onDetectionResult?.(detectionResult);
    } catch (error) {
      console.error('Error checking resume:', error);
      setResult({
        error: 'Failed to analyze resume. Please try again.'
      });
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="resume-upload">
      <label htmlFor="resume">Upload Resume</label>
      <input
        id="resume"
        type="file"
        accept=".pdf,.doc,.docx"
        onChange={handleFileChange}
        disabled={checking}
      />

      {checking && (
        <div className="checking-spinner">
          <p>Analyzing resume for AI generation...</p>
        </div>
      )}

      {result && !result.error && (
        <AIDetectionAlert result={result} />
      )}

      {result?.error && (
        <div className="error-message">{result.error}</div>
      )}

      {file && !checking && (
        <p className="file-name">📎 {file.name}</p>
      )}
    </div>
  );
}

export default ResumeUpload;
```

## 2. AI Detection Alert Component

```jsx
// frontend/src/components/atoms/AIDetectionAlert.jsx
import React from 'react';
import './AIDetectionAlert.scss';

const riskColors = {
  high: { bg: 'bg-red-50', border: 'border-red-300', badge: 'bg-red-100 text-red-800' },
  medium: { bg: 'bg-yellow-50', border: 'border-yellow-300', badge: 'bg-yellow-100 text-yellow-800' },
  low: { bg: 'bg-green-50', border: 'border-green-300', badge: 'bg-green-100 text-green-800' }
};

const riskIcons = {
  high: '⚠️',
  medium: '⚡',
  low: '✅'
};

function AIDetectionAlert({ result }) {
  if (!result || result.error) return null;

  const colors = riskColors[result.risk_level] || riskColors.low;
  const icon = riskIcons[result.risk_level];

  return (
    <div className={`ai-detection-alert ${colors.bg} border ${colors.border}`}>
      <div className="alert-header">
        <div className="alert-title">
          <span className="icon">{icon}</span>
          <h3>AI Generation Detection</h3>
        </div>
        <span className={`risk-badge ${colors.badge}`}>
          {result.risk_level.toUpperCase()}
        </span>
      </div>

      <div className="alert-content">
        <div className="confidence">
          <span className="label">Confidence Score:</span>
          <div className="score-bar">
            <div 
              className={`score-fill ${result.risk_level}`}
              style={{ width: `${result.confidence_score}%` }}
            />
          </div>
          <span className="value">{result.confidence_score}%</span>
        </div>

        <p className="explanation">{result.explanation}</p>

        {result.indicators && result.indicators.length > 0 && (
          <div className="indicators">
            <h4>Detected Issues:</h4>
            <ul>
              {result.indicators.map((indicator, idx) => (
                <li key={idx} className="indicator-item">
                  <strong>{indicator.type.replace(/_/g, ' ')}:</strong> {indicator.message}
                  <span className="score">(Score: {indicator.score}%)</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.detailed_analysis && (
          <details className="detailed-analysis">
            <summary>View Detailed Analysis</summary>
            <table>
              <tbody>
                {Object.entries(result.detailed_analysis).map(([key, value]) => (
                  <tr key={key}>
                    <td className="label">{key.replace(/_/g, ' ')}:</td>
                    <td className="value">{typeof value === 'number' ? value.toFixed(1) : value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        )}
      </div>
    </div>
  );
}

export default AIDetectionAlert;
```

## 3. Styling (SCSS)

```scss
// frontend/src/components/atoms/AIDetectionAlert.scss
.ai-detection-alert {
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;

  .alert-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .alert-title {
      display: flex;
      align-items: center;
      gap: 8px;

      .icon {
        font-size: 20px;
      }

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }

    .risk-badge {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }
  }

  .alert-content {
    .confidence {
      margin-bottom: 12px;

      .label {
        display: block;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 6px;
        color: #666;
      }

      .score-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 6px;

        .score-fill {
          height: 100%;
          transition: width 0.3s ease;

          &.high {
            background: #ef4444;
          }
          &.medium {
            background: #f59e0b;
          }
          &.low {
            background: #10b981;
          }
        }
      }

      .value {
        font-size: 14px;
        font-weight: 600;
      }
    }

    .explanation {
      margin: 12px 0;
      font-size: 14px;
      color: #374151;
      line-height: 1.5;
    }

    .indicators {
      margin: 12px 0;

      h4 {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
      }

      .indicator-item {
        font-size: 13px;
        margin-bottom: 6px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);

        strong {
          color: #111;
        }

        .score {
          float: right;
          color: #999;
          font-size: 12px;
        }
      }
    }

    .detailed-analysis {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(0, 0, 0, 0.1);

      summary {
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        color: #0066cc;
        user-select: none;

        &:hover {
          text-decoration: underline;
        }
      }

      table {
        width: 100%;
        margin-top: 8px;
        border-collapse: collapse;

        tr {
          &:not(:last-child) {
            border-bottom: 1px solid #e5e7eb;
          }
        }

        td {
          padding: 6px 4px;
          font-size: 12px;

          &.label {
            font-weight: 600;
            color: #666;
            width: 60%;
            text-transform: capitalize;
          }

          &.value {
            text-align: right;
            color: #111;
            font-weight: 500;
          }
        }
      }
    }
  }
}
```

## 4. Interview Scheduling Form with AI Detection

```jsx
// frontend/src/pages/Interviews/ScheduleInterview.jsx
import React, { useState } from 'react';
import ResumeUpload from '@/components/atoms/ResumeUpload';
import { useAuthStore } from '@/store/authStore';

function ScheduleInterviewForm() {
  const [formData, setFormData] = useState({
    candidate_name: '',
    candidate_email: '',
    role: '',
    date: '',
    time: '',
    resume: null,
  });
  
  const [aiDetection, setAiDetection] = useState(null);
  const [shouldBlock, setShouldBlock] = useState(false);
  const { token } = useAuthStore();

  const handleAIDetectionResult = (result) => {
    setAiDetection(result);
    
    // Optionally block submission for high-risk resumes
    if (result.risk_level === 'high') {
      setShouldBlock(true);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (shouldBlock && aiDetection?.risk_level === 'high') {
      if (!window.confirm(
        'This resume shows high risk of AI generation. Do you want to continue?'
      )) {
        return;
      }
    }

    const formPayload = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      if (value !== null) {
        formPayload.append(key, value);
      }
    });

    try {
      const response = await fetch('/api/v1/interviews/schedule', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formPayload
      });

      if (response.ok) {
        const interview = await response.json();
        console.log('Interview scheduled:', interview);
        
        if (interview.ai_detection) {
          console.log('AI Detection Result:', interview.ai_detection);
        }
      }
    } catch (error) {
      console.error('Error scheduling interview:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="schedule-form">
      <div className="form-group">
        <label>Candidate Name *</label>
        <input
          type="text"
          value={formData.candidate_name}
          onChange={(e) => setFormData({ ...formData, candidate_name: e.target.value })}
          required
        />
      </div>

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          value={formData.candidate_email}
          onChange={(e) => setFormData({ ...formData, candidate_email: e.target.value })}
        />
      </div>

      <div className="form-group">
        <label>Role *</label>
        <input
          type="text"
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          required
        />
      </div>

      {/* AI Detection Integration */}
      <div className="form-section">
        <h3>Resume Upload & AI Check</h3>
        <ResumeUpload onDetectionResult={handleAIDetectionResult} />
        
        {aiDetection && (
          <div className="ai-detection-info">
            <p className={`status ${aiDetection.risk_level}`}>
              {aiDetection.risk_level === 'high' && '🚨 This resume may be AI-generated'}
              {aiDetection.risk_level === 'medium' && '⚠️ This resume shows signs of AI generation'}
              {aiDetection.risk_level === 'low' && '✅ Resume appears human-written'}
            </p>
          </div>
        )}
      </div>

      <button 
        type="submit"
        disabled={!formData.candidate_name || !formData.role}
        className={shouldBlock && aiDetection?.risk_level === 'high' ? 'warning' : ''}
      >
        Schedule Interview
      </button>
    </form>
  );
}

export default ScheduleInterviewForm;
```

## 5. Interview Dashboard with AI Detection Display

```jsx
// frontend/src/pages/Interviews/InterviewsList.jsx
import React, { useEffect, useState } from 'react';
import AIDetectionAlert from '@/components/atoms/AIDetectionAlert';

function InterviewsList() {
  const [interviews, setInterviews] = useState([]);

  useEffect(() => {
    fetchInterviews();
  }, []);

  const fetchInterviews = async () => {
    try {
      const response = await fetch('/api/v1/interviews/');
      const data = await response.json();
      setInterviews(data);
    } catch (error) {
      console.error('Error fetching interviews:', error);
    }
  };

  return (
    <div className="interviews-container">
      <h1>Interviews</h1>
      
      {interviews.map(interview => (
        <div key={interview.id} className="interview-card">
          <div className="interview-header">
            <h3>{interview.candidate_name}</h3>
            <span className="role">{interview.role}</span>
          </div>

          <div className="interview-details">
            <p><strong>Email:</strong> {interview.candidate_email}</p>
            <p><strong>Scheduled:</strong> {new Date(interview.scheduled_at).toLocaleString()}</p>
            <p><strong>Status:</strong> {interview.status}</p>
          </div>

          {/* AI Detection Results */}
          {interview.ai_detection && (
            <AIDetectionAlert result={interview.ai_detection} />
          )}

          {/* Manual AI Check Button */}
          {!interview.ai_detection && interview.resume_filename && (
            <button className="check-ai-btn" onClick={() => handleManualCheck(interview.id)}>
              Check for AI Generation
            </button>
          )}
        </div>
      ))}
    </div>
  );

  async function handleManualCheck(interviewId) {
    // Implementation for manual AI check
    console.log('Checking interview', interviewId);
  }
}

export default InterviewsList;
```

## 6. Utility Hook for AI Detection

```jsx
// frontend/src/hooks/useAIDetection.js
import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';

export function useAIDetection() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { token } = useAuthStore();

  const checkResume = async (file) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('resume', file);

      const response = await fetch('/api/v1/interviews/check-resume-ai', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('AI detection failed');
      }

      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, error, checkResume };
}
```

Usage:
```jsx
function MyComponent() {
  const { result, loading, checkResume } = useAIDetection();

  const handleFileSelect = async (file) => {
    await checkResume(file);
  };

  return (
    <>
      <input type="file" onChange={(e) => handleFileSelect(e.target.files[0])} />
      {loading && <p>Checking...</p>}
      {result && <AIDetectionAlert result={result} />}
    </>
  );
}
```

## 7. API Service Functions

```javascript
// frontend/src/utils/api.js - Add these functions
export const interviewsAPI = {
  // ... existing functions ...

  /**
   * Check if a resume file is AI-generated
   * @param {File} resumeFile - The resume file to check
   * @returns {Promise<Object>} AI detection result
   */
  async checkResumeForAI(resumeFile) {
    const formData = new FormData();
    formData.append('resume', resumeFile);

    const response = await fetch('/api/v1/interviews/check-resume-ai', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to check resume for AI generation');
    }

    return response.json();
  },

  /**
   * Get AI detection result for an interview
   * @param {number} interviewId - Interview ID
   * @returns {Promise<Object>} AI detection result if available
   */
  async getInterviewAIDetection(interviewId) {
    const response = await fetch(`/api/v1/interviews/${interviewId}`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch interview');
    }

    const interview = await response.json();
    return interview.ai_detection || null;
  }
};
```

## Best Practices

1. **Show Detection Results Clearly**
   - Use color coding (red=high, yellow=medium, green=low)
   - Include confidence percentage
   - Provide actionable explanation

2. **Implement Confirmation Flow**
   - Warn users before scheduling interviews with high-risk resumes
   - Allow HR to proceed if they choose
   - Log the decision for audit trail

3. **Performance Considerations**
   - Show loading spinner during detection
   - Disable form submission during checking
   - Cache results to avoid duplicate checks

4. **User Experience**
   - Add detailed analysis as collapsible section
   - Provide clear explanations in plain language
   - Include tips for legitimate resumes that trigger false positives

5. **Accessibility**
   - Use semantic HTML
   - Include ARIA labels
   - Ensure color is not the only indicator
