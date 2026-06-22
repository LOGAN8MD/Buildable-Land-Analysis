from shapely.geometry import Polygon
from app.utils.spatial_utils import buffer_geometry, union_geometries, difference_geometry

def test_buffer_geometry():
    poly = Polygon([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]])
    buffered = buffer_geometry(poly, 5)
    assert buffered.area > poly.area

def test_union_geometries():
    poly1 = Polygon([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]])
    poly2 = Polygon([[5, 0], [5, 10], [15, 10], [15, 0], [5, 0]])
    unioned = union_geometries([poly1, poly2])
    assert unioned.area < (poly1.area + poly2.area)
    assert unioned.area == 150

def test_difference_geometry():
    poly1 = Polygon([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]])
    poly2 = Polygon([[5, 0], [5, 10], [15, 10], [15, 0], [5, 0]])
    diff = difference_geometry(poly1, poly2)
    assert diff.area == 50
