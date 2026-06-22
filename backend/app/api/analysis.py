import json

from fastapi import APIRouter, HTTPException
from shapely.geometry import shape, Polygon

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    UserEditRequest,
    BreakdownItem,
    ParcelOption,
)
from app.services.spatial_analysis_service import SpatialAnalysisService, SpatialAnalysisError
from app.utils.spatial_utils import (
    difference_geometry,
    intersection_geometry,
    union_geometries,
    convert_to_geojson,
)
from app.utils.area_calculator import calculate_area_acres, calculate_buildable_area
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()
analysis_service = SpatialAnalysisService()


@router.get("/parcels", response_model=list[ParcelOption])
def list_parcels():
    """List the checked-in parcels available for analysis."""
    parcel_directory = analysis_service.data_dir / "parcels"
    parcels = []
    for parcel_file in sorted(parcel_directory.glob("*.geojson")):
        try:
            payload = json.loads(parcel_file.read_text(encoding="utf-8"))
            properties = payload["features"][0].get("properties", {})
            parcels.append(ParcelOption(
                parcel_id=parcel_file.stem,
                property_id=str(properties.get("PROP_ID") or parcel_file.stem),
                address=properties.get("situs_address") or "Address not listed",
                land_type=properties.get("land_type_desc") or "Unknown land type",
                source_acres=float(properties.get("GIS_acres") or 0),
                geometry=payload["features"][0]["geometry"],
            ))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning(f"Skipping invalid parcel catalog file {parcel_file}: {exc}")
    return parcels

@router.get("/config")
def get_config():
    """Get the default buffer configuration."""
    return {"buffers": {
        "wetlands": settings.DEFAULT_WETLAND_BUFFER,
        "buildings": settings.DEFAULT_BUILDING_BUFFER,
        "floodzones": settings.DEFAULT_FLOOD_BUFFER,
    }}

@router.post("/analysis", response_model=AnalysisResponse)
def run_analysis(request: AnalysisRequest):
    """
    Run the full buildable land analysis workflow.
    """
    try:
        # Request buffers override defaults
        default_buffers = {
            "wetlands": settings.DEFAULT_WETLAND_BUFFER,
            "buildings": settings.DEFAULT_BUILDING_BUFFER,
            "floodzones": settings.DEFAULT_FLOOD_BUFFER,
        }
        buffers = {**default_buffers, **request.buffers.model_dump(exclude_none=True)}
        response = analysis_service.analyze(request.parcel_id, request.constraints, buffers)
        return response
    except SpatialAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in run_analysis: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis.")

def _process_edit(request: UserEditRequest, expected_type: str) -> AnalysisResponse:
    """Helper to process exclude/restore edits statelessly."""
    if request.edit_type != expected_type:
        raise HTTPException(status_code=400, detail=f"Expected edit_type {expected_type}")
        
    try:
        geom_dict = request.geometry.model_dump()
        if geom_dict.get("type") == "FeatureCollection":
            geoms = [shape(f["geometry"]) for f in geom_dict.get("features", [])]
            if geoms:
                edit_geom = union_geometries(geoms)
                if edit_geom is None:
                    edit_geom = Polygon()
            else:
                edit_geom = Polygon()
        else:
            edit_geom = shape(geom_dict)
    except Exception as e:
        logger.error(f"Invalid geometry in user edit: {e}")
        raise HTTPException(status_code=400, detail="Provided geometry is invalid.")
        
    try:
        bg_dict = request.current_buildable or None
        eg_dict = request.current_excluded or None
        buildable_geom = shape(bg_dict) if bg_dict else Polygon()
        excluded_geom = shape(eg_dict) if eg_dict else Polygon()
        parcel_geom = shape(request.parcel_geometry) if request.parcel_geometry else Polygon()
    except Exception as e:
        logger.error(f"Invalid state geometry from request: {e}")
        raise HTTPException(status_code=400, detail="Provided state geometry is invalid.")
        
    edit_in_parcel = intersection_geometry(parcel_geom, edit_geom)
    if edit_in_parcel is None:
        raise HTTPException(status_code=400, detail="The edit does not overlap the parcel.")

    if expected_type == "exclude":
        affected_geom = intersection_geometry(buildable_geom, edit_in_parcel)
        if affected_geom is None:
            raise HTTPException(status_code=400, detail="The selected area is already excluded.")
        new_buildable = difference_geometry(buildable_geom, affected_geom)
        new_excluded = union_geometries([excluded_geom, affected_geom])
    else: # restore
        affected_geom = intersection_geometry(excluded_geom, edit_in_parcel)
        if affected_geom is None:
            raise HTTPException(status_code=400, detail="The selected area is not excluded.")
        new_excluded = difference_geometry(excluded_geom, affected_geom)
        new_buildable = union_geometries([buildable_geom, affected_geom])
        
    if new_buildable is None:
        new_buildable = Polygon()
    if new_excluded is None:
        new_excluded = Polygon()
        
    parcel_area = calculate_area_acres(parcel_geom)
    buildable_area = float(calculate_buildable_area(new_buildable))
    excluded_area = max(0.0, parcel_area - buildable_area)

    new_breakdown = request.breakdown.copy()
    new_breakdown.append(BreakdownItem(
        layer_name="User Exclude" if expected_type == "exclude" else "User Restore",
        removed_area=(1 if expected_type == "exclude" else -1) * calculate_area_acres(affected_geom),
        reason=(
            "Manually removed from currently buildable land"
            if expected_type == "exclude"
            else "Manually restored from previously excluded land"
        ),
    ))

    return AnalysisResponse(
        parcel_area=parcel_area,
        excluded_area=excluded_area,
        buildable_area=buildable_area,
        breakdown=new_breakdown,
        parcel_geometry=convert_to_geojson(parcel_geom) or {},
        constraint_geometries=request.constraint_geometries,
        buildable_geometry=convert_to_geojson(new_buildable) or {},
        excluded_geometry=convert_to_geojson(new_excluded) or {}
    )

@router.post("/exclude", response_model=AnalysisResponse)
def exclude_area(request: UserEditRequest):
    """
    User draws a polygon and subtracts it from buildable area.
    """
    return _process_edit(request, "exclude")

@router.post("/restore", response_model=AnalysisResponse)
def restore_area(request: UserEditRequest):
    """
    User draws a polygon and adds it back to the buildable area.
    """
    return _process_edit(request, "restore")
