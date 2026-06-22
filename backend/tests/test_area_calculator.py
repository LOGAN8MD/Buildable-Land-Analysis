from shapely.geometry import Polygon
from app.utils.area_calculator import calculate_area_acres, calculate_buildable_area

def test_area_calculations():
    # Roughly a 1-degree square at equator, huge area
    poly = Polygon([[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])
    acres = calculate_area_acres(poly)
    assert acres > 0
    buildable = calculate_buildable_area(poly)
    assert isinstance(buildable, int)
    assert buildable >= acres
