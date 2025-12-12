# AI Integration Guide for Talent Connect

## 🤖 AI Strategy Overview

This document outlines the AI integration points across all modules with implementation recommendations suitable for a hackathon timeline.

---

## 1️⃣ Jobs Module

### A. Job Description Generator

**AI Agent**: JD Composer Agent

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/jdComposer.js

import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: import.meta.env.VITE_ANTHROPIC_API_KEY,
})

export async function generateJobDescription(conversationHistory, userPrompt) {
  const systemPrompt = `You are an expert HR assistant specializing in creating comprehensive job descriptions. 
  
  Your role is to:
  1. Ask clarifying questions about the role
  2. Generate detailed, inclusive job descriptions
  3. Ensure compliance with employment laws
  4. Use engaging, non-discriminatory language
  
  Structure JDs with: Title, Summary, Responsibilities, Requirements, Benefits`

  const messages = [
    ...conversationHistory,
    { role: 'user', content: userPrompt }
  ]

  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    system: systemPrompt,
    messages: messages,
  })

  return response.content[0].text
}
```

**Key Features**:
- **Multi-turn conversation**: Build JD through dialogue
- **Context retention**: Remember previous answers
- **Template injection**: Use company's past JDs as examples
- **Bias detection**: Flag potentially discriminatory language

**Demo Flow**:
1. User: "Create JD for Senior AI Engineer"
2. Agent: "Great! What tech stack will they work with?"
3. User: "Python, TensorFlow, AWS"
4. Agent: Generates complete JD

---

### B. Profile Matcher

**AI Agent**: Talent Scorer Agent

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/profileMatcher.js

import { createEmbedding, cosineSimilarity } from './embeddings'

export async function matchProfiles(jobDescription, candidateProfiles) {
  // 1. Create embedding for JD
  const jdEmbedding = await createEmbedding(jobDescription)
  
  // 2. Create embeddings for each profile
  const profileEmbeddings = await Promise.all(
    candidateProfiles.map(profile => createEmbedding(profile.text))
  )
  
  // 3. Calculate similarity scores
  const matches = candidateProfiles.map((profile, index) => {
    const similarity = cosineSimilarity(jdEmbedding, profileEmbeddings[index])
    const score = Math.round(similarity * 100)
    
    return {
      ...profile,
      score,
      strengths: extractStrengths(profile, jobDescription),
      gaps: extractGaps(profile, jobDescription)
    }
  })
  
  // 4. Sort by score
  return matches.sort((a, b) => b.score - a.score)
}

async function extractStrengths(profile, jd) {
  // Use Claude to analyze match
  const prompt = `Compare this profile with the job requirements and list 3 key strengths:
  
  JD: ${jd.substring(0, 500)}
  Profile: ${profile.text.substring(0, 500)}
  
  Return only the strengths as bullet points.`
  
  // Call Claude API...
  return ['Strong technical skills', 'Relevant experience', 'Cultural fit']
}
```

**Key Features**:
- **Semantic matching**: Beyond keyword search
- **Explainable scores**: Show why candidates match
- **Batch processing**: Handle multiple profiles efficiently
- **Ranking with reasoning**: Not just a number

---

## 2️⃣ Documents Module

### A. Letter Generator Agent

**AI Agent**: Letter Craft Agent

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/letterGenerator.js

export async function generateLetter(templateType, employeeData, customInstructions) {
  const baseTemplate = getBaseTemplate(templateType)
  
  const systemPrompt = `You are an HR document specialist. Generate professional, 
  legally compliant employment letters.
  
  Requirements:
  - Use formal, professional tone
  - Include all mandatory clauses based on region
  - Personalize while maintaining legal structure
  - Ensure compliance with employment laws`
  
  const userPrompt = `Generate a ${templateType} using this information:
  
  Employee: ${employeeData.name}
  Position: ${employeeData.position}
  Department: ${employeeData.department}
  Start Date: ${employeeData.startDate}
  Salary: ${employeeData.salary}
  
  Base Template:
  ${baseTemplate}
  
  Additional Instructions: ${customInstructions || 'None'}
  
  Personalize the introduction and add any context-specific clauses.`
  
  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    system: systemPrompt,
    messages: [{ role: 'user', content: userPrompt }],
  })
  
  return response.content[0].text
}
```

**Key Features**:
- **Template + AI hybrid**: Structure + Personalization
- **Legal compliance**: Auto-include mandatory clauses
- **Multi-language**: Generate in local languages
- **Variable substitution**: Smart placeholder filling

---

### B. Document Search Agent

**AI Agent**: Doc Finder Agent

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/documentSearch.js

export async function semanticDocumentSearch(query) {
  // 1. Convert query to embedding
  const queryEmbedding = await createEmbedding(query)
  
  // 2. Search vector database
  const results = await vectorDB.search(queryEmbedding, {
    topK: 10,
    filter: { type: 'employment_document' }
  })
  
  // 3. Re-rank with Claude for better relevance
  const reranked = await rerankWithAI(query, results)
  
  return reranked
}

// Natural language query examples:
// "Find all termination letters from Q2 2024"
// "Show me offers with signing bonuses over $10k"
// "Letters with garden leave clauses"
```

**Key Features**:
- **Natural language queries**: No SQL needed
- **Semantic understanding**: "termination" = "separation" = "exit"
- **Metadata filtering**: Date, type, department
- **Privacy-aware**: Auto-redact sensitive info in previews

---

## 3️⃣ Interview Module

### A. Interview Co-Pilot Agent

**AI Agent**: Interview Assistant

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/interviewCopilot.js

export class InterviewCoPilot {
  constructor(jobDescription, candidateResume) {
    this.jd = jobDescription
    this.resume = candidateResume
    this.transcript = []
    this.suggestedQuestions = []
  }
  
  async onTranscriptUpdate(newText, speaker) {
    this.transcript.push({ speaker, text: newText, timestamp: Date.now() })
    
    // Real-time analysis
    if (speaker === 'candidate') {
      await this.analyzeResponse(newText)
      await this.generateFollowUpQuestions()
    }
  }
  
  async generateFollowUpQuestions() {
    const recentTranscript = this.transcript.slice(-5)
    
    const prompt = `Based on this interview transcript, suggest 2 intelligent follow-up questions:
    
    Job: ${this.jd.title}
    Recent conversation: ${JSON.stringify(recentTranscript)}
    
    Questions should:
    - Probe deeper into the candidate's last answer
    - Assess technical depth or behavioral fit
    - Be open-ended and thoughtful`
    
    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 500,
      messages: [{ role: 'user', content: prompt }],
    })
    
    this.suggestedQuestions = parseQuestions(response.content[0].text)
    return this.suggestedQuestions
  }
  
  async analyzeResponse(candidateAnswer) {
    const prompt = `Analyze this interview response:
    
    Question context: ${this.transcript.slice(-2)[0].text}
    Candidate answer: ${candidateAnswer}
    
    Provide:
    1. Relevance score (0-10)
    2. Key strengths demonstrated
    3. Potential red flags
    4. Suggested follow-up areas`
    
    // Return analysis...
  }
  
  async generateInterviewSummary() {
    const prompt = `Generate a comprehensive interview summary:
    
    Position: ${this.jd.title}
    Candidate: ${this.resume.name}
    
    Full transcript: ${JSON.stringify(this.transcript)}
    
    Include:
    - Overall assessment
    - Technical competencies demonstrated
    - Soft skills observed
    - Strengths and concerns
    - Hiring recommendation (Strong Hire / Maybe / No) with reasoning`
    
    // Return summary...
  }
}
```

**Key Features**:
- **Real-time transcription**: Whisper API or Deepgram
- **Context-aware questions**: Based on JD + resume + conversation
- **Answer evaluation**: Score responses instantly
- **Auto-summarization**: Generate interview report

**UI Integration**:
```jsx
// In InterviewerPanel component
const [copilot] = useState(() => new InterviewCoPilot(jobDesc, resume))
const [suggestions, setSuggestions] = useState([])

useEffect(() => {
  const interval = setInterval(async () => {
    const newQuestions = await copilot.generateFollowUpQuestions()
    setSuggestions(newQuestions)
  }, 30000) // Every 30 seconds
  
  return () => clearInterval(interval)
}, [])
```

---

### B. Proctoring Agent (Privacy-First)

**AI Agent**: ProctorGuard (Client-Side)

**Implementation**:
```javascript
// frontend/src/utils/aiAgents/proctoring.js
import * as tf from '@tensorflow/tfjs'
import * as faceapi from 'face-api.js'

export class ProctorAgent {
  constructor() {
    this.violations = []
    this.isActive = false
  }
  
  async initialize() {
    // Load lightweight models (face detection only)
    await faceapi.nets.tinyFaceDetector.loadFromUri('/models')
    this.isActive = true
  }
  
  async analyzeFrame(videoElement) {
    if (!this.isActive) return
    
    const detection = await faceapi.detectSingleFace(
      videoElement, 
      new faceapi.TinyFaceDetectorOptions()
    )
    
    const analysis = {
      faceDetected: !!detection,
      multipleFaces: false, // Can be enhanced
      timestamp: Date.now()
    }
    
    // Flag violations
    if (!analysis.faceDetected) {
      this.violations.push({
        type: 'NO_FACE',
        timestamp: Date.now()
      })
    }
    
    return analysis
  }
  
  // Check tab visibility
  onVisibilityChange() {
    if (document.hidden) {
      this.violations.push({
        type: 'TAB_SWITCH',
        timestamp: Date.now()
      })
    }
  }
  
  getViolationSummary() {
    return {
      total: this.violations.length,
      byType: groupBy(this.violations, 'type'),
      severity: this.calculateSeverity()
    }
  }
}
```

**Key Features**:
- **Browser-based**: No server-side video processing
- **Privacy-first**: No video recording, only flags
- **Lightweight**: TensorFlow.js models (<5MB)
- **Non-intrusive**: Gentle monitoring, not surveillance

---

## 🚀 Quick Start Guide

### 1. Install Dependencies

```bash
cd frontend
npm install @anthropic-ai/sdk @tensorflow/tfjs face-api.js
```

### 2. Set Environment Variables

```env
VITE_ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Test Job Description Generator

```javascript
// pages/Jobs/JobDescriptionGenerator/index.jsx

import { generateJobDescription } from '@utils/aiAgents/jdComposer'

const handleSend = async () => {
  const aiResponse = await generateJobDescription(
    messages, 
    userInput
  )
  
  setMessages([...messages, {
    sender: 'ai',
    message: aiResponse,
    timestamp: 'Just now'
  }])
}
```

---

## 💡 Hackathon Demo Tips

### Must-Have for Demo (3-5 min pitch)

1. **Live AI Interaction**: Show JD generation in real-time
2. **Profile Matching**: Upload 3 resumes, show instant ranking
3. **Interview Co-Pilot**: Mock interview with live question suggestions
4. **Speed Comparison**: "Manual: 2 hours → AI: 30 seconds"

### Wow Factors

- **Explainable AI**: Show *why* candidate scored 87%
- **Bias Detection**: Highlight when AI flags discriminatory language
- **Multi-agent Orchestra**: Show 3 agents working together
- **Cost Savings**: Calculate "This saved 40 hours of HR time"

### What Judges Want to See

✅ **Real AI integration** (not just UI mockups)  
✅ **Practical business value** (time/cost savings)  
✅ **Ethical AI** (bias detection, privacy)  
✅ **Scalability** (can handle 1000 profiles)  
✅ **User experience** (AI is helpful, not overwhelming)

---

## 📊 Performance Optimization

### Reduce Latency

```javascript
// Cache embeddings
const embeddingCache = new Map()

async function createEmbedding(text) {
  const cacheKey = hash(text)
  if (embeddingCache.has(cacheKey)) {
    return embeddingCache.get(cacheKey)
  }
  
  const embedding = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text
  })
  
  embeddingCache.set(cacheKey, embedding.data[0].embedding)
  return embedding.data[0].embedding
}
```

### Streaming Responses

```javascript
// Stream JD generation for better UX
async function* streamJobDescription(prompt) {
  const stream = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  })
  
  for await (const event of stream) {
    if (event.type === 'content_block_delta') {
      yield event.delta.text
    }
  }
}
```

---

## 🔒 Security & Privacy

### Best Practices

1. **Never send PII to logs**
2. **Redact sensitive info** before AI processing
3. **Client-side proctoring** (no video upload)
4. **Token expiry** for guest interviews
5. **Audit trail** for all AI decisions

```javascript
// Redact sensitive info
function redactPII(text) {
  return text
    .replace(/\b[\w\.-]+@[\w\.-]+\.\w+\b/g, '[EMAIL]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]')
    .replace(/\b\d{10}\b/g, '[PHONE]')
}
```

---

## 📈 Success Metrics

Track these for demo:

- **Time Saved**: JD generation: 2 hrs → 30 sec
- **Accuracy**: Profile matching: 85%+ precision
- **User Satisfaction**: "Would use this daily" (survey)
- **Cost Reduction**: $50k/year in HR time savings

---

Built with 🤖 AI · Ready for DHL Hackathon 2025
