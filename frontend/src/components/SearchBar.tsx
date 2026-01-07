'use client'

import { useState } from 'react'
import { Input } from './ui/input'
import { Search, X } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onClear: () => void
}

export default function SearchBar({
  value,
  onChange,
  onClear,
}: SearchBarProps) {
  const [inputValue, setInputValue] = useState(value)

  const handleChange = (newValue: string) => {
    setInputValue(newValue)
    onChange(newValue)
  }

  return (
    <div className="relative">
      <Search className="absolute top-2.5 left-3 h-4 w-4 text-gray-400 dark:text-gray-500" />
      <Input
        type="text"
        value={inputValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="Search tasks..."
        className="border border-gray-200 bg-white pr-10 pl-10 dark:border-neutral-700 dark:bg-neutral-800/80"
        aria-label="Search tasks"
      />
      {inputValue && (
        <button
          onClick={() => {
            setInputValue('')
            onClear()
          }}
          className="absolute top-2.5 right-3 text-gray-400 transition-colors hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-300"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
