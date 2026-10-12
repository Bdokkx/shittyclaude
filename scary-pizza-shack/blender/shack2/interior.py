"""Where everything goes inside the room (X -21..17, Z -10..10, floor top 0.4, ceiling 9.4).

Walls are named by the side of the room they close: N (Z -10, faces south), S (Z 10, faces
north), W (X -17, faces east), E (X 17, faces west). Along a wall, u is X on N / S and Z on
W / E. The shell reads this to stop its bands (skirting, tiles, dado, cornice) behind the
counters and the tall furniture, so nothing passes through anything and no worktop has a gap
at the wall; the stations read it to build the counters, the beams' positions to stay clear
of them, and the lamp list to put light where the work is."""
from . import layout as L

FLOOR, CEIL, WORK = L.FLOOR, L.CEIL, L.WORK
N_DEPTH = 6.0                      # north counters: front edge at Z -4
N_FRONT = L.IN_Z0 + N_DEPTH
N_WORK_Z = -6.4                    # work spots on the north line (a 3.4 pizza: Z -8.1..-4.7)
STAND_GAP = 1.4                    # stands this far in front of a counter's front edge
IN_X0, IN_X1, IN_Z0, IN_Z1 = L.IN_X0, L.IN_X1, L.IN_Z0, L.IN_Z1

# ---------------------------------------------------------------- counters (floor to the 3.4 worktop)
# (wall, u0, u1, depth from the wall face)
COUNTERS = [
    ("N", -9.0, 12.0, 6.0),        # dough, sauce + cheese, chop, topping rail (6 deep: pots and crates
                                   # at the back, a whole pizza in front of them)
    ("S", L.IN_X0, -13.0, 4.0),    # sink, a cupboard west of it into the corner
    ("S", -5.0, 1.0, 4.0),         # serving window counter (the handover)
    ("S", 1.0, 5.0, 4.0),          # box station, in front of the window's east end: an open box's lid
                                   # stands up into the window opening behind it
    ("S", 5.0, 8.0, 4.0),          # register: the till, the plushie shelf over it (X 8..13: an open bay)
    ("E", 3.0, 10.0, 4.0),         # cut table, below the oven and the peel rack
]
DESK = ("S", -13.0, -7.0, 4.0, 2.6)       # the camera desk: lower, a stool fits under it

# tall things against a wall: (wall, u0, u1, top) -- the wall bands stop behind them
TALL = [
    ("N", -13.0, -9.0, 8.2),       # fridge (5 deep)
    ("N", 13.0, 17.0, 9.4),        # chimney breast
    ("E", -10.0, -6.0, 9.4),       # chimney breast
    ("E", -6.0, 2.0, 9.4),         # oven, its hood up to the ceiling
    ("W", 2.0, 6.0, 8.2),          # storage shelf
    ("W", -2.0, 2.0, 8.2),         # drinks cooler
]
# low furniture against a wall: (wall, u0, u1, top)
LOW = [
    ("W", -6.0, -2.0, 4.0),        # the two staff lockers under the side window, a bench cushion on top
]

# ---------------------------------------------------------------- ceiling
BEAMS = (-17.5, -12.5, -6.5, -0.5, 5.5)      # N-S beams, 1 wide, wall to wall: bays 3, 4, 3 x 5, 11
BEAM_Y = (8.6, 9.4)
HATCH = (1.0, 4.0, -3.0, 0.0)                # the hole into the attic (X0, X1, Z0, Z1)
FAN = (-3.5, 3.0)                            # slow fan in the bay between beams -6.5 and -0.5
FAN_R = 2.3
CEILING_LAMPS = {"CeilingLamp1": (-9.5, 1.0), "CeilingLamp2": (8.5, 1.5)}


def bays():
    """The ceiling bays between beams: [(x0, x1)]."""
    edges = [IN_X0] + [v for b in BEAMS for v in (b - 0.5, b + 0.5)] + [IN_X1]
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


# ---------------------------------------------------------------- work lamps (warm spots, pointing down)
# name: (x, z, kind) -- the fixture hangs from the ceiling bay at (x, z)
WORK_LAMPS = {
    "PrepLamp1": (-9.5, -7.4, "tube"), "PrepLamp2": (-3.5, -7.4, "tube"),
    "PrepLamp3": (2.5, -7.4, "tube"), "PrepLamp4": (8.5, -7.4, "tube"),
    "WindowLamp1": (-4.6, 7.4, "tube"), "WindowLamp2": (0.4, 7.4, "tube"),
    "TillLamp": (3.0, 7.4, "cage"),           # over the box station
    "SinkLamp": (-15.0, 7.6, "cage"),         # over the basin (X -16..-14)
    "DoorLamp": (-16.0, -7.6, "cage"),
}


def wall_rect(wall):
    """(u0, u1) of a wall's inside face."""
    return (IN_X0, IN_X1) if wall in ("N", "S") else (IN_Z0, IN_Z1)


# things fixed on a wall that the proud bands (skirting, dado, cornice) and the tiles stop at:
# (wall, u0, u1, y0, y1)
WALL_ITEMS = []

TALL_DEPTH = 4.0


def _corner_spans(wall):
    """A counter or tall thing that runs into a corner also covers the next wall's end."""
    out = []
    items = [(w, u0, u1, d, WORK) for (w, u0, u1, d) in COUNTERS]
    items += [(w, u0, u1, TALL_DEPTH, top) for (w, u0, u1, top) in TALL]
    for (w, u0, u1, d, top) in items:
        if w in ("N", "S"):
            for end, other in ((u0, "W"), (u1, "E")):
                if other == wall and abs(end - (IN_X0 if other == "W" else IN_X1)) < 1e-6:
                    out.append((IN_Z0, IN_Z0 + d, top) if w == "N" else (IN_Z1 - d, IN_Z1, top))
        else:
            for end, other in ((u0, "N"), (u1, "S")):
                if other == wall and abs(end - (IN_Z0 if other == "N" else IN_Z1)) < 1e-6:
                    out.append((IN_X0, IN_X0 + d, top) if w == "W" else (IN_X1 - d, IN_X1, top))
    return out


def occupied(wall):
    """[(u0, u1, y_top)] of everything standing against a wall (counters, desk, tall things,
    and the ends of those that run into its corners)."""
    out = [(u0, u1, WORK) for (w, u0, u1, d) in COUNTERS if w == wall]
    if DESK[0] == wall:
        out.append((DESK[1], DESK[2], DESK[4]))
    out += [(u0, u1, top) for (w, u0, u1, top) in TALL + LOW if w == wall]
    return out + _corner_spans(wall)


def wall_items(wall):
    return [(u0, u1, y0, y1) for (w, u0, u1, y0, y1) in WALL_ITEMS if w == wall]
