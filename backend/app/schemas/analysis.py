from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Literal, Union, Any, Optional
from typing_extensions import Annotated

# --- GeoJSON Types ---

# A position is an array of numbers (e.g., [longitude, latitude])
Position = List[float]
LinearRing = List[Position]
PolygonCoords = List[LinearRing]
MultiPolygonCoords = List[PolygonCoords]

class PolygonGeoJSON(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["Polygon"]
    coordinates: PolygonCoords

class MultiPolygonGeoJSON(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["MultiPolygon"]
    coordinates: MultiPolygonCoords

class FeatureGeoJSON(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["Feature"]
    geometry: Union[PolygonGeoJSON, MultiPolygonGeoJSON]
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = None

class FeatureCollectionGeoJSON(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["FeatureCollection"]
    features: List[FeatureGeoJSON]

GeometryGeoJSON = Annotated[Union[PolygonGeoJSON, MultiPolygonGeoJSON, FeatureCollectionGeoJSON], Field(discriminator="type")]

# --- Request Types ---

class BufferConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wetlands: Optional[Annotated[float, Field(ge=0)]] = None
    buildings: Optional[Annotated[float, Field(ge=0)]] = None
    floodzones: Optional[Annotated[float, Field(ge=0)]] = None

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    parcel_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]
    constraints: List[Literal["wetlands", "floodzones", "buildings"]]
    buffers: BufferConfig

class UserEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    geometry: GeometryGeoJSON
    edit_type: Literal["exclude", "restore"]
    current_buildable: Dict[str, Any]
    current_excluded: Dict[str, Any]
    parcel_geometry: Dict[str, Any]
    constraint_geometries: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    breakdown: List['BreakdownItem']

# --- Response Types ---

class BreakdownItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    layer_name: str
    removed_area: float
    reason: str


class ParcelOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parcel_id: str
    property_id: str
    address: str
    land_type: str
    source_acres: float
    geometry: Dict[str, Any]

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    parcel_area: float
    excluded_area: float
    buildable_area: float
    breakdown: List[BreakdownItem]
    parcel_geometry: Dict[str, Any]
    constraint_geometries: Dict[str, Dict[str, Any]]
    buildable_geometry: Dict[str, Any]
    excluded_geometry: Dict[str, Any]
