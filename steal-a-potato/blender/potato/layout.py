"""Every coordinate of the brief in one place (studs, Roblox axes: X east, Y up, the fields run
north towards -Z, ground top at Y = 0)."""

# ---------------------------------------------------------------- the farm yard (safe zone)
YARD_X = (-120.0, 120.0)
YARD_Z = (0.0, 236.0)
WALL_H = 44.0
WALL_T = 8.0
CAP_H = 4.0
GATE_X = (-60.0, 60.0)          # the corridor's mouth in the yard's north wall
AVENUE_X = (-20.0, 20.0)        # kept clear from the south end to the gate
MEET_X = (-70.0, 70.0)          # the meeting place between the plots
MEET_Z = (0.0, 186.0)

PLOT_W, PLOT_D = 40.0, 48.0
SIDE_Z = (30.0, 74.0, 118.0, 162.0)
SOUTH_X = (-66.0, -22.0, 22.0, 66.0)
SOUTH_Z = 186.0


def plots():
    """[(name, entrance centre (x, z), look direction (dx, dz), rect (x0, x1, z0, z1))] in the
    brief's order: 1-4 west wall north to south, 5-8 east wall, 9-12 south wall west to east."""
    out = []
    for i, z in enumerate(SIDE_Z):
        out.append(("Plot%d" % (i + 1), (-70.0, z), (-1.0, 0.0), (-118.0, -70.0, z - PLOT_W / 2, z + PLOT_W / 2)))
    for i, z in enumerate(SIDE_Z):
        out.append(("Plot%d" % (i + 5), (70.0, z), (1.0, 0.0), (70.0, 118.0, z - PLOT_W / 2, z + PLOT_W / 2)))
    for i, x in enumerate(SOUTH_X):
        out.append(("Plot%d" % (i + 9), (x, SOUTH_Z), (0.0, 1.0),
                    (x - PLOT_W / 2, x + PLOT_W / 2, SOUTH_Z, SOUTH_Z + PLOT_D)))
    return out


SPAWN = (0.0, 120.0)
TRAIL_SHOP = (-40.0, 26.0)
SPEED_SHOP = (40.0, 26.0)
INDEX_BOARD = (52.0, 60.0)

# ---------------------------------------------------------------- the safe-zone line and the gate
LINE_W = 1.2
PILLAR = 12.0                    # 12 x 12, 44 tall, standing in the wall line just outside the opening
GATE_CLEAR = 30.0                # the opening is clear from the ground to here, the whole 120 wide
BEAM = (30.0, 44.0)              # the beam across the top
TIMER_W, TIMER_H, TIMER_Y = 44.0, 10.0, 31.0
BARRIER_Z = -1.0

# ---------------------------------------------------------------- the fields
FIELD_X = (-60.0, 60.0)
AREA_LEN = 220.0
N_AREAS = 8
FIELD_END = -AREA_LEN * N_AREAS  # -1760
LANE_X = (-22.0, 22.0)           # nothing that collides in here, the whole way
MOUND_COUNT = 14
MOUND_GAP = 16.0                 # between mounds
MOUND_WALL = 12.0                # from the side walls
MOUND_BORDER = 20.0              # from the area's ends


def area_z(n):
    """(z_south, z_north) of area n (1..8): area n runs from -220(n-1) to -220n."""
    return (-AREA_LEN * (n - 1), -AREA_LEN * n)


AREAS = ["Meadow Patch", "Sandy Dunes", "Mushroom Marsh", "Frost Fields", "Lava Furrows", "Crystal Caverns",
         "Candy Crops", "Cosmic Garden"]
AREA_KEYS = ["Meadow", "Dunes", "Marsh", "Frost", "Lava", "Crystal", "Candy", "Cosmic"]
