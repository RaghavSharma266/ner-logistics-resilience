import { Marker, Popup } from 'react-leaflet'
import { vehicleIcon } from './mapIcons.js'

export default function VehicleLayer({ vehicles }) {
  return (
    <>
      {vehicles.map((vehicle) => (
        <Marker key={vehicle.id} position={vehicle.coords} icon={vehicleIcon(vehicle.status)}>
          <Popup>
            <div className="p-3">
              <div className="font-mono text-[10px] tracking-wide text-text-tertiary">VEHICLE {vehicle.id}</div>
              <div className="mt-0.5 text-sm font-semibold text-text-primary">{vehicle.cargo}</div>
              <div className="mt-1 text-xs text-text-secondary">To: {vehicle.destination}</div>
              <div className="mt-2 flex items-center justify-between text-[11px]">
                <span className={vehicle.status === 'DELAYED' ? 'text-risk-medium' : 'text-risk-low'}>
                  {vehicle.status}
                </span>
                <span className="font-mono text-text-secondary">ETA {vehicle.eta}</span>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  )
}
