'use client'

import { useState, useEffect } from 'react'
import { Task, TaskUpdate } from '@/services/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
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
import { Badge } from './ui/badge'
import { X, Plus, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EditTaskModalProps {
  task: Task
  onSave: (id: string, updates: TaskUpdate) => void
  onClose: () => void
}

export default function EditTaskModal({
  task,
  onSave,
  onClose,
}: EditTaskModalProps) {
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description || '')
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>(
    task.priority as 'low' | 'medium' | 'high'
  )
  const [tags, setTags] = useState<string[]>(task.tags || [])
  const [tagInput, setTagInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setLoading(true)
    try {
      onSave(task.id, {
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        tags: tags.length > 0 ? tags : undefined,
      })
    } finally {
      setLoading(false)
    }
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Task</DialogTitle>
          <DialogDescription>
            Make changes to your task below.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          {/* Title Input */}
          <div className="mb-4">
            <label
              htmlFor="edit-title"
              className="mb-1 block text-sm font-medium"
            >
              Title <span className="text-destructive">*</span>
            </label>
            <Input
              id="edit-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done?"
              required
              autoFocus
            />
          </div>

          {/* Description Input */}
          <div className="mb-4">
            <label
              htmlFor="edit-description"
              className="mb-1 block text-sm font-medium"
            >
              Description
            </label>
            <textarea
              id="edit-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more details (optional)..."
              rows={3}
              className={cn(
                'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input shadow-xs min-w-full rounded-md bg-transparent px-3 py-2 text-sm outline-none transition-[color,box-shadow] disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700',
                'focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]'
              )}
            />
          </div>

          {/* Priority Selector */}
          <div className="mb-4">
            <label
              htmlFor="edit-priority"
              className="mb-1 block text-sm font-medium"
            >
              Priority
            </label>
            <Select
              value={priority}
              onValueChange={(v) => setPriority(v as 'low' | 'medium' | 'high')}
            >
              <SelectTrigger className="w-full">
                <SelectValue className="" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tags Input */}
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium">Tags</label>
            <div className="flex gap-2">
              <Input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type and press Enter..."
                className="flex-1"
              />
              <Button type="button" onClick={addTag} size="sm">
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* Tags Display */}
            {tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
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
          </div>

          {/* Status Badge */}
          <div className="mb-6">
            <span className="text-muted-foreground text-sm">
              Status:{' '}
              <span className="font-medium capitalize">{task.status}</span>
            </span>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !title.trim()}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
