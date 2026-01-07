'use client'

import { useState } from 'react'
import { Task } from '../services/api'
import { Check, Edit, Trash2, Loader2 } from 'lucide-react'
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
      className={`rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all dark:border-neutral-700 dark:bg-neutral-800/80 ${
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
              ? 'bg-lime-700 text-white dark:border-neutral-500 dark:bg-lime-600'
              : 'border-gray-300 dark:border-neutral-700 dark:hover:border-neutral-500'
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
            className={`font-medium ${isCompleted ? 'text-gray-400 line-through dark:text-gray-500' : 'text-gray-900 dark:text-gray-100'}`}
          >
            {task.title}
          </div>

          {task.description && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {task.description}
            </p>
          )}

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {task.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="border border-gray-200 text-xs dark:border-neutral-700"
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
              ? 'bg-lime-500'
              : priorityBadgeVariant === 'secondary'
                ? 'bg-lime-400'
                : 'bg-lime-700'
          }`}
        >
          {task.priority}
        </Badge>

        {/* Actions */}
        <div className="ml-2 flex items-center justify-end gap-2">
          <button
            onClick={() => onEdit(task.id)}
            disabled={isDeleting || isToggling}
            className="rounded p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 dark:text-gray-400 dark:hover:bg-neutral-700 dark:hover:text-gray-100"
            aria-label={`Edit task ${task.title}`}
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting || isToggling}
            className="rounded p-2 text-gray-500 transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:text-gray-400 dark:hover:bg-red-900/20 dark:hover:text-red-400"
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
