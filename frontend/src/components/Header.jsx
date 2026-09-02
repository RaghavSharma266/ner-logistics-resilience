import { useEffect, useState } from 'react'
import { Bell, Radio } from 'lucide-react'

function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

export default function Header({ alertCount }) {
  const now = useClock()
  const dateStr = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface px-5">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded border border-accent/40 bg-accent-dim">
          <Radio size={18} className="text-accent-strong" />
        </div>
        <div>
          <h1 className="text-[15px] font-semibold tracking-[0.02em] text-text-primary">
            NER LOGISTICS INTELLIGENCE PLATFORM
          </h1>
          <p className="text-[11px] text-text-secondary">
            North Eastern Region &middot; Logistics Resilience &amp; Accessibility
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-1.5 rounded border border-border-strong bg-panel px-2.5 py-1.5 sm:flex">
          <span className="status-pulse h-1.5 w-1.5 rounded-full bg-risk-medium" />
          <span className="font-mono text-[10px] tracking-[0.14em] text-risk-medium">PROTOTYPE MODE &middot; SIMULATED DATA</span>
        </div>

        <div className="hidden flex-col items-end leading-tight md:flex">
          <span className="font-mono text-xs text-text-primary">{timeStr}</span>
          <span className="font-mono text-[10px] text-text-tertiary">{dateStr}</span>
        </div>

        <div className="relative flex h-9 w-9 items-center justify-center rounded border border-border-strong bg-panel">
          <Bell size={16} className="text-text-secondary" />
          {alertCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-risk-high px-1 font-mono text-[9px] font-bold text-white">
              {alertCount}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
