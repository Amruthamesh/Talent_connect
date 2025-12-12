import React, { useState } from 'react'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import SearchBar from '@components/molecules/SearchBar'
import Badge from '@components/atoms/Badge'
import Button from '@components/atoms/Button'
import { FiDownload, FiEye } from 'react-icons/fi'
import content from './content.json'
import './style.scss'

export default function DocumentQuery() {
  const [searchQuery, setSearchQuery] = useState('')
  
  const documents = [
    { 
      id: 1, 
      title: 'Offer Letter - John Doe', 
      type: 'Offer Letter', 
      date: '2024-11-10',
      department: 'Engineering'
    },
    { 
      id: 2, 
      title: 'Termination Letter - Jane Smith', 
      type: 'Termination Letter', 
      date: '2024-11-08',
      department: 'Sales'
    },
  ]

  return (
    <AppLayout>
      <div className="document-query">
        <div className="document-query__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle}</p>
          </div>
        </div>

        <Card padding="medium">
          <SearchBar 
            placeholder={content.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </Card>

        <div className="document-query__results">
          {documents.map((doc) => (
            <Card key={doc.id} hoverable padding="medium">
              <div className="document-query__result">
                <div className="document-query__result-content">
                  <h3>{doc.title}</h3>
                  <div className="document-query__result-meta">
                    <Badge variant="primary" size="small">{doc.type}</Badge>
                    <span>{doc.date}</span>
                    <span>{doc.department}</span>
                  </div>
                </div>
                <div className="document-query__result-actions">
                  <Button variant="ghost" size="small" icon={<FiEye />}>View</Button>
                  <Button variant="primary" size="small" icon={<FiDownload />}>Download</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
