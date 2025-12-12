import { create } from 'zustand'
import { api } from '@utils/api'

const useJobChatStore = create((set, get) => ({
  // State
  messages: [],
  conversationHistory: [],
  extractedData: {
    role: null,
    seniority: null,
    department: null,
    location: null,
    must_have_skills: [],
    preferred_skills: [],
    responsibilities: [],
    expectations: null,
    team_context: null,
    joining_timeline: null,
    company_tone: null,
    salary_range: null,
    special_requirements: null,
    additional_notes: null
  },
  completionPercentage: 0,
  missingFields: ['role', 'seniority', 'location', 'must_have_skills', 'joining_timeline', 'salary_range'],
  isComplete: false,
  isTyping: false,
  error: null,
  summary: null,

  // Actions
  sendMessage: async (message) => {
    const state = get()
    
    // Add user message to UI
    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }
    
    set({
      messages: [...state.messages, userMessage],
      isTyping: true,
      error: null
    })
    try {
      // Call API
      const response = await api.post('/jobs/chat/interactive-builder', {
        message,
        conversation_history: state.conversationHistory,
        current_data: state.extractedData
      })

      // Add assistant message to UI
      const assistantMessage = {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString()
      }

      // Update state with response
      set({
        messages: [...get().messages, assistantMessage],
        conversationHistory: [
          ...state.conversationHistory,
          { role: 'user', content: message },
          { role: 'assistant', content: response.reply }
        ],
        extractedData: response.extracted_data,
        completionPercentage: response.completion_percentage,
        missingFields: response.missing_required,
        isComplete: response.is_complete,
        summary: response.summary || null,
        isTyping: false
      })

    } catch (error) {
      console.error('Chat error:', error)
      
      // More specific error messages
      let errorContent = 'I apologize, I\'m having trouble processing that.'
      
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        errorContent = 'Your session has expired. Please log in again.'
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        errorContent = 'You don\'t have permission to use this feature.'
      } else if (error.message.includes('Failed to fetch') || error.message.includes('Network')) {
        errorContent = 'Unable to connect to the server. Please check your connection.'
      } else if (error.message) {
        errorContent = `Error: ${error.message}`
      }
      
      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: errorContent,
        timestamp: new Date().toISOString(),
        isError: true
      }
      
      set({
        messages: [...get().messages, errorMessage],
        isTyping: false,
        error: error.message || 'Failed to send message'
      })
    }
  },
  // Reset chat state
  resetChat: () => {
    set({
      messages: [],
      conversationHistory: [],
      extractedData: {
        role: null,
        seniority: null,
        department: null,
        location: null,
        must_have_skills: [],
        preferred_skills: [],
        responsibilities: [],
        expectations: null,
        team_context: null,
        joining_timeline: null,
        company_tone: null,
        salary_range: null,
        special_requirements: null,
        additional_notes: null
      },
      completionPercentage: 0,
      missingFields: ['role', 'seniority', 'location', 'must_have_skills', 'joining_timeline', 'salary_range'],
      isComplete: false,
      isTyping: false,
      error: null,
      summary: null
    })
  },

  // Start fresh chat (reset and initialize, no localStorage)
  startFreshChat: () => {
    set({
      messages: [{
        role: 'assistant',
        content: 'Hi! I\'m here to help you create a job description. What role are you looking to hire for?',
        timestamp: new Date().toISOString()
      }],
      conversationHistory: [],
      extractedData: {
        role: null,
        seniority: null,
        department: null,
        location: null,
        must_have_skills: [],
        preferred_skills: [],
        responsibilities: [],
        expectations: null,
        team_context: null,
        joining_timeline: null,
        company_tone: null,
        salary_range: null,
        special_requirements: null,
        additional_notes: null
      },
      completionPercentage: 0,
      missingFields: ['role', 'seniority', 'location', 'must_have_skills', 'joining_timeline', 'salary_range'],
      isComplete: false,
      isTyping: false,
      error: null,
      summary: null
    })
  },

  // Get form data for auto-fill
  getFormData: () => {
    const data = get().extractedData
    return {
      role: data.role || '',
      seniority: data.seniority || '',
      department: data.department || '',
      location: data.location || '',
      must_have_skills: data.must_have_skills || [],
      preferred_skills: data.preferred_skills || [],
      responsibilities: data.responsibilities || [],
      expectations: data.expectations || '',
      team_context: data.team_context || '',
      joining_timeline: data.joining_timeline || '',
      company_tone: data.company_tone || '',
      salary_range: data.salary_range || '',
      special_requirements: data.special_requirements || '',
      additional_notes: data.additional_notes || ''
    }
  },

  // Update extracted data manually (if user edits in UI)
  updateExtractedData: (field, value) => {
    set(state => ({
      extractedData: {
        ...state.extractedData,
        [field]: value
      }
    }))
  }
}))

export default useJobChatStore
