const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Task {
  id: string
  owner_id: string
  title: string
  description?: string
  status: 'pending' | 'completed'
  priority: 'low' | 'medium' | 'high'
  due_date?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high'
  due_date?: string
  tags?: string[]
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: 'pending' | 'completed'
  priority?: 'low' | 'medium' | 'high'
  due_date?: string
  tags?: string[]
}

// Auth types
export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  refresh_token?: string
}

const getHeaders = () => {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

// Handle 401 errors - redirect to login with message
const handleAuthError = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token')
    // Dispatch event for AuthContext to handle
    window.dispatchEvent(new CustomEvent('auth:expired'))
    // Redirect to login
    window.location.href = '/login?expired=true'
  }
}

export const api = {
  tasks: {
    list: async (
      params: {
        search?: string
        status?: string
        priority?: string
        sort_by?: string
      } = {}
    ): Promise<Task[]> => {
      // Filter out undefined/null/empty values and "all" (special value for no filter)
      const filteredParams = Object.entries(params).reduce(
        (acc, [key, value]) => {
          if (
            value !== undefined &&
            value !== null &&
            value !== '' &&
            value !== 'all'
          ) {
            acc[key] = value
          }
          return acc
        },
        {} as Record<string, string>
      )
      const query = new URLSearchParams(filteredParams).toString()
      const url = query
        ? `${API_URL}/tasks?${query}`
        : `${API_URL}/tasks`
      const response = await fetch(url, {
        headers: getHeaders(),
      })
      if (response.status === 401) {
        handleAuthError()
        return []
      }
      if (!response.ok) {
        // Return empty array for 400+ responses - user-friendly handling
        return []
      }
      return response.json()
    },

    create: async (task: TaskCreate): Promise<Task> => {
      const response = await fetch(`${API_URL}/tasks`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(task),
      })
      if (response.status === 401) {
        handleAuthError()
        throw new Error('Session expired')
      }
      if (!response.ok) throw new Error('Failed to create task')
      return response.json()
    },

    get: async (id: string): Promise<Task> => {
      const response = await fetch(`${API_URL}/tasks/${id}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Task not found')
      return response.json()
    },

    update: async (id: string, task: TaskUpdate): Promise<Task> => {
      const response = await fetch(`${API_URL}/tasks/${id}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(task),
      })
      if (!response.ok) throw new Error('Failed to update task')
      return response.json()
    },

    delete: async (id: string): Promise<void> => {
      const response = await fetch(`${API_URL}/tasks/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (response.status !== 204) throw new Error('Failed to delete task')
    },
  },

  chat: {
    smartParse: async (text: string): Promise<TaskCreate> => {
      const response = await fetch(`${API_URL}/api/chat/smart-parse`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ text }),
      })
      if (!response.ok) {
        // Return a basic task create object as fallback
        return {
          title: text.trim().substring(0, 100),
          priority: 'medium' as const,
        }
      }
      return response.json()
    },
  },

  ping: {
    keepAlive: async (): Promise<void> => {
      try {
        await fetch(`${API_URL}/tasks`, {
          method: 'HEAD',
          headers: getHeaders(),
        })
      } catch (error) {
        // Silent fail - don't alert users about ping failures
        console.debug('Ping failed:', error)
      }
    },
  },

  auth: {
    login: async (email: string, password: string): Promise<TokenResponse> => {
      const response = await fetch(`${API_URL}/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }
      return response.json()
    },

    register: async (
      username: string,
      email: string,
      password: string
    ): Promise<User> => {
      const response = await fetch(`${API_URL}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
        credentials: 'include',
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Registration failed')
      }
      return response.json()
    },

    me: async (): Promise<User> => {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Failed to get user')
      return response.json()
    },

    logout: () => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
      }
    },
  },

  health: {
    check: async (): Promise<{ status: string }> => {
      const response = await fetch(`${API_URL}/health`)
      return response.json()
    },
  },
}
