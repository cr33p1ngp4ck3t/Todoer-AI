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
      className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-gray-200 bg-white text-gray-700 shadow-sm transition-colors duration-300 hover:bg-gray-100 dark:dark:border-neutral-700 dark:bg-neutral-800 dark:text-gray-100 dark:hover:bg-neutral-800"
    >
      {current === 'dark' ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </button>
  )
}
