'use client'

import { useState } from 'react'
import { Loader2, UserPlus, X } from 'lucide-react'
import { api, type ProjectDetail } from '../services/api'
import { Button } from './ui/button'
import { Input } from './ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog'

interface Props {
  project: ProjectDetail
  onClose: () => void
  onChange: (project: ProjectDetail) => void
}

export default function ProjectSettings({ project, onClose, onChange }: Props) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'editor' | 'viewer'>('editor')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const owner = project.role === 'owner'

  async function invite(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.projects.invite(project.id, email.trim(), role)
      onChange(await api.projects.get(project.id))
      setEmail('')
      setNotice('Invitation sent. They can accept it in their workspace.')
    } catch (failure) {
      setError(
        failure instanceof Error ? failure.message : 'Unable to invite member.'
      )
    } finally {
      setBusy(false)
    }
  }

  async function remove(userId: string) {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await api.projects.removeMember(project.id, userId)
      onChange(await api.projects.get(project.id))
    } catch (failure) {
      setError(
        failure instanceof Error ? failure.message : 'Unable to remove member.'
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{project.name}</DialogTitle>
          <DialogDescription>
            People, permissions, and shared work.
          </DialogDescription>
        </DialogHeader>
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
        <div>
          {project.members.map((member) => (
            <div key={member.user_id} className="member-row">
              <div className="avatar">
                {member.username.slice(0, 2).toUpperCase()}
              </div>
              <div className="account-info">
                <strong>{member.username}</strong>
                <span>{member.email}</span>
              </div>
              <span className="member-role">
                {member.accepted ? member.role : 'Invited'}
              </span>
              {owner && member.role !== 'owner' && (
                <button
                  className="icon-button danger"
                  disabled={busy}
                  aria-label={`Remove member ${member.username}`}
                  onClick={() => remove(member.user_id)}
                >
                  <X size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
        {owner && (
          <form onSubmit={invite} className="modal-section">
            <h3>Invite someone</h3>
            <p className="workspace-note mb-4">
              Invite an existing Todoer account. Editors can manage tasks;
              viewers can read them.
            </p>
            <label htmlFor="invite-email" className="field-label">
              Email address
            </label>
            <Input
              id="invite-email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="teammate@example.com"
            />
            <div className="editor-footer">
              <select
                className="field-select max-w-32"
                aria-label="Invitation role"
                value={role}
                onChange={(event) =>
                  setRole(event.target.value as 'editor' | 'viewer')
                }
              >
                <option value="editor">Editor</option>
                <option value="viewer">Viewer</option>
              </select>
              <Button type="submit" disabled={busy}>
                {busy ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <UserPlus size={14} />
                )}
                Send invitation
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
