// API utility functions for making HTTP requests

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token

    const isFormData = options.body instanceof FormData

    const config = {
      ...options,
      headers: {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    }

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config)
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Something went wrong' }))
        throw new Error(error.detail || error.message || 'Something went wrong')
      }

      return await response.json()
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' })
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  postFormData(endpoint, formData) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
    })
  }

  // Special method for OAuth2 form data (used by login)
  async postForm(endpoint, data) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token

    const formData = new URLSearchParams()
    Object.keys(data).forEach(key => {
      formData.append(key, data[key])
    })

    const config = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    }

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config)
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Something went wrong' }))
        throw new Error(error.detail || error.message || 'Something went wrong')
      }

      return await response.json()
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  }
}

export const api = new ApiClient(API_BASE_URL)
export default api

// Specific API endpoints
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
}

export const jobsAPI = {
  generateJD: (prompt) => api.post('/jobs/generate', { prompt }),
  matchProfiles: (jobDescription, profiles) => 
    api.post('/jobs/match', { jobDescription, profiles }),
}

export const matcherAPI = {
  streamMatch: async (jobDescription, files, onEvent) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token
    const formData = new FormData()
    formData.append('job_description', jobDescription)
    files.forEach(file => formData.append('files', file))

    const response = await fetch(`${API_BASE_URL}/matcher/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    })

    if (!response.ok || !response.body) {
      throw new Error('Failed to start streaming match')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    // Parse SSE-style chunks: event: <type>\ndata: <json>\n\n
    const processBuffer = () => {
      const parts = buffer.split('\n\n')
      // keep last partial
      buffer = parts.pop() || ''
      parts.forEach(part => {
        const lines = part.split('\n')
        let event = 'message'
        let data = ''
        lines.forEach(line => {
          if (line.startsWith('event:')) {
            event = line.replace('event:', '').trim()
          } else if (line.startsWith('data:')) {
            data += line.replace('data:', '').trim()
          }
        })
        if (data) {
          try {
            const parsed = JSON.parse(data)
            onEvent?.({ event, data: parsed })
          } catch (e) {
            console.error('Failed to parse SSE data', e)
          }
        }
      })
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      processBuffer()
    }
    // flush remainder
    processBuffer()
  },
  getCandidate: (candidateId) => api.get(`/matcher/candidate/${candidateId}`),
  downloadSingle: async (uploadId) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token
    const res = await fetch(`${API_BASE_URL}/matcher/download/${uploadId}`, {
      method: 'GET',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || 'Failed to download file')
    }
    const filename = res.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] || `resume_${uploadId}.pdf`
    return { blob: await res.blob(), filename }
  },
  downloadZip: async (ids) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token
    const res = await fetch(`${API_BASE_URL}/matcher/download-zip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({ candidate_ids: ids }),
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || 'Failed to download ZIP')
    }
    return await res.blob()
  },
}

export const documentsAPI = {
  getTemplates: () => api.get('/documents/templates'),
  downloadCsvTemplate: async (templateId) => {
    // Use axios to get a blob and filename from Content-Disposition
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const token = user.token
    const axiosOpts = {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      responseType: 'blob',
    }
    const res = await (await import('axios')).default.get(
      `${API_BASE_URL}/documents/templates/${templateId}/csv-template`,
      axiosOpts
    )
    const blob = res.data
    const dispo = res.headers['content-disposition'] || ''
    let filename = 'document_template.csv'
    const match = dispo.match(/filename="?([^";]+)"?/i)
    if (match && match[1]) {
      filename = match[1]
    }
    const url = window.URL.createObjectURL(blob)
    return { url, blob, filename }
  },
  generateDocument: (templateId, data) => 
    api.post('/documents/generate', { templateId, data }),
  queryDocuments: (query) => api.post('/documents/query', { query }),
}

export const interviewsAPI = {
  getInterviews: () => api.get('/interviews'),
  scheduleInterviewForm: (formData) => api.postFormData('/interviews/schedule', formData),
  getInterview: (id) => api.get(`/interviews/${id}`),
  updateStatus: (id, status, key) => api.put(`/interviews/${id}/status?key=${key}`, { status }),
  sendQuestion: (id, question, key) => api.post(`/interviews/${id}/questions?key=${key}`, { question }),
  sendResponse: (id, questionId, answer, key) => api.post(`/interviews/${id}/responses?key=${key}`, { question_id: questionId, answer }),
  submitFeedback: (id, feedback, key) => api.post(`/interviews/${id}/feedback?key=${key}`, feedback),
  resolveKey: (key) => api.get(`/interviews/resolve/key?key=${encodeURIComponent(key)}`),
}
