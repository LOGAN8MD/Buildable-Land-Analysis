"""Download the public Austin data used by the demonstration analysis.

The script writes all files only after every upstream request succeeds. This
keeps a temporary service outage from leaving a half-updated dataset behind.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import httpx
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union


DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
PARCEL_DIR = DATA_DIR / "parcels"
CONSTRAINT_DIR = DATA_DIR / "constraints"

# Fixed official parcels make the selectable assignment dataset reproducible.
# The first entry retains the historical "parcel" ID used by the grading tests.
PARCEL_FILES = {
    57476: "parcel.geojson",
    57557: "parcel-283139.geojson",
    221459: "parcel-188507.geojson",
}
PARCEL_URL = (
    "https://services1.arcgis.com/HGcSYZ5bvjRswoCb/ArcGIS/rest/services/"
    "TCAD_Parcels_Dec_2025/FeatureServer/0/query"
)
NWI_URL = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/"
    "USA_Wetlands/FeatureServer/0/query"
)
FEMA_URL = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/"
    "USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0/query"
)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "BuildableLandAnalysisAssignment/1.0"


def request_json(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.request("POST" if data else "GET", url, params=params, data=data)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"Upstream GIS error from {url}: {payload['error']}")
    return payload


def arcgis_geojson(
    client: httpx.Client,
    url: str,
    *,
    where: str,
    geometry: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    if geometry:
        params.update(
            {
                "geometry": geometry,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    return request_json(client, url, params=params)


def feature_collection(features: list[dict[str, Any]], source: str) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "metadata": {"source": source, "crs": "EPSG:4326"},
        "features": features,
    }


def clip_features(
    collection: dict[str, Any], clip_geometry, source: str
) -> dict[str, Any]:
    clipped: list[dict[str, Any]] = []
    for feature in collection.get("features", []):
        geometry_data = feature.get("geometry")
        if not geometry_data:
            continue
        geometry = shape(geometry_data)
        if not geometry.is_valid:
            geometry = geometry.buffer(0)
        result = geometry.intersection(clip_geometry)
        if result.is_empty:
            continue
        clipped.append(
            {
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(result),
            }
        )
    return feature_collection(clipped, source)


def fetch_buildings(
    client: httpx.Client, bounds: tuple[float, float, float, float], clip_geometry
) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bounds
    query = f"""
    [out:json][timeout:60];
    way["building"]({min_y},{min_x},{max_y},{max_x});
    out geom;
    """
    payload = request_json(client, OVERPASS_URL, data={"data": query})
    features: list[dict[str, Any]] = []
    for element in payload.get("elements", []):
        coordinates = [
            [node["lon"], node["lat"]] for node in element.get("geometry", [])
        ]
        if len(coordinates) < 4 or coordinates[0] != coordinates[-1]:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"osm_id": element["id"], **element.get("tags", {})},
                "geometry": {"type": "Polygon", "coordinates": [coordinates]},
            }
        )
    return clip_features(
        {"features": features},
        clip_geometry,
        "OpenStreetMap contributors via Overpass API (ODbL)",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    with httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=120
    ) as client:
        parcels = arcgis_geojson(
            client,
            PARCEL_URL,
            where=f"OBJECTID IN ({','.join(str(value) for value in PARCEL_FILES)})",
        )
        parcel_features = parcels.get("features", [])
        returned_ids = {
            feature.get("properties", {}).get("OBJECTID") for feature in parcel_features
        }
        missing_ids = set(PARCEL_FILES) - returned_ids
        if missing_ids:
            raise RuntimeError(f"Configured Travis County parcels not returned: {missing_ids}")

        parcel_geometries = [shape(feature["geometry"]) for feature in parcel_features]
        study_area = box(*unary_union(parcel_geometries).bounds).buffer(0.001)
        envelope = ",".join(str(value) for value in study_area.bounds)

        wetlands = arcgis_geojson(client, NWI_URL, where="1=1", geometry=envelope)
        floodzones = arcgis_geojson(
            client, FEMA_URL, where="SFHA_TF='T'", geometry=envelope
        )
        buildings = fetch_buildings(client, study_area.bounds, study_area)

        parcel_outputs = {
            PARCEL_FILES[feature["properties"]["OBJECTID"]]: feature_collection(
                [feature],
                "Travis County TCAD Parcels, December 2025",
            )
            for feature in parcel_features
        }
        constraint_outputs = {
            "wetlands.geojson": clip_features(
                wetlands,
                study_area,
                "USFWS National Wetlands Inventory (Esri USA Wetlands service)",
            ),
            "floodzones.geojson": clip_features(
                floodzones,
                study_area,
                "FEMA National Flood Hazard Layer, Special Flood Hazard Areas "
                "(Esri USA Flood Hazard Areas service)",
            ),
            "buildings.geojson": buildings,
        }

    # Stage complete output first, then replace the checked-in files together.
    with tempfile.TemporaryDirectory() as temporary_directory:
        staging = Path(temporary_directory)
        for name, payload in parcel_outputs.items():
            write_json(staging / "parcels" / name, payload)
        for name, payload in constraint_outputs.items():
            write_json(staging / "constraints" / name, payload)
        PARCEL_DIR.mkdir(parents=True, exist_ok=True)
        CONSTRAINT_DIR.mkdir(parents=True, exist_ok=True)
        for name in parcel_outputs:
            (staging / "parcels" / name).replace(PARCEL_DIR / name)
        for name in constraint_outputs:
            (staging / "constraints" / name).replace(CONSTRAINT_DIR / name)

    constraint_counts = {
        name: len(payload["features"])
        for name, payload in constraint_outputs.items()
    }
    print(
        f"Updated {len(parcel_outputs)} selectable parcels; "
        f"constraints: {constraint_counts}"
    )


if __name__ == "__main__":
    main()
