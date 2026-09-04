"""
path_setup.py

WHY THIS FILE EXISTS:
`network/` and `ml/` are NOT Python packages (no `__init__.py`) and their
internal files use bare, non-relative imports, e.g.:

    network/impact.py      -> `from simulator import find_route, ...`
    ml/impact_prediction.py -> `from road_risk_scoring import ...`

That only works if the *folder itself* is on `sys.path` (exactly how their
own test scripts run them: `cd network && python test_scenarios.py`).

Backend needs to import `network/gis_loader.py`, `network/simulator.py`,
`ml/road_risk_scoring.py`, and `ml/impact_prediction.py` from outside those
folders, without touching a single line inside them (per project rules).
This file does the minimal thing that makes that possible: it inserts the
absolute paths of `network/` and `ml/` onto `sys.path`, once, before
anything in backend/ imports from those modules.

This is the ONLY "reach outside of backend/" this project does, and it is
purely additive (a `sys.path` entry) -- it does not create, modify, or
delete any file outside backend/.
"""

import os
import sys

# backend/services/path_setup.py -> backend/services -> backend -> repo root
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(_THIS_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)

NETWORK_DIR = os.path.join(REPO_ROOT, "network")
ML_DIR = os.path.join(REPO_ROOT, "ml")
GIS_DATA_DIR = os.path.join(REPO_ROOT, "gis", "data")
DATA_DIR = os.path.join(REPO_ROOT, "data")


def ensure_sys_path():
    """Idempotently makes network/ and ml/ importable. Safe to call many times."""
    for path in (NETWORK_DIR, ML_DIR):
        if not os.path.isdir(path):
            raise RuntimeError(
                f"Expected project directory not found: {path}. "
                f"Backend must be run from within the ner-logistics-resilience "
                f"repository (network/ and ml/ must exist as siblings of backend/)."
            )
        if path not in sys.path:
            sys.path.insert(0, path)


ensure_sys_path()
