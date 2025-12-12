import { create } from 'zustand'
import { interviewsAPI } from '@utils/api'

const storedKeys = JSON.parse(sessionStorage.getItem('participantKeys') || '{}')

const dedupeById = (items = []) => {
  const seen = new Set()
  return items.filter((item) => {
    if (!item?.id) return false
    if (seen.has(item.id)) return false
    seen.add(item.id)
    return true
  })
}
const sameId = (a, b) => String(a) === String(b)

const getKeyForInterview = (state, interviewId) => {
  const keyFromStore =
    state.participantKeys[String(interviewId)] ?? state.participantKeys[interviewId]
  if (keyFromStore) return keyFromStore
  const interview = state.interviews.find((i) => sameId(i.id, interviewId))
  return interview?.interviewer_key || interview?.candidate_key
}

export const useInterviewStore = create((set, get) => ({
  interviews: [],
  pendingQuestions: {},
  loading: false,
  error: null,
  participantKeys: storedKeys, // track join keys used locally
  sockets: {},

  syncInterview: (interview) => {
    set((state) => {
      const exists = state.interviews.find((item) => sameId(item.id, interview.id))
      const updatedList = exists
        ? state.interviews.map((item) => (sameId(item.id, interview.id) ? interview : item))
        : [interview, ...state.interviews]

      // Pending questions are those without answers
      const pending = dedupeById((interview.transcript || []).filter((q) => !q.answer))
      const keyId = String(interview.id)
      const participantKeys = { ...state.participantKeys }
      if (!participantKeys[keyId] && interview.interviewer_key) {
        participantKeys[keyId] = interview.interviewer_key
        sessionStorage.setItem('participantKeys', JSON.stringify(participantKeys))
      }

      return {
        interviews: updatedList,
        pendingQuestions: {
          ...state.pendingQuestions,
          [keyId]: pending
        },
        participantKeys
      }
    })
  },

  fetchInterviews: async () => {
    set({ loading: true, error: null })
    try {
      const data = await interviewsAPI.getInterviews()
    set({
      interviews: data,
      pendingQuestions: Object.fromEntries(
        data.map((i) => [i.id, dedupeById((i.transcript || []).filter((q) => !q.answer))])
      ),
      loading: false
    })
  } catch (error) {
    set({ error: error.message, loading: false })
    throw error
  }
  },

  scheduleInterview: async (formValues, files) => {
    const formData = new FormData()
    formData.append('candidate_name', formValues.candidateName)
    formData.append('candidate_email', formValues.candidateEmail || '')
    formData.append('role', formValues.role)
    formData.append('company', formValues.company || '')
    formData.append('round_type', formValues.roundType)
    formData.append('date', formValues.date)
    formData.append('time', formValues.time)
    formData.append('notes', formValues.notes || '')
    formData.append('jd_text', formValues.jobDescriptionText || '')

    if (files.resume) formData.append('resume', files.resume)
    if (files.jobDescription) formData.append('job_description', files.jobDescription)

    const interview = await interviewsAPI.scheduleInterviewForm(formData)
    get().syncInterview(interview)
    return interview
  },

  resolveKey: async (key) => {
    const result = await interviewsAPI.resolveKey(key)
    set((state) => {
      const updatedKeys = { ...state.participantKeys, [result.interview.id]: key }
      sessionStorage.setItem('participantKeys', JSON.stringify(updatedKeys))
      return { participantKeys: updatedKeys }
    })
    return result
  },
  ensureKeyAndInterview: async (key) => {
    if (!key) return null
    const existing = Object.values(get().participantKeys || {}).find((v) => v === key)
    if (existing) return null
    const result = await get().resolveKey(key)
    get().syncInterview(result.interview)
    return result
  },
  getParticipantKey: (interviewId) => get().participantKeys[interviewId],

  connectSocket: (interviewId) => {
    const socketKey = String(interviewId)
    const existing = get().sockets[socketKey]
    if (existing) return existing
    const resolvedKey = getKeyForInterview(get(), interviewId)
    if (!resolvedKey) return null
    const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/^http/, 'ws')
    const ws = new WebSocket(`${base}/interviews/${interviewId}/ws?key=${resolvedKey}`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'question' && data.question) {
        get().applyQuestionEvent(interviewId, data.question)
      } else if (data.type === 'response') {
        get().applyResponseEvent(interviewId, data.question_id, data.answer)
      } else if (data.type === 'status' && data.status) {
        set((state) => ({
          interviews: state.interviews.map((i) =>
            sameId(i.id, interviewId) ? { ...i, status: data.status } : i
          )
        }))
      }
    }

    set((state) => ({
      sockets: { ...state.sockets, [socketKey]: ws }
    }))
    return ws
  },

  disconnectSocket: (interviewId) => {
    const sockets = get().sockets
    const ws = sockets[String(interviewId)]
    if (ws) ws.close()
    const updated = { ...sockets }
    delete updated[String(interviewId)]
    set({ sockets: updated })
  },

  updateStatus: async (interviewId, status) => {
    const key = getKeyForInterview(get(), interviewId)
    if (!key) throw new Error('Missing participant key for status update')
    const interview = await interviewsAPI.updateStatus(interviewId, status, key)
    get().syncInterview(interview)
    return interview
  },

  sendQuestion: async (interviewId, questionText) => {
    const key = getKeyForInterview(get(), interviewId)
    if (!key) throw new Error('Missing participant key for send question')
    const interview = await interviewsAPI.sendQuestion(interviewId, questionText, key)
    get().syncInterview(interview)
    return interview.transcript?.slice(-1)[0]
  },

  recordResponse: async (interviewId, questionId, answer) => {
    const key = getKeyForInterview(get(), interviewId)
    if (!key) throw new Error('Missing participant key for response')
    const interview = await interviewsAPI.sendResponse(interviewId, questionId, answer, key)
    get().syncInterview(interview)
    return interview
  },

  saveFeedback: async (interviewId, feedback) => {
    const key = getKeyForInterview(get(), interviewId)
    if (!key) throw new Error('Missing participant key for feedback')
    const interview = await interviewsAPI.submitFeedback(interviewId, feedback, key)
    get().syncInterview(interview)
    return interview
  },

  applyQuestionEvent: (interviewId, question) => {
    set((state) => {
      const keyId = String(interviewId)
      const interviews = state.interviews.map((i) => {
        if (!sameId(i.id, interviewId)) return i
        const mergedTranscript = dedupeById([...(i.transcript || []), question])
        return { ...i, transcript: mergedTranscript }
      })
      const pending = dedupeById([...(state.pendingQuestions[keyId] || []), question])
      return {
        interviews,
        pendingQuestions: { ...state.pendingQuestions, [keyId]: pending }
      }
    })
  },

  applyResponseEvent: (interviewId, questionId, answer) => {
    set((state) => {
      const keyId = String(interviewId)
      const interviews = state.interviews.map((i) =>
        sameId(i.id, interviewId)
          ? {
              ...i,
              transcript: (i.transcript || []).map((q) =>
                q.id === questionId ? { ...q, answer } : q
              )
            }
          : i
      )
      const updatedPending = { ...(state.pendingQuestions || {}) }
      if (updatedPending[keyId]) {
        updatedPending[keyId] = updatedPending[keyId].filter(
          (q) => q.id !== questionId
        )
      }
      return { interviews, pendingQuestions: updatedPending }
    })
  },

  resetAll: () => {
    set(() => {
      sessionStorage.removeItem('participantKeys')
      return {
        interviews: [],
        pendingQuestions: {},
        loading: false,
        error: null,
        participantKeys: {}
      }
    })
  }
}))
