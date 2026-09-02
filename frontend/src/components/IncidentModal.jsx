import { X, TriangleAlert } from 'lucide-react'
import RiskBadge from './RiskBadge.jsx'

export default function IncidentModal({ incident, onClose, onViewImpact }) {
  if (!incident) return null

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="w-full max-w-sm rounded-lg border border-border-strong bg-panel-raised p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-risk-high/40 bg-risk-high-dim">
              <TriangleAlert size={16} className="text-risk-high" />
            </div>
            <div>
              <div className="font-mono text-[10px] tracking-wide text-text-tertiary">INCIDENT REPORT</div>
              <div className="text-sm font-semibold text-text-primary">{incident.id}</div>
            </div>
          </div>
          <button onClick={onClose} className="rounded p-1 text-text-tertiary hover:bg-panel-hover hover:text-text-primary">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-3 text-[13px]">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Type</span>
            <span className="font-semibold text-text-primary">{incident.type}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Severity</span>
            <RiskBadge level={incident.severity} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Location</span>
            <span className="text-right font-medium text-text-primary">{incident.location}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Reported</span>
            <span className="font-mono text-text-primary">{incident.reportedAgo}</span>
          </div>
          <div className="flex items-center justify-between border-t border-border pt-3">
            <span className="text-text-secondary">Status</span>
            <span className="font-mono text-[12px] font-semibold text-risk-medium">{incident.status}</span>
          </div>
        </div>

        <button
          onClick={() => onViewImpact(incident)}
          className="mt-5 w-full rounded-md border border-accent/50 bg-accent-dim py-2.5 text-[13px] font-semibold text-accent-strong hover:bg-accent/20"
        >
          VIEW IMPACT
        </button>
      </div>
    </div>
  )
}
