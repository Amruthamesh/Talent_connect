// Role-Based Access Control (RBAC) Utilities

export const ROLES = {
  HR: 'hr',
  HIRING_MANAGER: 'hiring_manager',
  RECRUITER: 'recruiter'
}

// Permission definitions
export const PERMISSIONS = {
  // Jobs Module
  'jobs.jd.create': [ROLES.HR, ROLES.HIRING_MANAGER],
  'jobs.jd.edit': [ROLES.HR, ROLES.HIRING_MANAGER],
  'jobs.jd.view': [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER],
  'jobs.matcher.use': [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER],
  
  // Documents Module
  'docs.templates.all': [ROLES.HR],
  'docs.templates.offer': [ROLES.HR, ROLES.RECRUITER],
  'docs.templates.view': [ROLES.HIRING_MANAGER],
  'docs.query.full': [ROLES.HR],
  'docs.query.limited': [ROLES.RECRUITER],
  
  // Interviews Module
  'interviews.dashboard': [ROLES.HR, ROLES.HIRING_MANAGER],
  'interviews.schedule': [ROLES.HR, ROLES.HIRING_MANAGER],
  'interviews.conduct': [ROLES.HR, ROLES.HIRING_MANAGER],
  'interviews.view': [ROLES.RECRUITER]
}

// Route access definitions
export const ROUTE_PERMISSIONS = {
  '/dashboard': [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER],
  '/jobs/generator': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/jobs/generator/legacy': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/jobs/results': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/jobs/create/chat': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/jobs/create/form': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/jobs/matcher': [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER],
  '/documents': [ROLES.HR, ROLES.RECRUITER],
  '/documents/generate': [ROLES.HR, ROLES.RECRUITER],
  '/documents/templates': [ROLES.HR, ROLES.RECRUITER],
  '/documents/agent': [ROLES.HR, ROLES.RECRUITER],
  '/documents/library': [ROLES.HR, ROLES.RECRUITER],
  '/documents/query': [ROLES.HR],
  '/interviews/dashboard': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/interviews/schedule': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/interviews/candidate': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/interviews/interviewer': [ROLES.HR, ROLES.HIRING_MANAGER],
  '/interview/:interviewId/summary': [ROLES.HR, ROLES.HIRING_MANAGER]
}

// Menu visibility based on role
export const MENU_ACCESS = {
  jobs: {
    visible: [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER],
    submenus: {
      generator: [ROLES.HR, ROLES.HIRING_MANAGER],
      matcher: [ROLES.HR, ROLES.RECRUITER, ROLES.HIRING_MANAGER]
    }
  },
  documents: {
    visible: [ROLES.HR, ROLES.RECRUITER],
    submenus: {
      generate: [ROLES.HR, ROLES.RECRUITER],
      agent: [ROLES.HR, ROLES.RECRUITER],
      library: [ROLES.HR, ROLES.RECRUITER],
      templates: [ROLES.HR, ROLES.RECRUITER],
      query: [ROLES.HR]
    }
  },
  interviews: {
    visible: [ROLES.HR, ROLES.HIRING_MANAGER],
    submenus: {
      dashboard: [ROLES.HR, ROLES.HIRING_MANAGER],
      schedule: [ROLES.HR, ROLES.HIRING_MANAGER]
    }
  }
}

/**
 * Check if user has a specific permission
 * @param {Object} user - User object with role property
 * @param {string} permission - Permission string (e.g., 'jobs.jd.create')
 * @returns {boolean}
 */
export const hasPermission = (user, permission) => {
  if (!user || !user.role) return false
  const allowedRoles = PERMISSIONS[permission]
  return allowedRoles ? allowedRoles.includes(user.role) : false
}

/**
 * Check if user can access a specific route
 * @param {Object} user - User object with role property
 * @param {string} path - Route path
 * @returns {boolean}
 */
export const canAccessRoute = (user, path) => {
  if (!user || !user.role) return false
  const allowedRoles = ROUTE_PERMISSIONS[path]
  if (allowedRoles) return allowedRoles.includes(user.role)

  // Support parameterized routes (e.g., /interview/:interviewId/summary)
  const matchedRoute = Object.keys(ROUTE_PERMISSIONS).find((route) => {
    if (!route.includes(':')) return false
    const routeParts = route.split('/')
    const pathParts = path.split('/')
    if (routeParts.length !== pathParts.length) return false
    return routeParts.every((part, index) => part.startsWith(':') || part === pathParts[index])
  })

  if (!matchedRoute) return false
  return ROUTE_PERMISSIONS[matchedRoute].includes(user.role)
}

/**
 * Check if menu should be visible for user
 * @param {Object} user - User object with role property
 * @param {string} menuId - Menu identifier (e.g., 'jobs', 'documents')
 * @returns {boolean}
 */
export const canViewMenu = (user, menuId) => {
  if (!user || !user.role) return false
  const menu = MENU_ACCESS[menuId]
  return menu ? menu.visible.includes(user.role) : false
}

/**
 * Check if submenu item should be visible for user
 * @param {Object} user - User object with role property
 * @param {string} menuId - Menu identifier
 * @param {string} submenuKey - Submenu key
 * @returns {boolean}
 */
export const canViewSubmenu = (user, menuId, submenuKey) => {
  if (!user || !user.role) return false
  const menu = MENU_ACCESS[menuId]
  if (!menu || !menu.submenus) return false
  const allowedRoles = menu.submenus[submenuKey]
  return allowedRoles ? allowedRoles.includes(user.role) : false
}

/**
 * Filter menu items based on user role
 * @param {Object} user - User object with role property
 * @param {Array} menuItems - Array of menu items
 * @returns {Array} Filtered menu items
 */
export const filterMenuByRole = (user, menuItems) => {
  if (!user || !user.role) return []
  
  return menuItems
    .filter(menu => canViewMenu(user, menu.id))
    .map(menu => ({
      ...menu,
      submenus: menu.submenus.filter(submenu => {
        // Extract submenu key from link (e.g., '/jobs/generator' -> 'generator')
        const submenuKey = submenu.link.split('/').pop()
        return canViewSubmenu(user, menu.id, submenuKey)
      })
    }))
    .filter(menu => menu.submenus.length > 0) // Remove menus with no visible submenus
}

/**
 * Get user role display name
 * @param {string} role - Role identifier
 * @returns {string}
 */
export const getRoleDisplayName = (role) => {
  const roleNames = {
    [ROLES.HR]: 'HR Manager',
    [ROLES.HIRING_MANAGER]: 'Hiring Manager',
    [ROLES.RECRUITER]: 'Recruiter'
  }
  return roleNames[role] || role
}

/**
 * Get role badge color
 * @param {string} role - Role identifier
 * @returns {string}
 */
export const getRoleBadgeColor = (role) => {
  const colors = {
    [ROLES.HR]: '#10b981', // green
    [ROLES.HIRING_MANAGER]: '#3b82f6', // blue
    [ROLES.RECRUITER]: '#f59e0b' // orange
  }
  return colors[role] || '#6b7280'
}
