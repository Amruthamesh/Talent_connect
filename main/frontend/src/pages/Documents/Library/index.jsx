import { useState, useEffect } from 'react';
import axios from 'axios';
import AppLayout from '@layouts/AppLayout';
import './style.scss';
import Card from '../../../components/atoms/Card';
import Button from '../../../components/atoms/Button';
import SearchBar from '../../../components/molecules/SearchBar';

const DocumentLibrary = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState('employee_code');
  const [searchValue, setSearchValue] = useState('');
  const [selectedDoc, setSelectedDoc] = useState(null);

  useEffect(() => {
    fetchRecentDocuments();
  }, []);

  const fetchRecentDocuments = async () => {
    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/documents/query`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchValue.trim()) {
      fetchRecentDocuments();
      return;
    }

    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      const params = {};
      
      if (searchType === 'employee_code') {
        params.employee_code = searchValue;
      } else if (searchType === 'phone') {
        params.phone_number = searchValue;
      } else if (searchType === 'type') {
        params.document_type = searchValue;
      }

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/documents/query`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params
        }
      );
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (docId, format = 'pdf') => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/documents/${docId}/download?format=${format}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `document_${docId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download document');
    }
  };

  const handleEmailSend = async (docId) => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/documents/${docId}/send-email`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      alert('Email sent successfully!');
      fetchRecentDocuments();
    } catch (error) {
      console.error('Email send failed:', error);
      alert('Failed to send email');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      generated: { color: 'blue', icon: '📄', label: 'Generated' },
      email_sent: { color: 'green', icon: '✉️', label: 'Email Sent' },
      digitally_signed: { color: 'purple', icon: '✍️', label: 'Signed' }
    };

    const config = statusConfig[status] || statusConfig.generated;
    return (
      <span className={`status-badge status-badge--${config.color}`}>
        <span className="status-badge__icon">{config.icon}</span>
        {config.label}
      </span>
    );
  };

  return (
    <AppLayout>
    <div className="document-library">
      <div className="document-library__header">
        <h2>📚 Document Library</h2>
        <p>Search and manage all generated HR documents</p>
      </div>

      <Card className="document-library__search">
        <div className="search-controls">
          <select 
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="search-type"
          >
            <option value="employee_code">Employee Code</option>
            <option value="phone">Phone Number</option>
            <option value="type">Document Type</option>
          </select>
          
          <SearchBar
            placeholder={`Search by ${searchType.replace('_', ' ')}...`}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
          />
          
          <Button onClick={handleSearch} disabled={loading}>
            Search
          </Button>
          
          <Button 
            variant="outline" 
            onClick={() => {
              setSearchValue('');
              fetchRecentDocuments();
            }}
          >
            Clear
          </Button>
        </div>
      </Card>

      <div className="document-library__content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <Card className="empty-state">
            <span className="empty-state__icon">📭</span>
            <h3>No documents found</h3>
            <p>Try adjusting your search criteria or generate new documents</p>
          </Card>
        ) : (
          <div className="document-grid">
            {documents.map((doc) => (
              <Card key={doc.id} className="document-card">
                <div className="document-card__header">
                  <div className="document-card__title">
                    <span className="document-card__icon">📄</span>
                    <h3>{doc.document_type}</h3>
                  </div>
                  {getStatusBadge(doc.status)}
                </div>

                <div className="document-card__details">
                  <div className="detail-row">
                    <span className="detail-label">Recipient:</span>
                    <span className="detail-value">{doc.recipient_name}</span>
                  </div>
                  {doc.employee_code && (
                    <div className="detail-row">
                      <span className="detail-label">Employee Code:</span>
                      <span className="detail-value">{doc.employee_code}</span>
                    </div>
                  )}
                  <div className="detail-row">
                    <span className="detail-label">Generated:</span>
                    <span className="detail-value">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : new Date().toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="document-card__actions">
                  <Button 
                    variant="primary" 
                    size="small"
                    onClick={() => handleDownload(doc.id, 'pdf')}
                  >
                    📥 PDF
                  </Button>
                  <Button 
                    variant="outline" 
                    size="small"
                    onClick={() => handleDownload(doc.id, 'docx')}
                  >
                    📥 DOCX
                  </Button>
                  {doc.status !== 'email_sent' && (
                    <Button 
                      variant="outline" 
                      size="small"
                      onClick={() => handleEmailSend(doc.id)}
                    >
                      ✉️ Email
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
    </AppLayout>
  );
};

export default DocumentLibrary;
