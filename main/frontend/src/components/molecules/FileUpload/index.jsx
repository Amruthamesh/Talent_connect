import React, { useState } from 'react'
import Button from '@components/atoms/Button'
import { FiUpload, FiFile, FiX } from 'react-icons/fi'
import './style.scss'

export default function FileUpload({ 
  file,
  multiple = false,
  onFileSelect,
  onFilesSelect,
  onFileRemove,
  accept,
  label = 'Upload File',
  disabled = false,
  className = ''
}) {
  const [dragActive, setDragActive] = useState(false)

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files || [])
    if (!selectedFiles.length) return

    if (multiple && onFilesSelect) {
      onFilesSelect(selectedFiles)
      return
    }

    const selectedFile = selectedFiles[0]
    if (selectedFile && onFileSelect) {
      onFileSelect(selectedFile)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (disabled) return
    setDragActive(false)
    const droppedFiles = Array.from(e.dataTransfer?.files || [])
    if (!droppedFiles.length) return

    if (multiple && onFilesSelect) {
      onFilesSelect(droppedFiles)
      return
    }

    const first = droppedFiles[0]
    if (first && onFileSelect) {
      onFileSelect(first)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (disabled) return
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  return (
    <div className={`file-upload ${className}`}>
      {!file ? (
        <label
          className="file-upload__label"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            className="file-upload__input"
            onChange={handleFileChange}
            accept={accept}
            disabled={disabled}
            multiple={multiple}
          />
          <div className={`file-upload__button ${dragActive ? 'file-upload__button--active' : ''}`}>
            <FiUpload />
            <span>{label}</span>
          </div>
        </label>
      ) : (
        <div className="file-upload__preview">
          <FiFile className="file-upload__icon" />
          <span className="file-upload__name">{file.name}</span>
          <button
            type="button"
            className="file-upload__remove"
            onClick={onFileRemove}
            disabled={disabled}
          >
            <FiX />
          </button>
        </div>
      )}
    </div>
  )
}
