import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user })
  },
  logout: () => {
    localStorage.removeItem('user')
    set({ user: null })
  },
  isAuthenticated: () => {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    return user !== null
  }
}))
