const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

export type Priority = 'low' | 'medium' | 'high'
export type Recurrence = 'daily' | 'weekly' | 'monthly'
export type ProjectRole = 'owner' | 'editor' | 'viewer'

export interface Task {
  id: string
  owner_id: string
  title: string
  description?: string | null
  status: 'pending' | 'completed'
  priority: Priority
  due_date?: string | null
  tags?: string[]
  recurrence?: Recurrence | null
  recurrence_timezone?: string
  project_id?: string | null
  assignee_id?: string | null
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string | null
  priority?: Priority
  due_date?: string | null
  tags?: string[]
  recurrence?: Recurrence | null
  recurrence_timezone?: string
  project_id?: string | null
  assignee_id?: string | null
}

export interface TaskUpdate extends Partial<TaskCreate> {
  status?: 'pending' | 'completed'
}

export interface Project {
  id: string
  name: string
  owner_id: string
  role: ProjectRole
  created_at: string
}

export interface ProjectMember {
  user_id: string
  username: string
  email: string
  role: ProjectRole
  accepted: boolean
}

export interface ProjectDetail extends Project {
  members: ProjectMember[]
}

export interface Invitation {
  id: string
  project_id: string
  project_name: string
  role: 'editor' | 'viewer'
}

export interface TaskBackup {
  version: 1
  tasks: (TaskCreate & {
    id: string
    status: Task['status']
    recurrence_day?: number | null
    recurrence_spawned?: boolean
  })[]
}

export interface TaskDraft extends TaskCreate {
  source: 'ai' | 'fallback'
  warnings: string[]
}

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

export interface RegisterRequest extends LoginRequest {
  username: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  refresh_token?: string
}

function handleAuthError() {
  if (typeof window === 'undefined') return
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.dispatchEvent(new CustomEvent('auth:expired'))
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- Discard authenticated state after expiry.
  window.location.href = '/login?expired=true'
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true
): Promise<T> {
  const token =
    authenticated && typeof window !== 'undefined'
      ? localStorage.getItem('access_token')
      : null
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (response.status === 401 && authenticated) {
    handleAuthError()
    throw new Error('Session expired')
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const error = await response.json()
      if (typeof error.detail === 'string') message = error.detail
    } catch {
      // Gateways can return HTML instead of the API's JSON error response.
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  tasks: {
    list: (
      params: {
        search?: string
        status?: string
        priority?: string
        sort_by?: string
        project_id?: string | null
      } = {}
    ): Promise<Task[]> => {
      const query = new URLSearchParams()
      for (const [key, value] of Object.entries(params)) {
        if (value && value !== 'all') query.set(key, value)
      }
      return request(`/tasks${query.size ? `?${query}` : ''}`)
    },
    create: (task: TaskCreate): Promise<Task> =>
      request('/tasks', { method: 'POST', body: JSON.stringify(task) }),
    get: (id: string): Promise<Task> => request(`/tasks/${id}`),
    update: (id: string, task: TaskUpdate): Promise<Task> =>
      request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(task) }),
    delete: (id: string): Promise<void> =>
      request(`/tasks/${id}`, { method: 'DELETE' }),
    export: (): Promise<TaskBackup> => request('/tasks/export'),
    import: (
      backup: TaskBackup
    ): Promise<{ imported: number; skipped: number }> =>
      request('/tasks/import', {
        method: 'POST',
        body: JSON.stringify(backup),
      }),
  },
  projects: {
    list: (): Promise<Project[]> => request('/projects'),
    create: (name: string): Promise<Project> =>
      request('/projects', { method: 'POST', body: JSON.stringify({ name }) }),
    get: (id: string): Promise<ProjectDetail> => request(`/projects/${id}`),
    invite: (
      id: string,
      email: string,
      role: 'editor' | 'viewer'
    ): Promise<Invitation> =>
      request(`/projects/${id}/invitations`, {
        method: 'POST',
        body: JSON.stringify({ email, role }),
      }),
    removeMember: (id: string, userId: string): Promise<void> =>
      request(`/projects/${id}/members/${userId}`, { method: 'DELETE' }),
    invitations: (): Promise<Invitation[]> => request('/projects/invitations'),
    accept: (id: string): Promise<Project> =>
      request(`/projects/invitations/${id}/accept`, { method: 'POST' }),
  },
  chat: {
    smartParse: (
      text: string,
      context: { reference_time?: string; timezone?: string } = {}
    ): Promise<TaskDraft> =>
      request('/api/chat/smart-parse', {
        method: 'POST',
        body: JSON.stringify({
          text,
          reference_time: new Date().toISOString(),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          ...context,
        }),
      }),
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
    login: (email: string, password: string): Promise<TokenResponse> =>
      request(
        '/users/login',
        {
          method: 'POST',
          body: JSON.stringify({ email, password }),
          credentials: 'include',
        },
        false
      ),
    register: (
      username: string,
      email: string,
      password: string
    ): Promise<User> =>
      request(
        '/users/register',
        {
          method: 'POST',
          body: JSON.stringify({ username, email, password }),
          credentials: 'include',
        },
        false
      ),
    me: (): Promise<User> => request('/users/me'),
    logout: () => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    },
  },
  health: {
    check: (): Promise<{ status: string }> => request('/health', {}, false),
  },
}
