import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { FiChevronDown } from 'react-icons/fi'
import Button from '@components/atoms/Button'
import dhlLogo from '@assets/logo/dhl-logo.svg'
import { filterMenuByRole, getRoleDisplayName } from '@utils/permissions'
import './style.scss'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [activeMenu, setActiveMenu] = useState(null)
  const navbarRef = useRef(null)
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (navbarRef.current && !navbarRef.current.contains(event.target)) {
        setActiveMenu(null)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])
  
  const handleLogout = () => {
    // Add logout logic here
    localStorage.removeItem('user')
    navigate('/login')
  }

  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const allMenuItems = [
    {
      id: 'jobs',
      label: 'Jobs',
      submenus: [
        {
          title: 'Job Description Generator',
          description: 'AI-powered job description creation',
          link: '/jobs/generator',
          icon: '✨'
        },
        {
          title: 'Profile Matcher',
          description: 'Match candidates to job requirements',
          link: '/jobs/matcher'
        }
      ]
    },
    {
      id: 'documents',
      label: 'Documents',
      submenus: [
        {
          title: 'Document Agent',
          description: 'Generate HR letters with guided flow',
          link: '/documents/agent',
          icon: '✨'
        },
        {
          title: 'Document Library',
          description: 'View and download generated documents',
          link: '/documents/library'
        }
      ]
    },
    {
      id: 'interviews',
      label: 'Interviews',
      submenus: [
        {
          title: 'Interview Dashboard',
          description: 'Manage all interviews',
          link: '/interviews/dashboard'
        },
        {
          title: 'Schedule Interview',
          description: 'Create new interview sessions',
          link: '/interviews/schedule'
        }
      ]
    }
  ]

  // Filter menu items based on user role
  const menuItems = filterMenuByRole(user, allMenuItems)

  const toggleMenu = (menuId) => {
    setActiveMenu(activeMenu === menuId ? null : menuId)
  }
  
  // Check if current path matches a menu or submenu
  const isMenuActive = (menu) => {
    return menu.submenus.some(submenu => location.pathname === submenu.link)
  }

  return (
    <nav className="navbar" ref={navbarRef}>
      <div className="navbar__top">
        <div className="navbar__container">
          <Link to="/dashboard" className="navbar__brand">
            <img src={dhlLogo} alt="DHL Logo" className="navbar__logo" />
          </Link>
          
          <div className="navbar__actions">
            <div className="navbar__user-info">
              <span className="navbar__user-role">{getRoleDisplayName(user.role)}</span>
              <span className="navbar__user-name">{user.label || 'User'}</span>
            </div>
            
            <Button 
              variant="ghost" 
              size="small"
              onClick={handleLogout}
              className="navbar__logout-btn"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="navbar__secondary">
        <div className="navbar__container">
          <div className="navbar__menu">
            <Link 
              to="/dashboard" 
              className={`navbar__menu-item ${location.pathname === '/dashboard' ? 'navbar__menu-item--active' : ''}`}
            >
              Dashboard
            </Link>
            {menuItems.map((menu) => (
              <div key={menu.id} className="navbar__menu-item-wrapper">
                <button 
                  className={`navbar__menu-item ${
                    activeMenu === menu.id || isMenuActive(menu) 
                      ? 'navbar__menu-item--active' 
                      : ''
                  }`}
                  onClick={() => toggleMenu(menu.id)}
                >
                  {menu.label}
                  <FiChevronDown className="navbar__menu-icon" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {activeMenu && (
        <div className="navbar__submenu">
          <div className="navbar__submenu-inner">
            <div className="navbar__submenu-container">
              {menuItems.find(m => m.id === activeMenu)?.submenus.map((submenu, index) => (
                <Link 
                  key={index}
                  to={submenu.link}
                  className={`navbar__submenu-item ${location.pathname === submenu.link ? 'navbar__submenu-item--active' : ''}`}
                  onClick={() => setActiveMenu(null)}
                >
                  <h4>{submenu.title}</h4>
                  <p>{submenu.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
