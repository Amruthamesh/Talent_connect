import React from 'react'
import AppLayout from '@layouts/AppLayout'
import Card from '@components/atoms/Card'
import Badge from '@components/atoms/Badge'
import { FiBriefcase, FiFileText, FiVideo, FiTrendingUp } from 'react-icons/fi'
import content from './content.json'
import './style.scss'

export default function Dashboard() {
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const stats = [
    { 
      icon: <FiBriefcase />, 
      label: 'Active Jobs', 
      value: '12', 
      trend: '+3 this week',
      color: '#2563eb' 
    },
    { 
      icon: <FiFileText />, 
      label: 'Documents Generated', 
      value: '48', 
      trend: '+12 this month',
      color: '#7c3aed' 
    },
    { 
      icon: <FiVideo />, 
      label: 'Interviews Scheduled', 
      value: '8', 
      trend: '3 today',
      color: '#10b981' 
    },
    { 
      icon: <FiTrendingUp />, 
      label: 'Candidates Matched', 
      value: '156', 
      trend: '+24 this week',
      color: '#f59e0b' 
    },
  ]

  const recentActivity = [
    { action: 'Job Description created', detail: 'Senior AI Engineer', time: '2 hours ago' },
    { action: 'Interview scheduled', detail: 'John Doe - Product Manager', time: '4 hours ago' },
    { action: 'Offer letter generated', detail: 'Jane Smith - UX Designer', time: '1 day ago' },
    { action: 'Profile matched', detail: '5 candidates for Backend Developer', time: '1 day ago' },
  ]

  return (
    <AppLayout>
      <div className="dashboard">
        <div className="dashboard__header">
          <div>
            <h1>{content.title}</h1>
            <p>{content.subtitle.replace('{role}', user.label || 'User')}</p>
          </div>
          <Badge variant="success" size="medium">
            {user.role || 'Active'}
          </Badge>
        </div>

        <div className="dashboard__stats">
          {stats.map((stat, index) => (
            <Card key={index} hoverable className="dashboard__stat-card">
              <div className="dashboard__stat">
                <div 
                  className="dashboard__stat-icon" 
                  style={{ backgroundColor: `${stat.color}15`, color: stat.color }}
                >
                  {stat.icon}
                </div>
                <div className="dashboard__stat-content">
                  <span className="dashboard__stat-label">{stat.label}</span>
                  <h3 className="dashboard__stat-value">{stat.value}</h3>
                  <span className="dashboard__stat-trend">{stat.trend}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="dashboard__grid">
          <Card 
            title="Recent Activity" 
            subtitle="Latest actions in your workspace"
            padding="none"
          >
            <div className="dashboard__activity">
              {recentActivity.map((activity, index) => (
                <div key={index} className="dashboard__activity-item">
                  <div className="dashboard__activity-content">
                    <strong>{activity.action}</strong>
                    <p>{activity.detail}</p>
                  </div>
                  <span className="dashboard__activity-time">{activity.time}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card 
            title="Quick Actions" 
            subtitle="Get started with common tasks"
            padding="medium"
          >
            <div className="dashboard__quick-actions">
              <button className="dashboard__action-btn">
                <FiBriefcase />
                <span>Generate Job Description</span>
              </button>
              <button className="dashboard__action-btn">
                <FiFileText />
                <span>Create Document</span>
              </button>
              <button className="dashboard__action-btn">
                <FiVideo />
                <span>Schedule Interview</span>
              </button>
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
