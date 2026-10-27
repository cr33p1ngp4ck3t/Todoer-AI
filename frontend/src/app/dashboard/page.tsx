'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Inbox,
  CalendarDays,
  CheckCheck,
  Plus,
  Search,
  Sparkles,
  ChevronRight,
  Menu,
  LogOut,
  Download,
  Users,
  Repeat2,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type Task,
  type TaskCreate,
  type TaskUpdate,
  type Project,
  type ProjectDetail,
  type Invitation,
} from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import { parseTaskDate } from '../../lib/task-dates'
import Brand from '../../components/Brand'
import ThemeToggle from '../../components/ThemeToggle'
import TaskItem from '../../components/TaskItem'
import TaskForm from '../../components/TaskForm'
import EditTaskModal from '../../components/EditTaskModal'
import ProjectSettings from '../../components/ProjectSettings'
import WorkspaceBackup from '../../components/WorkspaceBackup'
import VoiceCommand from '../../components/VoiceCommand'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../../components/ui/dialog'

type View = 'all' | 'today' | 'completed' | 'recurring'

export default function Dashboard() {
  const router = useRouter()
  const { user, logout, loading: authLoading } = useAuth()
  const [tasks, setTasks] = useState<Task[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [view, setView] = useState<View>('all')
  const [search, setSearch] = useState('')
  const [priority, setPriority] = useState('all')
  const [sort, setSort] = useState('created_at')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [workspaceError, setWorkspaceError] = useState('')
  const [editor, setEditor] = useState<{ text: string } | null>(null)
  const [editorBusy, setEditorBusy] = useState(false)
  const [editing, setEditing] = useState<Task | null>(null)
  const [showProject, setShowProject] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showBackup, setShowBackup] = useState(false)
  const [showInvitations, setShowInvitations] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [projectError, setProjectError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const requestId = useRef(0)
  const editable =
    !projectId || project?.role === 'owner' || project?.role === 'editor'

  const loadWorkspace = useCallback(async () => {
    try {
      const [nextProjects, nextInvitations] = await Promise.all([
        api.projects.list(),
        api.projects.invitations(),
      ])
      setProjects(nextProjects)
      setInvitations(nextInvitations)
      setWorkspaceError('')
    } catch (failure) {
      setWorkspaceError(
        failure instanceof Error ? failure.message : 'Unable to load projects.'
      )
    }
  }, [])

  const loadTasks = useCallback(async () => {
    const id = ++requestId.current
    setLoading(true)
    setLoadError('')
    try {
      const [nextTasks, detail] = await Promise.all([
        api.tasks.list({
          project_id: projectId,
          search: search || undefined,
          priority,
          sort_by: sort,
        }),
        projectId ? api.projects.get(projectId) : Promise.resolve(null),
      ])
      if (id !== requestId.current) return
      setTasks(nextTasks)
      setProject(detail)
    } catch (failure) {
      if (id === requestId.current)
        setLoadError(
          failure instanceof Error ? failure.message : 'Unable to load tasks.'
        )
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [projectId, search, priority, sort])

  const reloadTasks = useRef(loadTasks)
  useEffect(() => {
    reloadTasks.current = loadTasks
  }, [loadTasks])

  useEffect(() => {
    if (!authLoading && !user) router.replace('/login')
  }, [authLoading, user, router])
  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Synchronize the workspace with authenticated API data.
      loadWorkspace()
    }
  }, [user, loadWorkspace])
  useEffect(() => {
    if (!user) return
    const timer = setTimeout(() => loadTasks(), search ? 200 : 0)
    return () => {
      clearTimeout(timer)
      requestId.current += 1
    }
  }, [user, loadTasks, search])

  function navigate(nextView: View, nextProject: string | null = null) {
    setView(nextView)
    setProjectId(nextProject)
    setProject(null)
    setTasks([])
    setSearch('')
    setSidebarOpen(false)
  }

  async function createTask(data: TaskCreate) {
    await api.tasks.create(data)
    setEditorBusy(false)
    setEditor(null)
    await reloadTasks.current()
    toast.success('Task created')
  }
  async function updateTask(id: string, data: TaskUpdate) {
    await api.tasks.update(id, data)
    setEditing(null)
    await reloadTasks.current()
    toast.success('Task updated')
  }
  async function toggleTask(id: string) {
    const task = tasks.find((item) => item.id === id)
    if (!task) return
    try {
      await api.tasks.update(id, {
        status: task.status === 'completed' ? 'pending' : 'completed',
      })
      await reloadTasks.current()
      toast.success(
        task.status === 'completed'
          ? 'Task reopened'
          : task.recurrence
            ? 'Completed. Your next occurrence is ready.'
            : 'Task completed'
      )
    } catch (failure) {
      toast.error(failure instanceof Error ? failure.message : 'Update failed')
      throw failure
    }
  }
  async function deleteTask(id: string) {
    try {
      await api.tasks.delete(id)
      setTasks((previous) => previous.filter((task) => task.id !== id))
      toast.success('Task deleted')
    } catch (failure) {
      toast.error(failure instanceof Error ? failure.message : 'Delete failed')
      throw failure
    }
  }
  async function createProject(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setProjectError('')
    try {
      const created = await api.projects.create(projectName.trim())
      await loadWorkspace()
      navigate('all', created.id)
      setShowProject(false)
      setProjectName('')
    } catch (failure) {
      setProjectError(
        failure instanceof Error ? failure.message : 'Unable to create project.'
      )
    } finally {
      setBusy(false)
    }
  }
  async function acceptInvitation(id: string) {
    setBusy(true)
    setProjectError('')
    try {
      const accepted = await api.projects.accept(id)
      await loadWorkspace()
      navigate('all', accepted.id)
      setShowInvitations(false)
    } catch (failure) {
      setProjectError(
        failure instanceof Error
          ? failure.message
          : 'Unable to accept invitation.'
      )
    } finally {
      setBusy(false)
    }
  }

  if (authLoading || !user)
    return (
      <div className="flex min-h-screen items-center justify-center gap-3 text-text-secondary">
        <Loader2 size={18} className="animate-spin" />
        Opening your workspace…
      </div>
    )

  const now = new Date()
  const today = now.toDateString()
  const pending = tasks.filter((task) => task.status === 'pending')
  const done = tasks.filter((task) => task.status === 'completed')
  const overdue = pending.filter(
    (task) =>
      task.due_date && parseTaskDate(task.due_date).getTime() < now.getTime()
  )
  const dueToday = pending.filter(
    (task) =>
      task.due_date && parseTaskDate(task.due_date).toDateString() === today
  )
  const visible =
    view === 'completed'
      ? done
      : view === 'today'
        ? dueToday
        : view === 'recurring'
          ? tasks.filter((task) => task.recurrence)
          : tasks
  const visiblePending = visible.filter((task) => task.status === 'pending')
  const visibleDone = visible.filter((task) => task.status === 'completed')
  const title = projectId
    ? projects.find((item) => item.id === projectId)?.name || 'Project'
    : view === 'today'
      ? 'Today'
      : view === 'completed'
        ? 'Completed'
        : view === 'recurring'
          ? 'Recurring tasks'
          : 'My Tasks'
  const upcoming = pending
    .filter((task) => task.due_date)
    .sort(
      (a, b) =>
        parseTaskDate(a.due_date!).getTime() -
        parseTaskDate(b.due_date!).getTime()
    )
    .slice(0, 3)
  const members = project?.members.filter((member) => member.accepted) || []
  function taskRow(task: Task) {
    return (
      <TaskItem
        key={task.id}
        task={task}
        onStatusToggle={toggleTask}
        now={now}
        onEdit={(id) =>
          setEditing(tasks.find((item) => item.id === id) || null)
        }
        onDelete={deleteTask}
        readOnly={!editable}
        assigneeName={
          members.find((member) => member.user_id === task.assignee_id)
            ?.username
        }
      />
    )
  }

  return (
    <div className="workspace">
      <button
        className={`sidebar-scrim ${sidebarOpen ? 'open' : ''}`}
        aria-label="Close navigation"
        onClick={() => setSidebarOpen(false)}
      />
      <aside
        className={`workspace-sidebar ${sidebarOpen ? 'open' : ''}`}
        aria-label="Workspace navigation"
      >
        <Brand />
        <div>
          <div className="sidebar-label">Workspace</div>
          <nav>
            <button
              className={`nav-item ${view === 'all' && !projectId ? 'active' : ''}`}
              onClick={() => navigate('all')}
            >
              <Inbox size={16} />
              My tasks
              {!projectId && (
                <span className="nav-count">{pending.length}</span>
              )}
            </button>
            <button
              className={`nav-item ${view === 'today' && !projectId ? 'active' : ''}`}
              onClick={() => navigate('today')}
            >
              <CalendarDays size={16} />
              Today
            </button>
            <button
              className={`nav-item ${view === 'recurring' && !projectId ? 'active' : ''}`}
              onClick={() => navigate('recurring')}
            >
              <Repeat2 size={16} />
              Recurring
            </button>
            <button
              className={`nav-item ${view === 'completed' && !projectId ? 'active' : ''}`}
              onClick={() => navigate('completed')}
            >
              <CheckCheck size={16} />
              Completed
            </button>
          </nav>
        </div>
        <div>
          <div className="sidebar-label">
            Projects
            <button
              className="icon-button h-5 w-5"
              aria-label="Create project"
              onClick={() => {
                setProjectError('')
                setShowProject(true)
              }}
            >
              <Plus size={13} />
            </button>
          </div>
          {projects.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${projectId === item.id ? 'active' : ''}`}
              onClick={() => navigate('all', item.id)}
            >
              <span className="project-dot" />
              <span className="truncate">{item.name}</span>
            </button>
          ))}
          {!projects.length && (
            <button
              className="nav-item text-xs"
              onClick={() => setShowProject(true)}
            >
              <Plus size={14} />
              Start a shared project
            </button>
          )}
          {workspaceError && (
            <button
              className="nav-item text-xs text-destructive"
              onClick={loadWorkspace}
            >
              Retry loading projects
            </button>
          )}
        </div>
        <div className="sidebar-spacer" />
        <div>
          <button
            className="nav-item"
            onClick={() => {
              setProjectError('')
              setShowInvitations(true)
            }}
          >
            <Users size={15} />
            Invitations
            <span className="nav-count">{invitations.length || ''}</span>
          </button>
          <button className="nav-item" onClick={() => setShowBackup(true)}>
            <Download size={15} />
            Import & export
          </button>
        </div>
        <div className="sidebar-hint">
          <strong>One thing at a time.</strong>A clear plan starts with a small
          next step.
        </div>
        <div className="account-row">
          <span className="avatar">
            {user.username.slice(0, 2).toUpperCase()}
          </span>
          <div className="account-info">
            <strong>{user.username}</strong>
            <span>{user.email}</span>
          </div>
          <button
            className="icon-button"
            aria-label="Logout"
            onClick={() => {
              logout()
              router.push('/login')
            }}
          >
            <LogOut size={14} />
          </button>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={18} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={12} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-actions">
            <span className="hidden text-[11px] text-text-muted sm:block">
              {now.toLocaleDateString(undefined, {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
              })}
            </span>
            <ThemeToggle />
          </div>
        </header>
        <main className="workspace-content">
          <div className="workspace-heading">
            <div>
              <h1>{title}</h1>
              <p>
                {projectId
                  ? 'A shared space to keep the work moving.'
                  : view === 'today'
                    ? 'A little focus for the day ahead.'
                    : view === 'completed'
                      ? 'Every small step adds up.'
                      : 'A clear space for what comes next.'}
              </p>
            </div>
            <div className="heading-actions">
              {project && (
                <Button
                  variant="outline"
                  aria-label="Project members"
                  onClick={() => setShowSettings(true)}
                >
                  <Users size={14} />
                  Members
                </Button>
              )}
              {editable && (
                <Button onClick={() => setEditor({ text: '' })}>
                  <Plus size={14} />+ New Task
                </Button>
              )}
            </div>
          </div>
          <div className="workspace-summary">
            <div className="summary-item">
              <strong>{pending.length}</strong>In progress
            </div>
            <div className="summary-item">
              <strong>{dueToday.length}</strong>Due today
            </div>
            <div className={`summary-item ${overdue.length ? 'warning' : ''}`}>
              <strong>{overdue.length}</strong>Overdue
            </div>
            <div className="summary-item">
              <strong>{done.length}</strong>Completed
            </div>
          </div>
          {workspaceError && (
            <div className="form-error" role="alert">
              {workspaceError}{' '}
              <button className="underline" onClick={loadWorkspace}>
                Retry
              </button>
            </div>
          )}
          <div className="workspace-columns">
            <div>
              <div className="task-toolbar">
                <div className="task-search">
                  <Search size={14} />
                  <Input
                    aria-label="Search tasks"
                    placeholder="Search your tasks…"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>
                <select
                  className="field-select toolbar-select"
                  aria-label="Filter by priority"
                  value={priority}
                  onChange={(event) => setPriority(event.target.value)}
                >
                  <option value="all">All priorities</option>
                  <option value="high">High priority</option>
                  <option value="medium">Medium priority</option>
                  <option value="low">Low priority</option>
                </select>
                <select
                  className="field-select toolbar-select"
                  aria-label="Sort tasks"
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                >
                  <option value="created_at">Newest first</option>
                  <option value="created_at_asc">Oldest first</option>
                  <option value="priority">Priority</option>
                  <option value="due_date">Due date</option>
                </select>
              </div>
              {loadError ? (
                <div className="form-error" role="alert">
                  {loadError}{' '}
                  <button className="underline" onClick={loadTasks}>
                    Retry loading tasks
                  </button>
                </div>
              ) : loading ? (
                <div
                  className="flex items-center gap-2 py-16 text-text-muted"
                  role="status"
                >
                  <Loader2 size={16} className="animate-spin" />
                  Loading tasks…
                </div>
              ) : visible.length ? (
                <>
                  {visiblePending.length > 0 && (
                    <section className="task-section">
                      <div className="task-section-header">
                        <h2>In progress ({visiblePending.length})</h2>
                        <span>
                          {editable ? 'Make your next move' : 'View only'}
                        </span>
                      </div>
                      {visiblePending.map(taskRow)}
                      {editable && (
                        <button
                          className="add-task-row"
                          onClick={() => setEditor({ text: '' })}
                        >
                          <Plus size={16} />
                          Add another task
                        </button>
                      )}
                    </section>
                  )}
                  {visibleDone.length > 0 && (
                    <section className="task-section">
                      <div className="task-section-header">
                        <h2>Completed ({visibleDone.length})</h2>
                        <CheckCheck size={14} />
                      </div>
                      {visibleDone.map(taskRow)}
                    </section>
                  )}
                </>
              ) : (
                <div className="empty-state">
                  <Inbox size={28} />
                  <h2>
                    {search
                      ? 'No matching tasks'
                      : view === 'completed'
                        ? 'Your progress starts here'
                        : 'Room for your next idea'}
                  </h2>
                  <p>
                    {search
                      ? 'Try a different search or priority.'
                      : view === 'today'
                        ? 'No tasks are due today. Enjoy a little breathing room.'
                        : 'Add a task manually, or let AI help you draft it.'}
                  </p>
                  {editable && (
                    <Button
                      variant="outline"
                      onClick={() => setEditor({ text: '' })}
                    >
                      <Plus size={14} />
                      Create a task
                    </Button>
                  )}
                </div>
              )}
            </div>
            <aside className="workspace-aside">
              <div className="assistant-panel">
                <div className="assistant-icon">
                  <Sparkles size={18} />
                </div>
                <h2>Start with a thought.</h2>
                <p>
                  Tell AI what you need to do. Review the details, then make it
                  a task.
                </p>
                <button
                  className="assistant-example"
                  disabled={!editable}
                  onClick={() =>
                    setEditor({
                      text: 'Review the project plan tomorrow at 10am, high priority, #work',
                    })
                  }
                >
                  “Review the project plan tomorrow at 10am, high priority.”
                </button>
                <Button
                  variant="outline"
                  className="w-full"
                  disabled={!editable}
                  onClick={() => setEditor({ text: '' })}
                >
                  Draft with AI
                  <ArrowRight size={13} />
                </Button>
                {editable && (
                  <div className="mt-3 flex justify-center">
                    <VoiceCommand
                      onCommandExecuted={(text) => {
                        if (editable) setEditor({ text })
                      }}
                    />
                  </div>
                )}
              </div>
              <div className="upcoming-panel">
                <h2>On the horizon</h2>
                {upcoming.length ? (
                  upcoming.map((task) => (
                    <div className="upcoming-task" key={task.id}>
                      <strong>{task.title}</strong>
                      <span>
                        {parseTaskDate(task.due_date!).toLocaleDateString(
                          undefined,
                          { weekday: 'short', month: 'short', day: 'numeric' }
                        )}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="workspace-note">
                    Add a due date to give your next steps a little structure.
                  </p>
                )}
              </div>
              <p className="workspace-note mt-8">
                {project
                  ? 'Shared work. Clear responsibilities.'
                  : 'Personal tasks are visible only to you.'}
              </p>
            </aside>
          </div>
        </main>
      </div>
      {editor && (
        <Dialog
          open
          onOpenChange={(open) => {
            if (!open && !editorBusy) setEditor(null)
          }}
        >
          <DialogContent
            showCloseButton={!editorBusy}
            onEscapeKeyDown={(event) => {
              if (editorBusy) event.preventDefault()
            }}
            onPointerDownOutside={(event) => {
              if (editorBusy) event.preventDefault()
            }}
          >
            <TaskForm
              onCreate={createTask}
              projects={projects.filter((item) => item.role !== 'viewer')}
              selectedProjectId={projectId}
              members={members}
              initialText={editor.text}
              onBusyChange={setEditorBusy}
            />
          </DialogContent>
        </Dialog>
      )}
      {editing && (
        <EditTaskModal
          task={editing}
          onSave={updateTask}
          onClose={() => setEditing(null)}
          members={members}
        />
      )}
      {showSettings && project && (
        <ProjectSettings
          project={project}
          onClose={() => setShowSettings(false)}
          onChange={() => reloadTasks.current()}
        />
      )}
      {showBackup && (
        <WorkspaceBackup
          onClose={() => setShowBackup(false)}
          onImported={() => reloadTasks.current()}
        />
      )}
      {showProject && (
        <Dialog open onOpenChange={() => setShowProject(false)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>A new shared project</DialogTitle>
              <DialogDescription>
                A place for your team to plan and get things done.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={createProject}>
              {projectError && (
                <div className="form-error" role="alert">
                  {projectError}
                </div>
              )}
              <label htmlFor="project-name" className="field-label">
                Project name
              </label>
              <Input
                id="project-name"
                placeholder="e.g. Website refresh"
                required
                maxLength={100}
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
              />
              <div className="editor-footer">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setShowProject(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={busy}>
                  {busy ? (
                    <Loader2 className="animate-spin" size={14} />
                  ) : (
                    <Plus size={14} />
                  )}
                  Create project
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}
      {showInvitations && (
        <Dialog open onOpenChange={() => setShowInvitations(false)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Project invitations</DialogTitle>
              <DialogDescription>
                Join the people you work with.
              </DialogDescription>
            </DialogHeader>
            {projectError && (
              <div className="form-error" role="alert">
                {projectError}
              </div>
            )}
            {invitations.length ? (
              invitations.map((invitation) => (
                <div className="member-row" key={invitation.id}>
                  <span className="avatar">
                    <Users size={14} />
                  </span>
                  <div className="account-info">
                    <strong>{invitation.project_name}</strong>
                    <span>Invited as {invitation.role}</span>
                  </div>
                  <Button
                    disabled={busy}
                    onClick={() => acceptInvitation(invitation.id)}
                  >
                    Accept
                  </Button>
                </div>
              ))
            ) : (
              <p className="workspace-note py-6">
                You’re all caught up. New invitations will appear here.
              </p>
            )}
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
