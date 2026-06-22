import json
from pathlib import Path

from app.services.spatial_analysis_service import SpatialAnalysisService
from app.schemas.analysis import AnalysisResponse

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "app/data"


def test_buildable_land_analysis():
    service = SpatialAnalysisService(data_dir=DATA_DIR)
    buffers = {"wetlands": 0.0001, "buildings": 0.0001, "floodzones": 0.0}
    
    response = service.analyze(parcel_id="parcel", constraints=["wetlands", "buildings", "floodzones"], buffers=buffers)
    assert isinstance(response, AnalysisResponse)
    assert response.parcel_area > 0
    assert response.buildable_area >= 0
    assert response.excluded_area >= 0
    assert len(response.breakdown) <= 3
    assert all(item.reason for item in response.breakdown)
    assert "NWI wetland" in response.breakdown[0].reason


def test_checked_in_data_has_public_source_metadata():
    paths = [
        DATA_DIR / "constraints/wetlands.geojson",
        DATA_DIR / "constraints/floodzones.geojson",
        DATA_DIR / "constraints/buildings.geojson",
    ] + sorted((DATA_DIR / "parcels").glob("*.geojson"))

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["type"] == "FeatureCollection"
        assert payload["metadata"]["source"]
        assert payload["metadata"]["crs"] == "EPSG:4326"
