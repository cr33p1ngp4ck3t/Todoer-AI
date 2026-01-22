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
      <Search className="absolute top-2.5 left-3 h-4 w-4 text-text-muted" />
      <Input
        type="text"
        value={inputValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="Search tasks..."
        className="border border-border bg-card pr-10 pl-10"
        aria-label="Search tasks"
      />
      {inputValue && (
        <button
          onClick={() => {
            setInputValue('')
            onClear()
          }}
          className="absolute top-2.5 right-3 text-text-muted transition-colors hover:text-foreground"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
