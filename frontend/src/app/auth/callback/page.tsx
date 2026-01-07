'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '../../../contexts/AuthContext'

function OAuthCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { setTokens } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      // Get tokens from URL parameters
      const accessToken = searchParams.get('access_token')
      const refreshToken = searchParams.get('refresh_token')
      const errorParam = searchParams.get('error')

      if (errorParam) {
        // OAuth failed
        setError(getErrorMessage(errorParam))
        setTimeout(() => {
          router.push('/login')
        }, 3000)
        return
      }

      if (accessToken && refreshToken) {
        // Save tokens
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('refresh_token', refreshToken)
        }

        // Update auth context if available
        if (setTokens) {
          setTokens(accessToken, refreshToken)
        }

        // Redirect to dashboard
        router.push('/dashboard')
      } else {
        setError('Invalid OAuth response - missing tokens')
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      }
    }

    handleCallback()
  }, [searchParams, router, setTokens])

  const getErrorMessage = (errorCode: string): string => {
    const errorMessages: Record<string, string> = {
      unsupported_provider: 'OAuth provider not supported',
      oauth_failed: 'OAuth authentication failed',
      account_inactive: 'Your account is inactive',
    }
    return errorMessages[errorCode] || 'OAuth authentication failed'
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
          <div className="mb-4 flex justify-center">
            <div className="rounded-full bg-red-100 p-3">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
          </div>
          <h2 className="mb-2 text-center text-xl font-semibold text-gray-900">
            Authentication Failed
          </h2>
          <p className="mb-4 text-center text-gray-600">{error}</p>
          <p className="text-center text-sm text-gray-500">
            Redirecting to login page...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        <div className="mb-4 flex justify-center">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-lime-600"></div>
        </div>
        <h2 className="mb-2 text-center text-xl font-semibold text-gray-900">
          Completing Sign In
        </h2>
        <p className="text-center text-gray-600">
          Please wait while we sign you in...
        </p>
      </div>
    </div>
  )
}

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        <div className="mb-4 flex justify-center">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-lime-600"></div>
        </div>
        <h2 className="mb-2 text-center text-xl font-semibold text-gray-900">
          Loading
        </h2>
        <p className="text-center text-gray-600">Please wait...</p>
      </div>
    </div>
  )
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <OAuthCallbackContent />
    </Suspense>
  )
}
