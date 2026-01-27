'use client'

import { useEffect, useRef } from 'react'
import { api } from '@/services/api'

const PING_INTERVAL = 30 * 1000 // 30 seconds in milliseconds

export function KeepAlivePing() {
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const pingBackend = () => {
      api.ping.keepAlive()
    }

    // Start the interval
    intervalRef.current = setInterval(pingBackend, PING_INTERVAL)

    // Do an initial ping immediately
    pingBackend()

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return null
}
