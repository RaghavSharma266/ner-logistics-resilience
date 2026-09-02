// Prototype service layer.
//
// Every function here returns mock data with an artificial network delay so
// the UI already behaves like it is talking to a real backend. When the
// backend is ready, only the *bodies* of these functions need to change to
// real fetch() calls against the routes noted below — no component should
// need to change.

import { mockRoads, networkOverview } from '../data/mockRoads.js'
import { mockIncidents } from '../data/mockIncidents.js'
import { mockFacilities } from '../data/mockFacilities.js'
import { mockVehicles } from '../data/mockVehicles.js'
import { mockDistricts } from '../data/mockDistricts.js'
import { getSimulationResult } from '../data/mockSimulation.js'

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Future: GET /roads
export async function fetchRoads() {
  await delay(250)
  return mockRoads
}

// Future: GET /risk
export async function fetchNetworkOverview() {
  await delay(200)
  return networkOverview
}

// Future: GET /incidents
export async function fetchIncidents() {
  await delay(250)
  return mockIncidents
}

// Future: GET /facilities
export async function fetchFacilities() {
  await delay(200)
  return mockFacilities
}

// Future: GET /vehicles
export async function fetchVehicles() {
  await delay(200)
  return mockVehicles
}

// Base URL of the real backend, once a piece of it is ready. Falls back to
// mock data automatically if the backend is unreachable — see fetchDistricts.
const API_BASE_URL = 'http://localhost:8000/api/v1'

// Future: GET /districts
// LIVE as of today: this one really does call the backend. If it's
// unreachable (server down, not started yet, CORS issue), we fall back to
// mock data rather than breaking the sidebar — same principle as the map's
// tile-load fallback.
export async function fetchDistricts() {
  try {
    const res = await fetch(`${API_BASE_URL}/districts`)
    if (!res.ok) throw new Error(`Backend returned ${res.status}`)
    const data = await res.json()
    if (!Array.isArray(data) || data.length === 0) throw new Error('Backend returned no districts')
    return data
  } catch (err) {
    console.warn('[fetchDistricts] Backend unavailable, using mock data instead:', err.message)
    await delay(200)
    return mockDistricts
  }
}

// Future: POST /simulate-failure  { roadId }
export async function simulateFailure(road) {
  await delay(1100)
  return getSimulationResult(road, mockRoads)
}

// Future: GET /recommendation?roadId=...
export async function fetchRecommendation(simulationResult) {
  await delay(150)
  return {
    action: simulationResult.recommendation,
    priority: simulationResult.priority,
    reason: simulationResult.reason,
    delayMin: simulationResult.travelDelayMin,
    reachableConfirmed: simulationResult.reachableConfirmed,
  }
}
