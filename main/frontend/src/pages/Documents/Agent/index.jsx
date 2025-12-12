import { React, useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AppLayout from '@layouts/AppLayout';
import './style.scss';
import Button from '../../../components/atoms/Button';
import Card from '../../../components/atoms/Card';
import TypingIndicator from '../../../components/atoms/TypingIndicator';
import DocumentBuilderChat from '../../../components/organisms/DocumentBuilderChat';
import { FiArrowLeft, FiDownload, FiUpload } from 'react-icons/fi';
import { documentsAPI } from '../../../utils/api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const DocumentAgent = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [hasFetchedTemplates, setHasFetchedTemplates] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentStep, setCurrentStep] = useState('greeting');
  const [loading, setLoading] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedTemplateName, setSelectedTemplateName] = useState('');
  const [requiredFields, setRequiredFields] = useState([]);
  const [optionalFields, setOptionalFields] = useState([]);
  const [inputMethod, setInputMethod] = useState(null); // 'manual_entry', 'upload_csv', 'download_template'
  const [authInfo, setAuthInfo] = useState({ authenticated: false, role: null });
  const [previewItem, setPreviewItem] = useState(null);
  const [editHtml, setEditHtml] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startConversation();
  }, []);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const authenticated = Boolean(user?.token);
    const role = user?.role || user?.user?.role || null;
    setAuthInfo({ authenticated, role });
  }, []);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

  const startConversation = async () => {
    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      
      const response = await axios.post(
        `${API_BASE}/documents/agent/start`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setSessionId(response.data.session_id);
      setCurrentStep(response.data.next_step);
      
      const initialTemplates = response.data.options || response.data.templates || [];
      setTemplates(initialTemplates);
      setMessages([
        {
          type: 'bot',
          content: response.data.message,
          templates: initialTemplates,
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error('Failed to start conversation:', error);
      console.error('Error details:', error.response?.data || error.message);
      setMessages([
        {
          type: 'bot',
          content: 'Sorry, I encountered an error starting the conversation. Please try again.',
          timestamp: new Date()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = async (templateId) => {
    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      
      // Add user message
      const template = messages[0].templates.find(t => t.id === templateId);
      setMessages(prev => [...prev, {
        type: 'user',
        content: template?.name,
        timestamp: new Date()
      }]);

      const response = await axios.post(
        `${API_BASE}/documents/agent/select-template`,
        {
          session_id: sessionId,
          template_id: templateId
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setCurrentStep(response.data.next_step);
      setSelectedTemplate(templateId);
      setSelectedTemplateName(template?.name || '');
      
      setMessages(prev => [...prev, {
        type: 'bot',
        content: response.data.message,
        required_fields: response.data.required_fields,
        optional_fields: response.data.optional_fields,
        options: response.data.options,
        timestamp: new Date()
      }]);

      // Store fields for tracking
      if (response.data.required_fields) {
        setRequiredFields(response.data.required_fields);
      }
      if (response.data.optional_fields) {
        setOptionalFields(response.data.optional_fields);
      }
    } catch (error) {
      console.error('Failed to select template:', error);
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputMethodSelect = async (method) => {
    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      
      const methodLabels = {
        'manual_entry': 'Fill fields manually',
        'upload_csv': 'Upload CSV file',
        'download_template': 'Download CSV template'
      };
      
      // Add user message
      setMessages(prev => [...prev, {
        type: 'user',
        content: methodLabels[method] || method,
        timestamp: new Date()
      }]);

      // Set input method
      setInputMethod(method);

      const payload = {
        session_id: sessionId,
        method: method
      };
      
      console.log('Sending input-method request:', payload);

      const response = await axios.post(
        `${API_BASE}/documents/agent/input-method`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      console.log('Input-method response:', response.data);

      setCurrentStep(response.data.current_step);
      
      // For manual entry, don't add messages - DocumentBuilderChat will handle it
      if (method !== 'manual_entry') {
        setMessages(prev => [...prev, {
          type: 'bot',
          content: response.data.message,
          csv_download_url: response.data.csv_download_url,
          timestamp: new Date()
        }]);
      }

      // Auto-download template when requested
      if (method === 'download_template' && response.data.csv_download_url) {
        try {
          const downloadUrl = `${API_BASE.replace('/api/v1','')}${response.data.csv_download_url}`;
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.setAttribute('download', 'document_template.csv');
          document.body.appendChild(link);
          link.click();
          link.parentNode.removeChild(link);
        } catch (e) {
          console.error('Failed to auto-download CSV template:', e);
        }
      }

      // For upload_csv, immediately prompt file picker for smoother UX
      if (method === 'upload_csv') {
        setTimeout(() => {
          const inputEl = document.getElementById('csv-upload');
          if (inputEl) inputEl.click();
        }, 300);
      }
    } catch (error) {
      console.error('Failed to select input method:', error);
      console.error('Error response:', error.response?.data);
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleManualEntryComplete = async (documentIds) => {
    // Navigate to library to see the generated document
    if (documentIds && documentIds.length > 0) {
      navigate(`/documents/library`);
    }
  };

  const handleCsvUpload = async () => {
    if (!csvFile) return;

    try {
      setLoading(true);
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      
      // Add user message
      setMessages(prev => [...prev, {
        type: 'user',
        content: `Uploading ${csvFile.name}...`,
        timestamp: new Date()
      }]);

      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('session_id', sessionId);

      const response = await axios.post(
        `${API_BASE}/documents/agent/upload-csv`,
        formData,
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setCurrentStep('completed');
      
      setMessages(prev => [...prev, {
        type: 'bot',
        content: response.data.message,
        generated_count: response.data.generated_count,
        document_ids: response.data.document_ids,
        preview_data: response.data.preview_data,
        template_name: selectedTemplateName,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Failed to upload CSV:', error);
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Failed to process CSV file. Please check the format and try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsvTemplate = async () => {
    if (!selectedTemplate) return;
    try {
      const { url, filename } = await documentsAPI.downloadCsvTemplate(selectedTemplate);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename || `${selectedTemplateName || 'document'}_template.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download CSV template:', e);
      // Fallback: generate CSV client-side using known fields
      try {
        const headers = [
          ...requiredFields,
          ...(optionalFields || [])
        ];
        if (!headers || headers.length === 0) {
          throw new Error('No fields available to construct CSV');
        }
        const exampleRow = headers.map(h => {
          const m = h.toLowerCase();
          const examples = {
            employee_name: 'John Michael Doe',
            candidate_name: 'Jane Smith',
            designation: 'Senior Software Engineer',
            department: 'Engineering',
            joining_date: '2024-12-01',
            offer_acceptance_date: '2024-11-30',
            confirmation_date: '2024-06-15',
            last_working_date: '2024-10-31',
            effective_date: '2025-01-01',
            salary: '85000',
            new_salary: '95000',
            increment_amount: '10000',
            location: 'Chennai',
            current_location: 'Bengaluru',
            new_location: 'Chennai',
            transfer_date: '2025-01-15',
            reporting_manager: 'Alice Johnson',
            phone_number: '+91-80-12345678',
            email: 'john.doe@example.com',
            company_name: 'DHL IT SERVICES',
            company_address: 'CHENNAI ONE IT SEZ',
            contact_info: '+91-80-12345678 | hr@company.com',
            reason: 'Business requirements',
            reason_for_termination: 'Policy violation',
            termination_date: '2024-12-15',
            probation_period: '6 months',
            probation_feedback: 'Meets expectations',
            employee_code: 'EMP-1024',
            skills: 'Python; React; SQL',
            achievements: 'Top Performer 2024',
            responsibilities: 'Backend development; API design',
            issue_date: '2025-11-27',
            warning_type: 'Performance Warning',
            signatory_name: 'Robert Williams',
            signatory_designation: 'HR Manager',
            signatory_signature: '<base64 or data URL of signature image>',
            signatory_signature_url: 'https://example.com/assets/signatures/john-smith.png'
          };
          return examples[m] ?? `<${h}>`;
        });
        const csv = [headers.join(','), exampleRow.map(v => {
          // Quote values containing commas
          return /,/.test(v) ? `"${v}"` : v;
        }).join(',')].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.setAttribute('download', `${selectedTemplateName || 'document'}_template.csv`);
        document.body.appendChild(a);
        a.click();
        a.parentNode.removeChild(a);
        window.URL.revokeObjectURL(url);
        // Notify user of fallback
        setMessages(prev => [...prev, {
          type: 'bot',
          content: 'Could not fetch from server; downloaded a client-generated CSV template based on the required fields.',
          timestamp: new Date()
        }]);
      } catch (fallbackErr) {
        alert('Failed to download CSV template. Please ensure you are logged in as HR/Admin.');
      }
    }
  };

  const downloadBulkDocuments = async (documentIds, templateName) => {
    // Deprecated bulk ZIP download in favor of per-document downloads
    alert('Use individual Download buttons below each preview to download single files.');
  };

  const downloadSingleDocument = async (documentId, suggestedName, employeeName) => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const token = user.token;
      const res = await axios.get(
        `${API_BASE}/documents/${documentId}/download?format=pdf`,
        { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' }
      );
      const blob = res.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const today = new Date().toISOString().slice(0,10);
      const safeName = (employeeName || 'document').replace(/\s+/g, '_');
      const safeType = (suggestedName || 'letter').replace(/\s+/g, '_');
      a.download = `${safeName}_${safeType}_${today}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.parentNode.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Single document download failed', e);
      alert('Failed to download document');
    }
  };

  const downloadEditedPreviewAsPdf = async (employeeName, suggestedName) => {
    try {
      const today = new Date().toISOString().slice(0,10);
      const safeName = (employeeName || 'document').replace(/\s+/g, '_');
      const safeType = (suggestedName || 'letter').replace(/\s+/g, '_');
      const filename = `${safeName}_${safeType}_${today}.pdf`;
      const node = document.getElementById('preview-edit-container');
      if (!node) throw new Error('Preview container not found');
      const canvas = await html2canvas(node, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'pt', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth;
      const imgHeight = canvas.height * (imgWidth / canvas.width);
      let position = 0;
      let heightLeft = imgHeight;
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
      while (heightLeft > 0) {
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, -heightLeft, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }
      pdf.save(filename);
    } catch (e) {
      console.error('Failed to download edited preview', e);
      alert('Failed to download edited preview');
    }
  };

  const handleBackToStart = () => {
    setMessages([]);
    setSessionId(null);
    setCurrentStep('greeting');
    setSelectedTemplate(null);
    setSelectedTemplateName('');
    setRequiredFields([]);
    setOptionalFields([]);
    setInputMethod(null);
    setCsvFile(null);
    startConversation();
  };

  // Fetch templates if not present in initial message (fallback)
  useEffect(() => {
    if (
      messages.length > 0 &&
      (!messages[0].templates || messages[0].templates.length === 0) &&
      !hasFetchedTemplates
    ) {
      const fetchTemplates = async () => {
        try {
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          const response = await documentsAPI.getTemplates();
          setTemplates(response.data || []);
          setMessages(prev => {
            const updated = [...prev];
            if (updated[0]) updated[0].templates = response.data || [];
            return updated;
          });
        } catch (err) {
          // fallback: do nothing
        } finally {
          setHasFetchedTemplates(true);
        }
      };
      fetchTemplates();
    }
  }, [messages, hasFetchedTemplates]);

  return (
    <AppLayout>
      <div className="document-agent">
        <div className="document-agent__header">
          <div>
            <h2>📄 Document Generator Agent</h2>
            <p>Generate HR letters with AI assistance</p>
          </div>
          <div className="auth-status" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>
              {authInfo.authenticated ? (
                <>🔐 Authenticated {authInfo.role ? `(role: ${authInfo.role})` : ''}</>
              ) : (
                <>⚠️ Not authenticated</>
              )}
            </span>
            {!authInfo.authenticated && (
              <Button variant="primary" onClick={() => navigate('/login')}>
                Login
              </Button>
            )}
          </div>
          {currentStep !== 'greeting' && (
            <Button variant="secondary" onClick={handleBackToStart}>
              <FiArrowLeft /> Start Over
            </Button>
          )}
        </div>

        {/* Show DocumentBuilderChat for manual entry */}
        {inputMethod === 'manual_entry' && (
          <DocumentBuilderChat
            sessionId={sessionId}
            templateName={selectedTemplateName}
            requiredFields={requiredFields}
            optionalFields={optionalFields}
            onComplete={handleManualEntryComplete}
          />
        )}

        {/* Show regular chat for template selection and other flows */}
        {inputMethod !== 'manual_entry' && (
          <Card className="document-agent__chat">
            <div className="messages">
              {messages.length === 0 && loading ? (
                <div className="message message--bot">
                  <div className="message__avatar">🤖</div>
                  <div className="message__content">
                    <div className="message__bubble">
                      <TypingIndicator />
                    </div>
                  </div>
                </div>
              ) : (
                <>
                {messages.map((msg, idx) => (
                  <>
                <div key={idx} className={`message message--${msg.type}`}>
                  <div className="message__avatar">
                    {msg.type === 'bot' ? '🤖' : '👤'}
                  </div>
                  <div className="message__content">
                    <div className="message__bubble">
                      {msg.content && (
                        <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }} />
                      )}
                      
                      {/* Template Cards - only show if this message explicitly has templates */}
                      {msg.templates && msg.templates.length > 0 && (
                        <div className="template-grid">
                          {msg.templates.map(template => (
                            <div
                              key={template.id}
                              className="template-card"
                              onClick={() => handleTemplateSelect(template.id)}
                            >
                              <div className="template-card__icon">📋</div>
                              <div className="template-card__name">{template.name}</div>
                              {template.description && (
                                <div className="template-card__description">{template.description}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Required/Optional Fields Display */}
                      {msg.required_fields && (
                        <div className="fields-display">
                          <div className="field-group">
                            <strong>Required fields:</strong>
                            <ul>
                              {msg.required_fields.map(field => (
                                <li key={field}>{field.replace('_', ' ')}</li>
                              ))}
                            </ul>
                          </div>
                          {msg.optional_fields && msg.optional_fields.length > 0 && (
                            <div className="field-group">
                              <strong>Optional fields:</strong>
                              <ul>
                                {msg.optional_fields.map(field => (
                                  <li key={field}>{field.replace('_', ' ')}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Input Method Options */}
                      {msg.options && msg.options.length > 0 && (
                        <div className="options-grid">
                          {msg.options.filter(option => option.id !== 'download_template').map((option, optIdx) => (
                            <Button
                              key={optIdx}
                              variant="secondary"
                              onClick={() => handleInputMethodSelect(option.id)}
                            >
                              {option.id === 'manual_entry' && '✏️ '}
                              {option.id === 'upload_csv' && '📤 '}
                              {option.label}
                            </Button>
                          ))}
                        </div>
                      )}
                      
                      {/* CSV Upload */}
                      {currentStep === 'csv_upload' && idx === messages.length - 1 && (
                        <div className="csv-upload-section">
                          <input
                            type="file"
                            accept=".csv"
                            onChange={(e) => setCsvFile(e.target.files[0])}
                            id="csv-upload"
                            className="upload-input"
                          />
                          <label htmlFor="csv-upload" className="upload-label">
                            {csvFile ? (
                              <>
                                <span className="icon">📎</span>
                                {csvFile.name}
                              </>
                            ) : (
                              <>
                                <FiUpload className="icon" />
                                Click to select CSV file
                              </>
                            )}
                          </label>
                          {csvFile && (
                            <Button variant="primary" onClick={handleCsvUpload}>
                              Upload and Generate
                            </Button>
                          )}
                        </div>
                      )}
                      
                      {/* Generated Documents: Preview list with per-item download */}
                      {msg.preview_data && msg.preview_data.length > 0 && (
                        <div className="previews-section">
                          <p>✅ Generated <strong>{msg.preview_data.length}</strong> {msg.template_name || 'documents'}</p>
                          <div className="preview-list">
                            {msg.preview_data.map(item => (
                              <div key={item.id} className="preview-item">
                                <div className="preview-meta">
                                  <strong>{item.employee_name}</strong> — Row {item.row_number}
                                </div>
                                <div className="preview-actions" style={{ display: 'flex', gap: '8px' }}>
                                  <Button variant="secondary" onClick={() => setPreviewItem(item)}>Preview</Button>
                                  <Button variant="primary" onClick={() => downloadSingleDocument(item.id, msg.template_name, item.employee_name)}>
                                    <FiDownload /> Download
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                {/* Add download template bubble after input method options - only for the last message */}
                {msg.options && msg.options.some(option => option.id === 'download_template') && idx === messages.length - 1 && (
                  <div className="message message--bot" style={{ marginTop: '0.5rem' }}>
                    <div className="message__avatar">🤖</div>
                    <div className="message__content">
                      <div className="message__bubble">
                        You can{' '}
                        <span
                          onClick={handleDownloadCsvTemplate}
                          style={{ color: '#FFCC00', textDecoration: 'underline', cursor: 'pointer', fontWeight: '500', display: 'inline' }}
                        >
                          download the CSV template
                        </span>
                        {' '}for this letter and then use Upload CSV, or choose Fill fields manually.
                      </div>
                    </div>
                  </div>
                )}
                </>
              ))}
              </>
              )}
              {loading && messages.length > 0 && (
                <div className="message message--bot">
                  <div className="message__avatar">🤖</div>
                  <div className="message__content">
                    <div className="message__bubble">
                      <TypingIndicator />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </Card>
        )}
      </div>
      {/* Simple Preview Modal */}
      {previewItem && (
        <div className="modal-overlay" onClick={() => setPreviewItem(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>Preview: {previewItem.employee_name}</strong>
              <Button variant="secondary" onClick={() => setPreviewItem(null)}>Close</Button>
            </div>
            <div className="modal-body" style={{ maxHeight: '60vh', overflow: 'auto' }}>
              <div
                id="preview-edit-container"
                dangerouslySetInnerHTML={{ __html: (editHtml || previewItem.preview_masked_html || previewItem.preview_html) }}
              />
              <div className="edit-controls" style={{ marginTop: '12px' }}>
                <label style={{ display: 'block', marginBottom: '6px' }}>Edit HTML (optional):</label>
                <textarea
                  value={editHtml}
                  onChange={(e) => setEditHtml(e.target.value)}
                  placeholder="Paste or edit HTML to customize before download"
                  style={{ width: '100%', minHeight: '120px' }}
                />
                <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                  <Button variant="primary" onClick={() => downloadEditedPreviewAsPdf(previewItem.employee_name, previewItem.document_type)}>
                    <FiDownload /> Download Edited (PDF)
                  </Button>
                  <Button variant="secondary" onClick={() => setEditHtml('')}>Reset Edits</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default DocumentAgent;
