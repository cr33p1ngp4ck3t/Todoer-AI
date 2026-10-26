'use client'

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react'
import { api, User } from '../services/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  setTokens: (accessToken: string, refreshToken: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const userData = await api.auth.me()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user:', error)
      localStorage.removeItem('access_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Initialize auth from browser storage after hydration.
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    const response = await api.auth.login(email, password)
    localStorage.setItem('access_token', response.access_token)
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token)
    } else {
      localStorage.removeItem('refresh_token')
    }
    await refreshUser()
  }

  const register = async (
    username: string,
    email: string,
    password: string
  ) => {
    await api.auth.register(username, email, password)
    await login(email, password)
  }

  const logout = () => {
    api.auth.logout()
    setUser(null)
  }

  const setTokens = (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    refreshUser()
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser, setTokens }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
