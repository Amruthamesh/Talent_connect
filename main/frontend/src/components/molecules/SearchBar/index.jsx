import React from 'react'
import { FiSearch } from 'react-icons/fi'
import Input from '@components/atoms/Input'
import './style.scss'

export default function SearchBar({ 
  placeholder = 'Search...', 
  value,
  onChange,
  onSearch,
  fullWidth = true,
  className = ''
}) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && onSearch) {
      onSearch(value)
    }
  }

  return (
    <div className={`search-bar ${className}`}>
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onKeyPress={handleKeyPress}
        icon={<FiSearch />}
        fullWidth={fullWidth}
      />
    </div>
  )
}
