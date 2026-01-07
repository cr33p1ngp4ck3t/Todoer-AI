'use client'

import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from './ui/select'

interface SortDropdownProps {
  sortBy: string
  onChange: (sortBy: string) => void
}

export default function SortDropdown({ sortBy, onChange }: SortDropdownProps) {
  return (
    <div className="relative min-w-48">
      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        Sort by
      </label>
      <Select value={sortBy} onValueChange={onChange}>
        <SelectTrigger className="w-full border border-gray-200 bg-white dark:border-neutral-700 dark:bg-neutral-800/80">
          <SelectValue placeholder="Sort by..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created_at">Created (Newest)</SelectItem>
          <SelectItem value="created_at_asc">Created (Oldest)</SelectItem>
          <SelectItem value="priority">Priority (High to Low)</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
