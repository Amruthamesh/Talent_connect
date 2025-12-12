import React from 'react'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Button from '@components/atoms/Button'
import Badge from '@components/atoms/Badge'
import { FiFileText, FiDownload, FiPlus } from 'react-icons/fi'
import content from './content.json'
import './style.scss'

const templates = [
  { id: 1, name: 'Offer Letter', category: 'Hiring', usage: 145 },
  { id: 2, name: 'Termination Letter', category: 'Exit', usage: 32 },
  { id: 3, name: 'Promotion Letter', category: 'Internal', usage: 89 },
  { id: 4, name: 'Warning Letter', category: 'Disciplinary', usage: 12 },
  { id: 5, name: 'Transfer Letter', category: 'Internal', usage: 56 },
  { id: 6, name: 'Experience Certificate', category: 'Exit', usage: 78 },
]

export default function DocumentTemplates() {
  return (
    <AppLayout>
      <div className="document-templates">
        <div className="document-templates__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle}</p>
            <div style={{
              background: '#fff3cd',
              border: '2px solid #FFCC00',
              padding: '1rem',
              borderRadius: '0.5rem',
              marginTop: '1rem'
            }}>
              <h3 style={{color: '#D40511', margin: '0 0 0.5rem 0'}}>🤖 NEW: AI Document Agent Available!</h3>
              <p style={{margin: '0 0 0.5rem 0'}}>Generate HR letters automatically using our AI chatbot.</p>
              <Button 
                variant="primary" 
                onClick={() => window.location.href = '/documents'}
                style={{background: '#FFCC00', borderColor: '#FFCC00', color: '#000'}}
              >
                Go to Document Dashboard →
              </Button>
            </div>
          </div>
          <Button variant="primary" icon={<FiPlus />}>
            Create Custom Template
          </Button>
        </div>

        <div className="document-templates__grid">
          {templates.map((template) => (
            <Card key={template.id} hoverable padding="medium">
              <div className="document-templates__template">
                <div className="document-templates__template-icon">
                  <FiFileText />
                </div>
                <div className="document-templates__template-content">
                  <h3>{template.name}</h3>
                  <Badge variant="primary" size="small">{template.category}</Badge>
                  <p>{template.usage} documents generated</p>
                </div>
                <div className="document-templates__template-actions">
                  <Button variant="ghost" size="small">Preview</Button>
                  <Button variant="primary" size="small">Use Template</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
