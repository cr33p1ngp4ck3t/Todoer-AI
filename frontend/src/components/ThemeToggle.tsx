'use client'

import { useTheme } from 'next-themes'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const current = theme === 'dark' ? 'dark' : 'light'

  return (
    <button
      aria-label="Toggle theme"
      onClick={() => setTheme(current === 'dark' ? 'light' : 'dark')}
      className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border bg-card text-foreground shadow-sm transition-colors duration-300 hover:bg-surface-hover"
    >
      {current === 'dark' ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </button>
  )
}
