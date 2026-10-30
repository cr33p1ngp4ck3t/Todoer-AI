import type { NextConfig } from 'next'
import { withSentryConfig } from '@sentry/nextjs/config'

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
  },
  rewrites() {
    return process.env.INTERNAL_API_URL
      ? [
          {
            source: '/api/:path*',
            destination: `${process.env.INTERNAL_API_URL}/:path*`,
          },
        ]
      : []
  },
  turbopack: {},
}

export default withSentryConfig(nextConfig, {
  org: 'todo-nl',
  project: 'todo-frontend',
  authToken: process.env.SENTRY_AUTH_TOKEN,
  silent: !process.env.CI,
  sourcemaps: { disable: !process.env.SENTRY_AUTH_TOKEN },
})
