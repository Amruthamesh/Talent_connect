# Talent Connect Frontend

AI-Powered HR Management Platform - Frontend Application

## 🏗️ Architecture

This project follows **Atomic Design** principles with a strict component hierarchy and page structure.

### Directory Structure

```
src/
├── components/
│   ├── atoms/          # Basic building blocks
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Badge/
│   │   ├── Card/
│   │   └── Icon/
│   ├── molecules/      # Combinations of atoms
│   │   ├── FormInput/
│   │   ├── CardHeader/
│   │   ├── SearchBar/
│   │   ├── ChatMessage/
│   │   └── FileUpload/
│   └── organisms/      # Complex components
│       ├── Navbar/
│       ├── Sidebar/
│       └── LoginForm/
├── layouts/
│   ├── AuthLayout/     # For login/auth screens
│   ├── AppLayout/      # Main app with navbar + sidebar
│   └── GuestLayout/    # For interview guest users
├── pages/
│   ├── Login/
│   ├── Dashboard/
│   ├── Jobs/
│   │   ├── JobDescriptionGenerator/
│   │   └── ProfileMatcher/
│   ├── Documents/
│   │   ├── Templates/
│   │   └── Query/
│   └── Interviews/
│       ├── Dashboard/
│       ├── Schedule/
│       ├── InterviewerPanel/
│       └── CandidatePanel/
├── router/
│   └── routes.jsx      # Centralized routing with role guards
├── store/
│   └── authStore.js    # Zustand state management
├── utils/
│   └── api.js          # API client utilities
└── styles/
    └── global.scss     # Global styles and variables
```

## 📋 Page Structure Convention

Every page must follow this pattern:

```
/src/pages/PageName/
   index.jsx         → main page component
   content.json      → static text, labels, config
   style.scss        → page-specific styling
```

**Example:**
```jsx
import AppLayout from "@layouts/AppLayout"
import content from "./content.json"
import "./style.scss"

export default function PageName() {
  return (
    <AppLayout>
      {/* page content */}
    </AppLayout>
  )
}
```

## 🎨 Component Hierarchy Rules

1. **Atoms** = Smallest UI primitives (Button, Input, Icon)
2. **Molecules** = Combinations (FormGroup, CardHeader)
3. **Organisms** = Full sections (LoginForm, Navbar, Sidebar)

**Rules:**
- Organisms may use molecules + atoms
- Molecules may use atoms
- Atoms cannot import molecule/organism code
- Pages should prefer using organisms and molecules

## 🔐 Authentication & Roles

**Demo Accounts:**

| Email | Password | Role | Access |
|-------|----------|------|--------|
| hr@talent.com | hr123 | hr | Full access to all modules |
| manager@talent.com | mgr123 | hiring_manager | Jobs, Interviews, Documents (view only) |
| recruiter@talent.com | rec123 | recruiter | Jobs (Profile Matcher), Limited access |

## 🚀 Getting Started

### Installation

```bash
cd frontend
npm install
```

### Environment Setup

Create a `.env` file:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_ANTHROPIC_API_KEY=your_anthropic_api_key
VITE_API_BASE_URL=http://localhost:5000/api
```

### Development

```bash
npm run dev
```

Visit http://localhost:6173

### Build

```bash
npm run build
```

## 🧩 Modules

### 1. Jobs Module
- **Job Description Generator**: AI-powered JD creation with chat interface
- **Profile Matcher**: Match candidate profiles against job descriptions

### 2. Documents Module
- **Template Library**: Browse and generate employment letters
- **Document Query**: Search and retrieve generated documents

### 3. Interviews Module
- **Dashboard**: Overview of scheduled interviews
- **Schedule**: Create new interviews
- **Interviewer Panel**: Conduct interviews with AI assistance
- **Candidate Panel**: Guest access for candidates (token-based)

## 🛣️ Routing

Routes are centralized in `/src/router/routes.jsx` with:
- **Lazy Loading**: All pages loaded on demand
- **Role Guards**: Route protection based on user roles
- **Guest Routes**: Token-based access for interview candidates

**Route Structure:**
```
/ → /dashboard or /login (based on auth)
/login
/dashboard
/jobs/generator
/jobs/matcher
/documents
/documents/agent
/documents/templates
/documents/query
/interviews/dashboard
/interviews/schedule
/interviews/panel/:id
/interview/join?token=xxx (guest)
```

## 🎯 AI Integration Points

1. **Job Description Generator**: Claude Sonnet 4 for contextual JD generation
2. **Profile Matcher**: Semantic matching using embeddings
3. **Document Generator**: Template + AI personalization
4. **Interview Co-Pilot**: Real-time question suggestions
5. **Proctoring**: TensorFlow.js for client-side monitoring

## 📦 Tech Stack

- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **State**: Zustand
- **Styling**: SCSS with CSS Variables
- **AI**: Anthropic Claude (via Vercel AI SDK)
- **Icons**: React Icons (Feather Icons)
- **Notifications**: React Hot Toast

## 🎨 Design System

**Colors:**
- Primary: `#2563eb` (Blue)
- Secondary: `#7c3aed` (Purple)
- Success: `#10b981` (Green)
- Warning: `#f59e0b` (Amber)
- Error: `#ef4444` (Red)

**Typography:**
- Font: Inter (sans-serif)
- Sizes: Responsive with rem units

**Spacing:**
- Uses CSS custom properties (--spacing-xs to --spacing-2xl)

## 📝 Code Style

- Use functional components with hooks
- Follow atomic design patterns strictly
- Import order: React → Libraries → Components → Utils → Styles
- Use path aliases (@components, @pages, @layouts, etc.)

## 🚀 Deployment

Build output goes to `/dist`:

```bash
npm run build
npm run preview  # Test production build
```

Deploy to:
- Vercel (recommended)
- Netlify
- Any static hosting

---

Built with ❤️ for DHL Hackathon 2025
