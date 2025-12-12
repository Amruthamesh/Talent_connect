import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import Badge from '@components/atoms/Badge'
import Input from '@components/atoms/Input'
import FormInput from '@components/molecules/FormInput'
import JobBuilderChat from '@components/organisms/JobBuilderChat'
import {
  FiStar, FiPlus, FiX, FiCopy, FiRefreshCw, FiCheck,
  FiSearch, FiFileText, FiMessageCircle, FiBriefcase,
  FiMail, FiDownload, FiPrinter, FiArrowLeft
} from 'react-icons/fi'
import toast from 'react-hot-toast'
import api from '@utils/api'
import useJobChatStore from '@store/jobChatStore'
import { jsPDF } from 'jspdf'
import './style.scss'

export default function JobDescriptionGenerator() {
  const location = useLocation()
  const navigate = useNavigate()
  // Mode toggle
  const [mode, setMode] = useState('form') // 'chat' or 'form'

  // Form state
  const [formData, setFormData] = useState({
    role: '',
    seniority: 'Mid',
    expectations: '',
    must_have_skills: [],
    preferred_skills: [],
    company_tone: 'formal',
    department: '',
    location: ''
  })

  const { resetChat } = useJobChatStore()

  // UI state
  const [loading, setLoading] = useState(false)
  const [generatedJD, setGeneratedJD] = useState(null)
  const [mustSkillInput, setMustSkillInput] = useState('')
  const [prefSkillInput, setPrefSkillInput] = useState('')
  const [skillSuggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeSkillType, setActiveSkillType] = useState(null)
  const [activeTab, setActiveTab] = useState('jd') // jd, explain, rewrite
  const [explainedJD, setExplainedJD] = useState(null)
  const [rewrittenJD, setRewrittenJD] = useState(null)
  const [prefillApplied, setPrefillApplied] = useState(false)

  const seniorityLevels = ['Entry', 'Mid', 'Senior', 'Lead', 'Principal']
  const toneOptions = [
    { value: 'formal', label: 'Formal/Corporate', icon: '🏢' },
    { value: 'startup', label: 'Startup/Dynamic', icon: '🚀' },
    { value: 'mnc', label: 'MNC/Global', icon: '🌍' },
    { value: 'tech', label: 'Tech/Engineering', icon: '💻' }
  ]

  // PII masking helpers
  const maskEmail = (text) => {
    if (!text) return text
    return text.replace(/([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})/g, '$1XXXXX$2')
  }
  const maskPhone = (text) => {
    if (!text) return text
    // Mask middle digits of common phone patterns
    return text.replace(/(\+?\d[\d\-\s\(\)]{2,}?)(\d{3})([\-\s\)]?)(\d{2,})(\d)/g, (m, p1, mid, sep, tail, last) => `${p1}XXX${sep}${tail.replace(/\d/g, 'X')}${last}`)
  }
  const maskPII = (text) => maskPhone(maskEmail(text))

  // Debounced autocomplete
  useEffect(() => {
    const input = activeSkillType === 'preferred' ? prefSkillInput : mustSkillInput
    if (!activeSkillType) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const timer = setTimeout(async () => {
      if (input.length >= 2) {
        try {
          const response = await api.get(`/jobs/skills/autocomplete?query=${input}&limit=8`)
          const normalized = (response.suggestions || []).map((s) => ({
            name: s.name || s.skill || '',
            category: s.category || '',
            popularity: s.popularity
          })).filter(s => s.name)
          setSuggestions(normalized)
          setShowSuggestions(true)
        } catch (error) {
          console.error('Autocomplete error:', error)
        }
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [mustSkillInput, prefSkillInput, activeSkillType])

  useEffect(() => {
    if (prefillApplied) return
    const state = location.state
    if (state?.fromChat && state.formData && state.autoGenerate) {
      const incomingData = state.formData
      setFormData(prev => ({
        ...prev,
        ...incomingData
      }))
      setMode('form')
      toast.success('Generating your job description from chat inputs...')
      setPrefillApplied(true)
      // Trigger generation after state is set
      setTimeout(() => handleGenerate(incomingData), 100)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, prefillApplied])

  const handleAddSkill = (skill, type = 'must_have') => {
    const skillList = type === 'must_have' ? formData.must_have_skills : formData.preferred_skills

    if (!skillList.includes(skill)) {
      setFormData({
        ...formData,
        [`${type}_skills`]: [...skillList, skill]
      })
      if (type === 'must_have') {
        setMustSkillInput('')
      } else {
        setPrefSkillInput('')
      }
      setShowSuggestions(false)
      toast.success(`Added ${skill}`)
    }
  }

  const handleRemoveSkill = (skill, type = 'must_have') => {
    setFormData({
      ...formData,
      [`${type}_skills`]: formData[`${type}_skills`].filter(s => s !== skill)
    })
  }

  const handleGenerate = async (dataOverride = null) => {
    const payload = {
      role: dataOverride?.role ?? formData.role ?? '',
      seniority: dataOverride?.seniority ?? formData.seniority ?? '',
      expectations: dataOverride?.expectations ?? formData.expectations ?? '',
      must_have_skills: dataOverride?.must_have_skills ?? formData.must_have_skills ?? [],
      preferred_skills: dataOverride?.preferred_skills ?? formData.preferred_skills ?? [],
      company_tone: dataOverride?.company_tone ?? formData.company_tone ?? 'formal',
      department: dataOverride?.department ?? formData.department ?? '',
      location: dataOverride?.location ?? formData.location ?? '',
      joining_timeline: dataOverride?.joining_timeline ?? formData.joining_timeline ?? '',
      salary_range: dataOverride?.salary_range ?? formData.salary_range ?? '',
      // include any extra fields passed in override
      ...(dataOverride || {})
    }
    // Validation - only check essential fields
    if (!payload.role || !payload.role.trim()) {
      toast.error('Please enter a job role')
      return
    }
    if (!Array.isArray(payload.must_have_skills) || payload.must_have_skills.length === 0) {
      toast.error('Please add at least one must-have skill')
      return
    }

    setLoading(true)
    toast.loading('Generating your job description...', { id: 'jd-generation' })
    const normalizedPayload = {
      ...payload,
      company_tone: (payload.company_tone || 'formal').toLowerCase()
    }

    try {
      const response = await api.post('/jobs/generate-jd', normalizedPayload)
      // Apply masking to any free-text fields we display
      const maskedResponse = {
        ...response,
        jd_content: {
          ...(response.jd_content || {}),
          title: maskPII(response.jd_content?.title || ''),
          overview: maskPII(response.jd_content?.overview || ''),
          responsibilities: (response.jd_content?.responsibilities || []).map(maskPII),
          qualifications: response.jd_content?.qualifications || response.jd_content?.required_qualifications || {},
          what_we_offer: (response.jd_content?.what_we_offer || []).map(maskPII)
        }
      }
      setGeneratedJD(maskedResponse)
      setActiveTab('jd')
      toast.success(dataOverride ? 'Detailed job description generated from chat!' : 'Job description generated successfully!', { id: 'jd-generation' })
      navigate('/jobs/results', {
        state: {
          generatedJD: response,
          formData: normalizedPayload
        }
      })
    } catch (error) {
      toast.error(error.message || 'Failed to generate JD', { id: 'jd-generation' })
    } finally {
      setLoading(false)
    }
  }

  const handleExplain = async () => {
    if (!generatedJD) return

    setLoading(true)
    try {
      const response = await api.post('/jobs/explain-jd', {
        jd_content: generatedJD.jd_content,
        role: formData.role
      })
      setExplainedJD(response.explanation)
      setActiveTab('explain')
      toast.success('Explanation generated!')
    } catch (error) {
      toast.error(error.message || 'Failed to explain JD')
    } finally {
      setLoading(false)
    }
  }

  const handleRewrite = async () => {
    if (!generatedJD) return

    setLoading(true)
    try {
      const response = await api.post('/jobs/rewrite-jd', {
        jd_content: generatedJD.jd_content,
        role: formData.role
      })
      setRewrittenJD(response.manager_briefing)
      setActiveTab('rewrite')
      toast.success('Manager briefing generated!')
    } catch (error) {
      toast.error(error.message || 'Failed to rewrite JD')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    let content = ''
    if (activeTab === 'jd' && generatedJD) {
      content = buildJDPlainText()
    } else if (activeTab === 'explain' && explainedJD) {
      content = explainedJD
    } else if (activeTab === 'rewrite' && rewrittenJD) {
      content = rewrittenJD
    }

    if (content) {
      navigator.clipboard.writeText(content)
      toast.success('Copied to clipboard!')
    }
  }

  const handleReset = () => {
    setFormData({
      role: '',
      seniority: 'Mid',
      expectations: '',
      must_have_skills: [],
      preferred_skills: [],
      company_tone: 'formal',
      department: '',
      location: ''
    })
    setGeneratedJD(null)
    setExplainedJD(null)
    setRewrittenJD(null)
    setActiveTab('jd')
    toast.success('Form reset')
  }

  const buildJDPlainText = () => {
    if (!generatedJD) return ''
    const { jd_content, skill_matrix, salary_benchmark, insights } = generatedJD
    const lines = []

    if (jd_content?.title) {
      lines.push(jd_content.title.toUpperCase())
    }
    if (jd_content?.overview) {
      lines.push('', jd_content.overview)
    }
    if (jd_content?.responsibilities?.length) {
      lines.push('', 'KEY RESPONSIBILITIES:')
      jd_content.responsibilities.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (jd_content?.qualifications?.required?.length) {
      lines.push('', 'REQUIRED QUALIFICATIONS:')
      jd_content.qualifications.required.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (jd_content?.qualifications?.preferred?.length) {
      lines.push('', 'PREFERRED QUALIFICATIONS:')
      jd_content.qualifications.preferred.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (jd_content?.what_we_offer?.length) {
      lines.push('', 'WHAT WE OFFER:')
      jd_content.what_we_offer.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (skill_matrix) {
      if (skill_matrix.technical_skills?.length) {
        lines.push('', 'TECHNICAL SKILL MATRIX:')
        skill_matrix.technical_skills.forEach(skill => {
          lines.push(`- ${skill.skill} | ${skill.proficiency} | ${skill.priority}`)
        })
      }
      if (skill_matrix.soft_skills?.length) {
        lines.push('', 'SOFT SKILLS:')
        skill_matrix.soft_skills.forEach(skill => {
          lines.push(`- ${skill.skill}: ${skill.context}`)
        })
      }
    }
    if (salary_benchmark) {
      lines.push('', 'SALARY BENCHMARK:')
      lines.push(
        `Range: ${salary_benchmark.currency} ${salary_benchmark.min_salary.toLocaleString()} - ${salary_benchmark.currency} ${salary_benchmark.max_salary.toLocaleString()}`
      )
      lines.push(`Median: ${salary_benchmark.currency} ${salary_benchmark.median_salary.toLocaleString()}`)
      lines.push(`Note: ${salary_benchmark.note}`)
    }
    if (insights) {
      lines.push('', 'MARKET INSIGHTS:')
      lines.push(`Market Demand: ${insights.market_demand}`)
      if (insights.key_differentiators?.length) {
        lines.push('Key Differentiators:')
        insights.key_differentiators.forEach(diff => lines.push(`- ${diff}`))
      }
      if (insights.candidate_persona) {
        lines.push(`Candidate Persona: ${insights.candidate_persona}`)
      }
      if (insights.retention_factors?.length) {
        lines.push('Retention Factors:')
        insights.retention_factors.forEach(factor => lines.push(`- ${factor}`))
      }
    }

    return lines.join('\n')
  }

  const buildJDPdfHtml = () => {
    if (!generatedJD) return ''
    const jdContent = generatedJD.jd_content || {}
    const qualifications = jdContent.qualifications || { required: [], preferred: [] }
    const skillMatrix = generatedJD.skill_matrix || { technical_skills: [], soft_skills: [] }
    const salaryBenchmark = generatedJD.salary_benchmark || {}
    const insights = generatedJD.insights || {}

    const list = (items) => (items && items.length ? `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>` : '')
    const sections = []

    if (jdContent.overview) {
      sections.push(`<p class="pdf-overview">${jdContent.overview}</p>`)
    }
    if (jdContent.responsibilities?.length) {
      sections.push(`<section><h3>Key Responsibilities</h3>${list(jdContent.responsibilities)}</section>`)
    }
    if ((qualifications.required || []).length) {
      sections.push(`<section><h3>Required Qualifications</h3>${list(qualifications.required)}</section>`)
    }
    if ((qualifications.preferred || []).length) {
      sections.push(`<section><h3>Preferred Qualifications</h3>${list(qualifications.preferred)}</section>`)
    }
    if (jdContent.what_we_offer?.length) {
      sections.push(`<section><h3>What We Offer</h3>${list(jdContent.what_we_offer)}</section>`)
    }

    if (skillMatrix.technical_skills?.length || skillMatrix.soft_skills?.length) {
      const techRows = (skillMatrix.technical_skills || []).map(skill => (
        `<tr><td>${skill.skill}</td><td>${skill.proficiency}</td><td>${skill.priority}</td></tr>`
      )).join('')
      const softRows = (skillMatrix.soft_skills || []).map(skill => (
        `<tr><td>${skill.skill}</td><td colspan="2">${skill.context}</td></tr>`
      )).join('')
      sections.push(`
        <section>
          <h3>Skill Matrix</h3>
          <table>
            <thead>
              <tr><th>Skill</th><th>Proficiency</th><th>Priority / Context</th></tr>
            </thead>
            <tbody>
              ${techRows}
              ${softRows}
            </tbody>
          </table>
        </section>
      `)
    }

    if (salaryBenchmark.min_salary || salaryBenchmark.median_salary || salaryBenchmark.max_salary) {
      const cards = []
      if (salaryBenchmark.min_salary) cards.push(`<div class="salary-card"><span>Minimum</span><strong>${salaryBenchmark.currency || ''} ${(salaryBenchmark.min_salary ?? 0).toLocaleString()}</strong></div>`)
      if (salaryBenchmark.median_salary) cards.push(`<div class="salary-card"><span>Median</span><strong>${salaryBenchmark.currency || ''} ${(salaryBenchmark.median_salary ?? 0).toLocaleString()}</strong></div>`)
      if (salaryBenchmark.max_salary) cards.push(`<div class="salary-card"><span>Maximum</span><strong>${salaryBenchmark.currency || ''} ${(salaryBenchmark.max_salary ?? 0).toLocaleString()}</strong></div>`)
      sections.push(`
        <section>
          <h3>Salary Benchmark</h3>
          <div class="salary-grid">${cards.join('')}</div>
          ${(salaryBenchmark.factors?.length || salaryBenchmark.note) ? `<p class="pdf-note">${[...(salaryBenchmark.factors || []), salaryBenchmark.note || ''].filter(Boolean).join(' · ')}</p>` : ''}
        </section>
      `)
    }

    const insightCards = []
    if (insights.market_demand) {
      insightCards.push(`<div class="insight-card"><h4>Market Demand</h4><p>${insights.market_demand}</p></div>`)
    }
    if (insights.key_differentiators?.length) {
      insightCards.push(`<div class="insight-card"><h4>Key Differentiators</h4>${list(insights.key_differentiators)}</div>`)
    }
    if (insights.candidate_persona) {
      insightCards.push(`<div class="insight-card"><h4>Candidate Persona</h4><p>${insights.candidate_persona}</p></div>`)
    }
    if (insights.retention_factors?.length) {
      insightCards.push(`<div class="insight-card"><h4>Retention Factors</h4>${list(insights.retention_factors)}</div>`)
    }
    if (insightCards.length) {
      sections.push(`
        <section>
          <h3>Market Insights</h3>
          <div class="insights-grid">${insightCards.join('')}</div>
        </section>
      `)
    }

    return `
      <html>
        <head>
          <meta charset="utf-8" />
          <title>${jdContent.title || 'Job Description'} – Job Description</title>
          <style>
            * { box-sizing: border-box; }
            body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 50px; background: #f4f6fb; color: #0f172a; }
            .pdf-card { background: #ffffff; border-radius: 28px; padding: 48px; max-width: 960px; margin: 0 auto; box-shadow: 0 25px 80px rgba(15, 23, 42, 0.12); }
            header { border-bottom: 2px solid #e2e8f0; padding-bottom: 24px; margin-bottom: 32px; }
            header span { text-transform: uppercase; letter-spacing: 0.3em; font-size: 0.75rem; color: #6366f1; display: block; }
            header h1 { margin: 12px 0 6px 0; font-size: 2.4rem; }
            header p { margin: 0; color: #475569; }
            section { margin-bottom: 28px; }
            h3 { margin: 0 0 12px; font-size: 0.95rem; letter-spacing: 0.35em; color: #94a3b8; text-transform: uppercase; }
            ul { margin: 0; padding-left: 20px; color: #334155; line-height: 1.7; }
            li { margin-bottom: 6px; }
            .pdf-overview { font-size: 1.1rem; line-height: 1.8; color: #1e293b; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; margin-top: 12px; }
            th, td { border: 1px solid #e2e8f0; padding: 10px 12px; font-size: 0.95rem; }
            th { background: #f8fafc; text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.75rem; color: #64748b; }
            .salary-grid { display: flex; flex-wrap: wrap; gap: 18px; }
            .salary-card { flex: 1; min-width: 180px; border: 1px solid #fcd34d; border-radius: 20px; padding: 16px 18px; background: linear-gradient(135deg, #fff7e0, #fffef5); }
            .salary-card span { text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.8rem; color: #b45309; }
            .salary-card strong { display: block; margin-top: 6px; font-size: 1.4rem; color: #92400e; }
            .pdf-note { margin-top: 12px; font-style: italic; color: #475569; }
            .insights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; }
            .insight-card { border: 1px solid #e2e8f0; border-radius: 18px; padding: 16px 18px; background: #f8fafc; }
            .insight-card h4 { margin: 0 0 8px; font-size: 0.85rem; letter-spacing: 0.2em; text-transform: uppercase; color: #475569; }
          </style>
        </head>
        <body>
          <div class="pdf-card">
            <header>
              <span>${formData.department || 'Talent Connect'}</span>
              <h1>${jdContent.title || 'Job Description'}</h1>
              <p>${formData.location || 'Global'} · ${formData.seniority || 'Professional'}</p>
            </header>
            ${sections.join('')}
          </div>
        </body>
      </html>
    `
  }

  const handleSendEmail = () => {
    if (!generatedJD) return
    const subject = `Job Description - ${formData.role || generatedJD.jd_content.title || 'Open Role'}`
    const body = buildJDPlainText()
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  const getBaseFileName = () => {
    const base = (formData.role || generatedJD?.jd_content?.title || 'job-description')
      .toLowerCase()
      .replace(/\s+/g, '-')
    return base
  }

  const handleDownloadWord = () => {
    if (!generatedJD) return
    const html = buildJDPdfHtml()
    if (!html) {
      toast.error('Nothing to export')
      return
    }
    const fileName = `${getBaseFileName()}-jd.doc`
    const blob = new Blob(
      ['\ufeff', html],
      { type: 'application/msword' }
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Word document downloaded!')
  }

  const handleDownloadPDF = async () => {
    if (!generatedJD) return
    const html = buildJDPdfHtml()
    if (!html) {
      toast.error('Nothing to export')
      return
    }
    const tempContainer = document.createElement('div')
    tempContainer.style.position = 'fixed'
    tempContainer.style.top = '-10000px'
    tempContainer.style.left = '-10000px'
    tempContainer.style.width = '1000px'
    tempContainer.innerHTML = html
    document.body.appendChild(tempContainer)

    const doc = new jsPDF('p', 'pt', 'a4')
    const fileName = `${getBaseFileName()}-jd.pdf`
    try {
      await doc.html(tempContainer, {
        callback: (docInstance) => {
          docInstance.save(fileName)
          toast.success('PDF downloaded!')
        },
        margin: 30,
        autoPaging: 'text',
        html2canvas: {
          scale: 0.55,
          useCORS: true
        },
        windowWidth: 1000
      })
    } catch (error) {
      console.error('PDF generation failed', error)
      toast.error('Failed to generate PDF')
    } finally {
      document.body.removeChild(tempContainer)
    }
  }

  // Chat handlers
  const handleChatComplete = (chatData) => {
    const updatedData = {
      ...formData,
      ...chatData
    }
    setFormData(updatedData)
    setMode('form')
    toast.success('Great! Generating a detailed job description from your chat inputs.')
    handleGenerate(updatedData)
  }

  const handleSwitchToForm = () => {
    setMode('form')
    resetChat()
  }

  const handleSwitchToChat = () => {
    setMode('chat')
    resetChat()
  }

  return (
    <AppLayout>
      <div className="jd-generator">
        {/* Loading Overlay */}
        {loading && (
          <div className="jd-generator__loading-overlay">
            <div className="loading-content">
              <div className="spinner"></div>
              <h2>Generating Your Job Description</h2>
              <p>Our AI is crafting a comprehensive, market-aligned job description...</p>
              <div className="loading-steps">
                <div className="step">✓ Analyzing role requirements</div>
                <div className="step">✓ Benchmarking skills & salary</div>
                <div className="step active">⟳ Generating detailed content</div>
              </div>
            </div>
          </div>
        )}

        <div className="jd-generator__header">
          <div>
            <h1>AI Job Description Generator</h1>
            <p>Create comprehensive, market-aligned job descriptions with AI assistance</p>
          </div>
          <div className="header-actions">
            <div className="mode-toggle">
              <Button
                variant={mode === 'chat' ? 'primary' : 'secondary'}
                size="small"
                icon={<FiMessageCircle />}
                onClick={handleSwitchToChat}
              >
                Chat Mode
              </Button>
              <Button
                variant={mode === 'form' ? 'primary' : 'secondary'}
                size="small"
                icon={<FiFileText />}
                onClick={handleSwitchToForm}
              >
                Form Mode
              </Button>
            </div>
            <Badge variant="primary" size="medium">AI Powered</Badge>
          </div>
        </div>

        {mode === 'chat' ? (
          /* Chat Mode */
          <Card
            title="Let's build your job description together"
            subtitle="Tell me about the role you're hiring for, and I'll help gather all the details"
            padding="none"
            className="jd-generator__chat-card"
          >
            <JobBuilderChat
              onComplete={handleChatComplete}
              onCancel={handleSwitchToForm}
              autoGeneratePrompt
            />
          </Card>
        ) : (
          /* Form Mode */
          <div className="jd-generator__grid">
            {/* Form Section */}
            <Card
              title="Job Details"
              subtitle="Fill in the key information about the role"
              padding="medium"
              className="jd-generator__form-card"
            >
              <div className="jd-generator__form">
                {/* Role Name */}
                <FormInput
                  label="Role Title *"
                  placeholder="e.g., Senior AI Engineer, Product Manager"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  fullWidth
                />

                {/* Seniority Level */}
                <div className="form-group">
                  <label>Seniority Level *</label>
                  <div className="button-group">
                    {seniorityLevels.map(level => (
                      <Button
                        key={level}
                        variant={formData.seniority === level ? 'primary' : 'secondary'}
                        size="small"
                        onClick={() => setFormData({ ...formData, seniority: level })}
                      >
                        {level}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Department & Location */}
                <div className="form-row">
                  <FormInput
                    label="Department"
                    placeholder="e.g., Engineering, Product"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    fullWidth
                  />
                  <FormInput
                    label="Location"
                    placeholder="e.g., Remote, Bangalore, Hybrid"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    fullWidth
                  />
                </div>

                {/* Expectations */}
                <div className="form-group">
                  <label>Role Expectations *</label>
                  <textarea
                    placeholder="Describe what this person will be responsible for, key outcomes expected..."
                    value={formData.expectations}
                    onChange={(e) => setFormData({ ...formData, expectations: e.target.value })}
                    rows={4}
                    className="form-textarea"
                  />
                </div>

                {/* Must-Have Skills */}
        <div className="form-group">
          <label>Must-Have Skills * <FiStar size={14} style={{ color: '#d40511' }} /></label>
          <div className="skill-input-wrapper">
            <Input
              placeholder="Type to search skills... (e.g., Python, React)"
              value={mustSkillInput}
              onChange={(e) => setMustSkillInput(e.target.value)}
              onFocus={() => { setActiveSkillType('must_have'); setShowSuggestions(true) }}
              icon={<FiSearch />}
              fullWidth
            />
            {showSuggestions && activeSkillType === 'must_have' && skillSuggestions.length > 0 && (
              <div className="skill-suggestions">
                {skillSuggestions.map(skill => (
                  <div
                    key={skill.name}
                    className="skill-suggestion"
                            onClick={() => handleAddSkill(skill.name, 'must_have')}
                          >
                            <span className="skill-name">{skill.name}</span>
                            <span className="skill-category">{skill.category}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="skill-chips">
                    {formData.must_have_skills.map(skill => (
                      <Badge
                        key={skill}
                        variant="error"
                        icon={<FiX onClick={() => handleRemoveSkill(skill, 'must_have')} style={{ cursor: 'pointer' }} />}
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Preferred Skills */}
        <div className="form-group">
          <label>Preferred Skills <FiPlus size={14} style={{ color: '#666' }} /></label>
          <div className="skill-input-wrapper">
            <Input
              placeholder="Nice-to-have skills..."
              value={prefSkillInput}
              onChange={(e) => setPrefSkillInput(e.target.value)}
              onFocus={() => { setActiveSkillType('preferred'); setShowSuggestions(true) }}
              icon={<FiSearch />}
              fullWidth
            />
            {showSuggestions && activeSkillType === 'preferred' && skillSuggestions.length > 0 && (
              <div className="skill-suggestions">
                {skillSuggestions.map(skill => (
                  <div
                    key={skill.name}
                    className="skill-suggestion"
                            onClick={() => handleAddSkill(skill.name, 'preferred')}
                          >
                            <span className="skill-name">{skill.name}</span>
                            <span className="skill-category">{skill.category}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="skill-chips">
                    {formData.preferred_skills.map(skill => (
                      <Badge
                        key={skill}
                        variant="warning"
                        icon={<FiX onClick={() => handleRemoveSkill(skill, 'preferred')} style={{ cursor: 'pointer' }} />}
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Company Tone */}
                <div className="form-group">
                  <label>Company Tone</label>
                  <div className="button-group">
                    {toneOptions.map(option => (
                      <Button
                        key={option.value}
                        variant={formData.company_tone === option.value ? 'primary' : 'secondary'}
                        size="small"
                        icon={<span style={{ fontSize: '16px' }}>{option.icon}</span>}
                        onClick={() => setFormData({ ...formData, company_tone: option.value })}
                      >
                        {option.label}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <Button
                  variant="primary"
                  size="large"
                  icon={loading ? <FiRefreshCw className="spin" /> : <FiCheck />}
                  onClick={() => handleGenerate()}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? 'Generating...' : 'Generate Job Description'}
                </Button>
              </div>
            </Card>

            {/* Results Section */}
            <Card
              title="Generated Output"
              subtitle={generatedJD ? 'AI-generated job description ready' : 'Output will appear here'}
              padding="medium"
              className="jd-generator__results-card"
            >
              {generatedJD ? (
                <>
                  {/* Tabs */}
                  <div className="result-tabs">
                    <button
                      className={`tab ${activeTab === 'jd' ? 'active' : ''}`}
                      onClick={() => setActiveTab('jd')}
                    >
                      <FiFileText /> Job Description
                    </button>
                    <button
                      className={`tab ${activeTab === 'explain' ? 'active' : ''}`}
                      onClick={explainedJD ? () => setActiveTab('explain') : handleExplain}
                      disabled={loading}
                    >
                      <FiMessageCircle /> {explainedJD ? 'For Candidate' : 'Explain to Candidate'}
                    </button>
                    <button
                      className={`tab ${activeTab === 'rewrite' ? 'active' : ''}`}
                      onClick={rewrittenJD ? () => setActiveTab('rewrite') : handleRewrite}
                      disabled={loading}
                    >
                      <FiBriefcase /> {rewrittenJD ? 'For Manager' : 'Rewrite for Manager'}
                    </button>
                  </div>

                  {/* Action Buttons */}
                  <div className="result-actions">
                    <Button variant="ghost" size="small" icon={<FiCopy />} onClick={handleCopy}>
                      Copy
                    </Button>
                    <Button variant="ghost" size="small" icon={<FiMail />} onClick={handleSendEmail}>
                      Send Email
                    </Button>
                    <Button variant="ghost" size="small" icon={<FiDownload />} onClick={handleDownloadWord}>
                      Download Word
                    </Button>
                    <Button variant="ghost" size="small" icon={<FiPrinter />} onClick={handleDownloadPDF}>
                      Download PDF
                    </Button>
                    <Button variant="ghost" size="small" icon={<FiRefreshCw />} onClick={handleReset}>
                      Reset
                    </Button>
                  </div>

                  {/* Tab Content */}
                  <div className="result-content">
                    {activeTab === 'jd' && (
                      <div className="jd-content">
                        <h2>{generatedJD.jd_content.title}</h2>
                        <p className="jd-overview">{maskPII(generatedJD.jd_content.overview)}</p>

                        <section>
                          <h3>Key Responsibilities</h3>
                          <ul>
                            {generatedJD.jd_content.responsibilities.map((item, i) => (
                              <li key={i}>{maskPII(item)}</li>
                            ))}
                          </ul>
                        </section>

                        <section>
                          <h3>Required Qualifications</h3>
                          <ul>
                            {generatedJD.jd_content.qualifications.required.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </section>

                        {generatedJD.jd_content.qualifications.preferred.length > 0 && (
                          <section>
                            <h3>Preferred Qualifications</h3>
                            <ul>
                              {generatedJD.jd_content.qualifications.preferred.map((item, i) => (
                                <li key={i}>{item}</li>
                              ))}
                            </ul>
                          </section>
                        )}

                        <section>
                          <h3>What We Offer</h3>
                          <ul>
                            {generatedJD.jd_content.what_we_offer.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </section>

                        {/* Skill Matrix */}
                        <section className="skill-matrix">
                          <h3>Skill Matrix</h3>
                          <div className="skill-grid">
                            <div className="skill-section">
                              <h4>Technical Skills</h4>
                              {generatedJD.skill_matrix.technical_skills.map((skill, i) => (
                                <div key={i} className="skill-item">
                                  <span className="skill-name">{skill.skill}</span>
                                  <Badge variant="primary" size="small">{skill.proficiency}</Badge>
                                  <Badge variant="secondary" size="small">{skill.priority}</Badge>
                                </div>
                              ))}
                            </div>
                            <div className="skill-section">
                              <h4>Soft Skills</h4>
                              {generatedJD.skill_matrix.soft_skills.map((skill, i) => (
                                <div key={i} className="skill-item">
                                  <span className="skill-name">{skill.skill}</span>
                                  <span className="skill-context">{skill.context}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </section>

                        {/* Salary Benchmark */}
                        <section className="salary-benchmark">
                          <h3>Salary Benchmark</h3>
                          <div className="salary-range">
                            <div className="salary-item">
                              <label>Minimum</label>
                              <span>{generatedJD.salary_benchmark.currency} {generatedJD.salary_benchmark.min_salary.toLocaleString()}</span>
                            </div>
                            <div className="salary-item">
                              <label>Median</label>
                              <span>{generatedJD.salary_benchmark.currency} {generatedJD.salary_benchmark.median_salary.toLocaleString()}</span>
                            </div>
                            <div className="salary-item">
                              <label>Maximum</label>
                              <span>{generatedJD.salary_benchmark.currency} {generatedJD.salary_benchmark.max_salary.toLocaleString()}</span>
                            </div>
                          </div>
                          <div className="salary-factors">
                            <h4>Factors Considered</h4>
                            <ul>
                              {generatedJD.salary_benchmark.factors.map((factor, i) => (
                                <li key={i}>{factor}</li>
                              ))}
                            </ul>
                            <p className="salary-note">{generatedJD.salary_benchmark.note}</p>
                          </div>
                        </section>

                        {/* Insights */}
                        <section className="insights">
                          <h3>Market Insights</h3>
                          <div className="insight-item">
                            <h4>Market Demand</h4>
                            <Badge variant="success">{generatedJD.insights.market_demand}</Badge>
                          </div>
                          <div className="insight-item">
                            <h4>Key Differentiators</h4>
                            <ul>
                              {generatedJD.insights.key_differentiators.map((diff, i) => (
                                <li key={i}>{diff}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="insight-item">
                            <h4>Candidate Persona</h4>
                            <p>{generatedJD.insights.candidate_persona}</p>
                          </div>
                          {generatedJD.insights.retention_factors && (
                            <div className="insight-item">
                              <h4>Retention Factors</h4>
                              <ul>
                                {generatedJD.insights.retention_factors.map((factor, i) => (
                                  <li key={i}>{factor}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </section>
                      </div>
                    )}

                    {activeTab === 'explain' && explainedJD && (
                      <div className="explained-content">
                        <div className="content-badge">
                          <Badge variant="info" icon={<FiMessageCircle />}>Candidate-Friendly Version</Badge>
                        </div>
                        <p className="explained-text">{explainedJD}</p>
                      </div>
                    )}

                    {activeTab === 'rewrite' && rewrittenJD && (
                      <div className="rewritten-content">
                        <div className="content-badge">
                          <Badge variant="warning" icon={<FiBriefcase />}>Internal Manager Briefing</Badge>
                        </div>
                        <div className="briefing-text">{rewrittenJD}</div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="jd-generator__empty">
                  <FiFileText size={48} color="#ccc" />
                  <p>Fill in the job details and click "Generate" to create a comprehensive job description</p>
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </AppLayout>
  )
}

export function JobDescriptionResultPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state || {}
  const generatedJD = state.generatedJD
  const formData = state.formData || {}

  useEffect(() => {
    if (!generatedJD) {
      navigate('/jobs/generator/legacy', { replace: true })
    }
  }, [generatedJD, navigate])

  if (!generatedJD) {
    return null
  }

  const jdContent = generatedJD.jd_content || {}
  const qualifications = jdContent.qualifications || { required: [], preferred: [] }
  const skillMatrix = generatedJD.skill_matrix || { technical_skills: [], soft_skills: [] }
  const salaryBenchmark = generatedJD.salary_benchmark || { currency: '', min_salary: 0, median_salary: 0, max_salary: 0, factors: [], note: '' }
  const insights = generatedJD.insights || {}

  const renderListTable = (title, items) => (
    items && items.length ? (
      <section className="result-block" key={title}>
        <h3>{title}</h3>
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>
              <span className="index-col">{idx + 1}.</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>
    ) : null
  )

  const renderOverviewTable = () => (
    jdContent.overview ? (
      <section className="result-block" key="overview">
        <h3>Role Overview</h3>
        <p className="jd-overview">{jdContent.overview}</p>
      </section>
    ) : null
  )

  const renderSkillTable = () => {
    const tech = skillMatrix.technical_skills || []
    const soft = skillMatrix.soft_skills || []
    if (!tech.length && !soft.length) return null
    return (
      <section className="skill-matrix" key="skills">
        <h3>Skill Matrix</h3>
        <div className="skill-grid">
          {tech.map((skill, idx) => (
            <div className="skill-card" key={`tech-${idx}`}>
              <div className="skill-title">{skill.skill}</div>
              <div className="skill-meta">
                <span>{skill.proficiency}</span>
                <span>{skill.priority}</span>
              </div>
            </div>
          ))}
          {soft.map((skill, idx) => (
            <div className="skill-card" key={`soft-${idx}`}>
              <div className="skill-title">{skill.skill}</div>
              <div className="skill-context">{skill.context}</div>
            </div>
          ))}
        </div>
      </section>
    )
  }

  const renderSalaryTable = () => {
    const cards = []
    if (salaryBenchmark.min_salary) cards.push({ label: 'Minimum', value: `${salaryBenchmark.currency || ''} ${(salaryBenchmark.min_salary ?? 0).toLocaleString()}` })
    if (salaryBenchmark.median_salary) cards.push({ label: 'Median', value: `${salaryBenchmark.currency || ''} ${(salaryBenchmark.median_salary ?? 0).toLocaleString()}` })
    if (salaryBenchmark.max_salary) cards.push({ label: 'Maximum', value: `${salaryBenchmark.currency || ''} ${(salaryBenchmark.max_salary ?? 0).toLocaleString()}` })
    if (!cards.length) return null
    return (
      <section className="salary-benchmark" key="salary">
        <h3>Salary Benchmark</h3>
        <div className="salary-grid">
          {cards.map(card => (
            <div className="salary-card" key={card.label}>
              <span className="salary-label">{card.label}</span>
              <span className="salary-value">{card.value}</span>
            </div>
          ))}
        </div>
        {(salaryBenchmark.factors?.length || salaryBenchmark.note) && (
          <p className="salary-note">
            {[...(salaryBenchmark.factors || []), salaryBenchmark.note || ''].filter(Boolean).join(' • ')}
          </p>
        )}
      </section>
    )
  }

  const renderInsightsTable = () => {
    const cards = []
    if (insights.market_demand) cards.push({ title: 'Market Demand', body: <p>{insights.market_demand}</p> })
    if (insights.key_differentiators?.length) cards.push({ title: 'Key Differentiators', body: <ul>{insights.key_differentiators.map((item, idx) => <li key={idx}>{item}</li>)}</ul> })
    if (insights.candidate_persona) cards.push({ title: 'Candidate Persona', body: <p>{insights.candidate_persona}</p> })
    if (insights.retention_factors?.length) cards.push({ title: 'Retention Factors', body: <ul>{insights.retention_factors.map((item, idx) => <li key={idx}>{item}</li>)}</ul> })
    if (!cards.length) return null
    return (
      <section className="result-block insights" key="insights">
        <h3>Market Insights</h3>
        <div className="insights-grid">
          {cards.map((card, idx) => (
            <div className="insight-card" key={idx}>
              <h4>{card.title}</h4>
              <div className="insight-body">{card.body}</div>
            </div>
          ))}
        </div>
      </section>
    )
  }

  const buildJDPlainText = () => {
    const { jd_content = {}, skill_matrix = {}, salary_benchmark = {}, insights = {} } = generatedJD
    const lines = []
    if (jd_content.title) {
      lines.push(jd_content.title.toUpperCase())
    }
    if (jd_content.overview) {
      lines.push('', jd_content.overview)
    }
    if (jd_content.responsibilities?.length) {
      lines.push('', 'KEY RESPONSIBILITIES:')
      jd_content.responsibilities.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    const req = jd_content.qualifications?.required || []
    if (req.length) {
      lines.push('', 'REQUIRED QUALIFICATIONS:')
      req.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    const pref = jd_content.qualifications?.preferred || []
    if (pref.length) {
      lines.push('', 'PREFERRED QUALIFICATIONS:')
      pref.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (jd_content.what_we_offer?.length) {
      lines.push('', 'WHAT WE OFFER:')
      jd_content.what_we_offer.forEach((item, index) => {
        lines.push(`${index + 1}. ${item}`)
      })
    }
    if (skill_matrix) {
      if (skill_matrix.technical_skills?.length) {
        lines.push('', 'TECHNICAL SKILL MATRIX:')
        skill_matrix.technical_skills.forEach(skill => {
          lines.push(`- ${skill.skill} | ${skill.proficiency} | ${skill.priority}`)
        })
      }
      if (skill_matrix.soft_skills?.length) {
        lines.push('', 'SOFT SKILLS:')
        skill_matrix.soft_skills.forEach(skill => {
          lines.push(`- ${skill.skill}: ${skill.context}`)
        })
      }
    }
    if (salary_benchmark) {
      lines.push('', 'SALARY BENCHMARK:')
      const min = salary_benchmark.min_salary ?? 0
      const med = salary_benchmark.median_salary ?? 0
      const max = salary_benchmark.max_salary ?? 0
      lines.push(`Range: ${salary_benchmark.currency || ''} ${min.toLocaleString()} - ${salary_benchmark.currency || ''} ${max.toLocaleString()}`)
      lines.push(`Median: ${salary_benchmark.currency || ''} ${med.toLocaleString()}`)
      if (salary_benchmark.note) {
        lines.push(`Note: ${salary_benchmark.note}`)
      }
    }
    if (insights) {
      lines.push('', 'MARKET INSIGHTS:')
      if (insights.market_demand) {
        lines.push(`Market Demand: ${insights.market_demand}`)
      }
      if (insights.key_differentiators?.length) {
        lines.push('Key Differentiators:')
        insights.key_differentiators.forEach(diff => lines.push(`- ${diff}`))
      }
      if (insights.candidate_persona) {
        lines.push(`Candidate Persona: ${insights.candidate_persona}`)
      }
      if (insights.retention_factors?.length) {
        lines.push('Retention Factors:')
        insights.retention_factors.forEach(factor => lines.push(`- ${factor}`))
      }
    }
    return lines.join('\n')
  }

  const buildResultPdfHtml = () => {
    if (!generatedJD) return ''
    const jd = generatedJD.jd_content || {}
    const skills = generatedJD.skill_matrix || {}
    const salary = generatedJD.salary_benchmark || {}
    const insightsData = generatedJD.insights || {}

    const styles = `
      * { box-sizing: border-box; }
      body { font-family: Arial, sans-serif; margin: 0; padding: 0; color: #111827; }
      .pdf-wrapper { width: 720px; margin: 0 auto; padding: 32px; }
      table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
      th { text-align: left; text-transform: uppercase; letter-spacing: 0.25em; font-size: 11px; color: #6b7280; padding: 8px 10px; background: #f3f4f6; }
      td { border-top: 1px solid #e5e7eb; padding: 8px 10px; font-size: 12px; }
      .index-cell { width: 28px; color: #94a3b8; font-weight: 600; }
      .label-cell { width: 140px; font-weight: 600; color: #475569; }
      .matrix-table th, .matrix-table td, .salary-table td { border: 1px solid #e5e7eb; }
      ul { margin: 0; padding-left: 18px; }
      header { border-bottom: 1px solid #e5e7eb; margin-bottom: 20px; padding-bottom: 12px; }
      header h1 { margin: 0; font-size: 24px; }
      header p { margin: 4px 0 0 0; color: #475569; }
    `

    const listSection = (title, items) => (
      items && items.length
        ? `
          <table class="section-table">
            <tr><th colspan="2">${title}</th></tr>
            ${items.map((item, idx) => `<tr><td class="index-cell">${idx + 1}.</td><td>${item}</td></tr>`).join('')}
          </table>
        `
        : ''
    )

    const overviewSection = jd.overview
      ? `
          <table class="section-table">
            <tr><th colspan="2">Role Overview</th></tr>
            <tr><td colspan="2">${jd.overview}</td></tr>
          </table>
        `
      : ''

    const techRows = (skills.technical_skills || []).map(skill => (
      `<tr><td>${skill.skill}</td><td>${skill.proficiency}</td><td>${skill.priority}</td></tr>`
    )).join('')
    const softRows = (skills.soft_skills || []).map(skill => (
      `<tr><td>${skill.skill}</td><td colspan="2">${skill.context}</td></tr>`
    )).join('')
    const skillSection = (techRows || softRows)
      ? `
          <table class="matrix-table">
            <tr><th>Skill</th><th>Proficiency</th><th>Priority / Context</th></tr>
            ${techRows}${softRows}
          </table>
        `
      : ''

    const salaryRows = []
    if (salary.min_salary) salaryRows.push(`<tr><td class="label-cell">Minimum</td><td>${salary.currency || ''} ${(salary.min_salary ?? 0).toLocaleString()}</td></tr>`)
    if (salary.median_salary) salaryRows.push(`<tr><td class="label-cell">Median</td><td>${salary.currency || ''} ${(salary.median_salary ?? 0).toLocaleString()}</td></tr>`)
    if (salary.max_salary) salaryRows.push(`<tr><td class="label-cell">Maximum</td><td>${salary.currency || ''} ${(salary.max_salary ?? 0).toLocaleString()}</td></tr>`)
    if (salary.factors?.length || salary.note) {
      salaryRows.push(`<tr><td class="label-cell">Notes</td><td>${[...(salary.factors || []), salary.note || ''].filter(Boolean).join(' • ')}</td></tr>`)
    }
    const salarySection = salaryRows.length
      ? `
          <table class="salary-table">
            <tr><th colspan="2">Salary Benchmark</th></tr>
            ${salaryRows.join('')}
          </table>
        `
      : ''

    const insightsRows = []
    if (insightsData.market_demand) insightsRows.push(`<tr><td class="label-cell">Market Demand</td><td>${insightsData.market_demand}</td></tr>`)
    if (insightsData.key_differentiators?.length) insightsRows.push(`<tr><td class="label-cell">Key Differentiators</td><td><ul>${insightsData.key_differentiators.map(item => `<li>${item}</li>`).join('')}</ul></td></tr>`)
    if (insightsData.candidate_persona) insightsRows.push(`<tr><td class="label-cell">Candidate Persona</td><td>${insightsData.candidate_persona}</td></tr>`)
    if (insightsData.retention_factors?.length) insightsRows.push(`<tr><td class="label-cell">Retention Factors</td><td><ul>${insightsData.retention_factors.map(item => `<li>${item}</li>`).join('')}</ul></td></tr>`)
    const insightsSection = insightsRows.length
      ? `
          <table class="section-table">
            <tr><th colspan="2">Market Insights</th></tr>
            ${insightsRows.join('')}
          </table>
        `
      : ''

    const content = `
      <div class="pdf-wrapper">
        <header>
          <h1>${jd.title || 'Job Description'}</h1>
          <p>${formData.department || ''} ${formData.location ? '• ' + formData.location : ''} ${formData.seniority ? '• ' + formData.seniority : ''}</p>
        </header>
        ${overviewSection}
        ${listSection('Key Responsibilities', jd.responsibilities || [])}
        ${listSection('Required Qualifications', jd.qualifications?.required || [])}
        ${listSection('Preferred Qualifications', jd.qualifications?.preferred || [])}
        ${listSection('What We Offer', jd.what_we_offer || [])}
        ${skillSection}
        ${salarySection}
        ${insightsSection ? `<div style="page-break-before: always;"></div>${insightsSection}` : ''}
      </div>
    `

    return `<!DOCTYPE html><html><head><meta charset="utf-8" /><style>${styles}</style></head><body>${content}</body></html>`
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(buildJDPlainText())
    toast.success('Copied to clipboard!')
  }

  const handleSendEmail = () => {
    const subject = `Job Description - ${formData.role || generatedJD.jd_content.title || 'Open Role'}`
    const body = buildJDPlainText()
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  const handleDownloadWord = () => {
    const html = buildResultPdfHtml()
    if (!html) {
      toast.error('Nothing to export')
      return
    }
    const fileName = `${(formData.role || generatedJD.jd_content.title || 'job-description').toLowerCase().replace(/\s+/g, '-')}-jd.doc`
    const blob = new Blob(['\ufeff', html], { type: 'application/msword' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Word document downloaded!')
  }

  const handleDownloadPDF = async () => {
    const html = buildResultPdfHtml()
    if (!html) {
      toast.error('Nothing to export')
      return
    }
    const iframe = document.createElement('iframe')
    iframe.style.position = 'fixed'
    iframe.style.top = '-10000px'
    iframe.style.left = '-10000px'
    iframe.style.width = '800px'
    iframe.style.height = '1200px'
    document.body.appendChild(iframe)

    await new Promise((resolve) => {
      iframe.onload = resolve
      iframe.srcdoc = html
    })

    const doc = new jsPDF('p', 'pt', 'a4')
    const fileName = `${(formData.role || generatedJD.jd_content.title || 'job-description').toLowerCase().replace(/\s+/g, '-')}-jd.pdf`
    try {
      await doc.html(iframe.contentDocument.documentElement, {
        callback: (docInstance) => {
          docInstance.save(fileName)
          toast.success('PDF downloaded!')
        },
        margin: 20,
        autoPaging: 'text',
        html2canvas: {
          scale: 0.65,
          useCORS: true,
          logging: false
        },
        windowWidth: 760
      })
    } catch (error) {
      console.error('PDF generation failed', error)
      toast.error('Failed to generate PDF')
    } finally {
      document.body.removeChild(iframe)
    }
  }

  return (
    <AppLayout>
      <div className="jd-result">
        <div className="jd-result__header">
          <div>
            <Button variant="ghost" icon={<FiArrowLeft />} onClick={() => navigate('/jobs/generator')}>
              Back to Generator
            </Button>
            <h1>{jdContent.title}</h1>
            <p>Your comprehensive job description is ready below with multiple sharing options.</p>
          </div>
          <Badge variant="primary" size="medium">Ready</Badge>
        </div>

        <div className="jd-result__actions">
          <Button variant="primary" icon={<FiCopy />} onClick={handleCopy}>Copy</Button>
          <Button variant="secondary" icon={<FiMail />} onClick={handleSendEmail}>Send Email</Button>
          <Button variant="secondary" icon={<FiDownload />} onClick={handleDownloadWord}>Download Word</Button>
          <Button variant="secondary" icon={<FiPrinter />} onClick={handleDownloadPDF}>Download PDF</Button>
        </div>

        <Card className="jd-result__card" padding="large">
          <div className="jd-result__tabs">
            <Badge variant="info" icon={<FiFileText />}>Job Description</Badge>
            <Badge variant="success" icon={<FiMessageCircle />}>Candidate Version</Badge>
            <Badge variant="warning" icon={<FiBriefcase />}>Manager Briefing</Badge>
          </div>

          <div className="jd-result__content">
            {renderOverviewTable()}
            {renderListTable('Key Responsibilities', jdContent.responsibilities)}
            {renderListTable('Required Qualifications', qualifications.required)}
            {renderListTable('Preferred Qualifications', qualifications.preferred)}
            {renderListTable('What We Offer', jdContent.what_we_offer)}
            {renderSkillTable()}
            {renderSalaryTable()}
            {renderInsightsTable()}
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}
