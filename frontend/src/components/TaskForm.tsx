'use client'

import { useEffect, useState } from 'react'
import { Sparkles, Loader2, ListChecks, X, Plus } from 'lucide-react'
import {
  api,
  type TaskCreate,
  type Project,
  type ProjectMember,
  type Priority,
  type Recurrence,
} from '../services/api'
import { toLocalDateTime, toUtcDateTime } from '../lib/task-dates'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { DialogTitle, DialogDescription } from './ui/dialog'
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from './ui/select'

export interface TaskCreateProps {
  onCreate: (task: TaskCreate) => Promise<void> | void
  creating?: boolean
  projects?: Project[]
  selectedProjectId?: string | null
  members?: ProjectMember[]
  initialText?: string
  onBusyChange?: (busy: boolean) => void
}

export default function TaskForm({
  onCreate,
  creating = false,
  projects = [],
  selectedProjectId = null,
  members = [],
  initialText = '',
  onBusyChange,
}: TaskCreateProps) {
  const [mode, setMode] = useState<'manual' | 'ai'>('ai')
  const [smartText, setSmartText] = useState(initialText)
  const [parsing, setParsing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<Priority>('medium')
  const [dueDate, setDueDate] = useState('')
  const [recurrence, setRecurrence] = useState<Recurrence | ''>('')
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone
  )
  const [projectId, setProjectId] = useState(selectedProjectId || '')
  const [projectMembers, setProjectMembers] = useState(members)
  const [loadingMembers, setLoadingMembers] = useState(false)
  const [assigneeId, setAssigneeId] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const busy = parsing || saving || creating || loadingMembers

  useEffect(() => {
    onBusyChange?.(busy)
  }, [busy, onBusyChange])

  async function changeProject(value: string) {
    setProjectId(value === 'personal' ? '' : value)
    setAssigneeId('')
    setProjectMembers([])
    setError('')
    if (value === 'personal') return
    setLoadingMembers(true)
    try {
      setProjectMembers((await api.projects.get(value)).members)
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not load project members'
      )
    } finally {
      setLoadingMembers(false)
    }
  }

  async function parse(event: React.FormEvent) {
    event.preventDefault()
    if (!smartText.trim() || busy) return
    setParsing(true)
    setError('')
    try {
      const draft = await api.chat.smartParse(smartText)
      setTitle(draft.title)
      setDescription(draft.description || '')
      setPriority(draft.priority || 'medium')
      setDueDate(toLocalDateTime(draft.due_date))
      setRecurrence(draft.recurrence || '')
      setTimezone(
        draft.recurrence_timezone ||
          Intl.DateTimeFormat().resolvedOptions().timeZone
      )
      setTags(draft.tags || [])
      setNotice(
        draft.warnings?.length
          ? draft.warnings.join(' ')
          : 'Draft ready. Review the details before creating your task.'
      )
      setMode('manual')
    } catch (cause) {
      setTitle(smartText.trim().slice(0, 255))
      setDescription('')
      setDueDate('')
      setRecurrence('')
      setTags([])
      setNotice(
        'AI drafting is unavailable. Your text is preserved; review the details below.'
      )
      setError(cause instanceof Error ? cause.message : 'Could not draft task')
      setMode('manual')
    } finally {
      setParsing(false)
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!title.trim() || busy) return
    setSaving(true)
    setError('')
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim() || null,
        priority,
        due_date: toUtcDateTime(dueDate),
        recurrence: recurrence || null,
        recurrence_timezone: timezone,
        project_id: projectId || null,
        assignee_id: assigneeId || null,
        tags,
      })
      setTitle('')
      setDescription('')
      setPriority('medium')
      setDueDate('')
      setRecurrence('')
      setAssigneeId('')
      setTags([])
      setTagInput('')
      setSmartText('')
      setNotice('')
      setMode('ai')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not create task')
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
    <div className="task-editor">
      <DialogTitle>Create New Task</DialogTitle>
      <DialogDescription>
        Turn an idea into a clear next step.
      </DialogDescription>
      <div className="editor-tabs" aria-label="Task entry mode">
        <button
          type="button"
          aria-pressed={mode === 'ai'}
          onClick={() => setMode('ai')}
          disabled={busy}
        >
          <Sparkles size={15} /> AI Smart
        </button>
        <button
          type="button"
          aria-pressed={mode === 'manual'}
          onClick={() => setMode('manual')}
          disabled={busy}
        >
          <ListChecks size={15} /> Manual
        </button>
      </div>
      {mode === 'ai' ? (
        <form onSubmit={parse}>
          <label className="field-label" htmlFor="smart-text">
            What needs to get done?
          </label>
          <textarea
            id="smart-text"
            className="field-textarea"
            value={smartText}
            onChange={(event) => setSmartText(event.target.value)}
            rows={5}
            maxLength={4000}
            required
            placeholder="Prepare the launch brief tomorrow at 10am, high priority, #work"
            disabled={busy}
          />
          <p className="editor-note">
            AI drafts the details. You review and confirm before anything is
            saved.
          </p>
          <div className="editor-footer">
            <Button type="submit" disabled={!smartText.trim() || busy}>
              {parsing ? <Loader2 className="animate-spin" /> : <Sparkles />}
              {parsing ? 'Drafting...' : 'Smart Parse'}
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={submit}>
          {notice ? (
            <p className="editor-note" role="status">
              {notice}
            </p>
          ) : null}
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="form-grid">
            <div className="col-span-full">
              <label className="field-label" htmlFor="title">
                Title
              </label>
              <Input
                id="title"
                className="field-input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                maxLength={255}
                disabled={busy}
                placeholder="What needs to be done?"
              />
            </div>
            <div className="col-span-full">
              <label className="field-label" htmlFor="description">
                Description
              </label>
              <textarea
                id="description"
                className="field-textarea"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={2}
                maxLength={1000}
                disabled={busy}
                placeholder="Add context, links, or a few notes"
              />
            </div>
            <div>
              <label className="field-label" htmlFor="priority">
                Priority
              </label>
              <Select
                value={priority}
                onValueChange={(value) => setPriority(value as Priority)}
                disabled={busy}
              >
                <SelectTrigger id="priority" className="field-select">
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
              <label className="field-label" htmlFor="due_date">
                Due Date
              </label>
              <Input
                id="due_date"
                className="field-input"
                type="datetime-local"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                required={!!recurrence}
                disabled={busy}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="recurrence">
                Repeat
              </label>
              <Select
                value={recurrence || 'none'}
                onValueChange={(value) =>
                  setRecurrence(value === 'none' ? '' : (value as Recurrence))
                }
                disabled={busy}
              >
                <SelectTrigger id="recurrence" className="field-select">
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
            <div>
              <label className="field-label" htmlFor="project">
                Project
              </label>
              <Select
                value={projectId || 'personal'}
                onValueChange={changeProject}
                disabled={busy}
              >
                <SelectTrigger id="project" className="field-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="personal">Personal tasks</SelectItem>
                  {projects
                    .filter((project) => project.role !== 'viewer')
                    .map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            {projectId ? (
              <div className="col-span-full">
                <label className="field-label" htmlFor="assignee">
                  Assignee
                </label>
                <Select
                  value={assigneeId || 'none'}
                  onValueChange={(value) =>
                    setAssigneeId(value === 'none' ? '' : value)
                  }
                  disabled={busy}
                >
                  <SelectTrigger id="assignee" className="field-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Unassigned</SelectItem>
                    {projectMembers
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
              <label className="field-label" htmlFor="tags">
                Tags
              </label>
              <div className="tag-entry">
                <Input
                  id="tags"
                  className="field-input"
                  value={tagInput}
                  onChange={(event) => setTagInput(event.target.value)}
                  maxLength={50}
                  disabled={busy}
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
                  disabled={busy || !tagInput.trim()}
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
                      disabled={busy}
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
              Repeats in {timezone}. Completing this task creates its next
              occurrence.
            </p>
          ) : null}
          <div className="editor-footer">
            <Button
              type="button"
              variant="outline"
              onClick={() => setMode('ai')}
              disabled={busy}
            >
              Back to AI
            </Button>
            <Button type="submit" disabled={!title.trim() || busy}>
              {saving || creating ? <Loader2 className="animate-spin" /> : null}
              {saving || creating ? 'Creating...' : 'Create Task'}
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}
