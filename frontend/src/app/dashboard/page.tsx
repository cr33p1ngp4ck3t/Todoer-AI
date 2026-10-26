'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api, Task, TaskCreate, TaskUpdate } from '../../services/api'
import TaskItem from '../../components/TaskItem'
import TaskForm from '../../components/TaskForm'
import SearchBar from '../../components/SearchBar'
import FilterControls from '../../components/FilterControls'
import SortDropdown from '../../components/SortDropdown'
import EditTaskModal from '../../components/EditTaskModal'
import { useAuth } from '../../contexts/AuthContext'
import ThemeToggle from '../../components/ThemeToggle'
import VoiceCommand from '../../components/VoiceCommand'
import StatsCard from '../../components/StatsCard'
import ProductivityChart from '../../components/ProductivityChart'
import { Button } from '../../components/ui/button'
import { Dialog, DialogContent } from '../../components/ui/dialog'
import { toast } from 'sonner'

export default function Dashboard() {
  const router = useRouter()
  const { user, logout, loading: authLoading } = useAuth()
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [sortBy, setSortBy] = useState('created_at')

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.tasks.list({
        search: searchQuery || undefined,
        status: statusFilter === 'all' ? undefined : statusFilter,
        priority: priorityFilter === 'all' ? undefined : priorityFilter,
        sort_by: sortBy === 'created_at_asc' ? 'created_at' : sortBy,
      })
      setTasks(data)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      setLoading(false)
    }
  }, [searchQuery, statusFilter, priorityFilter, sortBy])

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  // Load tasks when filters change (must be before early returns)
  useEffect(() => {
    if (user && !authLoading) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Show loading while synchronizing tasks with the API.
      loadTasks()
    }
  }, [user, authLoading, loadTasks])

  // Don't render anything while checking auth
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-page">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-border"></div>
          <p className="mt-4 text-text-secondary">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render dashboard if not logged in (will redirect)
  if (!user) {
    return null
  }

  const handleCreateTask = async (task: TaskCreate) => {
    if (creating) return
    setCreating(true)
    try {
      const newTask = await api.tasks.create(task)
      setTasks((prev) => [...prev, newTask])
      setShowForm(false)
      toast.success('Task created successfully')
    } catch (error) {
      console.error('Failed to create task:', error)
      toast.error('Failed to create task')
    } finally {
      setCreating(false)
    }
  }

  const handleStatusToggle = async (id: string) => {
    try {
      const task = tasks.find((t) => t.id === id)
      if (!task) return

      const updated = await api.tasks.update(id, {
        status: task.status === 'completed' ? 'pending' : 'completed',
      })
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)))

      if (updated.status === 'completed') {
        toast.success('Task completed!')
      } else {
        toast.info('Task marked as pending')
      }
    } catch (error) {
      console.error('Failed to update task status:', error)
      toast.error('Failed to update task status')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.tasks.delete(id)
      setTasks((prev) => prev.filter((t) => t.id !== id))
      toast.success('Task deleted')
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast.error('Failed to delete task')
    }
  }

  const handleEdit = async (id: string) => {
    const task = tasks.find((t) => t.id === id)
    if (task) {
      setEditingTask(task)
    }
  }

  const handleUpdateTask = async (id: string, updates: TaskUpdate) => {
    try {
      const updated = await api.tasks.update(id, updates)
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)))
      setEditingTask(null)
      toast.success('Task updated successfully')
    } catch (error) {
      console.error('Failed to update task:', error)
      toast.error('Failed to update task')
    }
  }

  const handleClearSearch = () => {
    setSearchQuery('')
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const pendingTasks = tasks.filter((t) => t.status === 'pending')
  const completedTasks = tasks.filter((t) => t.status === 'completed')

  return (
    <div className="min-h-screen bg-gradient-page px-4 py-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">My Tasks</h1>
            <p className="mt-1 text-sm text-text-secondary">{user?.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <VoiceCommand
              onCommandExecuted={(command) => {
                try {
                  const parsed = JSON.parse(command)
                  handleCreateTask(parsed)
                } catch (e) {
                  console.error('Failed to parse voice command:', e)
                }
              }}
            />
            <Button
              onClick={() => setShowForm(true)}
              className="bg-secondary"
              disabled={creating}
            >
              + New Task
            </Button>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="border border-border bg-card"
            >
              Logout
            </Button>
          </div>
        </header>

        {/* Stats & Chart */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <StatsCard tasks={tasks} />
          <div className="md:col-span-2">
            <ProductivityChart tasks={tasks} />
          </div>
        </div>

        {/* Search, Filter, Sort Controls */}
        <div className="mb-6 space-y-4 rounded-lg border border-border bg-card p-4 shadow-sm">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onClear={handleClearSearch}
          />
          <div className="flex flex-wrap gap-4 pt-2">
            <FilterControls
              statusFilter={statusFilter}
              priorityFilter={priorityFilter}
              onStatusChange={setStatusFilter}
              onPriorityChange={setPriorityFilter}
            />
            <SortDropdown sortBy={sortBy} onChange={setSortBy} />
          </div>
        </div>

        <Dialog open={showForm} onOpenChange={setShowForm}>
          <DialogContent>
            <TaskForm
              creating={creating}
              onCreate={(task) => {
                handleCreateTask(task)
                setShowForm(false)
              }}
            />
            <div className="mt-4 flex justify-end">
              <Button
                variant="ghost"
                onClick={() => setShowForm(false)}
                className="cursor-pointer"
              >
                Cancel
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {loading ? (
          <div className="py-8 text-center text-text-secondary">Loading...</div>
        ) : (
          <>
            {/* Pending Tasks */}
            {pendingTasks.length > 0 && (
              <section className="mb-8">
                <h2 className="mb-4 text-lg font-semibold text-foreground">
                  Pending ({pendingTasks.length})
                </h2>
                <ul className="flex flex-col gap-4 divide-y divide-divider rounded-lg">
                  {pendingTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onStatusToggle={handleStatusToggle}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))}
                </ul>
              </section>
            )}

            {/* Completed Tasks */}
            {completedTasks.length > 0 && (
              <section>
                <h2 className="mb-4 text-lg font-semibold text-foreground">
                  Completed ({completedTasks.length})
                </h2>
                <ul className="flex flex-col gap-4 divide-y divide-divider rounded-lg">
                  {completedTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onStatusToggle={handleStatusToggle}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))}
                </ul>
              </section>
            )}

            {/* Empty State */}
            {tasks.length === 0 && (
              <div className="rounded-lg border border-border bg-card py-16 text-center shadow-sm">
                <p className="text-lg text-text-secondary">No tasks found</p>
                <p className="mt-2 text-text-muted">
                  {searchQuery ||
                  statusFilter !== 'all' ||
                  priorityFilter !== 'all'
                    ? 'Try adjusting your filters or search terms.'
                    : 'Create your first task to get started!'}
                </p>
              </div>
            )}
          </>
        )}

        {/* Edit Task Modal */}
        {editingTask && (
          <EditTaskModal
            task={editingTask}
            onSave={handleUpdateTask}
            onClose={() => setEditingTask(null)}
          />
        )}
      </div>
    </div>
  )
}
