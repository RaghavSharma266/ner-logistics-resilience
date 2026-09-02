import { LayoutGrid, Route, TriangleAlert, Truck, Navigation } from 'lucide-react'
import DistrictStatusPanel from './DistrictStatusPanel.jsx'

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutGrid },
  { id: 'corridors', label: 'Risk Corridors', icon: Route },
  { id: 'incidents', label: 'Incidents', icon: TriangleAlert },
  { id: 'vehicles', label: 'Vehicles', icon: Truck },
  { id: 'emergency', label: 'Emergency Routes', icon: Navigation },
]

export default function RiskSummary({ overview, districts, activeNav, onNavChange }) {
  return (
    <aside className="flex h-full w-full flex-col gap-5 overflow-y-auto border-r border-border bg-surface p-4">
      <div>
        <h2 className="mb-3 font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
          NETWORK OVERVIEW
        </h2>
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-md border border-risk-low/30 bg-risk-low-dim px-2 py-2.5 text-center">
            <div className="font-mono text-lg font-bold text-risk-low">{overview.lowRisk}</div>
            <div className="mt-0.5 text-[9px] leading-tight text-text-secondary">LOW RISK</div>
          </div>
          <div className="rounded-md border border-risk-medium/30 bg-risk-medium-dim px-2 py-2.5 text-center">
            <div className="font-mono text-lg font-bold text-risk-medium">{overview.mediumRisk}</div>
            <div className="mt-0.5 text-[9px] leading-tight text-text-secondary">MEDIUM RISK</div>
          </div>
          <div className="rounded-md border border-risk-high/30 bg-risk-high-dim px-2 py-2.5 text-center">
            <div className="font-mono text-lg font-bold text-risk-high">{overview.highRisk}</div>
            <div className="mt-0.5 text-[9px] leading-tight text-text-secondary">HIGH RISK</div>
          </div>
        </div>

        <div className="mt-3 space-y-2 rounded-md border border-border bg-panel p-3">
          <Row label="Active incidents" value={overview.activeIncidents} />
          <Row label="Active vehicles" value={overview.activeVehicles} />
          <Row label="Affected corridors" value={overview.affectedCorridors} accent />
        </div>
      </div>

      <div>
        <h2 className="mb-2 font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
          NAVIGATION
        </h2>
        <nav className="space-y-1">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
            const active = activeNav === id
            return (
              <button
                key={id}
                onClick={() => onNavChange(id)}
                className={`flex w-full items-center gap-2.5 rounded-md border px-3 py-2 text-left text-[13px] transition-colors ${
                  active
                    ? 'border-accent/40 bg-accent-dim text-accent-strong'
                    : 'border-transparent text-text-secondary hover:border-border-strong hover:bg-panel'
                }`}
              >
                <Icon size={15} />
                {label}
              </button>
            )
          })}
        </nav>
      </div>

      <DistrictStatusPanel districts={districts} />

      <div className="mt-auto rounded-md border border-border bg-panel p-3 text-[11px] leading-relaxed text-text-tertiary">
        Corridor data, incident feeds, and vehicle positions shown here are simulated for this prototype demonstration.
      </div>
    </aside>
  )
}

function Row({ label, value, accent }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[12px] text-text-secondary">{label}</span>
      <span className={`font-mono text-[13px] font-semibold ${accent ? 'text-risk-medium' : 'text-text-primary'}`}>
        {value}
      </span>
    </div>
  )
}
