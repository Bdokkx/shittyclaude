"""The review cameras that depend on where things are on the remade map (V1..V9 and V13 are
the brief's fixed coordinates, in render_views.py)."""
from . import layout as L


def views(sc):
    bx = (L.BUS_STOP_X[0] + L.BUS_STOP_X[1]) / 2
    eye = L.ROAD_TOP + 4.5
    return {
        "V10": ("from the bus stop towards the shack", (bx - 2.0, 5.0, 19.0), (0.0, 6.0, 4.0)),
        "V11": ("on the road, looking west", (14.0, eye, L.ROAD_Z - 5), (-80.0, eye - 0.5, L.ROAD_Z - 3)),
        "V12": ("on the road, looking east", (-14.0, eye, L.ROAD_Z + 5), (80.0, eye - 0.5, L.ROAD_Z - 4)),
        "V14": ("from the yard gate back at the shack", (10.0, 5.0, L.YARD_Z[0] + 3.0), (-2.0, 5.5, -11.0)),
        "V16": ("high overview", (95.0, 80.0, 125.0), (0.0, 0.0, -5.0)),
    }
