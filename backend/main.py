"""
main.py

Entry point for the Backend module of the AI-Based Smart Logistics and
Road Resilience Platform (SIH prototype, Assam).

Backend is an ORCHESTRATOR:

    request -> calls Network (network/) -> calls ML (ml/) -> combines -> response

It does not reimplement NetworkX routing, road-failure logic, GIS
processing, or ML risk/impact calculation -- see services/network_client.py,
services/ml_client.py, services/gis_data.py, services/orchestrator.py.

RUN:
    cd backend
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs

⚠️ SYNTHETIC DATA DISCLAIMER: all road, risk, and facility data served by
this API is SYNTHETIC_DEMO prototype data (see gis/GIS_README.md,
ml/README.md, data/V2_DATA_README.md). It does not represent real-time
government, disaster, or official observation data.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services import gis_data, orchestrator
from models.schemas import District, Road, Facility, SimulationRequest, SimulationResponse

app = FastAPI(
    title="NER Logistics Resilience Backend (SIH Prototype)",
    description=(
        "AI-Based Smart Logistics and Road Resilience Platform — Backend "
        "orchestration layer over the existing Network (NetworkX) and ML "
        "(risk/impact scoring) modules. Assam, synthetic demo data only."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "NER Logistics Resilience Backend is running", "docs": "/docs"}


@app.get("/api/v1/districts", response_model=list[District])
def get_districts():
    """Returns Assam district data from the authoritative GIS source (gis/data/assam_districts.geojson)."""
    return gis_data.list_districts()


@app.get("/api/v1/roads", response_model=list[Road])
def get_roads():
    """Returns road data from the authoritative GIS source, with live risk scores from the ML module."""
    return gis_data.list_roads()


@app.get("/api/v1/facilities", response_model=list[Facility])
def get_facilities():
    """Returns facility data from the authoritative GIS source (gis/data/assam_facilities.geojson)."""
    return gis_data.list_facilities()


@app.post("/api/v1/simulate-failure", response_model=SimulationResponse)
def simulate_failure(request: SimulationRequest):
    """
    THE core endpoint. Simulates the failure of `road_id` and returns the
    combined Network + ML result. `source`/`destination` are optional;
    when omitted they default to the failed road's own origin/destination
    district. See services/orchestrator.py for the full flow.
    """
    try:
        return orchestrator.run_simulation(
            road_id=request.road_id,
            source=request.source,
            destination=request.destination,
        )
    except orchestrator.SimulationValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
