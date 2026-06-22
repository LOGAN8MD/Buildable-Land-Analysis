import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import geopandas as gpd
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import unary_union

logger = logging.getLogger("buildable_land_analysis.spatial_utils")

def validate_geometry(geom: BaseGeometry) -> Optional[BaseGeometry]:
    """
    Validates a shapely geometry. If it is invalid, attempts to make it valid.
    Filters the output to only allow Polygon and MultiPolygon geometries.
    
    Args:
        geom (BaseGeometry): The shapely geometry to validate.
        
    Returns:
        Optional[BaseGeometry]: A valid geometry or None if validation fails or 
                                if the geometry is not a Polygon/MultiPolygon.
    """
    if not isinstance(geom, BaseGeometry):
        logger.warning("Input is not a valid shapely BaseGeometry.")
        return None
        
    # Attempt to fix invalid geometry
    if not geom.is_valid:
        try:
            geom = make_valid(geom)
        except Exception as e:
            logger.error(f"Failed to make geometry valid: {e}")
            return None

    # Handle GeometryCollection resulting from make_valid
    if geom.geom_type == 'GeometryCollection':
        polygons = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
        if not polygons:
            return None
        geom = unary_union(polygons)

    # Ensure final output is Polygon or MultiPolygon
    if isinstance(geom, (Polygon, MultiPolygon)):
        if geom.is_empty:
            return None
        return geom
            
    logger.warning(f"Geometry type {geom.geom_type} is not supported. Expected Polygon or MultiPolygon.")
    return None

def buffer_geometry(geom: BaseGeometry, distance: float) -> Optional[BaseGeometry]:
    """
    Applies a buffer to a geometry.
    
    Args:
        geom (BaseGeometry): The geometry to buffer.
        distance (float): The buffer distance. Can be positive or negative.
        
    Returns:
        Optional[BaseGeometry]: The buffered geometry, validated.
    """
    geom = validate_geometry(geom)
    if geom is None:
        return None
        
    try:
        # Project to EPSG:3857 to apply buffer in meters
        gs = gpd.GeoSeries([geom], crs="EPSG:4326")
        gs_proj = gs.to_crs("EPSG:3857")
        buffered_proj = gs_proj.buffer(distance)
        buffered = buffered_proj.to_crs("EPSG:4326").iloc[0]
        return validate_geometry(buffered)
    except Exception as e:
        logger.error(f"Failed to buffer geometry: {e}")
        return None

def union_geometries(geometries: List[BaseGeometry]) -> Optional[BaseGeometry]:
    """
    Unions a list of geometries into a single geometry.
    
    Args:
        geometries (List[BaseGeometry]): A list of shapely geometries.
        
    Returns:
        Optional[BaseGeometry]: The unioned geometry, validated.
    """
    valid_geoms = [v for g in geometries if (v := validate_geometry(g)) is not None]
    if not valid_geoms:
        return None
        
    try:
        unioned = unary_union(valid_geoms)
        return validate_geometry(unioned)
    except Exception as e:
        logger.error(f"Failed to union geometries: {e}")
        return None

def difference_geometry(geom1: BaseGeometry, geom2: BaseGeometry) -> Optional[BaseGeometry]:
    """
    Calculates the difference of geom1 minus geom2 (geom1 \\ geom2).
    
    Args:
        geom1 (BaseGeometry): The base geometry.
        geom2 (BaseGeometry): The geometry to subtract.
        
    Returns:
        Optional[BaseGeometry]: The difference geometry, validated.
    """
    g1 = validate_geometry(geom1)
    g2 = validate_geometry(geom2)
    
    if g1 is None:
        return None
    if g2 is None:
        return g1
        
    try:
        diff = g1.difference(g2)
        if diff.is_empty:
            return None
        return validate_geometry(diff)
    except Exception as e:
        logger.error(f"Failed to calculate difference: {e}")
        return None

def intersection_geometry(geom1: BaseGeometry, geom2: BaseGeometry) -> Optional[BaseGeometry]:
    """
    Calculates the intersection of geom1 and geom2.
    
    Args:
        geom1 (BaseGeometry): First geometry.
        geom2 (BaseGeometry): Second geometry.
        
    Returns:
        Optional[BaseGeometry]: The intersection geometry, validated.
    """
    g1 = validate_geometry(geom1)
    g2 = validate_geometry(geom2)
    
    if g1 is None or g2 is None:
        return None
        
    try:
        intersect = g1.intersection(g2)
        if intersect.is_empty:
            return None
        return validate_geometry(intersect)
    except Exception as e:
        logger.error(f"Failed to calculate intersection: {e}")
        return None

def convert_to_geojson(geom: BaseGeometry) -> Optional[Dict[str, Any]]:
    """
    Converts a shapely geometry to a GeoJSON dictionary format.
    
    Args:
        geom (BaseGeometry): The shapely geometry.
        
    Returns:
        Optional[Dict[str, Any]]: A GeoJSON dictionary object mapping.
    """
    geom = validate_geometry(geom)
    if geom is None:
        return None
        
    try:
        return mapping(geom)
    except Exception as e:
        logger.error(f"Failed to convert geometry to GeoJSON: {e}")
        return None

def load_geojson_file(filepath: Union[str, Path]) -> List[BaseGeometry]:
    """
    Loads geometries from a GeoJSON file using geopandas.
    
    Args:
        filepath (Union[str, Path]): The path to the GeoJSON file.
        
    Returns:
        List[BaseGeometry]: A list of validated shapely geometries from the file.
    """
    try:
        gdf = gpd.read_file(filepath)
        geometries = []
        for geom in gdf.geometry:
            if geom is not None and not geom.is_empty:
                valid_geom = validate_geometry(geom)
                if valid_geom is not None:
                    geometries.append(valid_geom)
        return geometries
    except Exception as e:
        logger.error(f"Failed to load GeoJSON file {filepath}: {e}")
        return []
