import { MapPinned, Zap } from 'lucide-react'
import RiskBadge from './RiskBadge.jsx'
import { mockDistricts } from '../data/mockDistricts.js'

const districtName = (id) => mockDistricts.find((d) => d.id === id)?.name ?? id

export default function CorridorPanel({ road, onSimulate, simulationStatus }) {
  if (!road) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-lg border border-dashed border-border-strong bg-panel px-5 py-10 text-center">
        <MapPinned size={26} className="mb-3 text-text-tertiary" />
        <h3 className="text-[13px] font-semibold text-text-primary">SELECT A CORRIDOR</h3>
        <p className="mt-1.5 max-w-[220px] text-[12px] leading-relaxed text-text-secondary">
          Click any highlighted corridor on the map to view its risk profile.
        </p>
      </div>
    )
  }

  const isBusy = simulationStatus === 'loading'

  return (
    <div className="rounded-lg border border-border bg-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
          SELECTED CORRIDOR
        </h3>
        <RiskBadge level={road.riskLevel} />
      </div>

      <div className="mb-1 font-mono text-2xl font-bold text-text-primary">{road.id}</div>
      <div className="mb-1 text-[12px] text-text-secondary">{road.name}</div>
      <div className="mb-4 font-mono text-[11px] text-text-tertiary">
        {districtName(road.originDistrict)} <span className="text-accent-strong">&rarr;</span> {districtName(road.destinationDistrict)}
      </div>

      <div className="grid grid-cols-2 gap-2.5 text-[12px]">
        <Field label="Risk score" value={`${road.riskScore}%`} />
        <Field label="Status" value={road.status} />
        <Field label="Criticality" value={road.criticality} />
        <Field label="Length" value={`${road.lengthKm} km`} />
      </div>

      <div className="mt-3 space-y-2 border-t border-border pt-3 text-[12px]">
        <Field label="Cargo" value={road.cargo} />
        <Field label="Destination" value={road.destination} />
      </div>

      <button
        onClick={() => onSimulate(road)}
        disabled={isBusy}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-md border border-risk-high/50 bg-risk-high-dim py-2.5 text-[13px] font-semibold text-risk-high transition-colors hover:bg-risk-high/20 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Zap size={15} />
        {isBusy ? 'ANALYZING NETWORK IMPACT…' : 'WHAT IF THIS ROAD FAILS?'}
      </button>
    </div>
  )
}

function Field({ label, value }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-text-tertiary">{label}</div>
      <div className="mt-0.5 font-medium text-text-primary">{value}</div>
    </div>
  )
}
