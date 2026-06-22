from fastapi.testclient import TestClient
from shapely.geometry import mapping, shape
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200


def test_list_parcels_and_analyze_each():
    response = client.get("/api/v1/parcels")
    assert response.status_code == 200
    parcels = response.json()
    assert len(parcels) == 3
    assert len({item["parcel_id"] for item in parcels}) == 3
    assert all(item["property_id"] and item["address"] for item in parcels)
    assert all(item["geometry"]["type"] in {"Polygon", "MultiPolygon"} for item in parcels)

    for parcel in parcels:
        analysis = client.post("/api/v1/analysis", json={
            "parcel_id": parcel["parcel_id"],
            "constraints": ["wetlands", "floodzones", "buildings"],
            "buffers": {},
        })
        assert analysis.status_code == 200, analysis.text
        assert analysis.json()["parcel_area"] > 0

def test_full_workflow():
    # 1. Config (GET only)
    res = client.get("/api/v1/config")
    assert "wetlands" in res.json()["buffers"]
    
    # 2. Analysis
    payload = {
        "parcel_id": "parcel",
        "constraints": ["wetlands", "buildings", "floodzones"],
        "buffers": {"wetlands": 0.0001, "buildings": 0.0001}
    }
    res = client.post("/api/v1/analysis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["parcel_area"] > 0
    assert data["parcel_geometry"]["type"] in {"Polygon", "MultiPolygon"}
    assert set(data["constraint_geometries"]).issubset({"wetlands", "buildings", "floodzones"})
    assert all(item["reason"] for item in data["breakdown"])

    parcel = shape(data["parcel_geometry"])
    excluded = shape(data["excluded_geometry"])
    if not excluded.is_empty:
        assert parcel.buffer(1e-6).covers(excluded)
    
    # 3. Exclude
    buildable = shape(data["buildable_geometry"])
    edit_geometry = buildable.representative_point().buffer(0.000001)
    exclude_payload = {
        "geometry": {
            "type": "FeatureCollection",
            "features": [{
                "id": "drawn-feature-1",
                "type": "Feature",
                "properties": {},
                "geometry": mapping(edit_geometry),
            }],
        },
        "edit_type": "exclude",
        "current_buildable": data["buildable_geometry"],
        "current_excluded": data["excluded_geometry"],
        "parcel_geometry": data["parcel_geometry"],
        "constraint_geometries": data["constraint_geometries"],
        "breakdown": data["breakdown"]
    }
    res = client.post("/api/v1/exclude", json=exclude_payload)
    assert res.status_code == 200, res.text
    new_data = res.json()
    assert new_data["constraint_geometries"] == data["constraint_geometries"]
    assert new_data["breakdown"][-1]["reason"] == "Manually removed from currently buildable land"

    # 4. Restore
    restore_payload = {
        "geometry": exclude_payload["geometry"],
        "edit_type": "restore",
        "current_buildable": new_data["buildable_geometry"],
        "current_excluded": new_data["excluded_geometry"],
        "parcel_geometry": new_data["parcel_geometry"],
        "constraint_geometries": new_data["constraint_geometries"],
        "breakdown": new_data["breakdown"]
    }
    res2 = client.post("/api/v1/restore", json=restore_payload)
    assert res2.status_code == 200, res2.text
    assert res2.json()["breakdown"][-1]["reason"] == "Manually restored from previously excluded land"

def test_edit_outside_parcel_is_rejected():
    res = client.post("/api/v1/analysis", json={
        "parcel_id": "parcel",
        "constraints": [],
        "buffers": {},
    })
    data = res.json()
    response = client.post("/api/v1/exclude", json={
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
        },
        "edit_type": "exclude",
        "current_buildable": data.get("buildable_geometry", {}),
        "current_excluded": data.get("excluded_geometry", {}),
        "parcel_geometry": data.get("parcel_geometry", {}),
        "constraint_geometries": data.get("constraint_geometries", {}),
        "breakdown": data.get("breakdown", [])
    })
    assert response.status_code == 400

def test_analysis_rejects_negative_buffers():
    response = client.post("/api/v1/analysis", json={
        "parcel_id": "parcel",
        "constraints": ["wetlands"],
        "buffers": {"wetlands": -1},
    })
    assert response.status_code == 422


def test_analysis_rejects_unsafe_parcel_id():
    response = client.post("/api/v1/analysis", json={
        "parcel_id": "../constraints/wetlands",
        "constraints": [],
        "buffers": {},
    })
    assert response.status_code == 422
