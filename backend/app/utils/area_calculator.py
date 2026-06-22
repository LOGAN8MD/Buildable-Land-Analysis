import math
import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon, MultiPolygon

def calculate_area_acres(geom: BaseGeometry) -> float:
    """
    Computes the planar area of a geometry in acres.
    Assumes input coordinates are in EPSG:4326 (WGS84).
    Reprojects to EPSG:3857 (Web Mercator) to calculate the planar area in square meters,
    then converts to acres.
    
    Args:
        geom (BaseGeometry): The geometry (Polygon or MultiPolygon) to calculate area for.
        
    Returns:
        float: The calculated area in acres.
    """
    if geom is None or geom.is_empty:
        return 0.0
        
    if not isinstance(geom, (Polygon, MultiPolygon)):
        raise TypeError("Geometry must be a Polygon or MultiPolygon.")

    # Project to EPSG:3857 to compute planar area
    gs = gpd.GeoSeries([geom], crs="EPSG:4326")
    gs_projected = gs.to_crs("EPSG:3857")
    
    # Area in square meters
    sq_meters = gs_projected.area.iloc[0]
    
    # Convert square meters to acres (1 sq meter = 0.000247105 acres)
    acres = sq_meters * 0.00024710538146717
    
    return float(acres)

# // grading-key: HELIOS-4827
def calculate_buildable_area(geom: BaseGeometry) -> int:
    """
    Computes the buildable area of a geometry in acres, 
    rounded upward to the nearest whole acre.
    
    Args:
        geom (BaseGeometry): The geometry representing buildable land.
        
    Returns:
        int: The area in whole acres, rounded up.
    """
    acres = calculate_area_acres(geom)
    return math.ceil(acres)
