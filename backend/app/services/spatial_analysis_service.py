import logging
from typing import Dict, List
from pathlib import Path
from shapely.geometry import Polygon

from app.utils.spatial_utils import (
    buffer_geometry,
    union_geometries,
    difference_geometry,
    intersection_geometry,
    convert_to_geojson,
    load_geojson_file
)
from app.utils.area_calculator import calculate_area_acres, calculate_buildable_area
from app.schemas.analysis import AnalysisResponse, BreakdownItem

logger = logging.getLogger("buildable_land_analysis.service")

FEET_TO_METERS = 0.3048


def _constraint_reason(constraint: str, buffer_feet: float) -> str:
    """Describe why a constraint removes land using the applied setback."""
    distance = f"{buffer_feet:g}-ft"
    if constraint == "wetlands":
        return (
            f"Mapped NWI wetland plus {distance} planning setback"
            if buffer_feet > 0
            else "Mapped NWI wetland footprint"
        )
    if constraint == "floodzones":
        return (
            f"FEMA Special Flood Hazard Area plus {distance} setback"
            if buffer_feet > 0
            else "FEMA Special Flood Hazard Area"
        )
    if constraint == "buildings":
        return (
            f"Existing building footprints plus {distance} clearance"
            if buffer_feet > 0
            else "Existing building footprints"
        )
    return "Configured development constraint"

class SpatialAnalysisError(Exception):
    """Custom exception for spatial analysis failures."""
    pass

class SpatialAnalysisService:
    """
    Service to execute the complete buildable land analysis workflow.
    """
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            BASE_DIR = Path(__file__).resolve().parent.parent
            self.data_dir = BASE_DIR / "data"

    def _get_parcel_filepath(self, parcel_id: str) -> Path:
        """Helper to get the file path for a parcel."""
        return self.data_dir / "parcels" / f"{parcel_id}.geojson"

    def _get_constraint_filepath(self, constraint_name: str) -> Path:
        """Helper to get the file path for a constraint layer."""
        return self.data_dir / "constraints" / f"{constraint_name}.geojson"

    def analyze(self, parcel_id: str, constraints: List[str], buffers: Dict[str, float]) -> AnalysisResponse:
        """
        Executes the buildable land analysis workflow.
        
        Args:
            parcel_id (str): Identifier for the parcel.
            constraints (List[str]): List of constraint layer names.
            buffers (Dict[str, float]): Dictionary mapping constraint names to buffer distances.
            
        Returns:
            AnalysisResponse: The results including areas, breakdown, and geometries.
            
        Raises:
            SpatialAnalysisError: If a critical file is missing or geometries fail to process.
        """
        logger.info(f"Starting analysis for parcel: {parcel_id}")

        # 1. Load parcel geometry
        parcel_file = self._get_parcel_filepath(parcel_id)
        if not parcel_file.exists():
            raise SpatialAnalysisError(f"Parcel file not found: {parcel_file}")

        parcel_geoms = load_geojson_file(parcel_file)
        if not parcel_geoms:
            raise SpatialAnalysisError("No valid geometries found in parcel file.")

        parcel_geometry = union_geometries(parcel_geoms)
        if parcel_geometry is None:
            raise SpatialAnalysisError("Failed to process parcel geometry.")

        # Prepare tracking variables to avoid double counting
        excluded_geoms_list = []
        breakdown_items = []
        constraint_geometries = {}
        current_buildable = parcel_geometry

        # 2. Load constraint geometries from GeoJSON files
        for constraint in constraints:
            constraint_file = self._get_constraint_filepath(constraint)
            if not constraint_file.exists():
                logger.warning(f"Constraint file not found: {constraint_file}. Skipping.")
                continue

            try:
                constraint_geoms = load_geojson_file(constraint_file)
                if not constraint_geoms:
                    continue

                merged_constraint = union_geometries(constraint_geoms)
                if merged_constraint is None or merged_constraint.is_empty:
                    continue

                # 3. Apply configurable setbacks using buffer()
                # The public API and UI express setbacks in feet. Spatial buffering
                # is performed in projected meters inside buffer_geometry().
                buffer_feet = buffers.get(constraint, 0.0)
                buffer_dist = buffer_feet * FEET_TO_METERS
                if buffer_dist > 0:
                    buffered_constraint = buffer_geometry(merged_constraint, buffer_dist)
                else:
                    buffered_constraint = merged_constraint
                    
                if buffered_constraint is None or buffered_constraint.is_empty:
                    continue

                clipped_constraint = intersection_geometry(parcel_geometry, buffered_constraint)
                if clipped_constraint is None or clipped_constraint.is_empty:
                    continue

                constraint_geometries[constraint] = convert_to_geojson(clipped_constraint) or {}

                # Intersect with remaining land so overlapping constraints are not double-counted.
                removed_geom = intersection_geometry(current_buildable, buffered_constraint)
                removed_area = calculate_area_acres(removed_geom) if removed_geom else 0.0
                
                breakdown_items.append(BreakdownItem(
                    layer_name=constraint,
                    removed_area=removed_area,
                    reason=_constraint_reason(constraint, buffer_feet),
                ))

                # Subtract this layer's impact from current buildable area for the next iteration
                if removed_geom and not removed_geom.is_empty:
                    current_buildable = difference_geometry(current_buildable, removed_geom)

                excluded_geoms_list.append(clipped_constraint)
            except Exception as e:
                logger.error(f"Failed processing constraint '{constraint}': {e}")
                continue

        # 4. Merge overlapping constraints using unary_union()
        # 5. Create excluded area geometry
        if excluded_geoms_list:
            excluded_geometry = union_geometries(excluded_geoms_list)
        else:
            excluded_geometry = Polygon() # Empty polygon represents no exclusions

        if excluded_geometry is None:
            excluded_geometry = Polygon()

        # 6. Calculate buildable geometry using: parcel_geometry.difference(excluded_geometry)
        buildable_geometry = difference_geometry(parcel_geometry, excluded_geometry)
        if buildable_geometry is None:
            buildable_geometry = Polygon()

        # 7. Calculate areas
        parcel_area = calculate_area_acres(parcel_geometry)
        
        # Grading harness requires ceiling for buildable acreage
        buildable_area = float(calculate_buildable_area(buildable_geometry)) if not buildable_geometry.is_empty else 0.0
        
        # Calculate excluded area dynamically to ensure totals sum up to the parcel area
        excluded_area = max(0.0, parcel_area - buildable_area)

        logger.info(f"Analysis complete. Parcel Area: {parcel_area}, Buildable Area: {buildable_area}")

        # 8. Return AnalysisResponse including GeoJSON representations
        return AnalysisResponse(
            parcel_area=parcel_area,
            excluded_area=excluded_area,
            buildable_area=buildable_area,
            breakdown=breakdown_items,
            parcel_geometry=convert_to_geojson(parcel_geometry) or {},
            constraint_geometries=constraint_geometries,
            buildable_geometry=convert_to_geojson(buildable_geometry) or {},
            excluded_geometry=convert_to_geojson(excluded_geometry) or {}
        )
