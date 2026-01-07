'use client'

import { Task } from '../services/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from './ui/chart'
import { Bar, BarChart, XAxis, YAxis, Cell } from 'recharts'

interface ProductivityChartProps {
  tasks: Task[]
}

export default function ProductivityChart({ tasks }: ProductivityChartProps) {
  // Get last 7 days data
  const getChartData = () => {
    const data = []
    const today = new Date()
    const todayStr = today.toDateString()

    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      const dateStr = date.toLocaleDateString('en-US', { weekday: 'short' })
      const isToday = date.toDateString() === todayStr

      // Count completed tasks for this day (based on created_at since no completed_at)
      const completedCount = tasks.filter((t) => {
        if (t.status !== 'completed') return false
        const createdDate = new Date(t.created_at)
        return createdDate.toDateString() === date.toDateString()
      }).length

      data.push({ date: dateStr, completed: completedCount, isToday })
    }

    return data
  }

  const chartData = getChartData()
  const totalCompleted = tasks.filter((t) => t.status === 'completed').length

  const chartConfig = {
    completed: {
      label: 'Completed Tasks',
      color: '#84cc16', // lime-500
    },
  } satisfies ChartConfig

  return (
    <Card className="bg-white dark:bg-neutral-800/80">
      <CardHeader>
        <CardTitle className="text-lg">Last 7 Days</CardTitle>
      </CardHeader>
      <CardContent>
        {totalCompleted === 0 ? (
          <div className="flex h-48 items-center justify-center text-sm text-gray-500">
            No completed tasks yet
          </div>
        ) : (
          <ChartContainer config={chartConfig}>
            <BarChart data={chartData}>
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                allowDecimals={false}
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Bar dataKey="completed" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.isToday ? '#84cc16' : '#525252'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}
