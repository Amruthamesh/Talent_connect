import React from 'react'
import Input from '@components/atoms/Input'
import './style.scss'

export default function FormInput({ 
  label, 
  error, 
  required,
  icon,
  fullWidth = true,
  ...props 
}) {
  return (
    <div className="form-input">
      <Input
        label={label}
        error={error}
        required={required}
        icon={icon}
        fullWidth={fullWidth}
        {...props}
      />
    </div>
  )
}
