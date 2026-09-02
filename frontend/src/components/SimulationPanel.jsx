import { Loader2, TrendingDown, Clock, Users, Route as RouteIcon, HeartPulse, Package, Home, MapPin } from 'lucide-react'

const LOCATION_ICON = {
  HOSPITAL: HeartPulse,
  SUPPLY: Package,
  VILLAGE: Home,
}

const DISTRICT_STATUS_LABEL = {
  CONNECTED: 'Connected',
  AT_RISK: 'At risk',
  VULNERABLE: 'Vulnerable · no alternate',
}

export default function SimulationPanel({ status, result, onViewAlternative, alternativeShown }) {
  if (status === 'idle') return null

  if (status === 'loading') {
    return (
      <div className="rounded-lg border border-border bg-panel p-5">
        <div className="flex items-center gap-3">
          <Loader2 size={18} className="animate-spin text-accent" />
          <span className="text-[13px] text-text-secondary">Analyzing network impact&hellip;</span>
        </div>
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-panel-raised">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-accent" />
        </div>
      </div>
    )
  }

  if (!result) return null

  return (
    <div className="rounded-lg border border-risk-high/30 bg-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
          SIMULATION RESULT
        </h3>
        <span className="rounded border border-risk-high/40 bg-risk-high-dim px-2 py-0.5 font-mono text-[10px] font-semibold text-risk-high">
          {result.roadId} {result.status}
        </span>
      </div>

      {result.affectedDistrict && (
        <div className="mb-3 flex items-start gap-2 rounded-md border border-risk-high/30 bg-risk-high-dim px-3 py-2.5">
          <MapPin size={14} className="mt-0.5 shrink-0 text-risk-high" />
          <div className="text-[12px] leading-snug">
            <span className="font-semibold text-risk-high">{result.affectedDistrict.name} district</span>
            <span className="text-text-secondary"> ({result.affectedDistrict.state}) &middot; </span>
            <span className="text-text-secondary">
              ~{result.affectedDistrict.population.toLocaleString('en-IN')} population &middot;{' '}
            </span>
            <span className="font-medium text-risk-high">
              {DISTRICT_STATUS_LABEL[result.affectedDistrict.connectivityStatus]}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2 text-center">
        <Stat icon={Users} value={result.locationsAffected} label="Locations affected" />
        <Stat icon={TrendingDown} value={result.criticalFacilitiesAffected} label="Critical facility" accent="risk-high" />
        <Stat icon={RouteIcon} value={result.supplyRoutesDisrupted} label="Routes disrupted" />
      </div>

      <div className="mt-3 space-y-1.5">
        <div className="font-mono text-[10px] tracking-[0.1em] text-text-tertiary">AFFECTED LOCATIONS</div>
        {result.affectedLocations.map((loc) => {
          const Icon = LOCATION_ICON[loc.type] ?? MapPin
          return (
            <div
              key={loc.name}
              className="flex items-start gap-2.5 rounded-md border border-border bg-panel-raised px-3 py-2.5"
            >
              <Icon size={14} className={`mt-0.5 shrink-0 ${loc.critical ? 'text-risk-high' : 'text-text-secondary'}`} />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-[12px] font-medium text-text-primary">{loc.name}</span>
                  {loc.critical && (
                    <span className="shrink-0 rounded border border-risk-high/40 bg-risk-high-dim px-1.5 py-0.5 font-mono text-[9px] font-semibold text-risk-high">
                      CRITICAL
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-risk-medium">{loc.impact}</div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-3 rounded-md border border-border bg-panel-raised p-3">
        <div className="mb-1.5 flex items-center justify-between text-[11px] text-text-secondary">
          <span>Accessibility</span>
          <span className="font-mono">
            <span className="text-text-primary">{result.accessibilityBefore}%</span>
            <span className="mx-1 text-text-tertiary">&rarr;</span>
            <span className="text-risk-high">{result.accessibilityAfter}%</span>
          </span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-panel">
          <div
            className="h-full rounded-full bg-risk-high transition-all"
            style={{ width: `${result.accessibilityAfter}%` }}
          />
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between rounded-md border border-border bg-panel-raised px-3 py-2.5">
        <div className="flex items-center gap-2 text-[12px] text-text-secondary">
          <Clock size={14} />
          Travel impact
        </div>
        <span className="font-mono text-[13px] font-semibold text-risk-medium">+{result.travelDelayMin} min</span>
      </div>

      <div className="mt-3 flex items-center justify-between rounded-md border border-border bg-panel-raised px-3 py-2.5">
        <span className="text-[12px] text-text-secondary">Alternative route</span>
        {result.alternativeRoute ? (
          <span className="font-mono text-[13px] font-semibold text-accent-strong">{result.alternativeRoute}</span>
        ) : (
          <span className="font-mono text-[11px] font-semibold text-risk-high">NONE AVAILABLE</span>
        )}
      </div>

      {result.alternativeRoute ? (
        <button
          onClick={onViewAlternative}
          disabled={alternativeShown}
          className="mt-4 w-full rounded-md border border-accent/50 bg-accent-dim py-2.5 text-[13px] font-semibold text-accent-strong transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {alternativeShown ? 'ALTERNATIVE ROUTE SHOWN ON MAP' : 'VIEW ALTERNATIVE ROUTE'}
        </button>
      ) : (
        <button
          onClick={onViewAlternative}
          disabled={alternativeShown}
          className="mt-4 w-full rounded-md border border-risk-high/50 bg-risk-high-dim py-2.5 text-[13px] font-semibold text-risk-high transition-colors hover:bg-risk-high/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {alternativeShown ? 'CONTINGENCY PLAN SHOWN BELOW' : 'VIEW CONTINGENCY RECOMMENDATION'}
        </button>
      )}
    </div>
  )
}

function Stat({ icon: Icon, value, label, accent }) {
  return (
    <div className="rounded-md border border-border bg-panel-raised px-2 py-2.5">
      <Icon size={14} className={`mx-auto mb-1 ${accent ? 'text-risk-high' : 'text-text-secondary'}`} />
      <div className={`font-mono text-base font-bold ${accent ? 'text-risk-high' : 'text-text-primary'}`}>{value}</div>
      <div className="mt-0.5 text-[9px] leading-tight text-text-tertiary">{label}</div>
    </div>
  )
}
