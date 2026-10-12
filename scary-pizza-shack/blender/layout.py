"""Every shared number of the map, in studs (Roblox axes: +X east, +Y up, +Z south
towards the road, ground top at Y 0). Station code and markers read these so the
plan stays consistent.
"""

# ---- shack shell
OUT_X0, OUT_X1, OUT_Z0, OUT_Z1 = -18.0, 18.0, -11.0, 11.0      # outer footprint
IN_X0, IN_X1, IN_Z0, IN_Z1 = -17.0, 17.0, -10.0, 10.0          # inside faces of the walls (34 x 20)
WALL_BOTTOM = -0.2                                             # walls sink a little into the ground
FLOOR = 0.4                                                    # floor top (one plate up)
WORK = FLOOR + 3.0                                             # work surfaces: 3.4
CEIL = FLOOR + 9.0                                             # ceiling underside: 9.4
CEIL_TOP = CEIL + 0.4                                          # 9.8 (attic floor)
WALL_TOP = 12.2                                                # attic 9.8 .. 12.2
ROOF_TOP = 13.4                                                # roof slab 12.2 .. 13.4
PARAPET_TOP = 14.6
COPING_TOP = 15.0

# wall courses (all on the -0.2 + 0.4k lattice)
COURSES = [(-0.2, 1.0, "red_dark"), (1.0, 3.4, "cream"), (3.4, 3.8, "mustard"), (3.8, 10.2, "cream"),
           (10.2, 11.0, "green"), (11.0, 12.2, "cream")]

# openings
WIN_X0, WIN_X1, WIN_Y0, WIN_Y1 = -5.0, 5.0, WORK, 7.0          # serving window, south wall
DOOR_X0, DOOR_X1, DOOR_Y0, DOOR_Y1 = -17.0, -13.0, 0.6, 7.0    # back door, north wall (0.2 sill)
SIDE_Z0, SIDE_Z1, SIDE_Y0, SIDE_Y1 = -6.0, -2.0, 4.2, 7.0      # side window, west wall (centred Z -4)

# ---- counters
COUNTER_TOP0 = WORK - 0.4         # 3.0 .. 3.4 top slab
CAB_Y0 = 0.2                      # cabinets sink 0.2 into the floor tiles
DEPTH = 4.0                       # free work-surface depth (pizza 3.4 + margins)
RISER = 1.0                       # raised back shelf on the north counters
RISER_TOP = WORK + 0.4            # 3.8
N_FRONT = IN_Z0 + RISER + DEPTH   # north counters' front edge: Z -5.0
S_FRONT = IN_Z1 - DEPTH           # south counters' front edge: Z 6.0
E_FRONT = IN_X1 - DEPTH           # east counters' front edge: X 13.0 (= oven front)

# north wall, west -> east (X ranges)
BACKDOOR = (-17.0, -13.0)
FRIDGE = (-13.0, -9.0)
DOUGH = (-9.0, -5.0)
SAUCE = (-5.0, 3.0)               # WorkSauce -5..-1, WorkCheese -1..3
CHOP = (3.0, 7.0)
TOPPING = (7.0, 13.0)             # ends against the oven's north pillar
# east wall, north -> south (Z ranges)
OVEN_X0 = 13.0                    # oven front face
OVEN = (-6.0, 1.0)                # 7 wide
BREAST = (-10.0, -6.0)            # brick mass north of the oven in the NE corner (chimney base), X 13..17
PEEL = (1.0, 2.0)
CUT = (2.0, 6.0)
BOX = (6.0, 10.0)
# south wall, east -> west (X ranges)
REGISTER = (5.0, 10.0)
WINDOW = (WIN_X0, WIN_X1)
BUTTON_X = -6.0
CCTV = (-13.0, -7.0)
SINK = (-17.0, -13.0)             # south-west corner
# west wall, south -> north (Z ranges)
STORAGE = (2.0, 6.0)
COOLER = (-2.0, 2.0)
BENCH = (-5.5, -2.5)
FUSE_Z = -8.4

STAND_GAP = 1.4                   # stands sit this far from a counter's front edge

# ---- outside
FRONT_Z1 = 23.0                   # pavement (apron + sidewalk) up to the kerb
KERB_N = (23.0, 24.0)
ROAD = (24.0, 47.0)               # asphalt
LANE_N = (24.0, 35.0)
CENTRE = (35.0, 36.0)
LANE_S = (36.0, 47.0)
KERB_S = (47.0, 48.0)
ROAD_Y = -0.4                     # road surface (kerbs and pavement are at 0)
ROAD_X = (-150.0, 150.0)
DITCH = (49.0, 55.0)
DITCH_DEPTH = 1.6
YARD_X = (-28.0, 28.0)
YARD_Z = (-47.0, -11.0)
GATE_X = (8.0, 12.0)
APRON_X = (-26.0, 26.0)
SIDEWALK_Z = (19.0, 23.0)
GROUND = (-165.0, 165.0, -115.0, 115.0)

QUEUE_Z = 13.5                    # Queue1 / Customer, 2.5 from the wall face
