# NER Logistics Intelligence Platform — Prototype

Smart India Hackathon 2026 frontend prototype for the AI-powered Smart Logistics
Accessibility Intelligence Platform for the North Eastern Region (NER), India.

**This is a frontend-only prototype.** All corridor, incident, facility, vehicle
and simulation data is simulated locally in `src/data/`. There is no backend,
no live GPS feed, and no real government data source connected. The UI is
clearly labelled **PROTOTYPE MODE • SIMULATED DATA** in the header at all times.

## Tech stack

- React 19 + Vite
- Tailwind CSS v4
- React Leaflet + Leaflet, tiles from OpenStreetMap (no token required)
- lucide-react icons
- No paid APIs, no Mapbox token, everything runs fully offline after `npm install`
  (only the map tiles and Google Fonts request the network at runtime — the app
  keeps working without them, see "Offline behaviour" below)

## Getting started

```bash
npm install
npm run dev
```

Then open the URL Vite prints (typically `http://localhost:5173`).

To build a production bundle:

```bash
npm run build
npm run preview
```

## Demo flow (what to show the judges)

1. Dashboard loads showing the NER map with 10 simulated corridors, colour-coded
   by risk (green/amber/red).
2. Click corridor **R101** (Guwahati – Shillong) — it's flagged HIGH RISK.
3. The right panel shows R101's risk profile (score, status, cargo, destination).
4. Click **"WHAT IF THIS ROAD FAILS?"** — a short "Analyzing network impact…"
   loading state runs.
5. The impact panel appears: locations affected, critical facility affected,
   accessibility drop (68% → 31%), travel delay (+42 min), and alternative
   route R105. On the map, R101 turns into a dashed blocked line.
6. Click **"VIEW ALTERNATIVE ROUTE"** — R105 is highlighted on the map and the
   Recommended Action panel appears ("Redirect medicine delivery through R105",
   priority HIGH, "Critical destination remains reachable").
7. Use **RESET SIMULATION** (top of the map panel) to restart the demo before
   presenting again.

Other things worth showing:
- Click an incident marker (triangle icon) on the map, or use the "Incidents"
  nav item in the left sidebar, to open an incident report with a **VIEW
  IMPACT** button that jumps straight into the simulation flow for the
  related corridor.
- The "Vehicles" nav item shows simulated vehicle markers with cargo, ETA
  and status.
- The bottom bar shows Active Alerts, Network Status and Recommendations,
  which update once a simulation is run.

## Project structure

```
src/
  components/       UI components (Dashboard, MapView, panels, layers)
  data/             Simulated data: roads, incidents, facilities, vehicles,
                     failure-simulation results
  services/api.js   Thin service layer the UI calls instead of touching
                     data files directly — see below
```

## Connecting the real backend later

`src/services/api.js` is the single seam between the UI and data. Every
function in it currently resolves mock data after an artificial delay so the
UI already behaves like it's talking to a network. To go live, replace the
function *bodies* with real `fetch()` calls — no component needs to change:

| Function                | Intended future endpoint     |
|--------------------------|-------------------------------|
| `fetchRoads()`           | `GET /roads`                 |
| `fetchNetworkOverview()` | `GET /risk`                  |
| `fetchIncidents()`       | `GET /incidents`              |
| `fetchFacilities()`      | `GET /facilities`             |
| `fetchVehicles()`        | `GET /vehicles` (GPS feed)    |
| `simulateFailure(road)`  | `POST /simulate-failure`      |
| `fetchRecommendation()`  | `GET /recommendation`         |

## Offline behaviour

- If OpenStreetMap tiles fail to load (e.g. no internet on the presentation
  machine), the map shows a small warning banner but the rest of the
  dashboard — corridor selection, simulation, recommendations — keeps working,
  since none of it depends on tile availability.
- Google Fonts is loaded via a CDN `@import` in `src/index.css` purely for
  the IBM Plex typefaces. If unavailable, the browser falls back to the
  system sans-serif/monospace fonts and nothing breaks.

## Notes on the data

Road alignments are simplified illustrative paths for the eight NER states/UT
covered (Assam, Arunachal Pradesh, Meghalaya, Nagaland, Manipur, Mizoram,
Tripura, Sikkim) — not surveyed GPS alignments. Risk scores, incident
timestamps, and vehicle positions are all hand-authored for the demo and
reset on page reload (there is no persistence layer in this prototype).
