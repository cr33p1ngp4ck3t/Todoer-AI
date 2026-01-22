'use client'

import { Task } from '../services/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'

interface StatsCardProps {
  tasks: Task[]
}

export default function StatsCard({ tasks }: StatsCardProps) {
  const totalTasks = tasks.length
  const completedTasks = tasks.filter((t) => t.status === 'completed').length
  const pendingTasks = totalTasks - completedTasks
  const completionRate =
    totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0

  const getPriorityCount = (priority: 'low' | 'medium' | 'high') =>
    tasks.filter((t) => t.priority === priority && t.status === 'pending')
      .length

  return (
    <Card className="bg-card">
      <CardHeader>
        <CardTitle className="text-lg">Task Statistics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-text-secondary">
              Total Tasks
            </p>
            <p className="text-2xl font-bold">{totalTasks}</p>
          </div>
          <div>
            <p className="text-sm text-text-secondary">
              Completed
            </p>
            <p className="text-2xl font-bold text-success">
              {completedTasks}
            </p>
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Completion Rate</span>
            <span className="text-sm text-text-secondary">
              {completionRate.toFixed(0)}%
            </span>
          </div>
          <Progress value={completionRate} className="h-2 bg-secondary" />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Pending by Priority</p>
          <div className="flex flex-col gap-2">
            {getPriorityCount('high') > 0 && (
              <Badge
                variant="destructive"
                className="bg-priority-high text-primary-foreground"
              >
                High: {getPriorityCount('high')}
              </Badge>
            )}
            {getPriorityCount('medium') > 0 && (
              <Badge
                variant="default"
                className="bg-priority-medium"
              >
                Medium: {getPriorityCount('medium')}
              </Badge>
            )}
            {getPriorityCount('low') > 0 && (
              <Badge
                variant="secondary"
                className="bg-priority-low"
              >
                Low: {getPriorityCount('low')}
              </Badge>
            )}
            {pendingTasks === 0 && (
              <Badge
                variant="outline"
                className="border border-border"
              >
                No pending tasks
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
