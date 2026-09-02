// Simulated logistics corridors across the North Eastern Region.
// Coordinates are illustrative approximations for prototype purposes, not
// surveyed alignments.
//
// Every road is tagged with originDistrict / destinationDistrict (ids from
// mockDistricts.js). Where a district pair has more than one road, they
// share the SAME destinationDistrict on purpose — this is what lets the
// simulation logic offer a genuinely logical alternate (same place, safer
// path) instead of a route to somewhere else entirely. District pairs with
// only one road on purpose represent a real single point of failure.

export const RISK_LEVELS = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
}

export const mockRoads = [
  // Kamrup Metropolitan -> East Khasi Hills (Guwahati -> Shillong): primary + alternate
  {
    id: 'R101',
    name: 'Guwahati – Shillong Corridor',
    state: 'Assam / Meghalaya',
    originDistrict: 'kamrup-metropolitan',
    destinationDistrict: 'east-khasi-hills',
    riskLevel: RISK_LEVELS.HIGH,
    riskScore: 87,
    status: 'OPERATIONAL',
    criticality: 'HIGH',
    cargo: 'Medical Supplies',
    destination: 'District Hospital, Shillong',
    lengthKm: 96,
    path: [
      [26.1445, 91.7362],
      [26.0234, 91.8956],
      [25.8756, 91.9432],
      [25.7788, 91.8933],
      [25.5788, 91.8933],
    ],
  },
  {
    id: 'R105',
    name: 'Guwahati – Nongpoh – Shillong Bypass',
    state: 'Assam / Meghalaya',
    originDistrict: 'kamrup-metropolitan',
    destinationDistrict: 'east-khasi-hills',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 18,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'General Cargo',
    destination: 'District Hospital, Shillong',
    lengthKm: 112,
    path: [
      [26.1445, 91.7362],
      [26.0800, 91.8600],
      [25.9088, 91.8788],
      [25.7200, 91.8500],
      [25.5788, 91.8933],
    ],
  },

  // Dibrugarh -> Tinsukia: single well-connected route
  {
    id: 'R102',
    name: 'Dibrugarh – Tinsukia Link',
    state: 'Assam',
    originDistrict: 'dibrugarh',
    destinationDistrict: 'tinsukia',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 22,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Agricultural Produce',
    destination: 'Tinsukia Depot',
    lengthKm: 47,
    path: [
      [27.4728, 94.9120],
      [27.4200, 95.0500],
      [27.4922, 95.3600],
    ],
  },

  // Papum Pare -> Lower Subansiri: single route, no alternate (vulnerable)
  {
    id: 'R103',
    name: 'Itanagar – Ziro Valley Route',
    state: 'Arunachal Pradesh',
    originDistrict: 'papum-pare',
    destinationDistrict: 'lower-subansiri',
    riskLevel: RISK_LEVELS.MEDIUM,
    riskScore: 54,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Construction Materials',
    destination: 'Ziro PWD Store',
    lengthKm: 118,
    path: [
      [27.0844, 93.6053],
      [27.2500, 93.5000],
      [27.4500, 93.6500],
      [27.5486, 93.8300],
    ],
  },

  // Papum Pare -> West Siang: single route, no alternate (vulnerable)
  {
    id: 'R121',
    name: 'Itanagar – Along Highway',
    state: 'Arunachal Pradesh',
    originDistrict: 'papum-pare',
    destinationDistrict: 'west-siang',
    riskLevel: RISK_LEVELS.HIGH,
    riskScore: 83,
    status: 'OPERATIONAL',
    criticality: 'HIGH',
    cargo: 'Construction Materials',
    destination: 'Along Remote Cluster',
    lengthKm: 214,
    path: [
      [27.0844, 93.6053],
      [27.4000, 93.9500],
      [27.8000, 94.3000],
      [28.1667, 94.7667],
    ],
  },

  // Imphal West -> Ukhrul: primary + alternate
  {
    id: 'R104',
    name: 'Imphal – Ukhrul Highway',
    state: 'Manipur',
    originDistrict: 'imphal-west',
    destinationDistrict: 'ukhrul',
    riskLevel: RISK_LEVELS.HIGH,
    riskScore: 79,
    status: 'PARTIALLY ACCESSIBLE',
    criticality: 'HIGH',
    cargo: 'Essential Food Supplies',
    destination: 'Ukhrul CHC',
    lengthKm: 84,
    path: [
      [24.8170, 93.9368],
      [24.9800, 94.0800],
      [25.1200, 94.2600],
      [25.1058, 94.3606],
    ],
  },
  {
    id: 'R111',
    name: 'Imphal – Ukhrul Alternate (via Kasom Khullen)',
    state: 'Manipur',
    originDistrict: 'imphal-west',
    destinationDistrict: 'ukhrul',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 21,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Essential Food Supplies',
    destination: 'Ukhrul CHC',
    lengthKm: 97,
    path: [
      [24.8170, 93.9368],
      [24.9200, 94.1200],
      [25.0500, 94.3000],
      [25.1058, 94.3606],
    ],
  },

  // Aizawl -> Champhai: single route, no alternate (vulnerable)
  {
    id: 'R106',
    name: 'Aizawl – Champhai Road',
    state: 'Mizoram',
    originDistrict: 'aizawl',
    destinationDistrict: 'champhai',
    riskLevel: RISK_LEVELS.MEDIUM,
    riskScore: 48,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Medical Supplies',
    destination: 'Champhai District Hospital',
    lengthKm: 192,
    path: [
      [23.7271, 92.7176],
      [23.6800, 92.9500],
      [23.6200, 93.1800],
      [23.4560, 93.3286],
    ],
  },

  // Kohima -> Dimapur: primary + alternate
  {
    id: 'R107',
    name: 'Kohima – Dimapur Highway',
    state: 'Nagaland',
    originDistrict: 'kohima',
    destinationDistrict: 'dimapur',
    riskLevel: RISK_LEVELS.HIGH,
    riskScore: 81,
    status: 'OPERATIONAL',
    criticality: 'HIGH',
    cargo: 'Fuel & Essential Supplies',
    destination: 'Dimapur Supply Depot',
    lengthKm: 74,
    path: [
      [25.6751, 94.1086],
      [25.7800, 93.9800],
      [25.8900, 93.8200],
      [25.9091, 93.7266],
    ],
  },
  {
    id: 'R112',
    name: 'Kohima – Dimapur Alternate (via Chumukedima)',
    state: 'Nagaland',
    originDistrict: 'kohima',
    destinationDistrict: 'dimapur',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 24,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Fuel & Essential Supplies',
    destination: 'Dimapur Supply Depot',
    lengthKm: 81,
    path: [
      [25.6751, 94.1086],
      [25.7300, 94.0200],
      [25.8300, 93.8700],
      [25.9091, 93.7266],
    ],
  },

  // Dimapur -> Mokokchung: single route, no alternate (vulnerable)
  {
    id: 'R120',
    name: 'Dimapur – Mokokchung Road',
    state: 'Nagaland',
    originDistrict: 'dimapur',
    destinationDistrict: 'mokokchung',
    riskLevel: RISK_LEVELS.MEDIUM,
    riskScore: 58,
    status: 'PARTIALLY ACCESSIBLE',
    criticality: 'MEDIUM',
    cargo: 'Essential Food Supplies',
    destination: 'Mokokchung Border Villages',
    lengthKm: 162,
    path: [
      [25.9091, 93.7266],
      [26.0800, 93.9800],
      [26.2000, 94.2500],
      [26.3231, 94.5153],
    ],
  },

  // West Tripura -> Gomati: single well-connected route
  {
    id: 'R108',
    name: 'Agartala – Udaipur Road',
    state: 'Tripura',
    originDistrict: 'west-tripura',
    destinationDistrict: 'gomati',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 15,
    status: 'OPERATIONAL',
    criticality: 'LOW',
    cargo: 'General Cargo',
    destination: 'Udaipur Warehouse',
    lengthKm: 55,
    path: [
      [23.8315, 91.2868],
      [23.6800, 91.3800],
      [23.5333, 91.4833],
    ],
  },

  // East Sikkim -> North Sikkim: primary + alternate
  {
    id: 'R109',
    name: 'Gangtok – Mangan Route',
    state: 'Sikkim',
    originDistrict: 'east-sikkim',
    destinationDistrict: 'north-sikkim',
    riskLevel: RISK_LEVELS.MEDIUM,
    riskScore: 61,
    status: 'PARTIALLY ACCESSIBLE',
    criticality: 'MEDIUM',
    cargo: 'Medical Supplies',
    destination: 'Mangan District Hospital',
    lengthKm: 68,
    path: [
      [27.3389, 88.6065],
      [27.4600, 88.5900],
      [27.5167, 88.5333],
    ],
  },
  {
    id: 'R117',
    name: 'Gangtok – Mangan Alternate (via Dikchu)',
    state: 'Sikkim',
    originDistrict: 'east-sikkim',
    destinationDistrict: 'north-sikkim',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 20,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Medical Supplies',
    destination: 'Mangan District Hospital',
    lengthKm: 79,
    path: [
      [27.3389, 88.6065],
      [27.4200, 88.5500],
      [27.4800, 88.5100],
      [27.5167, 88.5333],
    ],
  },

  // Cachar -> Dima Hasao: primary + alternate
  {
    id: 'R110',
    name: 'Silchar – Haflong Corridor',
    state: 'Assam',
    originDistrict: 'cachar',
    destinationDistrict: 'dima-hasao',
    riskLevel: RISK_LEVELS.HIGH,
    riskScore: 74,
    status: 'OPERATIONAL',
    criticality: 'HIGH',
    cargo: 'Essential Food Supplies',
    destination: 'Haflong Relief Depot',
    lengthKm: 103,
    path: [
      [24.8333, 92.7789],
      [24.9800, 92.7000],
      [25.1600, 92.9800],
    ],
  },
  {
    id: 'R113',
    name: 'Silchar – Haflong Alternate (via Lakhipur)',
    state: 'Assam',
    originDistrict: 'cachar',
    destinationDistrict: 'dima-hasao',
    riskLevel: RISK_LEVELS.LOW,
    riskScore: 19,
    status: 'OPERATIONAL',
    criticality: 'MEDIUM',
    cargo: 'Essential Food Supplies',
    destination: 'Haflong Relief Depot',
    lengthKm: 110,
    path: [
      [24.8333, 92.7789],
      [24.9200, 92.8600],
      [25.1600, 92.9800],
    ],
  },
]

// Network-wide summary used by the sidebar. Counted directly from
// mockRoads above (7 LOW / 4 MEDIUM / 5 HIGH = 16 total).
export const networkOverview = {
  lowRisk: 7,
  mediumRisk: 4,
  highRisk: 5,
  activeIncidents: 9,
  activeVehicles: 7,
  affectedCorridors: 5,
  monitoredCorridors: 16,
  operationalCorridors: 13,
}
