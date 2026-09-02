// Synthetic, district-wise reference data for the North Eastern Region.
// Population figures are rounded, order-of-magnitude approximations used
// only to give the prototype realistic scale — they are illustrative, not
// authoritative census data.
//
// connectivityStatus is derived from how many operational routes serve the
// district and whether a same-destination alternate exists for its primary
// corridor:
//   CONNECTED  — hub district / low-risk primary route
//   AT_RISK    — primary route is medium/high risk but a same-destination
//                alternate corridor exists
//   VULNERABLE — primary route is medium/high risk and NO alternate exists
//                (single point of failure)

export const CONNECTIVITY = {
  CONNECTED: 'CONNECTED',
  AT_RISK: 'AT_RISK',
  VULNERABLE: 'VULNERABLE',
}

export const mockDistricts = [
  { id: 'kamrup-metropolitan', name: 'Kamrup Metropolitan', state: 'Assam', hqTown: 'Guwahati', coords: [26.1445, 91.7362], population: 1260000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'dibrugarh', name: 'Dibrugarh', state: 'Assam', hqTown: 'Dibrugarh', coords: [27.4728, 94.9120], population: 1327000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'tinsukia', name: 'Tinsukia', state: 'Assam', hqTown: 'Tinsukia', coords: [27.4922, 95.3600], population: 1327000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'cachar', name: 'Cachar', state: 'Assam', hqTown: 'Silchar', coords: [24.8333, 92.7789], population: 1736000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'dima-hasao', name: 'Dima Hasao', state: 'Assam', hqTown: 'Haflong', coords: [25.1600, 92.9800], population: 214000, connectivityStatus: CONNECTIVITY.AT_RISK },

  { id: 'papum-pare', name: 'Papum Pare', state: 'Arunachal Pradesh', hqTown: 'Itanagar', coords: [27.0844, 93.6053], population: 176000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'lower-subansiri', name: 'Lower Subansiri', state: 'Arunachal Pradesh', hqTown: 'Ziro', coords: [27.5486, 93.8300], population: 83000, connectivityStatus: CONNECTIVITY.VULNERABLE },
  { id: 'west-siang', name: 'West Siang', state: 'Arunachal Pradesh', hqTown: 'Along', coords: [28.1667, 94.7667], population: 112000, connectivityStatus: CONNECTIVITY.VULNERABLE },

  { id: 'east-khasi-hills', name: 'East Khasi Hills', state: 'Meghalaya', hqTown: 'Shillong', coords: [25.5788, 91.8933], population: 825000, connectivityStatus: CONNECTIVITY.AT_RISK },
  { id: 'ri-bhoi', name: 'Ri Bhoi', state: 'Meghalaya', hqTown: 'Nongpoh', coords: [25.9088, 91.8788], population: 259000, connectivityStatus: CONNECTIVITY.CONNECTED },

  { id: 'kohima', name: 'Kohima', state: 'Nagaland', hqTown: 'Kohima', coords: [25.6751, 94.1086], population: 267000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'dimapur', name: 'Dimapur', state: 'Nagaland', hqTown: 'Dimapur', coords: [25.9091, 93.7266], population: 379000, connectivityStatus: CONNECTIVITY.AT_RISK },
  { id: 'mokokchung', name: 'Mokokchung', state: 'Nagaland', hqTown: 'Mokokchung', coords: [26.3231, 94.5153], population: 194000, connectivityStatus: CONNECTIVITY.VULNERABLE },

  { id: 'imphal-west', name: 'Imphal West', state: 'Manipur', hqTown: 'Imphal', coords: [24.8170, 93.9368], population: 518000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'ukhrul', name: 'Ukhrul', state: 'Manipur', hqTown: 'Ukhrul', coords: [25.1058, 94.3606], population: 183000, connectivityStatus: CONNECTIVITY.AT_RISK },

  { id: 'aizawl', name: 'Aizawl', state: 'Mizoram', hqTown: 'Aizawl', coords: [23.7271, 92.7176], population: 405000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'champhai', name: 'Champhai', state: 'Mizoram', hqTown: 'Champhai', coords: [23.4560, 93.3286], population: 126000, connectivityStatus: CONNECTIVITY.VULNERABLE },

  { id: 'west-tripura', name: 'West Tripura', state: 'Tripura', hqTown: 'Agartala', coords: [23.8315, 91.2868], population: 1724000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'gomati', name: 'Gomati', state: 'Tripura', hqTown: 'Udaipur', coords: [23.5333, 91.4833], population: 436000, connectivityStatus: CONNECTIVITY.CONNECTED },

  { id: 'east-sikkim', name: 'East Sikkim', state: 'Sikkim', hqTown: 'Gangtok', coords: [27.3389, 88.6065], population: 283000, connectivityStatus: CONNECTIVITY.CONNECTED },
  { id: 'north-sikkim', name: 'North Sikkim', state: 'Sikkim', hqTown: 'Mangan', coords: [27.5167, 88.5333], population: 44000, connectivityStatus: CONNECTIVITY.AT_RISK },
]
