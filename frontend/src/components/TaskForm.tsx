'use client'

import { useState } from 'react'
import { api } from '../services/api'
import { Sparkles, Loader2, ListChecks, X } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from './ui/select'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { DialogTitle, DialogDescription } from './ui/dialog'
import { Badge } from './ui/badge'
import { cn } from '@/lib/utils'

export interface TaskCreateProps {
  onCreate: (task: {
    title: string
    description?: string
    priority: 'low' | 'medium' | 'high'
    due_date?: string
    tags?: string[]
  }) => void
  creating?: boolean
}

export default function TaskForm({
  onCreate,
  creating = false,
}: TaskCreateProps) {
  const [mode, setMode] = useState<'manual' | 'ai'>('ai')
  const [smartText, setSmartText] = useState('')
  const [isParsing, setIsParsing] = useState(false)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium')
  const [dueDate, setDueDate] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

  const handleSmartSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!smartText.trim() || isParsing) return

    setIsParsing(true)
    try {
      const parsed = await api.chat.smartParse(smartText)

      // Switch to manual mode with pre-filled values for confirmation
      setTitle(parsed.title || '')
      setDescription(parsed.description || '')
      setPriority((parsed.priority as 'low' | 'medium' | 'high') || 'medium')
      setTags(parsed.tags || [])
      setMode('manual')
    } catch (error) {
      console.error('Failed to parse task:', error)
      // On error, just use the text as title in manual mode
      setTitle(smartText.trim())
      setMode('manual')
    } finally {
      setIsParsing(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    onCreate({
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
      due_date: dueDate || undefined,
      tags: tags.length > 0 ? tags : undefined,
    })

    // Reset form
    setTitle('')
    setDescription('')
    setPriority('medium')
    setDueDate('')
    setTags([])
    setTagInput('')
    setSmartText('')
    setMode('ai')
  }

  const addTag = () => {
    const trimmed = tagInput.trim().toLowerCase()
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed])
    }
    setTagInput('')
  }

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag))
  }

  return (
    <>
      <DialogTitle className="sr-only">Create New Task</DialogTitle>
      <DialogDescription className="sr-only">
        Create a new task using AI smart parsing or manual entry
      </DialogDescription>
      <Card className="border-0 shadow-none">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Create New Task</CardTitle>
            <div className="flex gap-1 rounded-md bg-secondary p-1">
              <Button
                size="sm"
                variant={mode === 'ai' ? 'default' : 'ghost'}
                onClick={() => setMode('ai')}
                className={cn(
                  mode === 'ai' ? 'bg-card/80 shadow-sm' : '',
                  'cursor-pointer'
                )}
              >
                <Sparkles className="h-3.5 w-3.5" />
                AI Smart
              </Button>
              <Button
                size="sm"
                variant={mode === 'manual' ? 'default' : 'ghost'}
                onClick={() => setMode('manual')}
                className={cn(
                  mode === 'manual' ? 'bg-card/80 shadow-sm' : '',
                  'cursor-pointer'
                )}
              >
                <ListChecks className="h-3.5 w-3.5" />
                Manual
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {mode === 'ai' ? (
            <form onSubmit={handleSmartSubmit}>
              <div className="mb-4">
                <textarea
                  value={smartText}
                  onChange={(e) => setSmartText(e.target.value)}
                  placeholder="Example: Buy milk tomorrow high priority with #groceries tag..."
                  rows={3}
                  className={cn(
                    'shadow-xs min-w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none transition-[color,box-shadow] selection:bg-primary selection:text-primary-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
                    'focus-visible:ring-[3px]',
                    'aria-invalid:ring-destructive/20 aria-invalid:border-destructive'
                  )}
                  required
                />
                <p className="mt-2 text-xs italic text-muted-foreground">
                  Wait, I&apos;ll extract the details for you to review.
                </p>
              </div>
              <Button
                type="submit"
                className="w-full bg-secondary"
                disabled={!smartText.trim() || isParsing}
              >
                {isParsing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Smart Parse
                  </>
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSubmit}>
              {/* Title Input */}
              <div className="mb-4">
                <label
                  htmlFor="title"
                  className="mb-1 block text-sm font-medium"
                >
                  Title <span className="text-destructive">*</span>
                </label>
                <Input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="What needs to be done?"
                  required
                  className="border border-border"
                />
              </div>

              {/* Description Input */}
              <div className="mb-4">
                <label
                  htmlFor="description"
                  className="mb-1 block text-sm font-medium"
                >
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Add more details (optional)..."
                  rows={2}
                  className={cn(
                    'shadow-xs min-w-full rounded-md bg-transparent px-3 py-2 text-sm outline-none transition-[color,box-shadow] selection:bg-primary selection:text-primary-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
                    'border border-border focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50'
                  )}
                />
              </div>

              <div className="mb-4 grid grid-cols-2 gap-4">
                {/* Priority Selector */}
                <div>
                  <label
                    htmlFor="priority"
                    className="mb-1 block text-sm font-medium"
                  >
                    Priority
                  </label>
                  <Select
                    value={priority}
                    onValueChange={(v) =>
                      setPriority(v as 'low' | 'medium' | 'high')
                    }
                  >
                    <SelectTrigger className="w-full border border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Due Date Picker */}
                <div>
                  <label
                    htmlFor="due_date"
                    className="mb-1 block text-sm font-medium"
                  >
                    Due Date
                  </label>
                  <Input
                    id="due_date"
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="border border-border"
                  />
                </div>
              </div>

              <div className="mb-4">
                {/* Tags Input */}
                <label className="mb-1 block text-sm font-medium">Tags</label>
                <Input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) =>
                    e.key === 'Enter' && (e.preventDefault(), addTag())
                  }
                  placeholder="Add tag and press Enter..."
                  className="border border-border"
                />
              </div>

              {/* Tags Display */}
              {tags.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1 border border-border"
                  type="button"
                  onClick={() => {
                    setMode('ai')
                    setSmartText('')
                  }}
                  disabled={creating || isParsing}
                >
                  Back to AI
                </Button>
                <Button
                  className="flex-1 bg-secondary"
                  type="submit"
                  disabled={!title.trim() || creating}
                >
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Task'
                  )}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </>
  )
}
