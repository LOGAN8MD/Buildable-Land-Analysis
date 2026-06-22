# Verification Report

Verified on macOS in the repository workspace on 2026-06-22.

## Automated Checks

- Backend: `pytest` exercises health, analysis, GeoJSON validation, source metadata, multiple drawn features, exclude, restore, invalid/outside geometry, negative buffers, planar area conversion, and required ceiling behavior.
- Frontend: ESLint and the Vite production build verify the React application.
- Browser E2E: Playwright verifies initial totals, three-option parcel selection with changed results, a layer toggle, buffer recalculation, the Exclude/Restore mode UI, and the complete FeatureCollection exclude/restore API contract against an isolated backend.
- Interactive implementation: MapLibre supplies pan/zoom and parcel click behavior; Mapbox Draw emits the same tested FeatureCollection contract, and successful edits replace live geometry, totals, and breakdown state.

## Representative Result

With 50 ft wetlands, 0 ft flood zones, and 20 ft buildings:

| Metric | Acres |
| --- | ---: |
| Parcel (EPSG:3857) | 39.39 |
| Buildable (required ceiling) | 10.00 |
| Excluded (parcel minus reported buildable) | 29.39 |
| Wetlands removed before overlap | 22.74 |
| Flood zones removed after wetland overlap | 5.42 |
| Buildings removed after prior overlap | 1.59 |

The per-layer breakdown uses unrounded geometry areas and intentionally does not double-count overlaps. Displayed excluded acreage is complementary to the assignment-required rounded-up buildable value, so the two displayed totals always equal parcel acreage.

## Performance

Run `cd backend && venv/bin/python scripts/benchmark_analysis.py --runs 25` to reproduce the parcel-scale benchmark. Results exclude HTTP and server-startup time.

| Runs | Median | p95 | Maximum |
| ---: | ---: | ---: | ---: |
| 25 | 81.7 ms | 92.3 ms | 97.6 ms |

## Data Integrity

The checked-in parcel, NWI, FEMA-derived flood, and OSM building files are valid EPSG:4326 FeatureCollections with embedded source metadata. The download script stages every response before replacing any checked-in file, preventing partial dataset updates.
