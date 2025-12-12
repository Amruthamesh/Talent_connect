import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  FiHome, 
  FiBriefcase, 
  FiFileText, 
  FiVideo,
  FiChevronLeft,
  FiChevronRight 
} from 'react-icons/fi'
import './style.scss'

const menuItems = [
  { 
    path: '/dashboard', 
    icon: <FiHome />, 
    label: 'Dashboard',
    roles: ['hr', 'hiring_manager', 'recruiter']
  },
  { 
    path: '/jobs', 
    icon: <FiBriefcase />, 
    label: 'Jobs',
    roles: ['hr', 'hiring_manager', 'recruiter']
  },
  { 
    path: '/documents', 
    icon: <FiFileText />, 
    label: 'Documents',
    roles: ['hr', 'hiring_manager']
  },
  { 
    path: '/interviews', 
    icon: <FiVideo />, 
    label: 'Interviews',
    roles: ['hr', 'hiring_manager']
  },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const filteredMenuItems = menuItems.filter(item => 
    !item.roles || item.roles.includes(user.role)
  )

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      <button 
        className="sidebar__toggle"
        onClick={() => setCollapsed(!collapsed)}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <FiChevronRight /> : <FiChevronLeft />}
      </button>

      <nav className="sidebar__nav">
        {filteredMenuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
            }
          >
            <span className="sidebar__icon">{item.icon}</span>
            {!collapsed && <span className="sidebar__label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
