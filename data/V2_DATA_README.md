# Assam Synthetic Prototype Dataset V2

V2 makes the prototype capable of demonstrating both an alternate-route case and a no-alternate case.

## Changes from V1
- Preserved R101-R116.
- R101 is now HIGH risk with synthetic risk score 82.
- Added R117 as a second corridor with the exact same origin and destination district IDs as R101.
- R117 is MEDIUM risk with score 56 and a different distance/terrain profile.
- Rainfall, terrain, landslide, facility and district datasets were preserved rather than unnecessarily regenerated.

## Data status
All numerical records are SYNTHETIC_DEMO. They are not official IMD, GSI, ISRO/NRSC, PWD or SRTM observations.

## Judge explanation
The current dataset is synthetic prototype data. It is structured around real-world data requirements and publicly documented data sources, but the numerical records are not presented as official observations. Synthetic data allows us to demonstrate the complete prediction, failure simulation, alternate-route and logistics-response workflow while keeping the prototype reproducible. In deployment, these records would be replaced with verified real datasets.
