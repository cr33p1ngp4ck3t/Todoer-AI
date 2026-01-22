'use client'

import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from './ui/select'

interface FilterControlsProps {
  statusFilter: string
  priorityFilter: string
  onStatusChange: (status: string) => void
  onPriorityChange: (priority: string) => void
}

export default function FilterControls({
  statusFilter,
  priorityFilter,
  onStatusChange,
  onPriorityChange,
}: FilterControlsProps) {
  return (
    <div className="flex flex-wrap gap-4">
      {/* Status Dropdown */}
      <div className="min-w-40 flex-1">
        <label className="mb-1 block text-sm font-medium text-foreground">
          Status
        </label>
        <Select value={statusFilter} onValueChange={onStatusChange}>
          <SelectTrigger className="w-full border border-border bg-card">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Priority Dropdown */}
      <div className="min-w-40 flex-1">
        <label className="mb-1 block text-sm font-medium text-foreground">
          Priority
        </label>
        <Select value={priorityFilter} onValueChange={onPriorityChange}>
          <SelectTrigger className="w-full border border-border bg-card">
            <SelectValue placeholder="All priorities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
