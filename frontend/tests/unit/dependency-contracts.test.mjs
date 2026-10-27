import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { test } from 'node:test'

const require = createRequire(import.meta.url)
const { satisfies } = require('semver')

test('the locked ESLint and TypeScript versions satisfy their plugin peers', () => {
  const { packages } = JSON.parse(
    readFileSync(new URL('../../package-lock.json', import.meta.url), 'utf8')
  )
  const versions = Object.fromEntries(
    ['eslint', 'typescript'].map((name) => [
      name,
      packages[`node_modules/${name}`].version,
    ])
  )
  for (const [path, entry] of Object.entries(packages)) {
    for (const [name, range] of Object.entries(entry.peerDependencies || {})) {
      if (name in versions) {
        assert.ok(
          satisfies(versions[name], range),
          `${path} requires ${name} ${range}; locked ${versions[name]}`
        )
      }
    }
  }
})
