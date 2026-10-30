import { expect, test, type Page } from '@playwright/test'
import type { Task } from '../src/services/api'

const user = {
  id: 'user-1',
  username: 'tester',
  email: 'tester@example.com',
  is_active: true,
  created_at: '2026-01-01T12:00:00Z',
}
const password = 'test-password'

test.beforeEach(async ({ page }) => {
  let tasks: Task[] = []
  const projects: {
    id: string
    name: string
    owner_id: string
    role: string
    created_at: string
  }[] = []
  const members = [
    {
      user_id: user.id,
      email: user.email,
      username: user.username,
      role: 'owner',
      accepted: true,
    },
  ]
  await page.route('http://127.0.0.1:3100/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const apiPath = url.pathname.slice('/api'.length)
    const method = request.method()
    const headers = {
      'access-control-allow-origin': 'http://127.0.0.1:3100',
      'access-control-allow-credentials': 'true',
      'access-control-allow-headers': 'content-type,authorization',
      'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
    }
    if (method === 'OPTIONS') {
      await route.fulfill({ status: 204, headers })
      return
    }
    if (apiPath === '/health') {
      expect(request.headers().authorization).toBeUndefined()
      await route.fulfill({ json: { status: 'healthy' }, headers })
      return
    }
    if (apiPath === '/auth/oauth/github') {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: 'OAuth',
      })
      return
    }
    if (apiPath === '/users/register') {
      expect(request.postDataJSON()).toEqual({
        username: user.username,
        email: user.email,
        password,
      })
      await route.fulfill({ status: 201, json: user, headers })
      return
    }
    if (apiPath === '/users/login') {
      const credentials = request.postDataJSON()
      expect(credentials.email).toBe(user.email)
      await route.fulfill({
        status: credentials.password === password ? 200 : 401,
        json:
          credentials.password === password
            ? { access_token: 'test-token', token_type: 'bearer' }
            : { detail: 'Incorrect email or password' },
        headers,
      })
      return
    }
    expect(request.headers().authorization).toBe('Bearer test-token')
    if (apiPath === '/users/me') {
      await route.fulfill({ json: user, headers })
      return
    }
    if (apiPath === '/projects/invitations') {
      await route.fulfill({ json: [], headers })
      return
    }
    if (apiPath === '/projects' && method === 'GET') {
      await route.fulfill({ json: projects, headers })
      return
    }
    if (apiPath === '/projects' && method === 'POST') {
      const project = {
        id: 'project-1',
        name: request.postDataJSON().name,
        owner_id: user.id,
        role: 'owner',
        created_at: '2026-01-01T12:00:00Z',
      }
      projects.push(project)
      await route.fulfill({ status: 201, json: project, headers })
      return
    }
    if (apiPath === '/projects/project-1') {
      await route.fulfill({ json: { ...projects[0], members }, headers })
      return
    }
    if (apiPath === '/projects/project-1/invitations') {
      const invitation = request.postDataJSON()
      members.push({
        user_id: 'teammate-1',
        username: 'teammate',
        email: invitation.email,
        role: invitation.role,
        accepted: false,
      })
      await route.fulfill({
        status: 201,
        json: {
          id: 'invite-1',
          project_id: 'project-1',
          project_name: projects[0].name,
          role: invitation.role,
        },
        headers,
      })
      return
    }
    if (apiPath === '/tasks/export') {
      await route.fulfill({
        json: {
          version: 1,
          tasks: tasks
            .filter((task) => !task.project_id)
            .map((task) => ({
              id: task.id,
              title: task.title,
              description: task.description || null,
              status: task.status,
              priority: task.priority,
              due_date: task.due_date || null,
              tags: task.tags || [],
              recurrence: task.recurrence || null,
              recurrence_timezone: task.recurrence_timezone || 'UTC',
            })),
        },
        headers,
      })
      return
    }
    if (apiPath === '/tasks/import') {
      const backup = request.postDataJSON()
      expect(backup.version).toBe(1)
      for (const entry of backup.tasks)
        tasks.push({
          ...entry,
          id: `import-${entry.id}`,
          owner_id: user.id,
          created_at: '2026-01-01T12:00:00Z',
          updated_at: '2026-01-01T12:00:00Z',
        })
      await route.fulfill({
        json: { imported: backup.tasks.length, skipped: 0 },
        headers,
      })
      return
    }
    if (apiPath === '/api/chat/smart-parse') {
      const input = request.postDataJSON()
      expect(input.reference_time).toBeTruthy()
      expect(input.timezone).toBeTruthy()
      await route.fulfill({
        json: {
          title: 'Review the project plan',
          priority: 'high',
          description: null,
          tags: ['work'],
          due_date: '2030-03-12T05:00:00Z',
          recurrence: 'weekly',
          recurrence_timezone: input.timezone,
          source: 'ai',
          warnings: [],
        },
        headers,
      })
      return
    }
    if (apiPath === '/tasks' && method === 'GET') {
      const search = url.searchParams.get('search') || ''
      await route.fulfill({
        json: tasks.filter(
          (task) =>
            task.title.includes(search) &&
            (task.project_id || null) === url.searchParams.get('project_id')
        ),
        headers,
      })
      return
    }
    if (apiPath === '/tasks' && method === 'POST') {
      const task: Task = {
        id: `task-${tasks.length + 1}`,
        owner_id: user.id,
        status: 'pending',
        created_at: '2026-01-01T12:00:00Z',
        updated_at: '2026-01-01T12:00:00Z',
        ...request.postDataJSON(),
      }
      tasks.push(task)
      await route.fulfill({ status: 201, json: task, headers })
      return
    }
    if (apiPath.startsWith('/tasks/task-') && method === 'PATCH') {
      const index = tasks.findIndex(
        (task) => task.id === apiPath.split('/').pop()
      )
      const updates = request.postDataJSON()
      const previous = tasks[index]
      tasks[index] = { ...previous, ...updates }
      if (
        previous.recurrence &&
        previous.status === 'pending' &&
        updates.status === 'completed'
      ) {
        tasks.push({
          ...previous,
          id: `task-${tasks.length + 1}`,
          status: 'pending',
        })
      }
      await route.fulfill({ json: tasks[index], headers })
      return
    }
    if (apiPath === '/tasks/task-1' && method === 'DELETE') {
      tasks = tasks.filter((task) => task.id !== 'task-1')
      await route.fulfill({ status: 204, headers })
      return
    }
    throw new Error(`Unexpected API request: ${method} ${apiPath}`)
  })
})

async function login(page: Page) {
  await page.goto('/login')
  await page.getByLabel('Email address').fill(user.email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'My Tasks' })).toBeVisible()
}

test('unauthenticated dashboard redirects to login', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login$/)
  await expect(
    page.getByRole('heading', { name: 'Sign in to your account' })
  ).toBeVisible()
})

test('registration validates passwords and signs the user in', async ({
  page,
}) => {
  await page.goto('/register')
  await page.getByLabel('Username').fill(user.username)
  await page.getByLabel('Email address').fill(user.email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password').fill('different-password')
  await page
    .getByRole('button', { name: 'Create account', exact: true })
    .click()
  await expect(page.getByText('Passwords do not match')).toBeVisible()
  await page.getByLabel('Confirm password').fill(password)
  await page
    .getByRole('button', { name: 'Create account', exact: true })
    .click()
  await expect(page.getByRole('heading', { name: 'My Tasks' })).toBeVisible()
  await expect(page.getByText(user.email)).toBeVisible()
  expect(
    await page.evaluate(() => localStorage.getItem('refresh_token'))
  ).toBeNull()
})

test('login displays server errors and allows another attempt', async ({
  page,
}) => {
  await page.goto('/login')
  await page.getByLabel('Email address').fill(user.email)
  await page.getByLabel('Password', { exact: true }).fill('wrong-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByText('Incorrect email or password')).toBeVisible()
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'My Tasks' })).toBeVisible()
})

test('OAuth login uses the same-origin API gateway', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: 'Continue with GitHub' }).click()
  await expect(page).toHaveURL(/\/api\/auth\/oauth\/github$/)
})

test('expired task session clears stored tokens and returns to login', async ({
  page,
}) => {
  await login(page)
  await page.evaluate(() => localStorage.setItem('refresh_token', 'old-token'))
  await page.route('**/api/tasks?**', async (route) => {
    await route.fulfill({ status: 401, json: { detail: 'Token expired' } })
  })
  await page.getByRole('textbox', { name: 'Search tasks' }).fill('expired')
  await expect(page).toHaveURL(/\/login\?expired=true$/)
  expect(
    await page.evaluate(() => localStorage.getItem('access_token'))
  ).toBeNull()
  expect(
    await page.evaluate(() => localStorage.getItem('refresh_token'))
  ).toBeNull()
})

test('authenticated user creates, edits, completes and deletes a task', async ({
  page,
}) => {
  const runtimeErrors: string[] = []
  page.on('pageerror', (error) => runtimeErrors.push(error.message))
  await login(page)
  await expect(page).toHaveTitle('Todoer AI — A little more clarity')
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill('Buy groceries')
  await dialog.getByLabel('Due Date').fill('2000-01-01T12:00')
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Buy groceries', exact: true })
  ).toBeVisible()
  await expect(page.getByText(/Overdue:/)).toBeVisible()
  await page.getByRole('button', { name: 'Edit task Buy groceries' }).click()
  await dialog.getByLabel('Title').fill('Buy milk')
  await dialog.getByRole('button', { name: 'Save Changes' }).click()
  await expect(
    page.getByRole('heading', { name: 'Buy milk', exact: true })
  ).toBeVisible()
  await page
    .getByRole('button', { name: 'Mark task Buy milk as completed' })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Completed (1)' })
  ).toBeVisible()
  await page.getByRole('button', { name: 'Delete task Buy milk' }).click()
  await expect(page.getByText('Buy milk', { exact: true })).toHaveCount(0)
  await page.evaluate(() => localStorage.setItem('refresh_token', 'old-token'))
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL(/\/login$/)
  expect(
    await page.evaluate(() => localStorage.getItem('access_token'))
  ).toBeNull()
  expect(
    await page.evaluate(() => localStorage.getItem('refresh_token'))
  ).toBeNull()
  expect(runtimeErrors).toEqual([])
})

async function createManualTask(page: Page, title: string) {
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill(title)
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await expect(dialog).toHaveCount(0)
}

test('editing clears optional fields and preserves local deadline time', async ({
  page,
}) => {
  await login(page)
  await page.getByRole('button', { name: '+ New Task' }).click()
  let dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill('Clear my details')
  await dialog.getByLabel('Description').fill('Temporary notes')
  await dialog.getByLabel('Due Date').fill('2030-03-12T10:00')
  await dialog.getByLabel('Tags', { exact: true }).fill('work')
  await dialog.getByRole('button', { name: 'Add tag' }).click()
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await page.getByRole('button', { name: 'Edit task Clear my details' }).click()
  dialog = page.getByRole('dialog')
  await expect(dialog.getByLabel('Due Date')).toHaveValue('2030-03-12T10:00')
  await dialog.getByLabel('Description').fill('')
  await dialog.getByLabel('Due Date').fill('')
  await dialog.getByRole('button', { name: 'Remove tag work' }).click()
  const update = page.waitForRequest((request) => request.method() === 'PATCH')
  await dialog.getByRole('button', { name: 'Save Changes' }).click()
  const payload = (await update).postDataJSON()
  expect(payload.description).toBeNull()
  expect(payload.due_date).toBeNull()
  expect(payload.tags).toEqual([])
  await expect(page.getByText('Temporary notes')).toHaveCount(0)
})

test('failed save keeps the task draft for retry', async ({ page }) => {
  await login(page)
  await page.route('**/api/tasks', async (route) => {
    if (route.request().method() === 'POST')
      await route.fulfill({
        status: 503,
        json: { detail: 'Temporarily unavailable' },
      })
    else await route.fallback()
  })
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill('Keep this idea')
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await expect(dialog.getByRole('alert')).toHaveText('Temporarily unavailable')
  await expect(dialog.getByLabel('Title')).toHaveValue('Keep this idea')
})

test('a pending save keeps the editor open until a failed request can be retried', async ({
  page,
}) => {
  await login(page)
  let finish!: () => void
  const pending = new Promise<void>((resolve) => {
    finish = resolve
  })
  await page.route('**/api/tasks', async (route) => {
    if (route.request().method() !== 'POST') return route.fallback()
    await pending
    await route.fulfill({ status: 503, json: { detail: 'Please retry' } })
  })
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill('Keep this pending draft')
  const save = page.waitForRequest(
    (request) => request.method() === 'POST' && request.url().endsWith('/tasks')
  )
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await save
  await page.keyboard.press('Escape')
  await expect(dialog).toBeVisible()
  finish()
  await expect(dialog.getByRole('alert')).toHaveText('Please retry')
  await expect(dialog.getByLabel('Title')).toHaveValue(
    'Keep this pending draft'
  )
})

test('a delayed completion refreshes the current search', async ({ page }) => {
  await login(page)
  await createManualTask(page, 'First task')
  await createManualTask(page, 'Second task')
  let finish!: () => void
  const pending = new Promise<void>((resolve) => {
    finish = resolve
  })
  await page.route('**/api/tasks/task-1', async (route) => {
    await pending
    await route.fallback()
  })
  const update = page.waitForRequest((request) => request.method() === 'PATCH')
  await page
    .getByRole('button', { name: 'Mark task First task as completed' })
    .click()
  await update
  await page.getByLabel('Search tasks').fill('Second task')
  await expect(
    page.getByRole('heading', { name: 'First task', exact: true })
  ).toHaveCount(0)
  finish()
  await expect(page.getByText('Task completed', { exact: true })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Second task', exact: true })
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'First task', exact: true })
  ).toHaveCount(0)
})

test('failed task loading shows an error and supports retry', async ({
  page,
}) => {
  await login(page)
  await page.route('**/api/tasks?**', async (route) =>
    route.fulfill({ status: 503, json: { detail: 'Task service unavailable' } })
  )
  await page.getByRole('textbox', { name: 'Search tasks' }).fill('retry')
  await expect(page.locator('.form-error[role="alert"]')).toContainText(
    'Task service unavailable'
  )
  await page.unroute('**/api/tasks?**')
  await page.getByRole('button', { name: 'Retry loading tasks' }).click()
  await expect(page.locator('.form-error[role="alert"]')).toHaveCount(0)
})

test('oldest-first sort reaches the API without remapping', async ({
  page,
}) => {
  await login(page)
  const request = page.waitForRequest((request) =>
    request.url().includes('sort_by=created_at_asc')
  )
  await page.getByLabel('Sort tasks').selectOption('created_at_asc')
  await request
})

test('AI draft previews dates and recurrence before creating a task', async ({
  page,
}) => {
  await login(page)
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog
    .getByLabel('What needs to get done?')
    .fill('Review the project plan every week at 10am')
  await dialog.getByRole('button', { name: 'Smart Parse' }).click()
  await expect(dialog.getByLabel('Title')).toHaveValue(
    'Review the project plan'
  )
  await expect(dialog.getByRole('status')).toContainText('Review')
  await expect(page.locator('article.task-row')).toHaveCount(0)
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Review the project plan', exact: true })
  ).toBeVisible()
  await page
    .getByRole('button', {
      name: 'Mark task Review the project plan as completed',
    })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Completed (1)' })
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'In progress (1)' })
  ).toBeVisible()
})

test('creates a shared project and invites a viewer', async ({ page }) => {
  await login(page)
  await page
    .getByRole('button', { name: 'Create project', exact: true })
    .click()
  await page.getByLabel('Project name').fill('Website refresh')
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Create project', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Website refresh', exact: true })
  ).toBeVisible()
  await page.getByRole('button', { name: 'Project members' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Email address').fill('teammate@example.com')
  await dialog.getByLabel('Invitation role').selectOption('viewer')
  await dialog.getByRole('button', { name: 'Send invitation' }).click()
  await expect(dialog.getByText('teammate@example.com')).toBeVisible()
  await expect(dialog.getByText('Invited', { exact: true })).toBeVisible()
})

test('exports a backup and imports tasks from a JSON file', async ({
  page,
}) => {
  await login(page)
  await createManualTask(page, 'Back up this task')
  await page.getByRole('button', { name: 'Import & export' }).click()
  const dialog = page.getByRole('dialog')
  const download = page.waitForEvent('download')
  await dialog.getByRole('button', { name: 'Export JSON' }).click()
  expect((await download).suggestedFilename()).toMatch(/todoer-backup-.*\.json/)
  await dialog.getByLabel('Task backup file').setInputFiles({
    name: 'backup.json',
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        version: 1,
        tasks: [
          {
            id: 'd376c766-1ba2-4ed1-9eb0-9d23a1f4fdc4',
            title: 'Restored task',
            priority: 'medium',
            status: 'pending',
          },
        ],
      }) + ' '.repeat(2_100_000)
    ),
  })
  await expect(dialog.getByRole('status')).toContainText('Imported 1 tasks')
  await dialog.getByRole('button', { name: 'Close', exact: true }).click()
  await expect(page.getByText('Restored task', { exact: true })).toBeVisible()
})

test('mobile navigation and dark mode stay usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await login(page)
  await expect(page.locator('.workspace-sidebar')).not.toBeVisible()
  await page.getByRole('button', { name: 'Toggle theme' }).click()
  await expect(page.locator('html')).toHaveClass(/dark/)
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.getByRole('button', { name: 'Recurring', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Recurring tasks' })
  ).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth
    )
  ).toBe(true)
})

test('accepting a viewer invitation opens a read-only project', async ({
  page,
}) => {
  let accepted = false
  const project = {
    id: 'project-2',
    name: 'Shared roadmap',
    owner_id: 'other-user',
    role: 'viewer',
    created_at: user.created_at,
  }
  await page.route('**/api/projects', (route) =>
    route.fulfill({ json: accepted ? [project] : [] })
  )
  await page.route('**/api/projects/invitations', (route) =>
    route.fulfill({
      json: accepted
        ? []
        : [
            {
              id: 'invite-viewer',
              project_id: project.id,
              project_name: project.name,
              role: 'viewer',
            },
          ],
    })
  )
  await page.route(
    '**/api/projects/invitations/invite-viewer/accept',
    async (route) => {
      accepted = true
      await route.fulfill({ json: project })
    }
  )
  await page.route('**/api/projects/project-2', (route) =>
    route.fulfill({
      json: {
        ...project,
        members: [
          {
            user_id: user.id,
            email: user.email,
            username: user.username,
            role: 'viewer',
            accepted: true,
          },
        ],
      },
    })
  )
  await login(page)
  await page.getByRole('button', { name: /Invitations/ }).click()
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Accept', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: project.name, exact: true })
  ).toBeVisible()
  await expect(page.getByRole('button', { name: '+ New Task' })).toHaveCount(0)
  await expect(
    page.getByRole('button', { name: 'Draft with AI' })
  ).toBeDisabled()
  await page.getByRole('button', { name: 'Project members' }).click()
  await expect(
    page.getByRole('dialog').getByRole('button', { name: 'Send invitation' })
  ).toHaveCount(0)
})
