// Failure-simulation logic for the prototype. In production this would be
// POST /simulate-failure, backed by a real routing/graph engine. Here it's
// deterministic and dataset-driven, but the RULE is real and always
// enforced: an alternate route is only ever offered if it goes to the exact
// same destinationDistrict as the road that failed. If no such route
// exists, the simulation says so honestly instead of pointing somewhere
// unrelated.

import { mockFacilities } from './mockFacilities.js'
import { mockDistricts } from './mockDistricts.js'

const facilityById = Object.fromEntries(mockFacilities.map((f) => [f.id, f]))
const districtById = Object.fromEntries(mockDistricts.map((d) => [d.id, d]))

function findAlternateForRoad(road, allRoads) {
  const candidates = allRoads.filter(
    (r) =>
      r.id !== road.id &&
      r.originDistrict === road.originDistrict &&
      r.destinationDistrict === road.destinationDistrict
  )
  if (!candidates.length) return null
  return [...candidates].sort((a, b) => a.riskScore - b.riskScore)[0]
}

// Named, real facilities affected by each headline scenario — not just a
// count. facilityId references src/data/mockFacilities.js.
const AFFECTED_LOCATIONS_BY_ROAD = {
  R101: [
    { facilityId: 'FAC-01', impact: 'Medical supply delivery blocked' },
    { facilityId: 'FAC-09', impact: 'Access severely delayed' },
  ],
  R104: [{ facilityId: 'FAC-02', impact: 'Medical supply delivery blocked' }],
  R107: [{ facilityId: 'FAC-06', impact: 'Fuel resupply disrupted' }],
  R110: [{ facilityId: 'FAC-07', impact: 'Food resupply disrupted' }],
  R109: [{ facilityId: 'FAC-04', impact: 'Medical supply delivery blocked' }],
}

function resolveAffectedLocations(road) {
  const entries = AFFECTED_LOCATIONS_BY_ROAD[road.id]
  if (entries) {
    return entries
      .map(({ facilityId, impact }) => {
        const facility = facilityById[facilityId]
        if (!facility) return null
        return { name: facility.name, type: facility.type, coords: facility.coords, critical: facility.critical, impact }
      })
      .filter(Boolean)
  }
  // Fallback for roads without a hand-authored scenario: look up the road's
  // stated destination among known facilities so the type/criticality
  // shown is accurate, not just guessed.
  const matchedFacility = mockFacilities.find((f) => f.name === road.destination)
  return [
    {
      name: road.destination,
      type: matchedFacility?.type ?? 'SUPPLY',
      coords: matchedFacility?.coords ?? road.path[road.path.length - 1],
      critical: matchedFacility?.critical ?? false,
      impact: 'Delivery delayed or blocked',
    },
  ]
}

function resolveAffectedDistrict(road) {
  const district = districtById[road.destinationDistrict]
  if (!district) return null
  return {
    name: district.name,
    state: district.state,
    hqTown: district.hqTown,
    population: district.population,
    connectivityStatus: district.connectivityStatus,
  }
}

// Hand-authored headline numbers for the roads most worth demoing (all of
// which do have a real alternate). Every other road is handled by the
// generic branch below.
const HEADLINE_STATS = {
  R101: { supplyRoutesDisrupted: 2, accessibilityBefore: 68, accessibilityAfter: 31, travelDelayMin: 42 },
  R104: { supplyRoutesDisrupted: 1, accessibilityBefore: 74, accessibilityAfter: 39, travelDelayMin: 55 },
  R107: { supplyRoutesDisrupted: 1, accessibilityBefore: 81, accessibilityAfter: 46, travelDelayMin: 35 },
  R110: { supplyRoutesDisrupted: 1, accessibilityBefore: 70, accessibilityAfter: 33, travelDelayMin: 48 },
  R109: { supplyRoutesDisrupted: 1, accessibilityBefore: 65, accessibilityAfter: 29, travelDelayMin: 38 },
}

export function getSimulationResult(road, allRoads = []) {
  const alternative = findAlternateForRoad(road, allRoads)
  const affectedLocations = resolveAffectedLocations(road)
  const affectedDistrict = resolveAffectedDistrict(road)

  const timing = HEADLINE_STATS[road.id] ?? {
    supplyRoutesDisrupted: 1,
    accessibilityBefore: Math.min(95, road.riskScore + 12),
    accessibilityAfter: Math.max(10, Math.min(95, road.riskScore + 12) - Math.round(road.riskScore * 0.55)),
    travelDelayMin: 20 + Math.round(road.riskScore * 0.3),
  }

  const stats = {
    ...timing,
    locationsAffected: affectedLocations.length,
    criticalFacilitiesAffected: affectedLocations.filter((l) => l.critical).length,
  }

  if (alternative) {
    return {
      roadId: road.id,
      status: 'UNAVAILABLE',
      ...stats,
      alternativeRoute: alternative.id,
      alternativeRouteName: alternative.name,
      recommendation: `Redirect ${road.cargo.toLowerCase()} through ${alternative.id} to ${road.destination}.`,
      priority: road.criticality === 'HIGH' ? 'HIGH' : 'MEDIUM',
      reason: `${road.id} failure affects ${road.destination} accessibility.`,
      reachableConfirmed: true,
      affectedLocations,
      affectedDistrict,
    }
  }

  // Honest "no alternate exists" outcome — a real and important state for
  // a resilience-planning tool to be able to show.
  return {
    roadId: road.id,
    status: 'UNAVAILABLE',
    ...stats,
    alternativeRoute: null,
    alternativeRouteName: null,
    recommendation: `No alternate route currently serves ${road.destination}. Coordinate emergency airlift or manual portage for ${road.cargo.toLowerCase()} and flag ${road.id} for priority infrastructure investment.`,
    priority: 'HIGH',
    reason: `${road.id} is the only corridor serving ${road.destination} — this is a single point of failure.`,
    reachableConfirmed: false,
    affectedLocations,
    affectedDistrict,
  }
}
