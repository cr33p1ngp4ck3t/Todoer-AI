'use client'

import { useRef, useState } from 'react'
import { Download, Upload, Loader2 } from 'lucide-react'
import { api, type TaskBackup } from '../services/api'
import { Button } from './ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog'

export default function WorkspaceBackup({
  onClose,
  onImported,
}: {
  onClose: () => void
  onImported: () => Promise<void>
}) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function exportTasks() {
    setBusy(true)
    setError('')
    try {
      const data = await api.tasks.export()
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      )
      const link = document.createElement('a')
      link.href = url
      link.download = `todoer-backup-${new Date().toISOString().slice(0, 10)}.json`
      link.click()
      URL.revokeObjectURL(url)
      setNotice(`Exported ${data.tasks.length} personal tasks.`)
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Export failed.')
    } finally {
      setBusy(false)
    }
  }

  async function importTasks(file?: File) {
    if (!file) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      if (file.size > 20_000_000)
        throw new Error('Choose a JSON backup smaller than 20 MB.')
      const backup: TaskBackup = JSON.parse(await file.text())
      if (backup?.version !== 1 || !Array.isArray(backup.tasks))
        throw new Error('This file is not a Todoer version 1 backup.')
      const result = await api.tasks.import(backup)
      setNotice(
        `Imported ${result.imported} tasks. Skipped ${result.skipped} duplicates.`
      )
      await onImported()
    } catch (failure) {
      setError(
        failure instanceof SyntaxError
          ? 'This file is not valid JSON.'
          : failure instanceof Error
            ? failure.message
            : 'Import failed.'
      )
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Your task backups</DialogTitle>
          <DialogDescription>
            Keep a copy of your plans, or bring them back.
          </DialogDescription>
        </DialogHeader>
        <p className="workspace-note">
          Backups include personal tasks, deadlines, tags, and repeat schedules.
          Shared project tasks stay in their project. Imports add tasks and skip
          previously imported IDs; existing tasks are preserved.
        </p>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <p className="editor-note" role="status">
            {notice}
          </p>
        )}
        <div className="backup-actions">
          <Button disabled={busy} onClick={exportTasks}>
            {busy ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Download size={14} />
            )}
            Export JSON
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => input.current?.click()}
          >
            <Upload size={14} />
            Import JSON
          </Button>
        </div>
        <input
          ref={input}
          className="sr-only"
          type="file"
          accept="application/json,.json"
          aria-label="Task backup file"
          onChange={(event) => importTasks(event.target.files?.[0])}
        />
      </DialogContent>
    </Dialog>
  )
}
