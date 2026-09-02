import L from 'leaflet'

// Small hand-authored SVGs (kept dependency-free from lucide's React runtime
// so they can be embedded directly into Leaflet's divIcon HTML strings).

const wrap = (svgInner, { bg, ring, size = 26 }) => `
  <div style="
    width:${size}px;height:${size}px;
    background:${bg};
    border:2px solid ${ring};
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 8px rgba(0,0,0,0.55);
  ">
    ${svgInner}
  </div>
`

const svgIcon = (path, stroke = '#e7ebf3', size = 13) => `
  <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">${path}</svg>
`

const PATHS = {
  hospital: '<path d="M12 6v8M8 10h8" /><rect x="4" y="3" width="16" height="18" rx="2" />',
  supply: '<path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
  village: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
  incident: '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
  truck: '<path d="M3 17V6h9v11"/><path d="M12 10h5l3 3v4h-8"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="17.5" cy="17.5" r="1.5"/>',
}

export function facilityIcon(type, critical) {
  const size = critical ? 30 : 26
  if (type === 'HOSPITAL') {
    return L.divIcon({
      className: '',
      html: wrap(svgIcon(PATHS.hospital, '#ffffff', 14), { bg: '#7f1d1d', ring: critical ? '#ef4444' : '#b91c1c', size }),
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    })
  }
  if (type === 'SUPPLY') {
    return L.divIcon({
      className: '',
      html: wrap(svgIcon(PATHS.supply, '#e7ebf3', 13), { bg: '#0d1526', ring: '#2dd4ee', size }),
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    })
  }
  // VILLAGE
  return L.divIcon({
    className: '',
    html: wrap(svgIcon(PATHS.village, '#e7ebf3', 12), { bg: '#0d1526', ring: '#5b6883', size: 22 }),
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  })
}

export function incidentIcon(severity) {
  const ring = severity === 'HIGH' ? '#ef4444' : severity === 'MEDIUM' ? '#f0a825' : '#8b96ab'
  return L.divIcon({
    className: '',
    html: wrap(svgIcon(PATHS.incident, '#0a0f1a', 14), { bg: ring, ring: '#05070c', size: 28 }),
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

export function vehicleIcon(status) {
  const ring = status === 'DELAYED' ? '#f0a825' : '#2dd4ee'
  return L.divIcon({
    className: '',
    html: wrap(svgIcon(PATHS.truck, '#0a0f1a', 12), { bg: ring, ring: '#05070c', size: 24 }),
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

export function warningIcon() {
  return L.divIcon({
    className: '',
    html: wrap(svgIcon(PATHS.incident, '#0a0f1a', 13), { bg: '#ef4444', ring: '#ffffff', size: 26 }),
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  })
}
