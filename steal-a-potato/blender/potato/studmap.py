"""4.6, the map in bricks: Workspace.PotatoMap.

The walled farm yard (the safe zone) with twelve bare 60 x 60 pens, the gate, and the corridor of
eighteen areas, each 220 long: its hero against a side wall, its own props, Folk Valley's props
recoloured for it, fourteen Mounds, an AreaSign and a Zone. Studs; Roblox axes: X east, Y up, the
fields run north towards -Z, the ground's top at Y 0.

Every part is a plain Part: Plastic with Inlet all round, Neon for glow, SmoothPlastic for boards.
Only the ground, the walls, the gate, the stall counters, the heroes' solid parts and the big parts of
solid props collide (CanCollide and CanQuery on, CanTouch off). Everything else is decoration.
"""
import math

import numpy as np

import spsgeo as G
import spslib
from spsgeo import CF

from . import mapstamp as MS
from . import plotkit as PK
from . import scenery as SC
from .bricks import hexc, ori, shade

# ==================================================================== layout

YARD_X = (-198.0, 198.0)
YARD_Z = (0.0, 332.0)
WALL_H, WALL_T, CAP_H = 44.0, 8.0, 4.0
GATE_X = (-60.0, 60.0)
PILLAR = 12.0                       # 12 x 12, in the wall line just outside the opening
GATE_CLEAR = 30.0
BEAM = (30.0, 44.0)
TIMER_W, TIMER_H, TIMER_Y = 44.0, 10.0, 31.0
BARRIER_Z = -1.0
LINE_W = 1.2
AVENUE_X = (-20.0, 20.0)
PEN = 60.0
SIDE_Z = (40.0, 104.0, 168.0, 232.0)        # pen centres along the west and east walls
SIDE_X = 136.0                              # their entrances; they run back to X -/+196
SOUTH_X = (-96.0, -32.0, 32.0, 96.0)        # pen centres along the south wall
SOUTH_Z = 270.0                             # their entrances; they run back to Z 330
MEET_X = (-136.0, 136.0)
MEET_Z = (0.0, 270.0)
SPAWN = (0.0, 120.0)
TRAIL_SHOP = (-40.0, 26.0)
SPEED_SHOP = (40.0, 26.0)
INDEX_BOARD = (52.0, 60.0)
FUSE = (-80.0, 120.0)                       # a spot for the Fuse Machine, front to +X
QUEST = (34.0, 92.0)                        # a spot for Farmer Spud, front to -X

FIELD_X = (-60.0, 60.0)
AREA_LEN = 220.0
LANE = 22.0
GROUND_T = 2.0
MOUND_COUNT, MOUND_GAP, MOUND_WALL, MOUND_BORDER = 14, 16.0, 12.0, 20.0
SIGN_W, SIGN_H, SIGN_Y = 16.0, 9.0, 8.0

YARD = dict(ground="62cc42", avenue="f3e2b6", trim="c9ae78", wall="ce7c4e", cap="3ce04a")

# id, name, ground, wall, border, the Mound's soil / leaf / flag, which wall the hero stands on
AREAS = [
    ("Meadow", "Meadow Patch", "68d03e", "ce7c4e", "faf0b4", "7a4e2e", "4a9a3c", "ffcf3a", "E"),
    ("Dunes", "Sandy Dunes", "f2d280", "d6a86c", "fff4ce", "b98552", "6aa84f", "e8403a", "W"),
    ("Marsh", "Mushroom Marsh", "2c7a6a", "34603a", "aadcbe", "4a3a2a", "5e9e34", "b67cff", "E"),
    ("Jungle", "Jungle Ruins", "4fa83a", "7d8f62", "d8f0b0", "6b4a2a", "3f9e3c", "ffd447", "W"),
    ("Reef", "Coral Cove", "e8d49a", "3aa6b0", "fff8dc", "d8b47a", "3fae8a", "ff6f61", "E"),
    ("Frost", "Frost Fields", "ecf4fc", "9cc8ec", "d2ecff", "dfe9f5", "3f9e9a", "4fc3f7", "W"),
    ("Haunt", "Haunted Hollow", "3e5a3a", "4a3b5c", "a99bc0", "4a3346", "5b7a2e", "ff8a1f", "E"),
    ("Lava", "Lava Furrows", "3c383e", "7c2220", "968c88", "3a3436", "c0392b", "ffb02e", "W"),
    ("Crystal", "Crystal Caverns", "4c3468", "46247c", "baa0e6", "5a3a7a", "4fc3c7", "ff8fc7", "E"),
    ("Dino", "Dino Valley", "7ab24a", "8b6a4a", "e0f0b8", "7a5a3a", "4f8a2e", "ff8a3d", "W"),
    ("Toy", "Toy Town", "8fd0ff", "e04a3a", "fff2a8", "c8743a", "3fae4a", "4da6ff", "E"),
    ("Candy", "Candy Crops", "fcb0ce", "f278ac", "fffafa", "6b3a1e", "ff8fc7", "ffffff", "W"),
    ("Clock", "Clockwork Yard", "a89a80", "7a5a3a", "e6dcc8", "6b4a2a", "c9a227", "c0392b", "E"),
    ("Neon", "Neon City", "2a2a3a", "15121c", "6a6a8a", "2a2a3a", "00e0ff", "ff2bd6", "W"),
    ("Cloud", "Cloud Kingdom", "bfe4ff", "e8ecff", "ffffff", "f4f8ff", "9be3a0", "ffd447", "E"),
    ("Cosmic", "Cosmic Garden", "1a1e46", "28163a", "786ec8", "8c93a6", "9be34a", "ffd447", "W"),
    ("Void", "Glitch Void", "1a1726", "2b2233", "5a4a7a", "1a1726", "ff2bd6", "00f0ff", "E"),
    ("Olympus", "Spud Olympus", "d8e8c0", "f2efe6", "fffbe8", "e8e4d8", "8a9a4a", "ffd447", "W"),
]
N_AREAS = len(AREAS)
FIELD_END = -AREA_LEN * N_AREAS


def area_z(n):
    """(z_south, z_north) of area n (1..18): area n runs from Z -220(n-1) to Z -220n."""
    return (-AREA_LEN * (n - 1), -AREA_LEN * n)


def plots():
    """[(name, entrance (x, z), look (dx, dz), rect (x0, x1, z0, z1))]: 1-4 on the west wall north
    to south, 5-8 on the east wall, 9-12 on the south wall west to east."""
    out = []
    for i, z in enumerate(SIDE_Z):
        out.append(("Plot%d" % (i + 1), (-SIDE_X, z), (-1.0, 0.0), (-SIDE_X - PEN, -SIDE_X, z - PEN / 2, z + PEN / 2)))
    for i, z in enumerate(SIDE_Z):
        out.append(("Plot%d" % (i + 5), (SIDE_X, z), (1.0, 0.0), (SIDE_X, SIDE_X + PEN, z - PEN / 2, z + PEN / 2)))
    for i, x in enumerate(SOUTH_X):
        out.append(("Plot%d" % (i + 9), (x, SOUTH_Z), (0.0, 1.0), (x - PEN / 2, x + PEN / 2, SOUTH_Z, SOUTH_Z + PEN)))
    return out


def facing(dx, dz):
    """A turn whose LookVector (-Z) points along (dx, 0, dz)."""
    return G.facing(np.array((dx, 0.0, dz)) / math.hypot(dx, dz))


def heading(h):
    """A turn about Y: h = 0 faces north (-Z), 90 faces west (-X)... (Roblox's own Y turn)."""
    return G.ry(h)


# ==================================================================== plain parts

def part(sc, parent, name, size, cf_, col, solid=False, material="Plastic", shadow=None, transparency=0.0,
         checker=False, attrs=None):
    size = tuple(float(v) for v in size)
    if shadow is None:
        shadow = max(size) >= MS.SMALL
    p = sc.part(parent, name, size, cf_, hexc(col), material=material, transparency=transparency, grid=False,
                surfaces="inlet" if material == "Plastic" else "smooth", anchored=True, collide=solid, touch=False,
                query=solid, shadow=shadow, attrs=dict(attrs or {}))
    if checker:
        p.p["attrs"]["Checker"] = 4
    return p


def box(sc, parent, name, lo, hi, col, **kw):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return part(sc, parent, name, hi - lo, CF((lo + hi) / 2), col, **kw)


def invisible(sc, parent, name, size, cf_):
    return sc.part(parent, name, tuple(float(v) for v in size), cf_, (255, 255, 255), material="SmoothPlastic",
                   transparency=1.0, grid=False, surfaces="smooth", anchored=True, collide=False, touch=False,
                   query=False, shadow=False)


# ==================================================================== templates of my own (yard pieces)

WOOD = ("6b4226", "9a6238", "c8743a", "a0572b")
INK = "22232b"


def _stall(B, awning, header_col):
    """A market stall 10 wide, 4 deep: a planked counter, four posts, a striped awning, a header
    with the Board, an invisible Prompt in front (front -Z)."""
    for i in range(8):                                                  # planked counter front
        x = -4.2 + i * 1.2
        B.p("Counter", (1.2, 3.4, 0.6), (x, 1.7, -1.5 + 0.02 * (i % 2)), None, WOOD[1] if i % 2 else WOOD[3],
            solid=True)
    B.p("Counter", (9.7, 3.4, 2.4), (0, 1.7, 0.1), None, WOOD[0], solid=True)
    B.p("CounterTop", (10.5, 0.5, 3.66), (0, 3.65, -0.2), None, WOOD[2], solid=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.p("Post", (0.8, 9.4, 0.8), (sx * 4.9, 4.7, sz * 1.7), None, WOOD[0])
    for i in range(7):                                                  # the striped awning
        x = -4.5 + i * 1.5
        B.p("Awning", (1.46, 0.3 + 0.03 * (i % 2), 5.0 + 0.04 * (i % 2)), (x, 9.6, -0.7), G.rx(-14), awning[i % 2])
        B.p("Awning", (1.4, 0.9, 0.3 + 0.04 * (i % 2)), (x, 8.75 - 0.03 * (i % 2), -3.12), None, awning[i % 2])
    B.p("Header", (10.4, 2.6, 0.8), (0, 11.6, 1.2), None, header_col)
    B.plate("Board", (9.4, 2.0, 0.3), (0, 11.6, 0.65), None, INK)
    B.p("Prompt", (5.0, 5.0, 2.0), (0, 3.0, -4.0), None, "ffffff", material="SmoothPlastic", transparency=1.0,
        shadow=False)


def trail_shop(sc, parent):
    B = SC.Build(sc, parent, "TrailShop", seed=31)
    _stall(B, ("e8403a", "fff7ec"), "f5b700")
    B.p("Rail", (9.6, 0.35, 0.35), (0, 7.4, -1.7), None, WOOD[2])
    for i, c in enumerate(("ff4d6d", "ff9f3d", "ffe14d", "5ee06a", "4da6ff", "a46bff")):
        p = B.p("Ribbon", (0.5, 3.2 - 0.3 * (i % 2), 0.12), (-3.75 + i * 1.5, 5.7 + 0.15 * (i % 2), -1.7), None, c)
        p.p["attrs"]["Sway"] = 1.0
    return B.finish()


def speed_shop(sc, parent):
    B = SC.Build(sc, parent, "SpeedShop", seed=32)
    _stall(B, ("3e7bd8", "fff7ec"), "4fc3f7")
    with B.at(CF((0.0, 12.9, 1.0), G.ry(-18))):                         # a big sneaker on the roof
        B.p("Sneaker", (6.4, 0.9, 2.8), (0, 0.45, 0), None, "fff7ec")
        B.p("Sneaker", (4.4, 2.4, 2.6), (0.9, 2.0, 0), None, "e8403a")
        B.p("Sneaker", (2.4, 1.62, 2.46), (-1.9, 1.64, 0), None, "e8403a")
        B.p("Sneaker", (1.2, 1.2, 2.2), (2.9, 3.6, 0), None, "c0392b")
        for i in range(3):
            B.p("Lace", (0.3, 0.25, 2.66), (-0.6 + i * 0.9, 2.6 + i * 0.35, 0), None, "ffffff")
        B.plate("Stripe", (2.6, 0.6, 0.12), (0.6, 1.9, -1.32), G.rz(18), "ffd447")
        B.plate("Stripe", (2.6, 0.6, 0.12), (0.6, 1.9, 1.32), G.rz(18), "ffd447")
    return B.finish()


def index_board(sc, parent):
    """The big green chalkboard on legs with a little roof: Board (16 x 10) and a Prompt."""
    B = SC.Build(sc, parent, "IndexBoard", seed=33)
    for sx in (-1, 1):
        B.p("PostBase", (2.4, 1.6, 2.4), (sx * 9.0, 0.8, 0), None, "8e89a0", solid=True)
        B.p("Post", (1.4, 17.0, 1.4), (sx * 9.0, 9.1, 0), None, WOOD[0], solid=True)
    B.p("Frame", (18.0, 1.0, 1.0), (0, 2.9, 0), None, WOOD[2])
    B.p("Frame", (18.0, 1.0, 1.0), (0, 14.1, 0), None, WOOD[2])
    B.p("Frame", (1.0, 10.2, 0.96), (-8.5, 8.5, 0), None, WOOD[1])
    B.p("Frame", (1.0, 10.2, 0.96), (8.5, 8.5, 0), None, WOOD[1])
    B.p("Back", (15.8, 10.2, 0.6), (0, 8.5, 0.2), None, "2a4a32")
    B.plate("Board", (16.0, 10.0, 0.3), (0, 8.5, -0.2), None, "2f6a3e")
    B.p("Tray", (14.0, 0.4, 1.0), (0, 3.6, -0.7), None, WOOD[2])
    for i, c in enumerate(("ffffff", "ffd447", "ff8fc7")):
        B.p("Chalk", (0.9, 0.3, 0.3), (-3 + i * 1.6, 3.95, -0.7), None, c, shadow=False)
    for sz in (-1, 1):                                                  # the little roof
        B.p("Roof", (20.4 - 0.04 * (sz > 0), 0.5, 3.4), (0, 16.3, sz * 1.45), G.rx(sz * 24), "b5452b")
    B.p("Ridge", (20.8, 0.6, 0.7), (0, 17.0, 0), None, "a33d26")
    B.p("Prompt", (6.0, 5.0, 2.0), (0, 3.0, -3.5), None, "ffffff", material="SmoothPlastic", transparency=1.0,
        shadow=False)
    return B.finish()


def area_sign(sc, parent):
    """Folk Valley's sign: two brick posts on wider bases, a header beam, the dark Board (16 x 9,
    bottom edge at Y 8) between; front -Z (the map turns it to face south)."""
    B = SC.Build(sc, parent, "AreaSign", seed=34)
    for sx in (-1, 1):
        B.p("PostBase", (3.0, 2.2, 3.0), (sx * 9.6, 1.1, 0), None, "a0572b", solid=True)
        B.p("Post", (1.8, 19.0, 1.8), (sx * 9.6, 9.5 + 0.02, 0), None, "c8743a", solid=True)
    B.p("Header", (21.6, 3.4, 2.0), (0, 19.2, 0), None, "f5b700")
    B.p("Frame", (17.6, 0.8, 1.2), (0, SIGN_Y - 0.4, 0), None, "c8743a")
    B.p("Back", (16.8, 9.6, 0.56), (0, SIGN_Y + SIGN_H / 2, 0.3), None, "3a2a1e")
    B.plate("Board", (SIGN_W, SIGN_H, 0.4), (0, SIGN_Y + SIGN_H / 2, -0.2), None, INK)
    return B.finish()


def gate_potato(sc, parent):
    B = SC.Build(sc, parent, "PillarPotato", seed=35)
    SC.potato(B, (0, 4.5, 0), 9.0, ("d39a52", "c08440", "e0ac66"), cheeks="ff8fa8", glints=True)
    for sx in (-1, 1):                                                   # a sprout on top
        B.p("Sprout", (1.6, 0.5, 0.9), (sx * 0.8, 9.6, 0), G.rz(sx * 28), "55b848" if sx < 0 else "7ad155")
    B.p("Sprout", (0.5, 1.6, 0.5), (0, 9.2, 0), None, "3f9e3c")
    return B.finish()


def spawn_pad(sc, parent):
    B = SC.Build(sc, parent, "SpawnPad", seed=36)
    B.p("SpawnPad", (14.0, 0.14, 9.0), (0, 0.07, 0), None, "f3e2b6", shadow=False)
    B.p("SpawnPad", (9.0, 0.13, 14.0), (0, 0.065, 0), None, "f3e2b6", shadow=False)
    B.p("SpawnPad", (12.2, 0.12, 12.2), (0, 0.06, 0), G.ry(45), "c9ae78", shadow=False)
    B.p("SpawnRing", (8.0, 0.2, 5.0), (0, 0.1, 0), None, "5dbb46", shadow=False)
    B.p("SpawnRing", (5.0, 0.19, 8.0), (0, 0.095, 0), None, "5dbb46", shadow=False)
    B.p("SpawnRing", (6.9, 0.18, 6.9), (0, 0.09, 0), G.ry(45), "7ad155", shadow=False)
    return B.finish()


def well(sc, parent):
    B = SC.Build(sc, parent, "Well", seed=37)
    SC.round3(B, "Well", (0, 1.4, 0), 5.0, 2.8, 5.0, ("8e89a0", "a3adeb", "b9b4c8"), solid=True)
    B.p("Water", (3.2, 0.2, 3.2), (0, 2.78, 0), G.ry(22), "4fc3f7", shadow=False)
    for sx in (-1, 1):
        B.p("Post", (0.7, 5.6, 0.7), (sx * 2.2, 5.6, 0), None, WOOD[0])
    for sz in (-1, 1):
        B.p("Roof", (6.0 - 0.04 * (sz > 0), 0.4, 2.6), (0, 8.5, sz * 1.05), G.rx(sz * 32), "b5452b")
    B.p("Crank", (4.6, 0.35, 0.35), (0, 6.4, 0), None, WOOD[2])
    B.p("Bucket", (1.0, 1.0, 1.0), (0.6, 5.4, 0), None, "9a6238")
    return B.finish()


def bench(sc, parent):
    B = SC.Build(sc, parent, "Bench", seed=38)
    B.p("Seat", (5.0, 0.4, 1.6), (0, 1.6, 0), None, WOOD[2])
    B.p("Back", (5.0, 1.2, 0.35), (0, 2.6, 0.7), G.rx(-8), WOOD[1])
    for sx in (-1, 1):
        B.p("Leg", (0.45, 1.4, 1.4), (sx * 2.1, 0.7, 0), None, WOOD[0])
    return B.finish()


# ==================================================================== Folk Valley props by area

S_MARSH = dict(leaf=("2f6b4a", "3f8a5a", "5aa36a"), wood=("3a2a1e", "4a3426"), stone=("4a5a52", "5e7066", "7a8a80"))
S_JUNGLE = dict(leaf=("2f8a3c", "3fa34d", "5ebe45"), stone=("6a7a5a", "7d8f62", "93a578"))
S_REEF = dict(other=("c9806e", "e09a82", "f0b49a"), leaf=("2e8f7a", "3fae8a", "5ac8a0"))
S_LAVA = dict(other=("221e20", "2e2a2c", "3a3436", "4e4648", "5a5054"), stone=("2a2628", "3a3436", "4e4648"))
S_CRYST_ROCK = dict(other=("3a2456", "4c3468", "6a4a8a", "8a6aae", "a88ac8"), stone=("3a2456", "4c3468", "6a4a8a"))
S_CRYST = [dict(other=c) for c in (("d0509a", "ff8fc7", "ffc0e0"), ("2aa6c8", "7fe3ff", "c8f6ff"),
                                    ("c99a1a", "ffd447", "fff0a8"))]
S_DINO = dict(leaf=("3f7a2e", "5a9a3a", "7ab24a"), other=("6a4a2e", "7a5a3a", "8b6a4a", "a0805a", "c8a878"))
S_TOY = dict(leaf=("2fae4a", "4fd05a", "7ae07a"), wood=("e04a3a", "c0392b"))
S_CANDY = dict(leaf=("e85a9a", "ff8fc7", "ffc0dc"), wood=("6b3a1e", "8a4a2a"), other=("ff8fc7", "ffc0dc", "fff0f6"))
S_CLOCK = dict(stone=("5a5a5a", "7a7a72", "9a9a90"))
S_NEON = dict(stone=("1e1e2a", "2a2a3a", "3a3a4e"))
S_CLOUD = dict(leaf=("a8e6b8", "c8f0d0", "e0fae8"), stone=("dfe9f5", "eef4ff", "ffffff"), wood=("e8ecff", "f4f8ff"))
S_COSMIC = dict(stone=("4a4e66", "6a6e88", "8c93a6"), leaf=("6ac83a", "9be34a", "c8f070"),
                other=("4a4e66", "6a6e88", "8c93a6", "a8b0c8"))
S_VOID = dict(stone=("120f1a", "1e1a2a", "2b2233"), other=("2a1a3a", "5a2a7a", "ff2bd6"))
S_OLYMPUS = dict(leaf=("4a7a3a", "5e8f45", "7aa65a"), stone=("d8d4c8", "e8e4d8", "f6f2ea"))

# (group, indices, count, band, scale min, scale max, solid, recolour scheme or a list of them)
FV_SETS = {
    "Meadow": [("Meadow", (0, 2, 4, 5), 5, "Edge", 0.9, 1.15, False, None),
               ("Meadow", (1, 3), 3, "Edge", 0.9, 1.1, False, None),
               ("Meadow", (6, 7, 8, 9), 8, "Any", 0.9, 1.3, False, None),
               ("Meadow", (10, 11, 12, 13), 6, "Side", 0.9, 1.2, False, None),
               ("Meadow", (14, 15, 16), 4, "Edge", 0.9, 1.2, False, None),
               ("Meadow", (17, 18, 19), 3, "Side", 0.9, 1.2, True, None),
               ("Meadow", (22,), 1, "Side", 1.0, 1.0, False, None)],
    "Dunes": [("Desert", (2,), 3, "Edge", 0.9, 1.1, False, None),
              ("Desert", (0, 1, 3, 4), 6, "Side", 0.9, 1.3, False, None),
              ("Desert", (7, 8, 9, 10, 11), 3, "Edge", 0.9, 1.1, True, None),
              ("Desert", (12, 13, 14), 4, "Side", 0.9, 1.3, True, None),
              ("Desert", (15, 16, 17), 4, "Any", 0.9, 1.2, False, None),
              ("Desert", (18,), 4, "Any", 0.9, 1.2, False, None)],
    "Marsh": [("Meadow", (0, 4, 5), 4, "Edge", 0.9, 1.15, False, S_MARSH),
              ("Meadow", (14, 15, 16), 4, "Edge", 0.9, 1.2, False, S_MARSH),
              ("Meadow", (6, 7, 8), 8, "Any", 0.9, 1.3, False, S_MARSH),
              ("Meadow", (17, 18, 19), 3, "Side", 0.9, 1.2, True, S_MARSH)],
    "Jungle": [("Meadow", (5, 4, 2), 4, "Edge", 1.0, 1.25, False, S_JUNGLE),
               ("Desert", (2,), 2, "Edge", 1.0, 1.2, False, S_JUNGLE),
               ("Meadow", (14, 15, 16), 4, "Edge", 0.9, 1.3, False, S_JUNGLE),
               ("Meadow", (6, 7, 8, 9), 8, "Any", 1.0, 1.4, False, S_JUNGLE),
               ("Meadow", (17, 18, 19), 3, "Side", 1.0, 1.3, True, S_JUNGLE)],
    "Reef": [("Desert", (2,), 3, "Edge", 0.9, 1.1, False, None),
             ("Desert", (12, 13, 14), 4, "Side", 0.9, 1.3, True, S_REEF),
             ("Meadow", (6, 7), 6, "Any", 0.9, 1.3, False, S_REEF)],
    "Frost": [("Snow", (0, 1, 2, 3, 4, 5), 6, "Edge", 0.85, 1.1, False, None),
              ("Snow", (6, 7, 8, 9, 10), 5, "Side", 0.9, 1.3, False, None),
              ("Snow", (12, 13, 14), 3, "Side", 0.9, 1.2, True, None),
              ("Snow", (15, 16, 17), 6, "Any", 0.9, 1.4, False, None),
              ("Snow", (18, 19), 2, "Side", 1.0, 1.0, False, None),
              ("Snow", (20,), 1, "Side", 1.0, 1.0, False, None)],
    "Haunt": [("October", (0, 2, 3, 5), 4, "Edge", 0.9, 1.1, False, None),
              ("October", (6, 7, 8), 3, "Side", 0.9, 1.2, False, None),
              ("October", (12, 13, 14), 4, "Side", 0.9, 1.2, False, None),
              ("October", (15, 16), 2, "Side", 1.0, 1.0, False, None),
              ("October", (9, 10), 3, "Edge", 1.0, 1.2, False, None)],
    "Lava": [("Desert", (12, 13, 14), 5, "Side", 0.9, 1.4, True, S_LAVA),
             ("Desert", (7, 9, 10), 2, "Edge", 0.9, 1.1, True, S_LAVA),
             ("Desert", (15, 16, 17), 3, "Any", 0.9, 1.2, False, None)],
    "Crystal": [("Snow", (6, 7, 8, 9, 10), 6, "Side", 1.0, 1.5, False, S_CRYST),
                ("Desert", (12, 13, 14), 4, "Side", 0.9, 1.3, True, S_CRYST_ROCK),
                ("Desert", (8, 11), 2, "Edge", 0.9, 1.1, True, S_CRYST_ROCK)],
    "Dino": [("Meadow", (0, 4, 5), 3, "Edge", 1.1, 1.3, False, S_DINO),
             ("Desert", (7, 9, 10), 2, "Edge", 1.0, 1.2, True, S_DINO),
             ("Meadow", (17, 18, 19), 3, "Side", 1.0, 1.4, True, S_DINO),
             ("Desert", (15, 16, 17), 3, "Any", 1.0, 1.3, False, None),
             ("Meadow", (14, 15, 16), 3, "Edge", 1.0, 1.3, False, S_DINO)],
    "Toy": [("Lobby", (2,), 3, "Edge", 0.8, 1.0, False, S_TOY),
            ("Meadow", (14, 15, 16), 3, "Edge", 0.9, 1.2, False, S_TOY),
            ("Meadow", (10, 11, 12, 13), 4, "Any", 0.9, 1.2, False, None)],
    "Candy": [("Lobby", (0, 2, 3), 3, "Edge", 0.8, 1.0, False, S_CANDY),
              ("Meadow", (14, 15, 16), 3, "Edge", 0.9, 1.2, False, S_CANDY),
              ("Meadow", (10, 11, 12, 13), 4, "Any", 0.9, 1.2, False, None)],
    "Clock": [("Desert", (5, 6), 3, "Side", 0.9, 1.1, False, None),
              ("Meadow", (17, 18, 19), 3, "Side", 0.9, 1.2, True, S_CLOCK)],
    "Neon": [("Lobby", (4,), 4, "Edge", 1.0, 1.2, False, None),
             ("Meadow", (17, 18, 19), 2, "Side", 0.9, 1.2, True, S_NEON)],
    "Cloud": [("Snow", (15, 16, 17), 8, "Any", 1.0, 1.8, False, None),
              ("Meadow", (10, 11, 12, 13), 4, "Side", 0.9, 1.2, False, None),
              ("Snow", (0, 2), 2, "Edge", 0.8, 1.0, False, S_CLOUD)],
    "Cosmic": [("Desert", (19,), 1, "Edge", 1.0, 1.0, True, None),
               ("Meadow", (17, 18, 19), 4, "Side", 0.9, 1.4, True, S_COSMIC),
               ("Lobby", (14,), 1, "Edge", 0.8, 0.8, False, S_COSMIC)],
    "Void": [("Meadow", (17, 18, 19), 4, "Side", 0.9, 1.4, True, S_VOID),
             ("Snow", (6, 8, 10), 3, "Side", 1.0, 1.4, False, S_VOID)],
    "Olympus": [("Meadow", (1,), 4, "Edge", 0.9, 1.1, False, S_OLYMPUS),
                ("Meadow", (17, 18, 19), 3, "Side", 0.9, 1.2, True, S_OLYMPUS),
                ("Meadow", (14, 15, 16), 3, "Edge", 0.9, 1.1, False, S_OLYMPUS),
                ("Meadow", (10, 11, 12), 3, "Any", 0.9, 1.1, False, None)],
}
OWN_MAX = 3                 # copies of each of an area's own props (their Count is the game's scatter count)


# ==================================================================== the map

class MapBuild:
    def __init__(self, fv_path, seed=7):
        self.sc = spslib.Scene("PotatoMap")
        self.st = MS.Stamps(self.sc)
        self.fv = MS.FV(fv_path)
        self.seed = seed
        self.info = {}
        self.T = {}
        root = self.sc.root
        root.kind = "Model"
        self.markers = self.sc.folder(root, "Markers")
        self.yard = self.sc.folder(root, "Yard")
        self.fields = self.sc.folder(root, "Fields")

    def tpl(self, key, builder):
        if key not in self.T:
            self.T[key] = MS.build_template(key, builder)
        return self.T[key]

    def fvt(self, group, i):
        t = self.fv.template(group, i)
        if t.key not in self.T:
            for p in t.parts:                                   # glow lights up at night
                if p["material"] == "Neon":
                    p["attrs"]["NightLamp"] = True
            self.T[t.key] = t
        return self.T[t.key]

    # ---------------------------------------------------------------- the yard
    def yard_shell(self):
        sc, f = self.sc, self.yard
        x0, x1 = YARD_X
        z0, z1 = YARD_Z
        a0, a1 = AVENUE_X
        box(sc, f, "Ground", (x0, -GROUND_T, z0), (a0, 0.0, z1), YARD["ground"], solid=True, checker=True)
        av = box(sc, f, "Avenue", (a0, -GROUND_T, z0), (a1, 0.0, MEET_Z[1]), YARD["avenue"], solid=True, checker=True)
        box(sc, f, "Ground", (a0, -GROUND_T, MEET_Z[1]), (a1, 0.0, z1), YARD["ground"], solid=True, checker=True)
        box(sc, f, "Ground", (a1, -GROUND_T, z0), (x1, 0.0, z1), YARD["ground"], solid=True, checker=True)
        T, H = WALL_T, WALL_H
        walls = [((x0 - T, 0, z0 - T), (x0, H, z1 + T)),
                 ((x1, 0, z0 - T), (x1 + T, H, z1 + T)),
                 ((x0, 0, z1), (x1, H, z1 + T)),
                 ((x0, 0, z0 - T), (GATE_X[0] - PILLAR, H, z0)),
                 ((GATE_X[1] + PILLAR, 0, z0 - T), (x1, H, z0))]
        for lo, hi in walls:
            box(sc, f, "Wall", lo, hi, YARD["wall"], solid=True, checker=True)
            box(sc, f, "WallCap", (lo[0], H, lo[2]), (hi[0], H + CAP_H, hi[2]), YARD["cap"], solid=True)
        # the avenue's trim, and cream paths from it to the pens' gateways
        for sx in (-1, 1):
            box(sc, f, "AvenueTrim", (sx * 20.0 - 0.6, 0.0, 0.0), (sx * 20.0 + 0.6, 0.12, MEET_Z[1]), YARD["trim"],
                shadow=False)
        for z in SIDE_Z:
            for sx in (-1, 1):
                xa, xb = sorted((sx * 20.6, sx * SIDE_X))
                box(sc, f, "Path", (xa, 0.0, z - 4.0), (xb, 0.1, z + 4.0), YARD["avenue"], shadow=False)
                box(sc, f, "PathTrim", (xa, 0.0, z - 4.6), (xb, 0.11, z - 3.9), YARD["trim"], shadow=False)
                box(sc, f, "PathTrim", (xa, 0.0, z + 3.9), (xb, 0.11, z + 4.6), YARD["trim"], shadow=False)
        box(sc, f, "Path", (-126.0, 0.0, MEET_Z[1] - 8.0), (126.0, 0.1, MEET_Z[1]), YARD["avenue"], shadow=False)
        box(sc, f, "PathTrim", (-126.0, 0.0, MEET_Z[1] - 8.6), (-20.6, 0.11, MEET_Z[1] - 7.9), YARD["trim"],
            shadow=False)
        box(sc, f, "PathTrim", (20.6, 0.0, MEET_Z[1] - 8.6), (126.0, 0.11, MEET_Z[1] - 7.9), YARD["trim"],
            shadow=False)
        return av

    def gate(self):
        sc = self.sc
        g = sc.model(self.sc.root, "Gate")
        H = WALL_H
        gx0, gx1 = GATE_X
        s = PILLAR / 2
        first = None
        for sx in (-1, 1):
            cx = sx * (gx1 + s)
            p = box(sc, g, "Pillar", (cx - s, 0, -s), (cx + s, H, s), YARD["wall"], solid=True, checker=True)
            first = first or p
            box(sc, g, "PillarCap", (cx - s - 0.5, H, -s - 0.5), (cx + s + 0.5, H + CAP_H, s + 0.5), YARD["cap"],
                solid=True)
            pot = self.tpl("PillarPotato", gate_potato)
            self.st.place(g, "PillarPotato", pot, CF((cx, H + CAP_H, 0.0), G.ry(180 - sx * 20)))
        b0, b1 = BEAM
        box(sc, g, "Beam", (gx0, b0, -s), (gx1, b1, s), YARD["wall"], solid=True, checker=True)
        box(sc, g, "BeamCap", (gx0 - s, b1, -s - 0.5), (gx1 + s, b1 + CAP_H, s + 0.5), YARD["cap"], solid=True)
        W, Hh, y = TIMER_W, TIMER_H, TIMER_Y
        for name, fz, d in (("TimerSouth", s, 1.0), ("TimerNorth", -s, -1.0)):
            R = facing(0.0, d)
            yc = y + Hh / 2
            part(sc, g, name, (W, Hh, 0.6), CF((0.0, yc, fz + d * 0.3), R), "181a24", material="SmoothPlastic")
            t = 1.4
            for (fx, fy, fw, fh) in ((0, Hh / 2 + t / 2, W + 2 * t, t), (0, -Hh / 2 - t / 2, W + 2 * t, t),
                                     (W / 2 + t / 2, 0, t, Hh), (-W / 2 - t / 2, 0, t, Hh)):
                part(sc, g, name + "Frame", (fw, fh, 1.2), CF((0.0, yc, fz + d * 0.6), R) * CF((fx, fy, 0.0)),
                     "28305a")
            for i in range(9):
                bx = -W / 2 + 2.0 + i * (W - 4.0) / 8
                part(sc, g, name + "Bulbs", (1.0, 0.8, 0.5), CF((0.0, yc, fz + d * 1.3), R) * CF((bx, Hh / 2 + 0.7, 0)),
                     "ffdc5a", material="Neon", attrs={"Flicker": 0.2, "NightLamp": True})
        invisible(sc, g, "Barrier", (gx1 - gx0, GATE_CLEAR, 1.0), CF((0.0, GATE_CLEAR / 2, BARRIER_Z)))
        bar = g.children[-1]
        bar.p["color"] = (120, 200, 255)
        part(sc, g, "RedLine", (gx1 - gx0, 0.2, LINE_W), CF((0.0, 0.1, 0.0)), "e82828", shadow=False)
        # LineBoard lies face up: its Front face (-Z) looks at the sky and its top edge points north
        R_up = np.array(((-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, -1.0, 0.0)))
        part(sc, g, "LineBoard", (20.0, 3.0, 0.2), CF((0.0, 0.1, 3.6), R_up), "e82828", material="SmoothPlastic",
             shadow=False)
        g.p["primary"] = first
        sc.marker(self.markers, "SafeLine", CF((0.0, 0.0, 0.0), facing(0.0, -1.0)))
        return g

    def yard_pieces(self, rng):
        sc, st, y = self.sc, self.st, self.yard
        mk = self.markers
        for name, (x, z), (dx, dz), _r in plots():
            sc.marker(mk, name, CF((x, 0.0, z), facing(dx, dz)))
        sc.marker(mk, "Spawn", CF((SPAWN[0], 0.0, SPAWN[1])))
        sc.marker(mk, "FuseMachine", CF((FUSE[0], 0.0, FUSE[1]), facing(1.0, 0.0)))
        sc.marker(mk, "QuestNpc", CF((QUEST[0], 0.0, QUEST[1]), facing(-1.0, 0.0)))
        st.place(y, "SpawnPad", self.tpl("SpawnPad", spawn_pad), CF((SPAWN[0], 0.0, SPAWN[1])))
        st.place(y, "TrailShop", self.tpl("TrailShop", trail_shop), CF((TRAIL_SHOP[0], 0.0, TRAIL_SHOP[1]), facing(1, 0)))
        st.place(y, "SpeedShop", self.tpl("SpeedShop", speed_shop), CF((SPEED_SHOP[0], 0.0, SPEED_SHOP[1]), facing(-1, 0)))
        st.place(y, "IndexBoard", self.tpl("IndexBoard", index_board),
                 CF((INDEX_BOARD[0], 0.0, INDEX_BOARD[1]), facing(-1, 0)))
        lamps = sc.folder(y, "Lamps")
        lt = self.fvt("Lobby", 4)
        for p in lt.parts:
            if p["material"] == "Neon":
                p["name"] = "Bulb"
        for z in np.arange(16.0, MEET_Z[1] - 10.0, 30.0):
            for sx in (-1, 1):
                # the lantern's arm reaches over the avenue (its own -Z): face it at the avenue
                st.place(lamps, "LampPost", lt, CF((sx * 23.5, 0.0, float(z)), facing(-sx, 0.0)))
        scen = sc.folder(y, "Scenery")
        F = self.fvt
        R90 = G.ry(-90)            # Folk Valley's buildings face +X in their own frame: this turns them south
        st.place(scen, "Barn", F("Farm", 20), CF((-104.0, 0.0, 12.0), R90), solid=True)
        st.place(scen, "Silo", F("Farm", 21), CF((-124.0, 0.0, 10.0)), solid=True)
        st.place(scen, "Tractor", F("Farm", 23), CF((-82.0, 0.0, 20.0), G.ry(-120)))
        st.place(scen, "Windmill", F("Meadow", 20), CF((108.0, 0.0, 13.0), R90), solid=True)
        st.place(scen, "Scarecrow", F("Farm", 22), CF((126.0, 0.0, 26.0), G.ry(150)))
        st.place(scen, "Well", self.tpl("Well", well), CF((-62.0, 0.0, 200.0), G.ry(20)))
        st.place(scen, "Pond", F("Meadow", 22), CF((92.0, 0.0, 196.0), G.ry(12)))
        for (x, z, h) in ((-60.0, 228.0, 30), (70.0, 228.0, -20), (112.0, 222.0, 60)):
            st.place(scen, "Picnic", F("Meadow", 21), CF((x, 0.0, z), G.ry(h)))
        for (x, z, h, i) in ((-92.0, 34.0, 0, 15), (-96.0, 40.0, 40, 16), (-128.0, 24.0, 10, 17),
                             (96.0, 30.0, 20, 15), (120.0, 40.0, 70, 16)):
            st.place(scen, "HayBale", F("Farm", i), CF((x, 0.0, z), G.ry(h)))
        for (x, z, h, i) in ((-70.0, 30.0, 15, 12), (-76.0, 48.0, 80, 13), (78.0, 46.0, 30, 14)):
            st.place(scen, "Pumpkins", F("Farm", i), CF((x, 0.0, z), G.ry(h)))
        for (x, z, h, i) in ((-86.0, 8.0, 0, 5), (86.0, 8.0, 180, 6)):
            st.place(scen, "Crates", F("Desert", i), CF((x, 0.0, z), G.ry(h)))
        trees = [(-124.0, 72.0, 0), (-124.0, 136.0, 4), (-124.0, 200.0, 5), (124.0, 72.0, 5), (124.0, 136.0, 0),
                 (124.0, 200.0, 4), (-128.0, 254.0, 2), (128.0, 254.0, 2), (-44.0, 168.0, 3), (52.0, 150.0, 1),
                 (-100.0, 100.0, 0), (100.0, 110.0, 4)]
        for (x, z, i) in trees:
            st.place(scen, "Tree", F("Meadow", i), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 360)))))
        for (x, z, i) in ((-108.0, 62.0, 14), (110.0, 60.0, 15), (-110.0, 250.0, 16), (106.0, 250.0, 14),
                          (-40.0, 140.0, 15), (40.0, 190.0, 16)):
            st.place(scen, "Bush", F("Meadow", i), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 360)))))
        for k, z in enumerate(np.arange(30.0, MEET_Z[1] - 20.0, 30.0)):
            for sx in (-1, 1):
                st.place(scen, "Flowers", F("Meadow", 10 + (k + (sx > 0)) % 4),
                         CF((sx * 28.0, 0.0, float(z) + 8.0), G.ry(float(rng.uniform(0, 360)))))
        for k in range(10):
            x = float(rng.choice((-1, 1)) * rng.uniform(32, 120))
            z = float(rng.uniform(60, 250))
            st.place(scen, "Grass", F("Meadow", 6 + k % 4), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 360)))))
        for (x, z, i) in ((-70.0, 96.0, 17), (66.0, 160.0, 18), (-30.0, 250.0, 19)):
            st.place(scen, "Rock", F("Meadow", i), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 360)))), solid=True)
        for (x, z, sx) in ((-26.0, 60.0, 1), (-26.0, 180.0, 1), (26.0, 70.0, -1), (26.0, 210.0, -1)):
            st.place(scen, "Bench", self.tpl("Bench", bench), CF((x, 0.0, z), facing(sx, 0.0)))
        # a vegetable garden, fenced pumpkin patches, big shade trees and a few rustic fences
        for (x, z) in ((-96.0, 70.0), (-80.0, 70.0)):
            st.place(scen, "SoilRows", F("Lobby", 18), CF((x, 0.0, z)))
        for (x, z) in ((-112.0, 88.0), (-68.0, 88.0)):
            st.place(scen, "CornRow", F("Lobby", 17), CF((x, 0.0, z), G.ry(90)))
        for (x, z, h) in ((-100.0, 210.0, 0), (96.0, 140.0, 90)):
            st.place(scen, "PumpkinPatch", F("Lobby", 6), CF((x, 0.0, z), G.ry(h)))
        for (x, z, i) in ((-60.0, 252.0, 2), (62.0, 252.0, 0), (-50.0, 76.0, 3), (110.0, 84.0, 1), (-108.0, 154.0, 2),
                          (70.0, 120.0, 3)):
            st.place(scen, "BigTree", F("Lobby", i), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 360)))))
        for (x, z) in ((84.0, 70.0), (92.0, 84.0)):
            st.place(scen, "Picnic", F("Meadow", 21), CF((x, 0.0, z), G.ry(float(rng.uniform(0, 90)))))

    # ---------------------------------------------------------------- the fields
    def area_shell(self, n, a):
        sc = self.sc
        aid, title, ground, wall, border = a[:5]
        zs, zn = area_z(n)
        af = sc.folder(self.fields, "Area%d" % n)
        x0, x1 = FIELD_X
        box(sc, af, "Ground", (x0, -GROUND_T, zn), (x1, 0.0, zs), ground, solid=True, checker=True)
        ws = zs if n > 1 else -PILLAR / 2
        T, H = WALL_T, WALL_H
        for sx in (-1, 1):
            wx0, wx1 = (x0 - T, x0) if sx < 0 else (x1, x1 + T)
            box(sc, af, "Wall", (wx0, 0.0, zn), (wx1, H, ws), wall, solid=True, checker=True)
            box(sc, af, "WallCap", (wx0, H, zn), (wx1, H + CAP_H, ws), ground, solid=True)
        if n == N_AREAS:
            box(sc, af, "BackWall", (x0 - T, 0.0, zn - T), (x1 + T, H, zn), wall, solid=True, checker=True)
            box(sc, af, "BackWallCap", (x0 - T, H, zn - T), (x1 + T, H + CAP_H, zn), ground, solid=True)
        if n > 1:
            box(sc, af, "Border", (x0, 0.0, zs - 1.0), (x1, 0.2, zs + 1.0), border, shadow=False)
        return af

    def area(self, n, a, rng):
        sc, st = self.sc, self.st
        aid, title, ground, wall, border, soil, leaf, flag, side = a
        zs, zn = area_z(n)
        af = self.area_shell(n, a)
        am = sc.folder(self.markers, "Area%d" % n)
        zone = invisible(sc, am, "Zone", (FIELD_X[1] - FIELD_X[0], 60.0, AREA_LEN), CF((0.0, 30.0, (zs + zn) / 2)))
        zone.p["attrs"].update(Area=n, AreaName=title)
        lay = Layout(n, WALL_IN.get(aid, FIELD_X[1] - 0.6))
        # the sign, on the west side just inside the area, its Board facing south
        sz_ = zs - (10.0 if n == 1 else 5.0)
        sign = st.place(am, "AreaSign", self.tpl("AreaSign", area_sign), CF((-46.0, 0.0, sz_), facing(0.0, 1.0)),
                        recolour=self.sign_colours(wall, flag))
        sign.p.setdefault("attrs", {})["Area"] = n
        lay.rect(-57.0, -35.0, sz_ - 3.0, sz_ + 3.0)
        # the hero against its wall
        scen = sc.folder(af, "Scenery")
        area_mod = SC.AREAS.get(aid)
        hero_rect = None
        if area_mod is not None:
            t = self.tpl("Hero_" + aid, area_mod.hero)
            lo, hi = t.bounds()
            depth_lo, depth_hi = lo[2], hi[2]
            zc = (zs + zn) / 2 - 8.0
            if side == "E":
                R = G.ry(90)
                x = FIELD_X[1] - 0.6 - depth_hi
                xr = (x + depth_lo, x + depth_hi)
                zr = (zc - hi[0], zc - lo[0])
            else:
                R = G.ry(-90)
                x = FIELD_X[0] + 0.6 + depth_hi
                xr = (x - depth_hi, x - depth_lo)
                zr = (zc + lo[0], zc + hi[0])
            st.place(af, "Hero", t, CF((x, 0.0, zc), R))
            hero_rect = (xr[0], xr[1], zr[0], zr[1])
            lay.rect(xr[0] - 3.0, xr[1] + 3.0, zr[0] - 3.0, zr[1] + 3.0)
        self.area_extras(n, a, af, rng, lay)
        # props: the area's own, then Folk Valley's
        specs = []
        if area_mod is not None:
            for fn, attrs in area_mod.props:
                key = "Prop_%s_%s" % (aid, fn.__name__[2:] if fn.__name__.startswith("p_") else fn.__name__)
                t = self.tpl(key, fn)
                cnt = min(int(attrs.get("Count", 6)), OWN_MAX)
                specs.append((t, t.name, cnt, attrs.get("Band", "Side"),
                              attrs.get("ScaleMin", 0.9), min(attrs.get("ScaleMax", 1.3), 1.25),
                              bool(attrs.get("Solid", False)), None, True))
        for (group, idxs, cnt, band, smin, smax, solid, scheme) in FV_SETS.get(aid, []):
            for k in range(cnt):
                i = idxs[k % len(idxs)]
                t = self.fvt(group, i)
                sch = scheme[k % len(scheme)] if isinstance(scheme, list) else scheme
                rc = MS.recolour_map(t, sch) if sch else None
                specs.append((t, self.fv.kind(group, i), 1, band, smin, smax, solid, rc, False))
        order = {"Edge": 0, "Side": 1, "Any": 2}
        specs.sort(key=lambda s: (order.get(s[3], 1), -s[0].radius()))
        placed = []
        for (t, name, cnt, band, smin, smax, solid, rc, face) in specs:
            for _ in range(cnt):
                scale = float(rng.uniform(smin, smax))
                spot = lay.find(t, scale, band, rng, solid)
                if spot is None:
                    continue
                x, z, r = spot
                if face:                                # my props face the lane, give or take
                    h = (90.0 if x > 0 else -90.0) + float(rng.uniform(-35, 35))
                else:
                    h = float(rng.uniform(0, 360))
                h = round(h / 5.0) * 5.0
                st.place(scen, name, t, CF((x, 0.0, z), G.ry(h)), scale=scale, recolour=rc, solid=solid)
                placed.append((x, z, r, band))
        # the mounds: some tucked beside props, the rest spread evenly
        mt = self.tpl("Mound", PK.mound)
        mrc = mound_colours(mt, soil, leaf, flag)
        tucked = []
        for (x, z, r, band) in placed:
            if band in ("Edge", "Side") and r >= 2.0 and len(tucked) < 8:
                tx = x - math.copysign(r + 6.0, x)
                tucked.append((tx, z + float(rng.uniform(-3, 3))))
        spots = place_mounds(n, rng, tucked, lay)
        for (x, z) in spots:
            h = float(round(rng.uniform(0, 360) / 5.0) * 5.0)
            st.place(am, "Mound", mt, CF((x, PK.MOUND_FLOOR, z), G.ry(h)), recolour=mrc)
        self.info[n] = dict(aid=aid, hero=hero_rect, mounds=spots, props=placed, sign=(-46.0, sz_))

    def sign_colours(self, wall, flag):
        t = self.T["AreaSign"]
        cols = {tuple(p["color"]) for p in t.parts}
        out = {}
        for c in cols:
            hx = "%02x%02x%02x" % c
            if hx == "c8743a":
                out[c] = tuple(shade(wall, -0.12))
            elif hx == "a0572b":
                out[c] = tuple(shade(wall, -0.32))
            elif hx == "f5b700":
                out[c] = tuple(hexc(flag)) if flag.lower() not in ("ffffff",) else tuple(hexc("ff8fc7"))
        return out

    def area_extras(self, n, a, af, rng, lay):
        """Each area's own touch on its walls and ground (icicles, lava channels, icing...), and the
        Fx_* attachments the game hangs its particles on."""
        fn = EXTRAS.get(a[0])
        if fn:
            fn(self, n, a, af, rng, lay)
        fx = FX.get(a[0])
        if fx:
            ground = af.find("Ground")
            zs, zn = area_z(n)
            name, y, count = fx
            for k in range(count):
                z = zs - AREA_LEN * (k + 0.5) / count
                x = (-1.0) ** k * 30.0 if name != "Fx_Embers" else (-1.0) ** k * (FIELD_X[1] - 2.7)
                self.sc.attachment(ground, name, CF((x, y, z)))

    def build(self):
        rng = np.random.default_rng(self.seed)
        av = self.yard_shell()
        self.gate()
        self.yard_pieces(rng)
        for n, a in enumerate(AREAS, start=1):
            self.area(n, a, np.random.default_rng(self.seed * 100 + n))
        self.sc.root.p["primary"] = av
        return self


# ==================================================================== placing things in an area

WALL_IN = {"Lava": 52.6, "Toy": 58.6, "Olympus": 57.2}     # where props stop short of the walls


class Layout:
    """What is taken in one area: rectangles (the sign, the hero) and circles (props)."""

    def __init__(self, n, wall=FIELD_X[1] - 0.6):
        self.n = n
        self.wall = wall
        self.zs, self.zn = area_z(n)
        self.rects = []
        self.circles = []

    def rect(self, x0, x1, z0, z1):
        self.rects.append((min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)))

    def free(self, x, z, r):
        for (x0, x1, z0, z1) in self.rects:
            cx = min(max(x, x0), x1)
            cz = min(max(z, z0), z1)
            if math.hypot(x - cx, z - cz) < r:
                return False
        for (cx, cz, cr) in self.circles:
            if math.hypot(x - cx, z - cz) < (r + cr) * 0.92:
                return False
        return True

    def find(self, t, scale, band, rng, solid):
        r = max(t.radius(scale), 0.8)
        z_hi, z_lo = self.zs - 4.0 - r, self.zn + 4.0 + r
        wall = self.wall
        if band == "Edge" or (band == "Side" and LANE + r + 1.0 > wall - r):
            xr = (wall - r - 2.0, wall - r)
        elif band == "Side":
            xr = (LANE + r + 1.0, wall - r)
        else:
            xr = (0.0 if not solid else LANE + r + 1.0, wall - r)
        if xr[0] > xr[1]:
            return None
        for _ in range(60):
            x = float(rng.uniform(*xr)) * float(rng.choice((-1.0, 1.0)))
            z = float(rng.uniform(z_lo, z_hi))
            if self.free(x, z, r):
                self.circles.append((x, z, r))
                return (x, z, r)
        return None


def place_mounds(n, rng, tucked, lay):
    """14 spots: at least 16 apart, 12 from the walls, 20 from the area's ends, clear of what is
    placed (props by their radius plus 3, the hero and the sign)."""
    zs, zn = area_z(n)
    xlim = FIELD_X[1] - MOUND_WALL - 3.3
    z_hi, z_lo = zs - MOUND_BORDER, zn + MOUND_BORDER

    def ok(x, z, chosen):
        if abs(x) > xlim or not (z_lo <= z <= z_hi):
            return False
        for (x0, x1, z0, z1) in lay.rects:
            cx, cz = min(max(x, x0), x1), min(max(z, z0), z1)
            if math.hypot(x - cx, z - cz) < 4.0:
                return False
        for (cx, cz, cr) in lay.circles:
            if math.hypot(x - cx, z - cz) < cr + 3.6:
                return False
        return all(math.hypot(x - cx, z - cz) >= MOUND_GAP for (cx, cz) in chosen)

    chosen = []
    for (x, z) in tucked:
        if len(chosen) < 5 and ok(x, z, chosen):
            chosen.append((x, z))
    while len(chosen) < MOUND_COUNT:
        best, best_d = None, -1.0
        for t in range(600):
            x = float(rng.uniform(-xlim, xlim))
            z = float(rng.uniform(z_lo, z_hi))
            if not ok(x, z, chosen):
                continue
            d = min([math.hypot(x - cx, z - cz) for (cx, cz) in chosen] + [1e9])
            if d > best_d:
                best, best_d = (x, z), d
            if t > 60 and best is not None:
                break
        if best is None:
            raise RuntimeError("area %d: only %d mounds fit" % (n, len(chosen)))
        chosen.append(best)
    return chosen


def mound_colours(t, soil, leaf, flag):
    """The Mound tinted for an area: each Soil, Leaf and Flag brick takes shade(tint, its Shade)."""
    base = {"Soil": soil, "Leaf": leaf, "Flag": flag}
    out = {}
    for p in t.parts:
        if p["name"] in base:
            k = p["attrs"].get("Shade", 0.0)
            out[tuple(p["color"])] = tuple(shade(base[p["name"]], k))
    return out


# ==================================================================== each area's own touch

def _wall_x(sx):
    return sx * FIELD_X[1]


def ex_frost(mb, n, a, af, rng, lay):
    """Icicles hanging under the caps on both walls' lane faces."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Icicles")
    first = None
    for sx in (-1, 1):
        for k, z in enumerate(np.arange(zs - 8.0, zn + 4.0, -14.0)):
            L = 3.0 + 2.2 * ((k * 7 + (sx > 0) * 3) % 4) / 3.0
            x = sx * (FIELD_X[1] - 0.45)
            p = part(sc, m, "Icicle", (0.9, L, 0.9), CF((x, WALL_H - L / 2 + 0.02, float(z))), "cfeaff", shadow=False)
            part(sc, m, "Icicle", (0.5, L * 0.45, 0.5), CF((x, WALL_H - L - L * 0.2 + 0.1, float(z) + 0.05)), "e8f6ff",
                 shadow=False)
            first = first or p
    m.p["primary"] = first


def ex_lava(mb, n, a, af, rng, lay):
    """Glowing lava channels along both walls, behind low rock kerbs (not walkable)."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "LavaChannels")
    first = None
    for sx in (-1, 1):
        xin = sx * (FIELD_X[1] - 6.0)
        seg = 27.5
        for k in range(8):
            z0 = zs - k * seg
            z1 = z0 - seg
            zc = (z0 + z1) / 2
            if any((rx1 > 50.0 if sx > 0 else rx0 < -50.0) and rz0 < z0 and rz1 > z1
                   for (rx0, rx1, rz0, rz1) in lay.rects):
                continue
            p = part(sc, m, "Lava", (5.4, 0.3, seg - 0.04 * (k % 2)), CF((sx * (FIELD_X[1] - 2.7), 0.15, zc)),
                     "ff7a1a", material="Neon", attrs={"Flicker": 0.15, "NightLamp": True})
            first = first or p
            part(sc, m, "Kerb", (1.6, 1.0, seg - 0.6), CF((xin, 0.5, zc), G.ry(float(rng.uniform(-1.5, 1.5)))),
                 "2e2a2c" if k % 2 else "3a3436", solid=True)
    m.p["primary"] = first


def ex_candy(mb, n, a, af, rng, lay):
    """White icing drips under the caps and a candy-stripe cap band."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Icing")
    first = None
    for sx in (-1, 1):
        x = sx * (FIELD_X[1] - 0.4)
        for k, z in enumerate(np.arange(zs - 3.0, zn + 2.0, -6.0)):
            L = 2.0 + 3.0 * ((k * 5 + (sx > 0)) % 4) / 3.0
            p = part(sc, m, "Drip", (2.2, L, 0.8), CF((x, WALL_H - L / 2, float(z))), "fffafa", shadow=False)
            first = first or p
        for k, z in enumerate(np.arange(zs - 5.0, zn, -10.0)):
            part(sc, m, "Stripe", (8.4, 1.6, 1.4), CF((sx * (FIELD_X[1] + 4.0), WALL_H + CAP_H + 0.8, float(z)),
                                                       G.rx(30)), "e8403a" if k % 2 == 0 else "fffafa")
    m.p["primary"] = first


def ex_cosmic(mb, n, a, af, rng, lay):
    """Neon star specks on both walls and a few glowing star tiles on the ground."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Stars")
    first = None
    for sx in (-1, 1):
        for k in range(14):
            z = float(rng.uniform(zn + 4, zs - 4))
            y = float(rng.uniform(8, WALL_H - 4))
            s = float(rng.choice((0.8, 1.2, 1.6)))
            p = part(sc, m, "Star", (0.3, s, s), CF((sx * (FIELD_X[1] - 0.12), y, z), G.rx(45)),
                     "fff4c2" if k % 3 else "a8c8ff", material="Neon", shadow=False, attrs={"Flicker": 0.3})
            first = first or p
    for k in range(10):
        x = float(rng.uniform(-50, 50))
        z = float(rng.uniform(zn + 6, zs - 6))
        part(sc, m, "StarTile", (1.6, 0.06, 1.6), CF((x, 0.03, z), G.ry(45)), "fff4c2", material="Neon", shadow=False)
    m.p["primary"] = first


def ex_neon(mb, n, a, af, rng, lay):
    """Neon strips along both walls and the lane edges."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "NeonStrips")
    first = None
    for sx in (-1, 1):
        for y, c in ((6.0, "00e0ff"), (14.0, "ff2bd6")):
            p = part(sc, m, "Strip", (0.4, 0.6, AREA_LEN - 0.02 * (y > 10)), CF((sx * (FIELD_X[1] - 0.2), y, (zs + zn) / 2)),
                     c, material="Neon", attrs={"NightLamp": True})
            first = first or p
        part(sc, m, "LaneLine", (0.5, 0.06, AREA_LEN - 6.0), CF((sx * LANE, 0.03, (zs + zn) / 2)), "00e0ff",
             material="Neon", shadow=False)
    m.p["primary"] = first


def ex_marsh(mb, n, a, af, rng, lay):
    """Patches of murky water (walk-through, flush with the ground)."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Water")
    first = None
    for k, (x, z) in enumerate(((-38.0, zs - 40.0), (36.0, zs - 120.0), (-34.0, zs - 170.0), (40.0, zs - 60.0))):
        for j, (w, d, h) in enumerate(((16.0, 9.0, 0), (9.0, 14.0, 0), (13.0, 13.0, 45))):
            p = part(sc, m, "Water", (w, 0.06 + 0.01 * j, d), CF((x, 0.03 + 0.005 * j, z), G.ry(h + k * 10)), "2a6a78",
                     shadow=False)
            first = first or p
        lay.circles.append((x, z, 8.0))
    m.p["primary"] = first


def ex_olympus(mb, n, a, af, rng, lay):
    """White columns with gold capitals standing against both walls."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Columns")
    first = None
    for sx in (-1, 1):
        for k, z in enumerate(np.arange(zs - 12.0, zn + 6.0, -26.0)):
            x = sx * (FIELD_X[1] - 1.3)
            if not lay.free(x, float(z), 2.0):
                continue
            lay.circles.append((x, float(z), 2.0))
            p = part(sc, m, "Column", (2.4, 30.0, 2.4), CF((x, 15.0, float(z))), "f6f2ea", solid=True)
            first = first or p
            part(sc, m, "Capital", (3.2, 1.4, 3.2), CF((x, 30.7, float(z))), "ffd447")
            part(sc, m, "Base", (3.2, 1.0, 3.2), CF((x, 0.5, float(z))), "e8e4d8", solid=True)
    m.p["primary"] = first


def ex_toy(mb, n, a, af, rng, lay):
    """Toy-block bands along both walls."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Blocks")
    first = None
    cols = ("ffd447", "4da6ff", "5ee06a", "ff8a3d")
    for sx in (-1, 1):
        for k, z in enumerate(np.arange(zs - 10.0, zn + 5.0, -20.0)):
            p = part(sc, m, "Block", (1.2, 6.0, 19.6), CF((sx * (FIELD_X[1] - 0.6), 3.0, float(z))), cols[k % 4])
            first = first or p
    m.p["primary"] = first


def ex_void(mb, n, a, af, rng, lay):
    """Glitch squares flickering on both walls."""
    sc = mb.sc
    zs, zn = area_z(n)
    m = sc.model(af, "Glitch")
    first = None
    for sx in (-1, 1):
        for k in range(12):
            z = float(rng.uniform(zn + 4, zs - 4))
            y = float(rng.uniform(4, WALL_H - 6))
            s = float(rng.choice((1.5, 2.5, 3.5)))
            p = part(sc, m, "Glitch", (0.3, s, s * 1.6), CF((sx * (FIELD_X[1] - 0.12), y, z)),
                     ("ff2bd6", "00f0ff", "7a5cff")[k % 3], material="Neon", attrs={"Flicker": 0.6})
            first = first or p
    m.p["primary"] = first


# the particles each area gets: (attachment name, height, how many along the area)
FX = {"Frost": ("Fx_Snow", 40.0, 6), "Lava": ("Fx_Embers", 1.0, 8), "Reef": ("Fx_Bubbles", 2.0, 6),
      "Marsh": ("Fx_Bubbles", 0.5, 4), "Cosmic": ("Fx_Stars", 30.0, 6), "Crystal": ("Fx_Sparkle", 12.0, 6),
      "Candy": ("Fx_Sparkle", 12.0, 4), "Cloud": ("Fx_Sparkle", 16.0, 4), "Olympus": ("Fx_Sparkle", 16.0, 4),
      "Void": ("Fx_Stars", 20.0, 6), "Haunt": ("Fx_Smoke", 1.0, 4), "Neon": ("Fx_Sparkle", 20.0, 4)}

EXTRAS = {"Frost": ex_frost, "Lava": ex_lava, "Candy": ex_candy, "Cosmic": ex_cosmic, "Neon": ex_neon,
          "Marsh": ex_marsh, "Olympus": ex_olympus, "Toy": ex_toy, "Void": ex_void}


# ==================================================================== checks

def check(mb, budget=28000):
    """The rules the map keeps."""
    sc = mb.sc
    errs = []
    parts = [n for n in sc.root.walk() if n.kind == "Part"]
    if len(parts) > budget:
        errs.append("%d parts (budget %d)" % (len(parts), budget))
    from . import brickcheck
    for p in parts:
        sz = p.p["size"]
        if min(sz) < 0.05 - 1e-9:
            errs.append("%s: a side under 0.05" % p.path())
        if p.p["shadow"] and max(sz) < MS.SMALL:
            errs.append("%s: small part casts a shadow" % p.path())
        if p.p["material"] == "Plastic" and p.p["surfaces"] != "inlet":
            errs.append("%s: Plastic not Inlet" % p.path())
        if p.p["collide"] and (p.p["touch"] or not p.p["query"]):
            errs.append("%s: solid but CanTouch / not CanQuery" % p.path())
        if not p.p["anchored"]:
            errs.append("%s: not anchored" % p.path())
        at = p.p.get("attrs") or {}
        if ("Flicker" in at or "NightLamp" in at) and p.p["material"] != "Neon":
            errs.append("%s: Flicker / NightLamp on %s" % (p.path(), p.p["material"]))
    # the running lane: nothing solid in X -22..22 in the fields, above the ground
    for p in parts:
        if not p.p["collide"]:
            continue
        lo, hi = _aabb(p)
        if hi[2] < 0.0 and lo[2] > FIELD_END - 1 and hi[1] > 0.05:
            if lo[0] < LANE and hi[0] > -LANE and p.name not in ("Ground",):
                errs.append("lane: %s at x %.1f..%.1f z %.1f" % (p.path(), lo[0], hi[0], lo[2]))
    # the avenue: nothing stands in X -20..20 of the yard but flat marks
    for p in parts:
        lo, hi = _aabb(p)
        if lo[2] > 0.5 and hi[2] < MEET_Z[1] and lo[0] < AVENUE_X[1] and hi[0] > AVENUE_X[0] and hi[1] > 0.3 \
                and lo[1] < 12.0:
            errs.append("avenue: %s" % p.path())
    # the pens are bare
    for name, _e, _l, (x0, x1, z0, z1) in plots():
        for p in parts:
            lo, hi = _aabb(p)
            if lo[0] < x1 - 0.01 and hi[0] > x0 + 0.01 and lo[2] < z1 - 0.01 and hi[2] > z0 + 0.01 and hi[1] > 0.02:
                errs.append("%s is not bare: %s" % (name, p.path()))
    # the gate's opening is clear from the ground to Y 30, the whole 120 wide
    for p in parts:
        if p.name in ("Barrier", "RedLine", "LineBoard") or not p.p["collide"]:
            continue
        lo, hi = _aabb(p)
        if lo[0] < GATE_X[1] and hi[0] > GATE_X[0] and lo[2] < 1.0 and hi[2] > -1.0 and lo[1] < GATE_CLEAR and hi[1] > 0.05:
            errs.append("gate opening: %s" % p.path())
    # mounds
    for n, inf in mb.info.items():
        if not isinstance(n, int):
            continue
        s = inf["mounds"]
        if len(s) != MOUND_COUNT:
            errs.append("area %d: %d mounds" % (n, len(s)))
        for i in range(len(s)):
            for j in range(i + 1, len(s)):
                if math.hypot(s[i][0] - s[j][0], s[i][1] - s[j][1]) < MOUND_GAP - 1e-6:
                    errs.append("area %d: mounds %d and %d too close" % (n, i, j))
    errs += [e for e in zfight_by_model(mb)]
    return errs


def _aabb(p):
    c = p.p["cf"]
    h = np.abs(c.R) @ (np.asarray(p.p["size"]) / 2)
    return c.p - h, c.p + h


def zfight_by_model(mb):
    """Z-fighting inside each piece I made for the map (templates are checked once each)."""
    from . import brickcheck
    out = []
    for key, t in mb.T.items():
        if key.startswith(("FV_", "Hero_", "Prop_")):       # Folk Valley's own; heroes and props are checked
            continue                                         # when their piece is built (build_kit.py)
        sc = spslib.Scene("Z")
        m = sc.model(sc.root, key)
        for p in t.parts:
            sc.part(m, p["name"], p["size"], p["rel"], p["color"], shape=p["shape"], material=p["material"],
                    grid=False, surfaces=p["surfaces"], transparency=p["transparency"])
        ps = [n for n in m.walk() if n.kind == "Part"]
        for a, b, ar in brickcheck.zfight(ps, ground=0.0 if not key.startswith("Mound") else -PK.MOUND_FLOOR):
            out.append("z-fight in %s: %s / %s (%.3f)" % (key, a.name, b.name, ar))
    return out


def stats(mb):
    sc = mb.sc
    out = {}
    for top in sc.root.children:
        out[top.name] = sum(1 for n in top.walk() if n.kind == "Part")
    per_area = {}
    for n in range(1, N_AREAS + 1):
        f = mb.fields.find("Area%d" % n)
        mk = mb.markers.find("Area%d" % n)
        per_area[n] = sum(1 for x in f.walk() if x.kind == "Part") + sum(1 for x in mk.walk() if x.kind == "Part")
    return out, per_area
