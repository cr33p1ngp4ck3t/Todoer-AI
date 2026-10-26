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
  await page.route('**/api/**', async (route) => {
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
    if (apiPath === '/tasks' && method === 'GET') {
      const search = url.searchParams.get('search') || ''
      await route.fulfill({
        json: tasks.filter((task) => task.title.includes(search)),
        headers,
      })
      return
    }
    if (apiPath === '/tasks' && method === 'POST') {
      const task: Task = {
        id: 'task-1',
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
    if (apiPath === '/tasks/task-1' && method === 'PATCH') {
      tasks[0] = { ...tasks[0], ...request.postDataJSON() }
      await route.fulfill({ json: tasks[0], headers })
      return
    }
    if (apiPath === '/tasks/task-1' && method === 'DELETE') {
      tasks = []
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
  await expect(page).toHaveTitle('Todoer - Be Productive')
  await page.getByRole('button', { name: '+ New Task' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Manual', exact: true }).click()
  await dialog.getByLabel('Title').fill('Buy groceries')
  await dialog.getByLabel('Due Date').fill('2000-01-01T12:00')
  await dialog.getByRole('button', { name: 'Create Task', exact: true }).click()
  await expect(page.getByText('Buy groceries', { exact: true })).toBeVisible()
  await expect(page.getByText(/Overdue:/)).toBeVisible()
  await page.getByRole('button', { name: 'Edit task Buy groceries' }).click()
  await dialog.getByLabel('Title').fill('Buy milk')
  await dialog.getByRole('button', { name: 'Save Changes' }).click()
  await expect(page.getByText('Buy milk', { exact: true })).toBeVisible()
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
