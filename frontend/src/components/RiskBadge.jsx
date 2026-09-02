const STYLES = {
  LOW: 'bg-risk-low-dim text-risk-low border-risk-low/40',
  MEDIUM: 'bg-risk-medium-dim text-risk-medium border-risk-medium/40',
  HIGH: 'bg-risk-high-dim text-risk-high border-risk-high/40',
}

export default function RiskBadge({ level, size = 'sm' }) {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
  return (
    <span
      className={`inline-flex items-center rounded border font-mono font-semibold tracking-wide ${STYLES[level]} ${sizeClasses}`}
    >
      {level} RISK
    </span>
  )
}
