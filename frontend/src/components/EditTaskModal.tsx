'use client'

import { useState } from 'react'
import { Loader2, Plus, X } from 'lucide-react'
import type {
  Task,
  TaskUpdate,
  ProjectMember,
  Priority,
  Recurrence,
} from '../services/api'
import { toLocalDateTime, toUtcDateTime } from '../lib/task-dates'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog'
import { Input } from './ui/input'
import { Button } from './ui/button'
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from './ui/select'

export interface EditTaskModalProps {
  task: Task
  onSave: (id: string, updates: TaskUpdate) => Promise<void> | void
  onClose: () => void
  members?: ProjectMember[]
}

export default function EditTaskModal({
  task,
  onSave,
  onClose,
  members = [],
}: EditTaskModalProps) {
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description || '')
  const [priority, setPriority] = useState<Priority>(task.priority)
  const [dueDate, setDueDate] = useState(toLocalDateTime(task.due_date))
  const [recurrence, setRecurrence] = useState<Recurrence | ''>(
    task.recurrence || ''
  )
  const [assigneeId, setAssigneeId] = useState(task.assignee_id || '')
  const [tags, setTags] = useState(task.tags || [])
  const [tagInput, setTagInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!title.trim() || saving) return
    setSaving(true)
    setError('')
    try {
      await onSave(task.id, {
        title: title.trim(),
        description: description.trim() || null,
        priority,
        due_date: toUtcDateTime(dueDate),
        recurrence: recurrence || null,
        recurrence_timezone:
          (task.recurrence ? task.recurrence_timezone : undefined) ||
          Intl.DateTimeFormat().resolvedOptions().timeZone,
        ...(task.project_id ? { assignee_id: assigneeId || null } : {}),
        tags,
      })
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save task')
    } finally {
      setSaving(false)
    }
  }

  function addTag() {
    const tag = tagInput.trim().toLowerCase()
    if (tag && !tags.includes(tag) && tags.length < 20) setTags([...tags, tag])
    setTagInput('')
  }

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open && !saving) onClose()
      }}
    >
      <DialogContent
        className="task-editor sm:max-w-xl"
        showCloseButton={!saving}
        onEscapeKeyDown={(event) => {
          if (saving) event.preventDefault()
        }}
        onPointerDownOutside={(event) => {
          if (saving) event.preventDefault()
        }}
      >
        <DialogHeader>
          <DialogTitle>Edit Task</DialogTitle>
          <DialogDescription>
            Make room for what matters. Update the details below.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit}>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="form-grid">
            <div className="col-span-full">
              <label className="field-label" htmlFor="edit-title">
                Title
              </label>
              <Input
                id="edit-title"
                className="field-input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                maxLength={255}
                required
                disabled={saving}
              />
            </div>
            <div className="col-span-full">
              <label className="field-label" htmlFor="edit-description">
                Description
              </label>
              <textarea
                id="edit-description"
                className="field-textarea"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                maxLength={1000}
                disabled={saving}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="edit-priority">
                Priority
              </label>
              <Select
                value={priority}
                onValueChange={(value) => setPriority(value as Priority)}
                disabled={saving}
              >
                <SelectTrigger id="edit-priority" className="field-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="field-label" htmlFor="edit-due-date">
                Due Date
              </label>
              <Input
                id="edit-due-date"
                className="field-input"
                type="datetime-local"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                required={!!recurrence}
                disabled={saving}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="edit-recurrence">
                Repeat
              </label>
              <Select
                value={recurrence || 'none'}
                onValueChange={(value) =>
                  setRecurrence(value === 'none' ? '' : (value as Recurrence))
                }
                disabled={saving}
              >
                <SelectTrigger id="edit-recurrence" className="field-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Does not repeat</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {task.project_id ? (
              <div>
                <label className="field-label" htmlFor="edit-assignee">
                  Assignee
                </label>
                <Select
                  value={assigneeId || 'none'}
                  onValueChange={(value) =>
                    setAssigneeId(value === 'none' ? '' : value)
                  }
                  disabled={saving}
                >
                  <SelectTrigger id="edit-assignee" className="field-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Unassigned</SelectItem>
                    {members
                      .filter((member) => member.accepted)
                      .map((member) => (
                        <SelectItem key={member.user_id} value={member.user_id}>
                          {member.username}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}
            <div className="col-span-full">
              <label className="field-label" htmlFor="edit-tags">
                Tags
              </label>
              <div className="tag-entry">
                <Input
                  id="edit-tags"
                  className="field-input"
                  value={tagInput}
                  onChange={(event) => setTagInput(event.target.value)}
                  maxLength={50}
                  disabled={saving}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault()
                      addTag()
                    }
                  }}
                  placeholder="Add a tag"
                />
                <Button
                  type="button"
                  variant="outline"
                  aria-label="Add tag"
                  onClick={addTag}
                  disabled={saving || !tagInput.trim()}
                >
                  <Plus />
                </Button>
              </div>
              <div className="tag-list">
                {tags.map((tag) => (
                  <span className="tag-chip" key={tag}>
                    {tag}
                    <button
                      type="button"
                      aria-label={`Remove tag ${tag}`}
                      onClick={() =>
                        setTags(tags.filter((item) => item !== tag))
                      }
                      disabled={saving}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
          {recurrence ? (
            <p className="editor-note">
              Repeats in{' '}
              {(task.recurrence ? task.recurrence_timezone : undefined) ||
                Intl.DateTimeFormat().resolvedOptions().timeZone}
              .
            </p>
          ) : null}
          <div className="editor-footer">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving || !title.trim()}>
              {saving ? <Loader2 className="animate-spin" /> : null}
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
