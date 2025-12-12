import React from 'react'
import Badge from '@components/atoms/Badge'
import { FiCheck, FiAlertCircle } from 'react-icons/fi'
import './style.scss'

export default function DataSummary({ data, missingFields = [], completionPercentage = 0 }) {
  const hasValue = (value) => {
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== undefined && value !== ''
  }

  const fieldLabels = {
    role: 'Job Title',
    seniority: 'Seniority Level',
    location: 'Location',
    must_have_skills: 'Must-Have Skills',
    joining_timeline: 'Joining Timeline',
    salary_range: 'Salary Range'
  }

  return (
    <div className="data-summary">
      <div className="data-summary__header">
        <h4>Collected Information</h4>
        <div className="data-summary__progress">
          <div className="progress-bar">
            <div 
              className="progress-bar__fill" 
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          <span className="progress-text">{completionPercentage}%</span>
        </div>
      </div>

      <div className="data-summary__fields">
        {Object.entries(fieldLabels).map(([key, label]) => {
          const value = data[key]
          const isMissing = missingFields.includes(key)
          const hasData = hasValue(value)

          return (
            <div 
              key={key} 
              className={`data-summary__field ${hasData ? 'data-summary__field--filled' : ''} ${isMissing ? 'data-summary__field--missing' : ''}`}
            >
              <div className="field-label">
                {hasData ? (
                  <FiCheck size={14} className="icon-success" />
                ) : (
                  <FiAlertCircle size={14} className="icon-missing" />
                )}
                <span>{label}</span>
              </div>
            </div>
          )
        })}
      </div>

      {missingFields.length > 0 && (
        <div className="data-summary__missing">
          <FiAlertCircle size={16} />
          <span>Missing: {missingFields.map(f => fieldLabels[f] || f).join(', ')}</span>
        </div>
      )}
    </div>
  )
}
