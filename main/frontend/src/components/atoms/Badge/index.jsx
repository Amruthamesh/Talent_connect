import React from 'react'
import './style.scss'

export default function Badge({ 
  children, 
  variant = 'default',
  size = 'medium',
  rounded = false,
  className = ''
}) {
  const classNames = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    rounded && 'badge--rounded',
    className
  ].filter(Boolean).join(' ')

  return (
    <span className={classNames}>
      {children}
    </span>
  )
}
