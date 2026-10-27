'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/dashboard')
  }, [router])
  return (
    <div className="flex min-h-screen items-center justify-center gap-3 text-text-secondary">
      <Loader2 size={18} className="animate-spin" />
      Opening your workspace…
    </div>
  )
}
