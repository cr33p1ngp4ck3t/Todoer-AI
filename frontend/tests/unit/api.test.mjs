import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'
import { api } from '../../src/services/api.ts'

const originalWindow = Object.getOwnPropertyDescriptor(globalThis, 'window')
const originalStorage = Object.getOwnPropertyDescriptor(
  globalThis,
  'localStorage'
)
let tokens
let browser

beforeEach(() => {
  tokens = new Map([
    ['access_token', 'access'],
    ['refresh_token', 'refresh'],
  ])
  browser = { location: { href: '' }, dispatchEvent: mock.fn() }
  Object.defineProperty(globalThis, 'window', {
    value: browser,
    configurable: true,
  })
  Object.defineProperty(globalThis, 'localStorage', {
    value: {
      getItem: (key) => tokens.get(key) ?? null,
      removeItem: (key) => tokens.delete(key),
    },
    configurable: true,
  })
})

afterEach(() => {
  mock.restoreAll()
  for (const [name, descriptor] of [
    ['window', originalWindow],
    ['localStorage', originalStorage],
  ]) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor)
    else delete globalThis[name]
  }
})

test('task listing reports server failures instead of displaying an empty list', async () => {
  mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Database unavailable' }, { status: 503 })
  )
  await assert.rejects(api.tasks.list(), /Database unavailable/)
})

test('updating with an expired session clears both tokens and redirects', async () => {
  mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Expired' }, { status: 401 })
  )
  await assert.rejects(
    api.tasks.update('task-1', { title: 'Changed' }),
    /Session expired/
  )
  assert.equal(tokens.size, 0)
  assert.equal(browser.location.href, '/login?expired=true')
  assert.equal(
    browser.dispatchEvent.mock.calls[0].arguments[0].type,
    'auth:expired'
  )
})

test('list filters ignore empty selections and encode literal searches', async () => {
  let captured
  mock.method(globalThis, 'fetch', async (url, options) => {
    captured = { url, options }
    return Response.json([{ id: 'task-1' }])
  })
  assert.deepEqual(
    await api.tasks.list({
      search: 'milk & eggs',
      status: 'all',
      priority: '',
      sort_by: 'created_at_asc',
      project_id: 'project-1',
    }),
    [{ id: 'task-1' }]
  )
  const url = new URL(captured.url, 'http://local.test')
  assert.equal(url.pathname, '/api/tasks')
  assert.equal(url.searchParams.get('search'), 'milk & eggs')
  assert.equal(url.searchParams.get('sort_by'), 'created_at_asc')
  assert.equal(url.searchParams.get('project_id'), 'project-1')
  assert.equal(url.searchParams.has('status'), false)
  assert.equal(captured.options.headers.Authorization, 'Bearer access')
})

test('task writes preserve explicit clears, recurrence and assignment', async () => {
  const calls = []
  mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    return options.method === 'DELETE'
      ? new Response(null, { status: 204 })
      : Response.json({ id: 'task-1' })
  })
  const task = {
    title: 'Plan',
    recurrence: 'weekly',
    recurrence_timezone: 'Asia/Karachi',
    due_date: '2026-10-27T10:00:00Z',
    project_id: 'project-1',
    assignee_id: 'member-1',
  }
  assert.equal((await api.tasks.create(task)).id, 'task-1')
  await api.tasks.get('task-1')
  await api.tasks.update('task-1', {
    description: null,
    due_date: null,
    recurrence: null,
    assignee_id: null,
    tags: [],
  })
  assert.equal(await api.tasks.delete('task-1'), undefined)
  assert.deepEqual(JSON.parse(calls[0].options.body), task)
  assert.equal(calls[1].url, '/api/tasks/task-1')
  assert.deepEqual(JSON.parse(calls[2].options.body), {
    description: null,
    due_date: null,
    recurrence: null,
    assignee_id: null,
    tags: [],
  })
  assert.equal(calls[3].options.method, 'DELETE')
})

test('personal backup round trip sends the versioned payload unchanged', async () => {
  const backup = {
    version: 1,
    tasks: [{ id: 'source-1', title: 'Backup', status: 'completed' }],
  }
  mock.method(globalThis, 'fetch', async (url, options) => {
    if (url.endsWith('/export')) return Response.json(backup)
    assert.deepEqual(JSON.parse(options.body), backup)
    return Response.json({ imported: 1, skipped: 0 })
  })
  assert.deepEqual(await api.tasks.export(), backup)
  assert.deepEqual(await api.tasks.import(backup), { imported: 1, skipped: 0 })
})

test('project APIs carry invitations, acceptance, roles and removal to their endpoints', async () => {
  const calls = []
  mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    return options.method === 'DELETE'
      ? new Response(null, { status: 204 })
      : Response.json({ id: 'project-1' })
  })
  await api.projects.list()
  await api.projects.create('Launch')
  await api.projects.get('project-1')
  await api.projects.invite('project-1', 'member@example.com', 'viewer')
  await api.projects.invitations()
  await api.projects.accept('invite-1')
  await api.projects.removeMember('project-1', 'member-1')
  assert.deepEqual(
    calls.map((call) => call.url),
    [
      '/api/projects',
      '/api/projects',
      '/api/projects/project-1',
      '/api/projects/project-1/invitations',
      '/api/projects/invitations',
      '/api/projects/invitations/invite-1/accept',
      '/api/projects/project-1/members/member-1',
    ]
  )
  assert.deepEqual(JSON.parse(calls[1].options.body), { name: 'Launch' })
  assert.deepEqual(JSON.parse(calls[3].options.body), {
    email: 'member@example.com',
    role: 'viewer',
  })
  assert.equal(calls[5].options.method, 'POST')
  assert.equal(calls[6].options.method, 'DELETE')
})

test('AI drafting passes an explicit reference instant and timezone', async () => {
  mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/api/chat/smart-parse')
    assert.deepEqual(JSON.parse(options.body), {
      text: 'Tomorrow at 10',
      reference_time: '2026-10-27T08:00:00Z',
      timezone: 'Asia/Karachi',
    })
    return Response.json({
      title: 'Tomorrow',
      due_date: '2026-10-28T05:00:00Z',
      source: 'ai',
      warnings: [],
    })
  })
  assert.equal(
    (
      await api.chat.smartParse('Tomorrow at 10', {
        reference_time: '2026-10-27T08:00:00Z',
        timezone: 'Asia/Karachi',
      })
    ).due_date,
    '2026-10-28T05:00:00Z'
  )
})

test('login failures remain on the form and never reuse a stored bearer token', async () => {
  mock.method(globalThis, 'fetch', async (_url, options) => {
    assert.equal(options.headers.Authorization, undefined)
    assert.equal(options.credentials, 'include')
    return Response.json(
      { detail: 'Incorrect email or password' },
      { status: 401 }
    )
  })
  await assert.rejects(
    api.auth.login('email@example.com', 'wrong'),
    /Incorrect email or password/
  )
  assert.equal(tokens.size, 2)
  assert.equal(browser.location.href, '')
})

test('registration and authenticated profile loading use distinct credential boundaries', async () => {
  mock.method(globalThis, 'fetch', async (url, options) => {
    if (url.endsWith('/register')) {
      assert.equal(options.headers.Authorization, undefined)
      assert.deepEqual(JSON.parse(options.body), {
        username: 'tester',
        email: 'tester@example.com',
        password: 'password',
      })
    } else assert.equal(options.headers.Authorization, 'Bearer access')
    return Response.json({ id: 'user-1' })
  })
  assert.equal(
    (await api.auth.register('tester', 'tester@example.com', 'password')).id,
    'user-1'
  )
  assert.equal((await api.auth.me()).id, 'user-1')
  api.auth.logout()
  assert.equal(tokens.size, 0)
})

test('non-JSON and validation errors produce a readable fallback', async () => {
  mock.method(
    globalThis,
    'fetch',
    async () => new Response('<h1>Bad gateway</h1>', { status: 502 })
  )
  await assert.rejects(api.tasks.list(), /Request failed \(502\)/)
  mock.restoreAll()
  mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: [{ msg: 'Invalid input' }] }, { status: 422 })
  )
  await assert.rejects(
    api.tasks.create({ title: 'x' }),
    /Request failed \(422\)/
  )
})

test('health checks and server-side calls need no browser storage', async () => {
  delete globalThis.window
  mock.method(globalThis, 'fetch', async (_url, options) => {
    assert.equal(options.headers.Authorization, undefined)
    return Response.json({ status: 'healthy' })
  })
  assert.equal((await api.health.check()).status, 'healthy')
  await api.tasks.list()
  api.auth.logout()
  mock.restoreAll()
  mock.method(globalThis, 'fetch', async () =>
    Response.json({}, { status: 401 })
  )
  await assert.rejects(api.tasks.list(), /Session expired/)
})
