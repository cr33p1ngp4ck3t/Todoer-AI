import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { test } from 'node:test'

for (const [timezone, local, utc] of [
  ['UTC', '2026-10-27T14:30', '2026-10-27T14:30:00.000Z'],
  ['Asia/Karachi', '2026-10-27T14:30', '2026-10-27T09:30:00.000Z'],
  ['America/New_York', '2026-10-27T14:30', '2026-10-27T18:30:00.000Z'],
]) {
  test(`deadline round trips in ${timezone}`, () => {
    const output = execFileSync(
      process.execPath,
      [
        '--experimental-strip-types',
        '--input-type=module',
        '-e',
        `import { toLocalDateTime, toUtcDateTime } from './src/lib/task-dates.ts'; console.log(JSON.stringify([toUtcDateTime('${local}'), toLocalDateTime('${utc}'), toUtcDateTime(''), toLocalDateTime(null)]));`,
      ],
      {
        cwd: process.cwd(),
        env: { ...process.env, TZ: timezone },
        encoding: 'utf8',
      }
    )
    assert.deepEqual(JSON.parse(output), [utc, local, null, ''])
  })
}

test('invalid or nonexistent local times are rejected instead of silently changing the deadline', () => {
  const output = execFileSync(
    process.execPath,
    [
      '--experimental-strip-types',
      '--input-type=module',
      '-e',
      `import assert from 'node:assert/strict'; import { toUtcDateTime } from './src/lib/task-dates.ts'; assert.throws(()=>toUtcDateTime('invalid'), /valid/); assert.throws(()=>toUtcDateTime('2026-03-08T02:30'), /exist/); console.log('validated');`,
    ],
    {
      cwd: process.cwd(),
      env: { ...process.env, TZ: 'America/New_York' },
      encoding: 'utf8',
    }
  )
  assert.equal(output.trim(), 'validated')
})

test('legacy timezone-free API deadlines are interpreted as UTC', () => {
  const output = execFileSync(
    process.execPath,
    [
      '--experimental-strip-types',
      '--input-type=module',
      '-e',
      `import assert from 'node:assert/strict'; import { parseTaskDate, toLocalDateTime } from './src/lib/task-dates.ts'; assert.equal(parseTaskDate('2026-10-27T09:30:00').toISOString(), '2026-10-27T09:30:00.000Z'); assert.throws(()=>parseTaskDate('invalid'), /valid/); console.log(toLocalDateTime('2026-10-27T09:30:00'));`,
    ],
    {
      cwd: process.cwd(),
      env: { ...process.env, TZ: 'Asia/Karachi' },
      encoding: 'utf8',
    }
  )
  assert.equal(output.trim(), '2026-10-27T14:30')
})
