import { useNavigate } from 'react-router-dom';
import './style.scss';
import Card from '../../../components/atoms/Card';
import Button from '../../../components/atoms/Button';

const DocumentsDashboard = () => {
  const navigate = useNavigate();

  const features = [
    {
      id: 'generate',
      icon: '✨',
      title: 'AI Document Generator',
      description: 'Chat with AI to generate professional HR documents instantly',
      action: 'Start Chat',
      path: '/documents/generate',
      color: '#FFCC00'
    },
    {
      id: 'agent',
      icon: '🤖',
      title: 'Document Agent (Legacy)',
      description: 'Use the traditional agent flow to generate HR letters',
      action: 'Start Agent',
      path: '/documents/agent',
      color: '#6366f1'
    },
    {
      id: 'library',
      icon: '📚',
      title: 'Document Library',
      description: 'Browse, search and download all generated documents',
      action: 'View Library',
      path: '/documents/library',
      color: '#D40511'
    },
    {
      id: 'templates',
      icon: '📋',
      title: 'Template Manager',
      description: 'Manage and customize HR letter templates',
      action: 'Manage Templates',
      path: '/documents/templates',
      color: '#3b82f6'
    }
  ];

  return (
    <div className="documents-dashboard">
      <div className="documents-dashboard__header">
        <h1>📝 Document Automation</h1>
        <p>Generate, manage, and distribute HR documents with DHL branding</p>
      </div>

      <div className="documents-dashboard__grid">
        {features.map((feature) => (
          <Card key={feature.id} className="feature-card">
            <div 
              className="feature-card__icon"
              style={{ background: `${feature.color}15` }}
            >
              <span style={{ fontSize: '3rem' }}>{feature.icon}</span>
            </div>
            <h2 className="feature-card__title">{feature.title}</h2>
            <p className="feature-card__description">{feature.description}</p>
            <Button 
              variant="primary"
              onClick={() => navigate(feature.path)}
              style={{ 
                background: feature.color,
                borderColor: feature.color 
              }}
            >
              {feature.action}
            </Button>
          </Card>
        ))}
      </div>

      <Card className="documents-dashboard__info">
        <div className="info-section">
          <h3>🎨 DHL Branding</h3>
          <p>All documents are automatically branded with DHL colors and logo</p>
          <div className="color-palette">
            <div className="color-swatch" style={{ background: '#FFCC00' }}>
              <span>DHL Yellow</span>
            </div>
            <div className="color-swatch" style={{ background: '#D40511', color: 'white' }}>
              <span>DHL Red</span>
            </div>
          </div>
        </div>

        <div className="info-section">
          <h3>🔐 Security & Privacy</h3>
          <ul>
            <li>All PII data is encrypted at rest</li>
            <li>Documents stored with hashed identifiers</li>
            <li>Role-based access control (HR/Admin only)</li>
            <li>Secure email delivery with encryption</li>
          </ul>
        </div>

        <div className="info-section">
          <h3>📦 Supported Document Types</h3>
          <div className="document-types">
            <span className="doc-type">Offer Letter</span>
            <span className="doc-type">Experience Letter</span>
            <span className="doc-type">Relieving Letter</span>
            <span className="doc-type">Appointment Letter</span>
            <span className="doc-type">Promotion Letter</span>
            <span className="doc-type">Increment Letter</span>
            <span className="doc-type">Confirmation Letter</span>
            <span className="doc-type">Transfer Letter</span>
            <span className="doc-type">Warning Letter</span>
            <span className="doc-type">Internship Offer</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default DocumentsDashboard;
