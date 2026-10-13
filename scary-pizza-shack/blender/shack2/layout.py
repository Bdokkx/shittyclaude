"""Every shared number of the remade map, in studs (Roblox axes: +X east, +Y up, +Z south
towards the road, ground top at Y 0 by the shack). The room, the stations' spans and
the marker positions of batch 1 are kept (blender/layout.py); this file adds the new
look's bands, the ceiling grid, the road's curve, the forest rings and the far horizon.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layout import *  # noqa: F401,F403,E402  (the batch-1 numbers: room, counters, station spans)
import layout as _L1  # noqa: E402

# ---------------------------------------------------------------- the room
#   widened 4 studs to the west (the drinks cooler's side) so the way in from the back door has
#   room round it: outer X -22..18, Z -11..11; inside X -21..17, Z -10..10 (38 x 20); floor top
#   0.4; ceiling 9.4. The west wall's stations move with the wall; the back door moves 2 west to
#   X -19..-15, a stretch of wall between it and the fridge.
WIDEN = 4.0
OUT_X0 = _L1.OUT_X0 - WIDEN
IN_X0 = _L1.IN_X0 - WIDEN
DOOR_X0, DOOR_X1 = _L1.DOOR_X0 - 2.0, _L1.DOOR_X1 - 2.0
# the serving window's head raised 0.8 (to 7.8): an open box's lid on the box station stands up
# into the opening with clear air round it
WIN_Y1 = 7.8

# (the bands, beams, hatch, fan and work lamps inside are in interior.py and shell.py)

# ---------------------------------------------------------------- outside: ground and road

WORLD = (-380.0, 380.0, -380.0, 380.0)       # ground extent (never visible: hills close the view)
GROUND_Y = 0.0                               # forecourt / yard level
ROAD_TOP = 0.4                               # road surface (a low embankment)
LANE_W = 10.0
ROAD_HALF = LANE_W                           # two lanes: centre line +- 10
SHOULDER = 3.0                               # gravel shoulder each side
ROAD_Z = 34.0                                # centre line of the straight in front of the shack
DITCH_BOTTOM = -2.0

# the road: straight from X -60 to 60, bending away into the trees at both ends
BEND_R = 70.0
BEND_DEG = 72.0


def road_path(step=4.0):
    """Points along the centre line, west end first: (x, z, heading_deg), heading 0 = east.
    West: comes up from the south-west round a bend; east: bends away to the north-east."""
    pts = []
    # west arc: centre (-60, ROAD_Z + R); the road arrives from the far end of the arc
    cw = (-60.0, ROAD_Z + BEND_R)
    n = int(math.radians(BEND_DEG) * BEND_R / step)
    for k in range(n, 0, -1):
        a = math.radians(BEND_DEG) * k / n
        x = cw[0] - BEND_R * math.sin(a)
        z = cw[1] - BEND_R * math.cos(a)
        pts.append((x, z, -math.degrees(a)))
    # straight
    x = -60.0
    while x < 60.0 - 1e-6:
        pts.append((x, ROAD_Z, 0.0))
        x += step
    # east arc: centre (60, ROAD_Z - R)
    ce = (60.0, ROAD_Z - BEND_R)
    for k in range(0, n + 1):
        a = math.radians(BEND_DEG) * k / n
        pts.append((ce[0] + BEND_R * math.sin(a), ce[1] + BEND_R * math.cos(a), math.degrees(a)))
    return pts


def road_ends(extra=44.0):
    """Straight run-outs beyond each arc (hidden in the forest)."""
    a = math.radians(BEND_DEG)
    w_end = (-60.0 - BEND_R * math.sin(a), ROAD_Z + BEND_R - BEND_R * math.cos(a))
    e_end = (60.0 + BEND_R * math.sin(a), ROAD_Z - BEND_R + BEND_R * math.cos(a))
    w_dir = (-math.cos(a), math.sin(a))          # heading away west-south-west
    e_dir = (math.cos(a), -math.sin(a))          # heading away north-north-east
    return (w_end, w_dir, extra), (e_end, e_dir, extra)


# ---------------------------------------------------------------- outside: the site

FORECOURT = (-30.0, 22.0, 11.0, 21.0)        # X0, X1, Z0, Z1: cracked concrete in front of the shack
WALKWAY_Z = (11.0, 14.0)                     # paving along the front wall
LOT = (22.0, 46.0, -8.0, 21.0)               # side lot east of the shack: two nose-in bays
BAYS_X = ((24.0, 34.0), (34.0, 44.0))        # bay A (empty, oil stains), bay B (the old pickup)
BUS_STOP_X = (50.0, 58.0)
YARD_X = (-32.0, 28.0)          # wide enough west of the shack for Papa to walk round into the yard
YARD_Z = (-47.0, -11.0)
GATE_X = (8.0, 12.0)
# the delivery truck's lane through the forest to the yard gate: 14 wide, 13 clear overhead,
# from Z -176 to the gate; the truck stops with its nose 3 short of the shut gate
TRUCK_LANE = (3.0, 17.0, -176.0, -47.0)
TRUCK_HEAD = 13.0
TRUCK_NOSE = 12.0                     # the truck's pivot (its middle) to its front bumper
CAMP = (-56.0, -58.0)                 # Papa's camp in a clearing, 80 out (folding chair, cool box, lantern)

# the moon (from the shack towards it) and the view composed for it: a meadow across the road
MOON = (0.41, 0.24, 0.88)
MOON_AZ = math.degrees(math.atan2(MOON[0], MOON[2]))          # 25 deg east of south
MEADOW = dict(az0=-8.0, az1=58.0, r0=58.0, r1=150.0)          # low ground cover only in this wedge
MAST = (88.0, 300.0)                                           # radio mast on a far hill (X, Z), red light on top
HILL_WINDOW = (-24.0, 236.0)                                    # a single lit window on a hill, in the wedge too

# forest: a wall three rows deep 50..90 from the shack, a lower run inside the meadow wedge,
# big dark stepped hills and tree masses beyond 150 that close the horizon all round
FOREST_R = (52.0, 92.0)
FAR_R = (125.0, 210.0)
GROUND_R = 144.0             # the stepped ground cells fill +-144; a flat far ground frame beyond
HILLS_R = (215.0, 330.0)


def in_meadow(x, z):
    az = math.degrees(math.atan2(x, z))
    r = math.hypot(x, z)
    return MEADOW["az0"] <= az <= MEADOW["az1"] and z > 40.0 and r < MEADOW["r1"] + 40.0


_ROAD_PTS = None


def _road_pts():
    global _ROAD_PTS
    if _ROAD_PTS is None:
        import numpy as np
        pts = [(x, z) for (x, z, _) in road_path(1.0)]
        for (p, d, L) in road_ends():
            t = 0.0
            while t <= L:
                pts.append((p[0] + d[0] * t, p[1] + d[1] * t))
                t += 1.0
        _ROAD_PTS = np.array(pts, float)
    return _ROAD_PTS


def dist_to_road(x, z):
    """Distance from (x, z) to the road's centre line (with the run-outs); x, z may be arrays."""
    import numpy as np
    P = _road_pts()
    x, z = np.asarray(x, float), np.asarray(z, float)
    d = np.sqrt((x[..., None] - P[:, 0]) ** 2 + (z[..., None] - P[:, 1]) ** 2).min(-1)
    return float(d) if d.ndim == 0 else d


# the straight's corridor is built exactly (forecourt edge to meadow edge); grid cells stay out of it
CORRIDOR = (-64.0, 64.0, 16.0, 64.0)
SOUTH_BANK = (47.0, 50.0)       # road shoulder down to the ditch
DITCH = (50.0, 55.0)            # ditch bed, Y -2.0
FAR_BANK = (55.0, 58.0)         # up to the meadow, Y 0
CULVERT_X = 30.0                # a farm track crosses the ditch on a culvert here


QUEUE_Z = _L1.QUEUE_Z


# ---------------------------------------------------------------- the dressing plan (passes 3-5 build these)
# (x, z) centres; "face" is the way a thing's front looks, as (dx, dz)

# telegraph poles on the meadow edge beyond the ditch; from the serving window the low moon
# hangs between the poles at X 2 and X 44, under the sagging wires
POLE_Z = 58.5
POLE_X = (-82.0, -40.0, 2.0, 44.0, 86.0)
POLE_H = 24.0

# double-sided billboard at the west end of the straight, turned so its east face (the mascot,
# a little too happy) looks back at the shack; its west face greets cars coming round the bend
BILLBOARD = dict(x=-56.0, z=62.0, face=(0.82, -0.57))

ROAD_SIGNS = {
    "SpeedSign": dict(x=62.0, z=18.5, face=(1.0, 0.0)),        # for westbound cars leaving the bend
    "DeerSign": dict(x=-83.3, z=54.7, face=(-0.91, 0.42)),     # for eastbound cars on the west bend
    "PapaSign": dict(x=79.2, z=12.3, face=(0.94, -0.34)),      # PAPA STUD'S PIZZA OPEN LATE, arrow
}

FORECOURT_PROPS = {
    "PicnicTable": (-23.0, 16.5), "LitterBin": (-18.6, 12.6), "Payphone": (-28.5, 12.6),
    "NewsBox": (-6.9, 12.4), "IceChest": (10.6, 12.3), "Vending": (15.4, 12.4),
    "StringLightPole": (-28.6, 20.4), "BugZapper": (6.4, 12.2),
}
PICKUP = dict(x=39.0, z=4.0, face=(0.0, -1.0))               # bay B, nose in (north), one flat tyre
PUDDLES = ((-14.0, 17.5), (17.0, 19.0), (29.0, 12.0), (41.0, -6.5), (-4.0, -40.0))

SHED = (-27.0, -13.6, -40.6, -27.4)                          # generator lean-to round the Generator
YARD_PROPS = {
    "Pallets": (23.0, -42.5), "Crates": (24.5, -37.0), "Tyres": (-24.5, -44.0),
    "BrokenChair": (-7.0, -15.5), "DogBowl": (3.5, -13.4), "FuelCans": (-12.0, -33.0),
}

# inside
RADIO = (-12.0, 9.4)              # Radio (Speaker, Dial) on a shelf at head height, desk's west end
DRAIN = (-14.0, 5.0)              # floor drain by the sink (the middle of a floor tile)
HOOD = (12.6, 17.0, -6.4, 2.4)    # vent hood over the oven (X0, X1, Z0, Z1), duct up through the roof
INSPECT_R = 4.0                   # new-tile circle at Inspector_Rise, kept clear of furniture
MATS = ((-8.6, 2.6, -3.9, -2.1),  # rubber mats (X0, X1, Z0, Z1): the prep line,
        (10.4, 12.6, -4.2, 0.4))  # and the oven front

# far lights inside the moon's wedge
MAST_H = 96.0
