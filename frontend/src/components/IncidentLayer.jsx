import { Marker, Popup } from 'react-leaflet'
import { incidentIcon } from './mapIcons.js'

export default function IncidentLayer({ incidents, onSelect }) {
  return (
    <>
      {incidents.map((incident) => (
        <Marker
          key={incident.id}
          position={incident.coords}
          icon={incidentIcon(incident.severity)}
          eventHandlers={{ click: () => onSelect(incident) }}
        >
          <Popup>
            <div className="p-3">
              <div className="font-mono text-[10px] tracking-wide text-text-tertiary">{incident.id}</div>
              <div className="mt-0.5 text-sm font-semibold text-text-primary">{incident.type}</div>
              <div className="mt-1 text-xs text-text-secondary">{incident.location}</div>
              <button
                onClick={() => onSelect(incident)}
                className="mt-2 rounded border border-accent/40 bg-accent-dim px-2.5 py-1 text-[11px] font-medium text-accent-strong hover:bg-accent/20"
              >
                View impact
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  )
}
