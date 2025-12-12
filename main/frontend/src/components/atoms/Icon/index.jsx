import React from 'react'
import './style.scss'

export default function Icon({ name, size = 'medium', color, className = '' }) {
  const classNames = [
    'icon',
    `icon--${size}`,
    className
  ].filter(Boolean).join(' ')

  const style = color ? { color } : {}

  return (
    <span className={classNames} style={style}>
      {name}
    </span>
  )
}
