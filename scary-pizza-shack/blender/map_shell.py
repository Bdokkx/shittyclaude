"""The shack itself: checker floor, coursed walls with the three openings, ceiling with
the hatch hole, attic, flat roof with parapet, corner pilasters, the brick PIZZA sign
with its Bulbs, the serving window's awning / shutter box and the menu board."""
import numpy as np

import layout as L
import mk
import spsgeo as G
from spsgeo import CF


def build(sc):
    shack = sc.folder(sc.root, "Shack")
    floor(sc, sc.folder(shack, "Floor"))
    walls(sc, sc.folder(shack, "Walls"))
    roof(sc, sc.folder(shack, "Roof"))
    sign(sc, sc.model(shack, "PizzaSign"))
    awning(sc, sc.model(shack, "Awning"))
    menu_board(sc, sc.model(shack, "MenuBoard"))
    side_window(sc, sc.model(shack, "SideWindow"))
    trims(sc, sc.folder(shack, "Trim"))
    return shack


# ---------------------------------------------------------------- floor

def floor(sc, f):
    k = 0
    for i, x in enumerate(range(int(L.IN_X0), int(L.IN_X1), 2)):
        for j, z in enumerate(range(int(L.IN_Z0), int(L.IN_Z1), 2)):
            col = "tile_dark" if (i + j) % 2 == 0 else "tile_light"
            sc.box(f, "Tile", (x, 0.0, z), (x + 2, L.FLOOR, z + 2), col)
            k += 1
    return k


# ---------------------------------------------------------------- walls

def walls(sc, f):
    c = L.COURSES
    # south wall (front): X -17..17 between the side walls, serving window
    for ua, ub, ya, yb, col in mk.wall_pieces(L.IN_X0, L.IN_X1, c, [(L.WIN_X0, L.WIN_X1, L.WIN_Y0, L.WIN_Y1)]):
        sc.box(f, "WallSouth", (ua, ya, L.IN_Z1), (ub, yb, L.OUT_Z1), col)
    # north wall (back): back door
    for ua, ub, ya, yb, col in mk.wall_pieces(L.IN_X0, L.IN_X1, c, [(L.DOOR_X0, L.DOOR_X1, L.DOOR_Y0, L.DOOR_Y1)]):
        sc.box(f, "WallNorth", (ua, ya, L.OUT_Z0), (ub, yb, L.IN_Z0), col)
    # west wall: full depth incl. corners, side window
    for ua, ub, ya, yb, col in mk.wall_pieces(L.OUT_Z0, L.OUT_Z1, c, [(L.SIDE_Z0, L.SIDE_Z1, L.SIDE_Y0, L.SIDE_Y1)]):
        sc.box(f, "WallWest", (L.OUT_X0, ya, ua), (L.IN_X0, yb, ub), col)
    # east wall
    for ua, ub, ya, yb, col in mk.wall_pieces(L.OUT_Z0, L.OUT_Z1, c, []):
        sc.box(f, "WallEast", (L.IN_X1, ya, ua), (L.OUT_X1, yb, ub), col)


# ---------------------------------------------------------------- ceiling, attic, roof

HATCH = (3.0, 6.0, -3.0, 0.0)     # X0, X1, Z0, Z1 of the ceiling hole


def roof(sc, f):
    hx0, hx1, hz0, hz1 = HATCH
    y0, y1 = L.CEIL, L.CEIL_TOP
    for (x0, x1, z0, z1) in ((L.IN_X0, hx0, L.IN_Z0, L.IN_Z1), (hx1, L.IN_X1, L.IN_Z0, L.IN_Z1),
                             (hx0, hx1, L.IN_Z0, hz0), (hx0, hx1, hz1, L.IN_Z1)):
        sc.box(f, "Ceiling", (x0, y0, z0), (x1, y1, z1), "cream_dark")
    # ceiling beams (dark wood) running north-south, under the ceiling
    for z in (1.5, 7.0):
        sc.box(f, "CeilingBeam", (L.IN_X0, L.CEIL - 0.4, z - 0.5), (L.IN_X1, L.CEIL, z + 0.5), "wood_dark")
    # attic: joists over the ceiling and a dark lining under the roof (seen through the hatch)
    for x in (-13.0, -7.0, 1.0, 7.0, 12.0):
        sc.box(f, "AtticJoist", (x - 0.5, L.CEIL_TOP, L.IN_Z0), (x + 0.5, L.CEIL_TOP + 1.2, L.IN_Z1), "wood_dark",
               collide=False)
    sc.box(f, "AtticRidge", (L.IN_X0, L.WALL_TOP - 1.2, -1.0), (L.IN_X1, L.WALL_TOP, 1.0), "wood_dark", collide=False)
    # flat roof slab, parapet and coping
    sc.box(f, "Roof", (L.OUT_X0, L.WALL_TOP, L.OUT_Z0), (L.OUT_X1, L.ROOF_TOP, L.OUT_Z1), "grey_dark")
    p0, p1 = L.ROOF_TOP, L.PARAPET_TOP
    sc.box(f, "Parapet", (L.IN_X0, p0, L.IN_Z1), (L.IN_X1, p1, L.OUT_Z1), "cream")
    sc.box(f, "Parapet", (L.IN_X0, p0, L.OUT_Z0), (L.IN_X1, p1, L.IN_Z0), "cream")
    sc.box(f, "Parapet", (L.OUT_X0, p0, L.OUT_Z0), (L.IN_X0, p1, L.OUT_Z1), "cream")
    sc.box(f, "Parapet", (L.IN_X1, p0, L.OUT_Z0), (L.OUT_X1, p1, L.OUT_Z1), "cream")
    c0, c1 = L.PARAPET_TOP, L.COPING_TOP
    sc.box(f, "Coping", (L.IN_X0, c0, L.IN_Z1 - 0.5), (L.IN_X1, c1, L.OUT_Z1 + 0.5), "green")
    sc.box(f, "Coping", (L.IN_X0, c0, L.OUT_Z0 - 0.5), (L.IN_X1, c1, L.IN_Z0 + 0.5), "green")
    sc.box(f, "Coping", (L.OUT_X0 - 0.5, c0, L.IN_Z0 + 0.5 - 1.0), (L.IN_X0 + 0.5, c1, L.IN_Z1 - 0.5 + 1.0), "green")
    sc.box(f, "Coping", (L.IN_X1 - 0.5, c0, L.IN_Z0 + 0.5 - 1.0), (L.OUT_X1 + 0.5, c1, L.IN_Z1 - 0.5 + 1.0), "green")
    # corner pilasters, 2 x 2, from the ground to just above the coping
    for x in (L.OUT_X0, L.OUT_X1):
        for z in (L.OUT_Z0, L.OUT_Z1):
            sc.box(f, "Pilaster", (x - 1, L.WALL_BOTTOM - 0.4, z - 1), (x + 1, 15.4, z + 1), "red")
    # roof hatch box and vents (silhouette)
    sc.box(f, "RoofVent", (-12.0, L.ROOF_TOP, -6.0), (-9.0, L.ROOF_TOP + 1.2, -3.0), "grey")
    sc.box(f, "RoofVentCap", (-12.5, L.ROOF_TOP + 1.2, -6.5), (-8.5, L.ROOF_TOP + 1.6, -2.5), "grey_dark")
    sc.box(f, "RoofUnit", (2.0, L.ROOF_TOP, -9.0), (8.0, L.ROOF_TOP + 2.4, -5.0), "steel_dark")
    sc.box(f, "RoofUnitTop", (2.0, L.ROOF_TOP + 2.4, -9.0), (8.0, L.ROOF_TOP + 2.8, -5.0), "steel")
    sc.cylinder(f, "RoofUnitFan", 0.4, 3, (5.0, L.ROOF_TOP + 3.0, -7.0), (0, 1, 0), "grey_dark")


# ---------------------------------------------------------------- PIZZA sign

SIGN_Y0 = L.COPING_TOP
SIGN_Y1 = SIGN_Y0 + 9.2           # board 15.0 .. 24.2
SIGN_X = 12.0


def sign(sc, m):
    z0, z1 = L.IN_Z1, L.OUT_Z1     # board sits on the front parapet line
    sc.box(m, "Board", (-SIGN_X, SIGN_Y0, z0), (SIGN_X, SIGN_Y1, z1), "red")
    sc.box(m, "BoardTop", (-SIGN_X - 0.5, SIGN_Y1, z0 - 0.5), (SIGN_X + 0.5, SIGN_Y1 + 0.4, z1 + 0.5), "mustard")
    # support legs behind the board
    for x in (-9.0, 0.0, 9.0):
        sc.wedge(m, "Brace", (1, 5.6, 4), (x, L.ROOF_TOP + 2.8, z0 - 2.0), np.eye(3), "grey_dark")
    # letters: 3x5 pixels of 1 x 1.2 bricks, 1 stud proud of the board
    rects, width = mk.pixel_runs("PIZZA")
    px, py = 1.0, 1.2
    ly0 = SIGN_Y0 + 1.6
    lx0 = -width * px / 2
    for c0, c1, r0, r1 in rects:
        x0, x1 = lx0 + c0 * px, lx0 + c1 * px
        ya, yb = ly0 + (5 - r1) * py, ly0 + (5 - r0) * py
        sc.box(m, "Letter", (x0, ya, z1), (x1, yb, z1 + 1.0), "mustard")
    # marquee bulbs round the board
    bulbs = []
    yb_, yt_ = SIGN_Y0 + 0.8, SIGN_Y1 - 0.8
    for x in np.arange(-SIGN_X + 1, SIGN_X - 0.5, 2.0):
        bulbs.append((x, yt_))
        bulbs.append((x, yb_))
    for y in (yb_ + 2.6, yb_ + 5.0):
        bulbs.append((-SIGN_X + 1.0, y))
        bulbs.append((SIGN_X - 1.0, y))
    bulbs.sort(key=lambda b: (-b[1], b[0]))
    out = []
    for i, (x, y) in enumerate(bulbs):
        b = sc.ball(m, "Bulb", 1.0, (x, y, z1 + 0.3), "bulb", material="Neon", collide=False, shadow=False)
        out.append(b)
    # three PointLights so the sign lights the front (in bottom-row bulbs)
    lows = [b for b in out if abs(b.p["cf"].p[1] - yb_) < 1e-6]
    lows.sort(key=lambda b: b.p["cf"].p[0])
    for b in (lows[1], lows[len(lows) // 2], lows[-2]):
        sc.light(b, "PointLight", "Light", "bulb", brightness=1.2, range_=22, shadows=False)
    sc.attr(m, "Bulbs", len(out))
    return out


# ---------------------------------------------------------------- awning / shutter box

HOUSING = (-6.0, 6.0, 6.6, 11.0, L.OUT_Z1, L.OUT_Z1 + 2.0)       # x0 x1 y0 y1 z0 z1


def awning(sc, m):
    x0, x1, y0, y1, z0, z1 = HOUSING
    sc.box(m, "ShutterBox", (x0, y0, z0), (x1, y1, z1), "green")
    sc.box(m, "ShutterBoxTrim", (x0 - 0.5, y1, z0), (x1 + 0.5, y1 + 0.4, z1 + 1.0), "mustard")
    # window posts (the shutter runs in them), ground to the box
    for xa in (x0, L.WIN_X1):
        sc.box(m, "Post", (xa, L.WALL_BOTTOM, z0), (xa + 1, y0, z1), "green")
    # striped awning: 2-wide wedges, high side at the box, low edge 4 out
    for i, x in enumerate(np.arange(x0, x1, 2.0)):
        col = "red" if i % 2 == 0 else "cream"
        sc.wedge(m, "Stripe", (2, 2.0, 4), (x + 1, y1 - 1.0, z1 + 2.0), G.ry(180), col)
        sc.box(m, "Valance", (x, y1 - 2.8, z1 + 3.0), (x + 2, y1 - 2.0, z1 + 4.0), col)


# ---------------------------------------------------------------- menu board (outside, east of the window)

def menu_board(sc, m):
    z = L.OUT_Z1
    sc.box(m, "Frame", (7.0, 3.8, z), (12.0, 8.6, z + 1.0), "mustard")
    sc.box(m, "Board", (7.5, 4.2, z + 0.2), (11.5, 8.2, z + 1.2), "green_dark")
    sc.box(m, "Title", (8.0, 7.4, z + 0.4), (11.0, 7.8, z + 1.4), "red")
    for i, y in enumerate((6.4, 5.6, 4.8)):
        sc.box(m, "Line", (8.0, y, z + 0.4), (10.0, y + 0.4, z + 1.4), "cream")
        sc.box(m, "Price", (10.4, y, z + 0.4), (11.4, y + 0.4, z + 1.4), "mustard")
    sc.cylinder(m, "Lamp", 1, 1, (9.5, 9.2, z + 0.8), (0, 0, 1), "grey_dark")
    sc.part(m, "LampBulb", (1, 1, 1), CF((9.5, 8.9, z + 1.2)), "bulb", shape="Ball", material="Neon", collide=False,
            shadow=False)


# ---------------------------------------------------------------- side window (west wall)

def side_window(sc, m):
    zc = (L.SIDE_Z0 + L.SIDE_Z1) / 2
    mk.panel_x(sc, m, "Glass", (L.OUT_X0 + L.IN_X0) / 2, L.SIDE_Y0 - 0.1, L.SIDE_Y1 + 0.1,
               L.SIDE_Z0, L.SIDE_Z1, "glass", material="Glass", transparency=0.55)
    # outside frame: sill, head, mullion
    sc.box(m, "SillOut", (L.OUT_X0 - 1.0, L.SIDE_Y0 - 0.4, L.SIDE_Z0 - 0.5), (L.OUT_X0, L.SIDE_Y0, L.SIDE_Z1 + 0.5),
           "mustard")
    sc.box(m, "SillIn", (L.IN_X0, L.SIDE_Y0 - 0.4, L.SIDE_Z0), (L.IN_X0 + 1.0, L.SIDE_Y0, L.SIDE_Z1), "mustard")
    sc.box(m, "Head", (L.OUT_X0 - 1.0, L.SIDE_Y1, L.SIDE_Z0 - 1.0), (L.OUT_X0, L.SIDE_Y1 + 0.4, L.SIDE_Z1 + 1.0),
           "green")
    mk.panel_x(sc, m, "Mullion", L.OUT_X0 - 0.2, L.SIDE_Y0 - 0.1, L.SIDE_Y1 + 0.1, zc - 0.5, zc + 0.5, "green")
    return m


# ---------------------------------------------------------------- trims

def trims(sc, f):
    # back door head outside + a caged lamp over it
    sc.box(f, "DoorHead", (L.DOOR_X0, L.DOOR_Y1, L.OUT_Z0 - 1.0), (L.DOOR_X1 + 1.0, L.DOOR_Y1 + 0.8, L.OUT_Z0),
           "mustard")
    # serving window: inside head trim
    sc.box(f, "WindowHeadIn", (L.WIN_X0, L.WIN_Y1, L.IN_Z1 - 1.0), (L.WIN_X1, L.WIN_Y1 + 0.4, L.IN_Z1),
           "mustard")
