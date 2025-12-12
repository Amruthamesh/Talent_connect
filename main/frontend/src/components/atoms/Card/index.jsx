import React from 'react'
import './style.scss'

export default function Card({ 
  children, 
  title,
  subtitle,
  header,
  footer,
  hoverable = false,
  bordered = true,
  padding = 'medium',
  className = '',
  onClick
}) {
  const classNames = [
    'card',
    hoverable && 'card--hoverable',
    bordered && 'card--bordered',
    `card--padding-${padding}`,
    onClick && 'card--clickable',
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={classNames} onClick={onClick}>
      {(title || subtitle || header) && (
        <div className="card__header">
          {header || (
            <>
              {title && <h3 className="card__title">{title}</h3>}
              {subtitle && <p className="card__subtitle">{subtitle}</p>}
            </>
          )}
        </div>
      )}
      
      <div className="card__body">
        {children}
      </div>
      
      {footer && (
        <div className="card__footer">
          {footer}
        </div>
      )}
    </div>
  )
}
