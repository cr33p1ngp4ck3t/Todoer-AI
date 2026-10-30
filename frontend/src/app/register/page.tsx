'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Loader2, ArrowRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { AuthScreen, SocialLogin } from '../../components/AuthScreen'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (loading) return
    setError('')
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await register(username, email, password)
      router.push('/dashboard')
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : 'Unable to create your account. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthScreen>
      <h2>Create your account</h2>
      <p className="auth-subtitle">
        A fresh space for everything you want to do.
      </p>
      <SocialLogin />
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div>
          <label className="field-label" htmlFor="username">
            Username
          </label>
          <Input
            id="username"
            autoComplete="username"
            placeholder="Your name"
            required
            minLength={3}
            maxLength={50}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
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
        <div className="form-grid">
          <div>
            <label className="field-label" htmlFor="password">
              Password
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="field-label" htmlFor="confirm-password">
              Confirm password
            </label>
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
        </div>
        <Button type="submit" className="h-11 w-full" disabled={loading}>
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <ArrowRight size={16} />
          )}
          {loading ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="mt-7 text-center text-xs text-text-secondary">
        Already have an account?{' '}
        <Link href="/login" className="auth-link">
          Sign in
        </Link>
      </p>
    </AuthScreen>
  )
}
