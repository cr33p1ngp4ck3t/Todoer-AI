'use client'

import { useState } from 'react'
import { Task } from '../services/api'
import { Check, Edit, Trash2, Loader2, Calendar } from 'lucide-react'
import { Badge } from './ui/badge'

interface TaskItemProps {
  task: Task
  onStatusToggle: (id: string) => void
  onEdit: (id: string) => void
  onDelete: (id: string) => void
}

export default function TaskItem({
  task,
  onStatusToggle,
  onEdit,
  onDelete,
}: TaskItemProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [isToggling, setIsToggling] = useState(false)
  const isCompleted = task.status === 'completed'

  // Check if task is overdue
  const isOverdue = task.due_date && !isCompleted && new Date(task.due_date) < new Date()
  const isDueSoon = task.due_date && !isCompleted && !isOverdue &&
    new Date(task.due_date) < new Date(Date.now() + 24 * 60 * 60 * 1000) // within 24 hours

  // Format due date for display
  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)

    const isToday = date.toDateString() === now.toDateString()
    const isTomorrow = date.toDateString() === tomorrow.toDateString()

    if (isToday) {
      return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    }
    if (isTomorrow) {
      return `Tomorrow at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    }
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const handleDelete = async () => {
    if (isDeleting) return
    setIsDeleting(true)
    try {
      await onDelete(task.id)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleToggle = async () => {
    if (isToggling) return
    setIsToggling(true)
    try {
      await onStatusToggle(task.id)
    } finally {
      setIsToggling(false)
    }
  }

  const priorityBadgeVariant =
    task.priority === 'high'
      ? 'destructive'
      : task.priority === 'medium'
        ? 'default'
        : 'secondary'

  return (
    <li
      className={`rounded-lg border border-border bg-card p-4 shadow-sm transition-all ${
        isCompleted ? 'opacity-60' : 'hover:shadow-md'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Status Checkbox */}
        <button
          onClick={handleToggle}
          disabled={isToggling}
          aria-label={`Mark task ${task.title} as ${isCompleted ? 'pending' : 'completed'}`}
          className={`flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center rounded border-2 transition-colors ${
            isCompleted
              ? 'border-primary bg-primary text-primary-foreground'
              : 'border-border hover:border-muted-foreground'
          } ${isToggling ? 'opacity-50' : ''}`}
        >
          {isToggling ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            isCompleted && <Check className="h-3 w-3" />
          )}
        </button>

        {/* Task Content */}
        <div className="min-w-0 flex-1">
          <div
            className={`font-medium ${isCompleted ? 'text-text-muted line-through' : 'text-foreground'}`}
          >
            {task.title}
          </div>

          {task.description && (
            <p className="mt-1 text-sm text-text-secondary">
              {task.description}
            </p>
          )}

          {/* Due Date */}
          {task.due_date && (
            <div
              className={`mt-2 flex items-center gap-1 text-xs ${
                isOverdue
                  ? 'text-destructive font-medium'
                  : isDueSoon
                    ? 'text-warning font-medium'
                    : 'text-text-muted'
              }`}
            >
              <Calendar className="h-3 w-3" />
              <span>{isOverdue ? 'Overdue: ' : ''}{formatDueDate(task.due_date)}</span>
            </div>
          )}

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {task.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="border border-border text-xs"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Priority Badge */}
        <Badge
          variant={priorityBadgeVariant}
          className={`capitalize ${
            priorityBadgeVariant === 'default'
              ? 'bg-priority-medium'
              : priorityBadgeVariant === 'secondary'
                ? 'bg-priority-low'
                : 'bg-priority-high'
          }`}
        >
          {task.priority}
        </Badge>

        {/* Actions */}
        <div className="ml-2 flex items-center justify-end gap-2">
          <button
            onClick={() => onEdit(task.id)}
            disabled={isDeleting || isToggling}
            className="rounded p-2 text-text-secondary transition-colors hover:bg-surface-hover hover:text-foreground disabled:opacity-50"
            aria-label={`Edit task ${task.title}`}
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting || isToggling}
            className="rounded p-2 text-text-secondary transition-colors hover:bg-destructive-light hover:text-destructive disabled:opacity-50"
            aria-label={`Delete task ${task.title}`}
          >
            {isDeleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </li>
  )
}
