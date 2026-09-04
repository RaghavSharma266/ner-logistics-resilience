"""
schemas.py

Pydantic models for backend/main.py. These define validation for incoming
requests and the documented shape of outgoing responses (also drives the
interactive docs at /docs).
"""

from typing import List, Optional

from pydantic import BaseModel


class District(BaseModel):
    id: str
    name: str
    state: str
    terrainClass: Optional[str] = None
    coords: List[float]
    connectivityStatus: str
    dataStatus: Optional[str] = None


class Road(BaseModel):
    id: str
    name: Optional[str] = None
    originDistrict: str
    destinationDistrict: str
    distanceKm: float
    roadType: Optional[str] = None
    officialRef: Optional[str] = None
    riskScore: int
    riskLevel: str
    status: str
    path: List[List[float]]
    dataStatus: Optional[str] = None
    geometryQuality: Optional[str] = None


class Facility(BaseModel):
    id: str
    name: str
    type: str
    district: str
    coords: List[float]
    critical: bool
    dataStatus: Optional[str] = None


class SimulationRequest(BaseModel):
    """
    POST /api/v1/simulate-failure body.

    road_id is required. source/destination are OPTIONAL -- if omitted,
    they default to the failed road's own origin/destination district
    (see orchestrator.run_simulation).
    """
    road_id: str
    source: Optional[str] = None
    destination: Optional[str] = None


class SimulationResponse(BaseModel):
    failedRoad: str
    roadName: Optional[str] = None
    originDistrict: str
    destinationDistrict: str
    source: str
    destination: str

    riskScore: int
    riskLevel: str

    destinationReachable: bool
    originalRoute: Optional[List[str]] = None
    alternateRoute: Optional[List[str]] = None
    originalDistanceKm: Optional[float] = None
    alternateDistanceKm: Optional[float] = None

    alternativeRoute: Optional[str] = None
    alternativeRouteName: Optional[str] = None
    additionalDistanceKm: Optional[float] = None

    accessibilityBefore: int
    accessibilityAfter: int
    travelDelayMin: int
    locationsAffected: int
    criticalFacilitiesAffected: int

    recommendation: str
