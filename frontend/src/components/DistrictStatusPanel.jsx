const STATUS_META = {
  CONNECTED: { label: 'Connected', dot: 'bg-risk-low', text: 'text-risk-low' },
  AT_RISK: { label: 'At risk · alt. available', dot: 'bg-risk-medium', text: 'text-risk-medium' },
  VULNERABLE: { label: 'Vulnerable · no alt.', dot: 'bg-risk-high', text: 'text-risk-high' },
}

export default function DistrictStatusPanel({ districts }) {
  const sorted = [...districts].sort((a, b) => {
    const order = { VULNERABLE: 0, AT_RISK: 1, CONNECTED: 2 }
    return order[a.connectivityStatus] - order[b.connectivityStatus]
  })

  return (
    <div>
      <h2 className="mb-2 font-mono text-[10px] font-semibold tracking-[0.14em] text-text-tertiary">
        DISTRICT CONNECTIVITY
      </h2>
      <div className="max-h-52 space-y-1 overflow-y-auto rounded-md border border-border bg-panel p-2">
        {sorted.map((district) => {
          const meta = STATUS_META[district.connectivityStatus]
          return (
            <div key={district.id} className="flex items-center justify-between gap-2 rounded px-1.5 py-1.5 hover:bg-panel-hover">
              <div className="min-w-0">
                <div className="truncate text-[12px] font-medium text-text-primary">{district.name}</div>
                <div className="truncate text-[10px] text-text-tertiary">{district.state}</div>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
                <span className={`whitespace-nowrap text-[10px] font-medium ${meta.text}`}>{meta.label}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
