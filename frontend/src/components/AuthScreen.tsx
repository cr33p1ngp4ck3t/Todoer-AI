'use client'

import { Check, Github, Sparkles } from 'lucide-react'
import Brand from './Brand'
import ThemeToggle from './ThemeToggle'
import { Button } from './ui/button'

export function AuthScreen({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-shell">
      <aside className="auth-story">
        <Brand />
        <div className="auth-story-content">
          <h1>
            A little more clarity.
            <br />A lot less busywork.
          </h1>
          <p>
            A thoughtful space for your tasks, your ideas, and the people you
            work with. Make a plan. Move it forward.
          </p>
          <div className="auth-preview" aria-label="Example task list">
            <div className="auth-preview-title">
              <Sparkles size={15} /> From a thought to a plan
            </div>
            <div className="auth-preview-row">
              <Check size={14} className="text-primary" />
              <span className="text-text-muted line-through">
                Gather the ideas
              </span>
            </div>
            <div className="auth-preview-row">
              <span className="auth-preview-circle" />
              Make room for what matters<small>Today</small>
            </div>
            <div className="auth-preview-row">
              <span className="auth-preview-circle" />
              Take the next small step<small>Tomorrow</small>
            </div>
          </div>
        </div>
        <p className="auth-footer">Your plans. Your pace.</p>
      </aside>
      <main className="auth-main">
        <Brand className="auth-mobile-brand" />
        <div className="auth-theme">
          <ThemeToggle />
        </div>
        <div className="auth-form">{children}</div>
      </main>
    </div>
  )
}

export function SocialLogin() {
  function signIn(provider: string) {
    const base = process.env.NEXT_PUBLIC_API_URL || '/api'
    window.location.href = new URL(
      `${base}/auth/oauth/${provider}`,
      window.location.origin
    ).href
  }
  return (
    <>
      <div className="auth-social">
        <Button
          variant="outline"
          className="h-10 w-full"
          onClick={() => signIn('google')}
        >
          <span className="font-bold" aria-hidden="true">
            G
          </span>{' '}
          Continue with Google
        </Button>
        <Button
          variant="outline"
          className="h-10 w-full"
          onClick={() => signIn('github')}
        >
          <Github size={16} /> Continue with GitHub
        </Button>
      </div>
      <div className="auth-divider">Or continue with email</div>
    </>
  )
}
