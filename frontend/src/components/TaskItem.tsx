'use client'

import { useState } from 'react'
import {
  Check,
  Pencil,
  Trash2,
  Loader2,
  CalendarDays,
  Repeat2,
  UserRound,
} from 'lucide-react'
import type { Task } from '../services/api'
import { parseTaskDate } from '../lib/task-dates'

interface TaskItemProps {
  task: Task
  onStatusToggle: (id: string) => Promise<void>
  onEdit: (id: string) => void
  onDelete: (id: string) => Promise<void>
  readOnly?: boolean
  assigneeName?: string
  now?: Date
}

export default function TaskItem({
  task,
  onStatusToggle,
  onEdit,
  onDelete,
  readOnly = false,
  assigneeName,
  now = new Date(),
}: TaskItemProps) {
  const [busy, setBusy] = useState(false)
  const completed = task.status === 'completed'
  const deadline = task.due_date ? parseTaskDate(task.due_date) : null
  const overdue = deadline && !completed && deadline.getTime() < now.getTime()
  const dateText = deadline?.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })

  async function run(action: () => Promise<void>) {
    if (busy) return
    setBusy(true)
    try {
      await action()
    } catch {
      /* The dashboard displays the request error. */
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className={`task-row ${completed ? 'completed' : ''}`}>
      <button
        className={`task-check ${completed ? 'checked' : ''}`}
        aria-label={`Mark task ${task.title} as ${completed ? 'pending' : 'completed'}`}
        disabled={busy || readOnly}
        onClick={() => run(() => onStatusToggle(task.id))}
      >
        {busy ? (
          <Loader2 size={12} className="animate-spin" />
        ) : completed ? (
          <Check size={12} strokeWidth={3} />
        ) : null}
      </button>
      <div className="task-text">
        <h3 className="task-title">{task.title}</h3>
        {task.description && (
          <p className="task-description">{task.description}</p>
        )}
        <div className="task-meta">
          {deadline && (
            <span className={overdue ? 'overdue' : ''}>
              <CalendarDays size={11} />
              {overdue ? `Overdue: ${dateText}` : dateText}
            </span>
          )}
          {task.recurrence && (
            <span>
              <Repeat2 size={11} />
              {task.recurrence}
            </span>
          )}
          {assigneeName && (
            <span>
              <UserRound size={11} />
              {assigneeName}
            </span>
          )}
          {task.tags?.map((tag) => (
            <span key={tag} className="task-tag">
              {tag}
            </span>
          ))}
        </div>
      </div>
      <span className={`task-priority ${task.priority}`}>{task.priority}</span>
      {!readOnly && (
        <div className="task-actions">
          <button
            className="icon-button"
            aria-label={`Edit task ${task.title}`}
            disabled={busy}
            onClick={() => onEdit(task.id)}
          >
            <Pencil size={13} />
          </button>
          <button
            className="icon-button danger"
            aria-label={`Delete task ${task.title}`}
            disabled={busy}
            onClick={() => run(() => onDelete(task.id))}
          >
            <Trash2 size={13} />
          </button>
        </div>
      )}
    </article>
  )
}
