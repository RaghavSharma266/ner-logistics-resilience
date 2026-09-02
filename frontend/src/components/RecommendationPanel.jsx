import { CheckCircle2, ArrowRight, TriangleAlert } from 'lucide-react'

export default function RecommendationPanel({ recommendation }) {
  if (!recommendation) return null

  return (
    <div className={`rounded-lg border p-4 ${recommendation.reachableConfirmed ? 'border-accent/30 bg-panel' : 'border-risk-high/30 bg-panel'}`}>
      <h3 className="mb-3 font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
        {recommendation.reachableConfirmed ? 'RECOMMENDED ACTION' : 'CONTINGENCY RECOMMENDATION'}
      </h3>

      <div className="flex items-start gap-2.5">
        <ArrowRight size={16} className={`mt-0.5 shrink-0 ${recommendation.reachableConfirmed ? 'text-accent-strong' : 'text-risk-high'}`} />
        <p className="text-[13px] font-medium leading-snug text-text-primary">{recommendation.action}</p>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="text-[11px] text-text-secondary">Priority</span>
        <span className="rounded border border-risk-high/40 bg-risk-high-dim px-2 py-0.5 font-mono text-[10px] font-semibold text-risk-high">
          {recommendation.priority}
        </span>
        <span className="ml-auto font-mono text-[11px] text-text-secondary">
          Est. delay <span className="font-semibold text-risk-medium">+{recommendation.delayMin} min</span>
        </span>
      </div>

      <p className="mt-3 text-[12px] leading-relaxed text-text-secondary">{recommendation.reason}</p>

      {recommendation.reachableConfirmed ? (
        <div className="mt-3 flex items-center gap-2 rounded-md border border-risk-low/40 bg-risk-low-dim px-3 py-2.5">
          <CheckCircle2 size={16} className="shrink-0 text-risk-low" />
          <span className="text-[12px] font-medium text-risk-low">Critical destination remains reachable</span>
        </div>
      ) : (
        <div className="mt-3 flex items-center gap-2 rounded-md border border-risk-high/40 bg-risk-high-dim px-3 py-2.5">
          <TriangleAlert size={16} className="shrink-0 text-risk-high" />
          <span className="text-[12px] font-medium text-risk-high">No road alternate — destination access is degraded</span>
        </div>
      )}
    </div>
  )
}
