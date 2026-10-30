'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Loader2, ArrowRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { AuthScreen, SocialLogin } from '../../components/AuthScreen'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (loading) return
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : 'Unable to sign in. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthScreen>
      <h2>Sign in to your account</h2>
      <p className="auth-subtitle">Welcome back. Pick up where you left off.</p>
      <SocialLogin />
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div>
          <label className="field-label" htmlFor="email">
            Email address
          </label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="field-label" htmlFor="password">
            Password
          </label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="Your password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button type="submit" className="h-11 w-full" disabled={loading}>
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <ArrowRight size={16} />
          )}
          {loading ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <p className="mt-7 text-center text-xs text-text-secondary">
        New here?{' '}
        <Link href="/register" className="auth-link">
          Create a new account
        </Link>
      </p>
    </AuthScreen>
  )
}
