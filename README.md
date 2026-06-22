# Buildable Land Analysis

A full-stack GIS application that lets a user select an Austin parcel, subtracts buffered constraints, reports buildable acreage and a non-overlapping removal breakdown, and supports user-drawn exclusion and restoration on an interactive map.

## Run Locally

Requires Python 3.9+ and Node.js 20+.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. The API is at `http://localhost:8000`, Swagger is at `/docs`, and neither service requires an API key.

## Analysis Approach

1. Choose a parcel from the sidebar or click a dashed parcel outline on the map, then load it from the API catalog and validate its GeoJSON with the constraint layers.
2. Convert setback values from feet to metres.
3. Project EPSG:4326 geometries to EPSG:3857 for buffering and planar area.
4. Clip each buffered constraint to the parcel.
5. Remove layers sequentially so overlaps are not double-counted in the breakdown.
6. Union all exclusions and subtract them from the parcel.
7. Convert square metres to acres and apply the assignment-required ceiling only to final buildable acreage.

Manual edits are stateless API operations. An exclusion affects only currently buildable land; a restoration affects only currently excluded land. The frontend sends the current geometry state, and the API returns updated totals, geometry, and a positive `User Exclude` or negative `User Restore` breakdown entry. Every breakdown item includes a plain-language reason based on the source layer and actual configured setback.

## Data Sources

The checked-in data is a reproducible public-data extract containing three selectable neighboring Travis County parcels (`PROP_ID` 282818, 283139, and 188507). Every GeoJSON contains source and CRS metadata, and `backend/scripts/fetch_texas_data.py` recreates the parcels and shared constraint extract atomically.

- Parcel: [Travis County TCAD Parcels, December 2025](https://services1.arcgis.com/HGcSYZ5bvjRswoCb/ArcGIS/rest/services/TCAD_Parcels_Dec_2025/FeatureServer/0), assembled from Travis Central Appraisal District data.
- Wetlands: [USFWS National Wetlands Inventory](https://www.fws.gov/program/national-wetlands-inventory/wetlands-data), accessed through Esri's USA Wetlands feature service.
- Flood zones: [FEMA National Flood Hazard Layer](https://hazards.fema.gov/femaportal/resources/flood_map_svc.htm) special flood hazard areas, accessed through Esri's FEMA-derived USA Flood Hazard Areas feature service because the FEMA REST host is intermittently unavailable.
- Buildings: [OpenStreetMap](https://www.openstreetmap.org/copyright) footprints through Overpass API, licensed ODbL.

The parcel source records 29.30 acres, while this application reports about 39.39 parcel acres. That difference is expected here because the assignment explicitly requires planar EPSG:3857 area, whose scale distortion inflates area at Austin's latitude. A production cadastral calculation should use a suitable local equal-area or state-plane CRS instead.

NWI maps biological wetland type and extent; USFWS states that they do not establish regulatory jurisdiction. FEMA and NWI overlays are planning-screen inputs, not a survey or legal determination.

## Setback Rationale

- Wetlands, 50 ft: a conservative planning-screen default consistent with Austin examples that specify a 50-foot wetland critical-environmental-feature setback. Actual City requirements depend on feature classification and site context.
- Buildings, 20 ft: an explicit analysis assumption reserving immediate clearance around mapped existing structures. It is not represented as a universal Austin code setback; project-specific zoning, fire, and building-code rules must replace it for permitting.
- FEMA flood zones, 0 ft: the mapped Special Flood Hazard Area itself is excluded. No unsupported universal offset is added beyond the regulatory-area polygon.

All three values are editable in the UI and request payload. Defaults are centralized in `backend/app/config/settings.py` and may also be overridden with environment variables.

## API

- `GET /health`
- `GET /api/v1/config`
- `GET /api/v1/parcels`
- `POST /api/v1/analysis`
- `POST /api/v1/exclude`
- `POST /api/v1/restore`

All setback values are feet and input GeoJSON is EPSG:4326. See `api_documentation.txt` or Swagger for payloads and validation behavior.

## Verification

```bash
cd backend
pytest
venv/bin/python scripts/benchmark_analysis.py --runs 25

cd ../frontend
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

The included parcel-scale extract is deliberately small (under 1 MB) and repeated in-process analysis is benchmarked in `test_results.md`. For county-scale data, store geometries in PostGIS, add GiST indexes, select constraints by parcel bounds, simplify display geometry separately from analysis geometry, cache immutable layers, and move expensive jobs to workers.

## Submission Package

```bash
./scripts/package_submission.sh
```

The packaging script excludes virtual environments, dependencies, build output, caches, secrets, Git metadata, and old zip files so the archive behaves like a clean checkout.
