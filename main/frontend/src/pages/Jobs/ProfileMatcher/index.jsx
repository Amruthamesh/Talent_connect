import React, { useState } from 'react'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import Badge from '@components/atoms/Badge'
import Input from '@components/atoms/Input'
import FileUpload from '@components/molecules/FileUpload'
import { FiUser, FiDownload } from 'react-icons/fi'
import toast from 'react-hot-toast'
import { matcherAPI } from '@utils/api'
import content from './content.json'
import './style.scss'

export default function ProfileMatcher() {
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [mustHaveSkills, setMustHaveSkills] = useState('')
  const [preferredSkills, setPreferredSkills] = useState('')
  const [profiles, setProfiles] = useState([])
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedIds, setSelectedIds] = useState([])
  const [minScoreFilter, setMinScoreFilter] = useState(0)
  const [jdFile, setJdFile] = useState(null)
  const [currentStep, setCurrentStep] = useState(1)
  const [detailCandidate, setDetailCandidate] = useState(null)
  const [detailData, setDetailData] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const maskName = (name) => {
    if (!name) return 'Candidate'
    const parts = name.trim().split(/\s+/)
    if (parts.length === 1) {
      return parts[0]
    }
    return parts[0] + ' ' + parts[parts.length - 1].charAt(0) + '***'
  }

  const maskEmail = (email) => {
    if (!email) return email
    return email.replace(/([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})/g, '$1XXXXX$2')
  }

  const maskPhone = (phone) => {
    if (!phone) return phone
    return phone.replace(/(\+?\d[\d\-\s\(\)]{2,}?)(\d{3})([\-\s\)]?)(\d{2,})(\d)/g, (m, p1, mid, sep, tail, last) => `${p1}XXX${sep}${tail.replace(/\d/g, 'X')}${last}`)
  }

  const handleFileSelect = (file) => {
    toast.success(`Profile uploaded: ${file.name}`)
    setProfiles((prev) => [...prev, { name: file.name, file }])
  }

  const handleFileRemove = (index) => {
    setProfiles((prev) => prev.filter((_, i) => i !== index))
    toast.success('Profile removed')
  }

  const handleResumeBatch = (files) => {
    if (!files || files.length === 0) return
    toast.success(`Added ${files.length} profiles`)
    setProfiles((prev) => [...prev, ...files.map((file) => ({ name: file.name, file }))])
  }

  const parseSkills = (value) => value.split(',').map((s) => s.trim()).filter(Boolean)

  const handleMatch = async () => {
    let jdText = jobDescription

    if (!jdText.trim() && jdFile) {
      try {
        const textFromFile = await jdFile.text()
        jdText = textFromFile
        setJobDescription(textFromFile)
        toast.success('Loaded JD text from file')
      } catch (err) {
        console.error(err)
      }
    }

    if (!jdText.trim()) {
      toast.error('Please enter a job description or upload a readable JD file')
      return
    }

    if (profiles.length === 0) {
      toast.error('Please upload at least one profile')
      return
    }

    setMatches([])
    setSelectedIds([])
    setLoading(true)

    const files = profiles.map((p) => p.file)

    try {
      await matcherAPI.streamMatch(jdText, files, ({ event, data }) => {
        if (event === 'update') {
          setMatches((prev) => {
            const existingIndex = prev.findIndex((m) => m.file === data.file)
            const card = {
              id: typeof data.upload_id === 'number' ? data.upload_id : null,
              file: data.file,
              name: data.name || data.file || 'Candidate',
              score: data.match_percentage || 0,
              matchedSkills: data.strengths || [],
              missingSkills: data.gaps || [],
              highlights: data.strengths || [],
              rationale: data.experience_alignment || data.technical_alignment || '',
              email: data.email,
              phone: data.phone,
              aiSummary: data.recommendation ? `${data.recommendation}: ${data.technical_alignment || ''}` : '',
              raw: data,
            }
            if (existingIndex >= 0) {
              const copy = [...prev]
              copy[existingIndex] = card
              return copy
            }
            return [...prev, card]
          })
        }
        if (event === 'error') {
          toast.error(data.message || 'Error processing a resume')
        }
        if (event === 'done') {
          // Sort descending by score
          setMatches((prev) => [...prev].sort((a, b) => (b.score || 0) - (a.score || 0)))
          setLoading(false)
          toast.success('Streaming completed')
        }
      })
    } catch (error) {
      console.error(error)
      toast.error(error.message || 'Failed to stream matcher')
      setLoading(false)
    }
  }

  const openDetails = async (match) => {
    setDetailCandidate(match)
    setDetailData(match.raw || match)
  }

  const closeDetails = () => {
    setDetailCandidate(null)
    setDetailData(null)
  }

  const getScoreBadgeVariant = (score) => {
    if (score >= 90) return 'success'
    if (score >= 75) return 'primary'
    if (score >= 60) return 'warning'
    return 'error'
  }

  const toggleSelected = (candidateId) => {
    if (!Number.isFinite(candidateId)) return
    setSelectedIds((prev) =>
      prev.includes(candidateId) ? prev.filter((id) => id !== candidateId) : [...prev, candidateId]
    )
  }

  const handleDownloadSelected = async () => {
    if (selectedIds.length === 0) {
      toast.error('Select at least one profile to download')
      return
    }
    try {
      const cleanIds = selectedIds.filter((id) => Number.isFinite(id))
      if (cleanIds.length === 0) {
        toast.error('No downloadable profiles in selection yet.')
        return
      }
      
      if (cleanIds.length === 1) {
        // Download single file directly with original filename
        const { blob, filename } = await matcherAPI.downloadSingle(cleanIds[0])
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
        toast.success(`Downloaded ${filename}`)
      } else {
        // Download multiple files as ZIP
        const blob = await matcherAPI.downloadZip(cleanIds)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'selected_resumes.zip'
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
        toast.success(`Downloaded ${cleanIds.length} resumes`)
      }
    } catch (err) {
      console.error(err)
      toast.error(err.message || 'Failed to download')
    }
  }

  const steps = [
    { id: 1, title: 'Upload JD', description: 'Add the job description and basics' },
    { id: 2, title: 'Upload CVs', description: 'Bulk upload candidate profiles' },
    { id: 3, title: 'Match & Results', description: 'Add skills, run, and shortlist' },
  ]

  const canProceed = (step) => {
    if (step === 1) return Boolean(jobDescription.trim() || jdFile)
    if (step === 2) return profiles.length > 0
    return true
  }

  return (
    <AppLayout>
      <div className="profile-matcher">
        <div className="profile-matcher__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle}</p>
          </div>
          <Badge variant="primary" size="medium">AI Powered</Badge>
        </div>

        <Card padding="large" className="profile-matcher__stepper-card">
          <div className="profile-matcher__stepper">
            {steps.map((step, idx) => {
              const isActive = currentStep === step.id
              const isCompleted = currentStep > step.id
              return (
                <div key={step.id} className={`profile-matcher__step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
                  <div className="profile-matcher__step-index">{step.id}</div>
                  <div>
                    <div className="profile-matcher__step-title">{step.title}</div>
                    <div className="profile-matcher__step-desc">{step.description}</div>
                  </div>
                  {/* {idx < steps.length - 1 && <div className="profile-matcher__step-line" />} */}
                </div>
              )
            })}
          </div>

          <div className="profile-matcher__step-content">
            {currentStep === 1 && (
              <div className="profile-matcher__fields">
                <FileUpload
                  accept=".pdf,.doc,.docx,.txt"
                  label={jdFile ? `JD Selected: ${jdFile.name}` : 'Upload JD (PDF/DOC/TXT)'}
                  onFileSelect={(file) => setJdFile(file)}
                />
                <Input
                  label="Job Title"
                  placeholder="Senior Backend Engineer"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  fullWidth
                />
                <textarea
                  className="profile-matcher__textarea"
                  placeholder={content.jobDescriptionPlaceholder}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={8}
                />
              </div>
            )}

            {currentStep === 2 && (
              <div className="profile-matcher__fields">
                <FileUpload
                  accept=".pdf,.doc,.docx"
                  label="Upload resumes (bulk supported)"
                  multiple
                  onFilesSelect={handleResumeBatch}
                />

                {profiles.length > 0 && (
                  <div className="profile-matcher__uploaded-files">
                    <h4>Uploaded Profiles ({profiles.length})</h4>
                    {profiles.map((profile, index) => (
                      <div key={`${profile.name}-${index}`} className="profile-matcher__file-item">
                        <FiUser />
                        <span>{profile.name}</span>
                        <button onClick={() => handleFileRemove(index)}>Remove</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {currentStep === 3 && (
              <div className="profile-matcher__fields">
                <Input
                  label="Must-have skills"
                  placeholder="Python, AWS, FastAPI"
                  value={mustHaveSkills}
                  onChange={(e) => setMustHaveSkills(e.target.value)}
                  fullWidth
                />
                <Input
                  label="Preferred skills"
                  placeholder="PostgreSQL, Docker"
                  value={preferredSkills}
                  onChange={(e) => setPreferredSkills(e.target.value)}
                  fullWidth
                />

                <Button 
                  variant="primary" 
                  fullWidth 
                  size="large"
                  onClick={handleMatch}
                  loading={loading}
                  disabled={(!jobDescription.trim() && !jdFile) || profiles.length === 0}
                  className="mt-lg"
                >
                  {content.matchButton}
                </Button>

                <div className="profile-matcher__results-block">
                  <div className="profile-matcher__results-header">
                    <h4>Results</h4>
                    {matches.length > 0 && (
                      <div className="profile-matcher__results-actions">
                        <div className="profile-matcher__results-meta">
                          <Badge variant="secondary">{matches.length} results</Badge>
                          {selectedIds.length > 0 && (
                            <span className="profile-matcher__selected-count">{selectedIds.length} selected</span>
                          )}
                        </div>
                        <div className="profile-matcher__results-controls">
                          <Button
                            variant="ghost"
                            size="small"
                            onClick={() => setMatches((prev) => [...prev].sort((a, b) => (b.score || 0) - (a.score || 0)))}
                          >
                            Sort by score
                          </Button>
                          <div className="profile-matcher__filter">
                            <span>Min %</span>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={minScoreFilter}
                              onChange={(e) => setMinScoreFilter(Number(e.target.value) || 0)}
                            />
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="small"
                          icon={<FiDownload />}
                          onClick={handleDownloadSelected}
                        >
                          {selectedIds.length === 1 ? 'Download' : 'Download ZIP'}
                        </Button>
                      </div>
                    )}
                  </div>

                  {matches.length > 0 ? (
                    <div className="profile-matcher__results">
                  {matches
                    .filter((m) => (m.score || 0) >= minScoreFilter)
                    .map((match, index) => (
                    <div
                      key={index}
                      className={`profile-matcher__match ${
                        match.score >= 70
                          ? 'score-high'
                          : match.score >= 50
                          ? 'score-mid'
                          : match.score >= 30
                          ? 'score-low'
                          : 'score-poor'
                      }`}
                    >
                      <div className="profile-matcher__match-header">
                        <div className="profile-matcher__match-info">
                          <input
                      type="checkbox"
                      checked={selectedIds.includes(match.id)}
                      onChange={() => toggleSelected(match.id)}
                      disabled={!Number.isFinite(match.id)}
                    />
                          <FiUser className="profile-matcher__match-icon" />
                          <span className="profile-matcher__match-name">{maskName(match.name)}</span>
                        </div>
                        <Badge 
                          variant={getScoreBadgeVariant(match.score)} 
                          size="medium"
                        >
                          {Number(match.score || 0).toFixed(1)}% Match
                        </Badge>
                      </div>
                      <div className="profile-matcher__contact-line">
                        {match.email && <span>{maskEmail(match.email)}</span>}
                        {match.phone && <span>{maskPhone(match.phone)}</span>}
                      </div>

                      <div className="profile-matcher__match-details">
                        <div className="profile-matcher__pill-group">
                          <strong>Matched skills:</strong>
                          <div className="profile-matcher__pills">
                            {match.matchedSkills.length > 0 ? (
                              match.matchedSkills.map((skill, i) => (
                                <span key={i} className="profile-matcher__pill">{skill}</span>
                              ))
                            ) : (
                              <span className="profile-matcher__pill profile-matcher__pill--muted">No direct matches</span>
                            )}
                          </div>
                        </div>

                        <div className="profile-matcher__pill-group">
                          <strong>Missing skills:</strong>
                          <div className="profile-matcher__pills">
                            {match.missingSkills.length > 0 ? (
                              match.missingSkills.map((skill, i) => (
                                <span key={i} className="profile-matcher__pill profile-matcher__pill--warning">{skill}</span>
                              ))
                            ) : (
                              <span className="profile-matcher__pill profile-matcher__pill--success">Covers all must-haves</span>
                            )}
                          </div>
                        </div>

                        {match.highlights.length > 0 && (
                          <div className="profile-matcher__highlights">
                            <strong>Highlights:</strong>
                            <ul>
                              {match.highlights.map((item, i) => (
                                <li key={i}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {match.aiSummary && (
                          <p
                            className={`profile-matcher__rationale ${
                              match.aiSummary.toLowerCase().startsWith('reject')
                                ? 'rationale-reject'
                                : match.aiSummary.toLowerCase().includes('interview')
                                ? 'rationale-interview'
                                : ''
                            }`}
                          >
                            {match.aiSummary.charAt(0).toUpperCase() + match.aiSummary.slice(1)}
                          </p>
                        )}
                      </div>

                      <div className="profile-matcher__match-actions">
                        {/* <Button variant="ghost" size="small" icon={<FiDownload />}>
                          Download Report
                        </Button> */}
                        <Button variant="primary" size="large" onClick={() => openDetails(match)}>
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                    </div>
                  ) : (
                    <div className="profile-matcher__empty">
                      <p>{content.emptyResults}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="profile-matcher__step-actions">
            {currentStep > 1 && (
              <Button variant="ghost" onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}>
                Back
              </Button>
            )}
            {currentStep < steps.length && (
              <Button
                variant="primary"
                onClick={() => setCurrentStep((s) => s + 1)}
                disabled={!canProceed(currentStep)}
                size="large"
              >
                Next step
              </Button>
            )}
          </div>
        </Card>

        {detailCandidate && (
          <div className="profile-matcher__modal">
            <div className="profile-matcher__modal-content">
              <div className="profile-matcher__modal-header">
                <h3>{maskName(detailCandidate.name)}</h3>
                <Button variant="ghost" size="small" onClick={closeDetails}>Close</Button>
              </div>
              {detailLoading && <p>Loading...</p>}
              {!detailLoading && detailData && (
                <div className="profile-matcher__modal-body">
                  <p><strong>Match:</strong> {detailCandidate.score.toFixed(1)}%</p>
                  <p><strong>Email:</strong> {maskEmail(detailData.email) || 'N/A'}</p>
                  <p><strong>Phone:</strong> {maskPhone(detailData.phone) || 'N/A'}</p>
                  <p><strong>Summary:</strong> {detailData.summary || detailData.experience_alignment || 'N/A'}</p>
                  <p><strong>Skills:</strong> {detailData.skills?.join(', ') || 'N/A'}</p>
                  {detailCandidate.aiSummary && (
                    <p><strong>AI Analysis:</strong> {detailCandidate.aiSummary}</p>
                  )}
                  {detailData.strengths && (
                    <div className="profile-matcher__highlights">
                      <strong>Strengths:</strong>
                      <ul>
                        {detailData.strengths.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  {detailData.gaps && (
                    <div className="profile-matcher__highlights">
                      <strong>Gaps:</strong>
                      <ul>
                        {detailData.gaps.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  <div className="profile-matcher__pill-group">
                    <strong>Matched skills:</strong>
                    <div className="profile-matcher__pills">
                      {detailCandidate.matchedSkills.length > 0 ? (
                        detailCandidate.matchedSkills.map((skill, i) => (
                          <span key={i} className="profile-matcher__pill">{skill}</span>
                        ))
                      ) : (
                        <span className="profile-matcher__pill profile-matcher__pill--muted">No direct matches</span>
                      )}
                    </div>
                  </div>
                  <div className="profile-matcher__pill-group">
                    <strong>Missing skills:</strong>
                    <div className="profile-matcher__pills">
                      {detailCandidate.missingSkills.length > 0 ? (
                        detailCandidate.missingSkills.map((skill, i) => (
                          <span key={i} className="profile-matcher__pill profile-matcher__pill--warning">{skill}</span>
                        ))
                      ) : (
                        <span className="profile-matcher__pill profile-matcher__pill--success">Covers all must-haves</span>
                      )}
                    </div>
                  </div>
                  {detailCandidate.highlights.length > 0 && (
                    <div className="profile-matcher__highlights">
                      <strong>Highlights:</strong>
                      <ul>
                        {detailCandidate.highlights.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {detailCandidate.rationale && (
                    <p className="profile-matcher__rationale">{detailCandidate.rationale}</p>
                  )}
                  {detailData.raw_text && (
                    <div className="profile-matcher__rawtext">
                      <strong>Resume Text (preview):</strong>
                      <div className="profile-matcher__rawtext-box">
                        {detailData.raw_text.slice(0, 1200)}...
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
