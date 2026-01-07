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
    <Card className="bg-white dark:bg-neutral-800/80">
      <CardHeader>
        <CardTitle className="text-lg">Task Statistics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Total Tasks
            </p>
            <p className="text-2xl font-bold">{totalTasks}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Completed
            </p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {completedTasks}
            </p>
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Completion Rate</span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {completionRate.toFixed(0)}%
            </span>
          </div>
          <Progress value={completionRate} className="h-2 bg-gray-200" />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Pending by Priority</p>
          <div className="flex flex-col gap-2">
            {getPriorityCount('high') > 0 && (
              <Badge
                variant="destructive"
                className="bg-neutral-700 text-white dark:bg-neutral-300 dark:text-black"
              >
                High: {getPriorityCount('high')}
              </Badge>
            )}
            {getPriorityCount('medium') > 0 && (
              <Badge
                variant="default"
                className="bg-neutral-400 dark:bg-neutral-500"
              >
                Medium: {getPriorityCount('medium')}
              </Badge>
            )}
            {getPriorityCount('low') > 0 && (
              <Badge
                variant="secondary"
                className="bg-gray-200 dark:bg-neutral-700"
              >
                Low: {getPriorityCount('low')}
              </Badge>
            )}
            {pendingTasks === 0 && (
              <Badge
                variant="outline"
                className="border border-gray-200 dark:border-neutral-700"
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
