import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import Badge from '@components/atoms/Badge'
import FormInput from '@components/molecules/FormInput'
import { FiCheck, FiAlertCircle, FiDownload, FiEdit } from 'react-icons/fi'
import { api } from '@utils/api'
import './style.scss'

export default function JobFormReview() {
  const location = useLocation()
  const navigate = useNavigate()
  
  // Get data from chat flow (if coming from chat)
  const fromChat = location.state?.fromChat || false
  const initialData = location.state?.formData || {}
  
  const [formData, setFormData] = useState({
    role: '',
    seniority: '',
    department: '',
    location: '',
    must_have_skills: [],
    preferred_skills: [],
    responsibilities: [],
    expectations: '',
    team_context: '',
    joining_timeline: '',
    company_tone: '',
    salary_range: '',
    special_requirements: '',
    additional_notes: ''
  })
  
  const [generatedJD, setGeneratedJD] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [errors, setErrors] = useState({})
  const [showValidation, setShowValidation] = useState(false)

  // Pre-fill form with chat data
  useEffect(() => {
    if (initialData && Object.keys(initialData).length > 0) {
      setFormData(prev => ({
        ...prev,
        ...initialData
      }))
    }
  }, [initialData])

  // Validation (match chat: 6 essential fields only)
  const validateForm = () => {
    const newErrors = {}

    if (!formData.role?.trim()) newErrors.role = 'Role is required'
    if (!formData.seniority?.trim()) newErrors.seniority = 'Seniority is required'
    if (!formData.location?.trim()) newErrors.location = 'Location is required'
    if (!formData.must_have_skills || formData.must_have_skills.length < 2) {
      newErrors.must_have_skills = 'At least 2 must-have skills required'
    }
    // joining_timeline and salary_range are collected but not required for the API

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const handleArrayChange = (field, value) => {
    // Convert comma-separated string to array
    const arrayValue = value.split(',').map(item => item.trim()).filter(Boolean)
    handleChange(field, arrayValue)
  }

  const handleGenerateJD = async () => {
    setShowValidation(true)
    
    if (!validateForm()) {
      alert('Please fill in all required fields correctly')
      return
    }

    setIsGenerating(true)
    
    try {
      // Send data directly (same trigger as chat)
      const payload = {
        role: formData.role || '',
        seniority: formData.seniority || 'Mid',
        location: formData.location || '',
        must_have_skills: formData.must_have_skills || [],
        // Optional fields - include if provided
        ...(formData.expectations && { expectations: formData.expectations }),
        ...(formData.department && { department: formData.department }),
        ...(formData.preferred_skills?.length > 0 && { preferred_skills: formData.preferred_skills }),
        ...(formData.company_tone && { company_tone: formData.company_tone })
      }
      
      const response = await api.post('/jobs/generate-jd', payload)

      // Navigate to the JD results page, same as chat flow
      navigate('/jobs/results', {
        state: {
          fromChat: false,
          autoGenerate: false,
          generatedJD: response,
          formData: payload
        }
      })
    } catch (error) {
      console.error('Error generating JD:', error)
      alert('Failed to generate job description. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!generatedJD) return
    
    const blob = new Blob([generatedJD.full_jd], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formData.role}_JD.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSaveJob = async () => {
    try {
      await api.post('/jobs', {
        ...formData,
        job_description: generatedJD.full_jd
      })
      
      alert('Job saved successfully!')
      navigate('/jobs')
    } catch (error) {
      console.error('Error saving job:', error)
      alert('Failed to save job. Please try again.')
    }
  }

  const requiredFieldsComplete = Object.keys(errors).length === 0 || !showValidation

  return (
    <AppLayout>
      <div className="job-form-review">
        <div className="job-form-review__header">
          <div>
            <h1>{fromChat ? 'Review & Generate' : 'Create Job Description'}</h1>
            <p>
              {fromChat 
                ? 'Review the information collected and make any changes before generating the job description'
                : 'Fill in the job details to generate a professional job description'
              }
            </p>
          </div>
          <Badge variant={fromChat ? 'success' : 'primary'} size="medium">
            {fromChat ? '✓ From Chat' : '📝 Form Mode'}
          </Badge>
        </div>

        <div className="job-form-review__content">
          {/* Form Section */}
          <Card className="form-section">
            <h2>Job Information</h2>
            
            <div className="form-grid">
              {/* Basic Info */}
              <FormInput
                label="Role"
                value={formData.role}
                onChange={(e) => handleChange('role', e.target.value)}
                error={showValidation && errors.role}
                required
                placeholder="e.g., Senior Software Engineer"
              />
              
              <FormInput
                label="Seniority"
                value={formData.seniority}
                onChange={(e) => handleChange('seniority', e.target.value)}
                error={showValidation && errors.seniority}
                required
                placeholder="e.g., Senior, Mid-level, Junior"
              />
              
              <FormInput
                label="Department"
                value={formData.department}
                onChange={(e) => handleChange('department', e.target.value)}
                error={showValidation && errors.department}
                required
                placeholder="e.g., Engineering, Product"
              />
              
              <FormInput
                label="Location"
                value={formData.location}
                onChange={(e) => handleChange('location', e.target.value)}
                error={showValidation && errors.location}
                required
                placeholder="e.g., Remote, New York, Hybrid"
              />
            </div>

            {/* Skills */}
            <h3>Skills & Requirements</h3>
            <div className="form-grid">
              <FormInput
                label="Must-Have Skills"
                value={formData.must_have_skills?.join(', ') || ''}
                onChange={(e) => handleArrayChange('must_have_skills', e.target.value)}
                error={showValidation && errors.must_have_skills}
                required
                placeholder="Comma-separated: React, Node.js, TypeScript"
                helpText="At least 3 required"
              />
              
              <FormInput
                label="Preferred Skills"
                value={formData.preferred_skills?.join(', ') || ''}
                onChange={(e) => handleArrayChange('preferred_skills', e.target.value)}
                error={showValidation && errors.preferred_skills}
                required
                placeholder="Comma-separated: Docker, AWS, GraphQL"
                helpText="At least 2 required"
              />
            </div>

            {/* Responsibilities */}
            <FormInput
              label="Responsibilities"
              value={formData.responsibilities?.join(', ') || ''}
              onChange={(e) => handleArrayChange('responsibilities', e.target.value)}
              error={showValidation && errors.responsibilities}
              required
              placeholder="Comma-separated: Lead development, Code reviews, Mentor juniors"
              helpText="At least 3 required"
              type="textarea"
              rows={3}
            />

            {/* Context */}
            <h3>Role Context</h3>
            <div className="form-grid">
              <FormInput
                label="Expectations"
                value={formData.expectations}
                onChange={(e) => handleChange('expectations', e.target.value)}
                error={showValidation && errors.expectations}
                required
                placeholder="What are the key expectations for this role?"
                type="textarea"
                rows={3}
              />
              
              <FormInput
                label="Team Context"
                value={formData.team_context}
                onChange={(e) => handleChange('team_context', e.target.value)}
                error={showValidation && errors.team_context}
                required
                placeholder="Describe the team structure and dynamics"
                type="textarea"
                rows={3}
              />
            </div>

            <FormInput
              label="Joining Timeline"
              value={formData.joining_timeline}
              onChange={(e) => handleChange('joining_timeline', e.target.value)}
              error={showValidation && errors.joining_timeline}
              required
              placeholder="e.g., Immediate, 1 month, 3 months"
            />

            {/* Optional Fields */}
            <h3>Additional Information (Optional)</h3>
            <div className="form-grid">
              <FormInput
                label="Company Tone"
                value={formData.company_tone}
                onChange={(e) => handleChange('company_tone', e.target.value)}
                placeholder="e.g., Professional, Casual, Innovative"
              />
              
              <FormInput
                label="Salary Range"
                value={formData.salary_range}
                onChange={(e) => handleChange('salary_range', e.target.value)}
                placeholder="e.g., $100k-$150k"
              />
            </div>

            <FormInput
              label="Special Requirements"
              value={formData.special_requirements}
              onChange={(e) => handleChange('special_requirements', e.target.value)}
              placeholder="Any special requirements or certifications"
              type="textarea"
              rows={2}
            />

            <FormInput
              label="Additional Notes"
              value={formData.additional_notes}
              onChange={(e) => handleChange('additional_notes', e.target.value)}
              placeholder="Any other information to include"
              type="textarea"
              rows={2}
            />

            {/* Validation Summary */}
            {showValidation && Object.keys(errors).length > 0 && (
              <div className="validation-summary">
                <FiAlertCircle />
                <span>Please fix {Object.keys(errors).length} error(s) before generating</span>
              </div>
            )}

            <div className="form-actions">
              <Button
                variant="primary"
                icon={<FiCheck />}
                onClick={handleGenerateJD}
                size="large"
                disabled={isGenerating}
                loading={isGenerating}
              >
                {isGenerating ? 'Generating...' : 'Generate Job Description'}
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => navigate(fromChat ? '/jobs/create/chat' : '/dashboard')}
              >
                {fromChat ? 'Back to Chat' : 'Cancel'}
              </Button>
            </div>
          </Card>

          {/* Generated JD Preview */}
          {generatedJD && (
            <Card className="jd-preview">
              <div className="jd-preview__header">
                <h2>Generated Job Description</h2>
                <div className="actions">
                  <Button
                    icon={<FiDownload />}
                    onClick={handleDownload}
                    variant="secondary"
                    size="small"
                  >
                    Download
                  </Button>
                  <Button
                    icon={<FiCheck />}
                    onClick={handleSaveJob}
                    variant="primary"
                    size="small"
                  >
                    Save Job
                  </Button>
                </div>
              </div>
              
              <div className="jd-preview__content">
                <pre>{generatedJD.full_jd}</pre>
              </div>
            </Card>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
