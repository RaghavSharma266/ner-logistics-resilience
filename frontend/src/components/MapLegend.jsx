const items = [
  { label: 'Low risk', swatch: 'bg-risk-low', kind: 'line' },
  { label: 'Medium risk', swatch: 'bg-risk-medium', kind: 'line' },
  { label: 'High risk', swatch: 'bg-risk-high', kind: 'line' },
  { label: 'Hospital', swatch: 'bg-red-900 border border-red-500', kind: 'dot' },
  { label: 'Supply point', swatch: 'bg-panel-raised border border-accent', kind: 'dot' },
  { label: 'Incident', swatch: 'bg-risk-high border border-white', kind: 'dot' },
  { label: 'Vehicle', swatch: 'bg-accent border border-void', kind: 'dot' },
]

export default function MapLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-[500] rounded-lg border border-border-strong bg-panel/95 backdrop-blur-sm px-3 py-2.5 shadow-lg">
      <div className="mb-1.5 font-mono text-[10px] tracking-[0.12em] text-text-tertiary">MAP LEGEND</div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            {item.kind === 'line' ? (
              <span className={`h-[3px] w-4 rounded-full ${item.swatch}`} />
            ) : (
              <span className={`h-2.5 w-2.5 rounded-full ${item.swatch}`} />
            )}
            <span className="text-[11px] text-text-secondary">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
