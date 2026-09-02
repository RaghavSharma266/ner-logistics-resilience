import { TriangleAlert, Activity, ListChecks } from 'lucide-react'

function PanelShell({ icon: Icon, title, children }) {
  return (
    <div className="flex-1 rounded-lg border border-border bg-panel p-3.5">
      <div className="mb-2.5 flex items-center gap-2">
        <Icon size={14} className="text-text-tertiary" />
        <h4 className="font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">{title}</h4>
      </div>
      <ul className="space-y-1.5">{children}</ul>
    </div>
  )
}

function ListItem({ children, tone }) {
  const dot =
    tone === 'high' ? 'bg-risk-high' : tone === 'medium' ? 'bg-risk-medium' : tone === 'low' ? 'bg-risk-low' : 'bg-accent'
  return (
    <li className="flex items-start gap-2 text-[12px] leading-snug text-text-secondary">
      <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
      <span>{children}</span>
    </li>
  )
}

export default function AlertsPanel({ incidents, overview, activeRecommendation }) {
  const topAlerts = incidents.slice(0, 3)

  return (
    <div className="flex flex-col gap-3 border-t border-border bg-surface p-3 sm:flex-row">
      <PanelShell icon={TriangleAlert} title="ACTIVE ALERTS">
        {topAlerts.map((incident) => (
          <ListItem key={incident.id} tone={incident.severity.toLowerCase()}>
            {incident.type.charAt(0) + incident.type.slice(1).toLowerCase()} &middot; {incident.location}
          </ListItem>
        ))}
      </PanelShell>

      <PanelShell icon={Activity} title="NETWORK STATUS">
        <ListItem>{overview.monitoredCorridors} monitored corridors</ListItem>
        <ListItem tone="low">{overview.operationalCorridors} operational</ListItem>
        <ListItem tone="high">{overview.highRisk} high-risk</ListItem>
      </PanelShell>

      <PanelShell icon={ListChecks} title="RECOMMENDATIONS">
        <ListItem>{overview.affectedCorridors} routes require attention</ListItem>
        <ListItem tone={activeRecommendation ? 'high' : undefined}>
          {activeRecommendation
            ? `Active: ${activeRecommendation.action}`
            : '1 emergency rerouting recommendation pending'}
        </ListItem>
      </PanelShell>
    </div>
  )
}
