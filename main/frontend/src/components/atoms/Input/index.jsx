import React, { forwardRef } from 'react'
import './style.scss'

const Input = forwardRef(({ 
  type = 'text',
  label,
  error,
  helperText,
  fullWidth = false,
  icon = null,
  disabled = false,
  className = '',
  ...props 
}, ref) => {
  const classNames = [
    'input-wrapper',
    fullWidth && 'input-wrapper--full-width',
    error && 'input-wrapper--error',
    disabled && 'input-wrapper--disabled',
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={classNames}>
      {label && (
        <label className="input__label">
          {label}
          {props.required && <span className="input__required">*</span>}
        </label>
      )}
      
      <div className="input__field-wrapper">
        {icon && <span className="input__icon">{icon}</span>}
        <input
          ref={ref}
          type={type}
          className="input__field"
          disabled={disabled}
          {...props}
        />
      </div>
      
      {(error || helperText) && (
        <span className={`input__helper ${error ? 'input__helper--error' : ''}`}>
          {error || helperText}
        </span>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input
