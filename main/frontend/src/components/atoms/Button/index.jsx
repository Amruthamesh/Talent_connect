import React from 'react'
import './style.scss'

export default function Button({ 
  children, 
  variant = 'primary', 
  size = 'medium',
  fullWidth = false,
  disabled = false,
  loading = false,
  icon = null,
  onClick,
  type = 'button',
  className = '',
  ...props 
}) {
  const classNames = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    fullWidth && 'btn--full-width',
    loading && 'btn--loading',
    disabled && 'btn--disabled',
    className
  ].filter(Boolean).join(' ')

  return (
    <button
      type={type}
      className={classNames}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="btn__spinner"></span>}
      {!loading && icon && <span className="btn__icon">{icon}</span>}
      <span className="btn__text">{children}</span>
    </button>
  )
}
