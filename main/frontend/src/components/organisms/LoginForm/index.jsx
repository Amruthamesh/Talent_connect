import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi'
import Button from '@components/atoms/Button'
import FormInput from '@components/molecules/FormInput'
import toast from 'react-hot-toast'
import api from '@utils/api'
import './style.scss'

const demoAccounts = [
  {
    username: 'hr@talent.com',
    password: 'hr123',
    label: 'HR Manager Demo',
    role: 'hr',
    description: 'Access HR Letters, Job Mapping, and Interview management'
  },
  {
    username: 'manager@talent.com',
    password: 'mgr123',
    label: 'Hiring Manager Demo',
    role: 'hiring_manager',
    description: 'Generate Job Descriptions and manage interviews'
  },
  {
    username: 'recruiter@talent.com',
    password: 'rec123',
    label: 'Recruiter Demo',
    role: 'recruiter',
    description: 'Find and match candidates to job positions'
  }
]

export default function LoginForm() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    // Clear error for this field
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: '' })
    }
  }

  const validate = () => {
    const newErrors = {}
    
    if (!formData.username) {
      newErrors.username = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.username)) {
      newErrors.username = 'Email is invalid'
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validate()) return
    
    setLoading(true)
    
    try {
      // Call real backend API with OAuth2 form data
      const response = await api.postForm('/auth/login', {
        username: formData.username,
        password: formData.password
      })
      
      // Store user data and token (response has nested user object)
      const userData = {
        username: response.user.email,
        email: response.user.email,
        role: response.user.role,
        label: response.user.full_name,
        token: response.access_token
      }
      
      localStorage.setItem('user', JSON.stringify(userData))
      toast.success(`Welcome, ${response.user.full_name}!`)
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.message || 'Invalid credentials')
      setErrors({ password: 'Invalid email or password' })
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async (account) => {
    setLoading(true)
    
    try {
      // Call backend demo-login endpoint
      const response = await api.post('/auth/demo-login', {
        email: account.username
      })
      
      // Store user data and token (response has nested user object)
      const userData = {
        username: response.user.email,
        email: response.user.email,
        role: response.user.role,
        label: response.user.full_name,
        token: response.access_token
      }
      
      localStorage.setItem('user', JSON.stringify(userData))
      toast.success(`Welcome, ${response.user.full_name}!`)
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.message || 'Demo login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-form">
      {!showDemoAccounts ? (
        <>
          <div className="login-form__header">
            <h2>Welcome Back</h2>
            <p>Sign in to access your Talent Connect portal</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form__form">
            <FormInput
              type="email"
              name="username"
              label="Email Address"
              placeholder="Enter your email"
              value={formData.username}
              onChange={handleChange}
              error={errors.username}
              icon={<FiMail />}
              required
            />

            <div className="login-form__password">
              <FormInput
                type={showPassword ? 'text' : 'password'}
                name="password"
                label="Password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                error={errors.password}
                icon={<FiLock />}
                required
              />
              <button
                type="button"
                className="login-form__password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              fullWidth 
              size="large"
              loading={loading}
            >
              Sign In
            </Button>
          </form>

          <div className="login-form__divider">
            <span>Or</span>
          </div>

          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={() => setShowDemoAccounts(true)}
          >
            Use Demo Accounts
          </Button>
        </>
      ) : (
        <>
          <div className="login-form__header">
            <h2>Demo Accounts</h2>
            <p>Select a demo account to explore the platform</p>
          </div>

          <div className="login-form__demo-accounts">
            {demoAccounts.map((account) => (
              <button
                key={account.username}
                type="button"
                className="login-form__demo-account"
                onClick={() => handleDemoLogin(account)}
                disabled={loading}
              >
                <strong>{account.label}</strong>
                <small>{account.description}</small>
              </button>
            ))}
          </div>

          <Button
            type="button"
            variant="ghost"
            fullWidth
            onClick={() => setShowDemoAccounts(false)}
          >
            Back to Login
          </Button>
        </>
      )}
    </div>
  )
}
