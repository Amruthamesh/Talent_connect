import React from 'react'
import Badge from '@components/atoms/Badge'
import './style.scss'

export default function CardHeader({ 
  title, 
  subtitle, 
  badge,
  actions,
  className = ''
}) {
  return (
    <div className={`card-header ${className}`}>
      <div className="card-header__content">
        <div className="card-header__text">
          <h3 className="card-header__title">
            {title}
            {badge && <Badge variant={badge.variant} size="small">{badge.text}</Badge>}
          </h3>
          {subtitle && <p className="card-header__subtitle">{subtitle}</p>}
        </div>
        
        {actions && (
          <div className="card-header__actions">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}
