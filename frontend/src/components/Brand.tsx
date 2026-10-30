import { Check } from 'lucide-react'

export default function Brand({ className = '' }: { className?: string }) {
  return (
    <div className={`brand ${className}`}>
      <span className="brand-mark">
        <Check size={19} strokeWidth={3} />
      </span>
      <span>
        Todoer <small>AI</small>
      </span>
    </div>
  )
}
