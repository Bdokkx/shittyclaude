"""Stations (section B): every station is a Model in PizzaShack.Stations with a Stand
marker on the floor (facing the station) and the extra markers asked for. Item
markers lie exactly on the surface an item rests on and face the same way as the
Stand (so an item keeps the orientation it had in the player's hand).

Moving pieces are single anchored Parts/MeshParts with PivotOffset on the hinge or
slide axis (pivot frames are axis-aligned with the world); their small decorations
are welded to them, so PivotTo / setting CFrame carries everything along.
"""
import math

import numpy as np

import layout as L
import map_items as I
import mk
import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

N, S_, E, W = (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)
MOVING = []          # (model, part, how it moves) for the README


def facing(d):
    return G.facing(d)


def station(sc, name):
    return sc.model(sc.root.get("Stations"), name)


def stand(sc, m, x, z, d, name="Stand", y=None):
    return sc.marker(m, name, CF((x, L.FLOOR if y is None else y, z), facing(d)))


def spot(sc, m, name, x, y, z, d):
    return sc.marker(m, name, CF((x, y, z), facing(d)))


def pivot(node, world_cf):
    node.p["pivot"] = node.p["cf"].inv() * world_cf


def moving(m, part, how):
    MOVING.append((m.name if hasattr(m, "name") else m, part, how))


def mesh(sc, m, pname, geo, color, owner=None, frame=None, **kw):
    owner = owner or m.name
    return sc.mesh(m, pname, owner + "__" + pname, geo, frame or CF(), color, owner=owner, **kw)


def weld_all(sc, root, parts):
    for p in parts:
        p.p["anchored"] = False
        p.p["massless"] = True
        sc.weld(root, p, "Weld")


# ---------------------------------------------------------------- counters

def north_counter(sc, m, x0, x1, riser=True, top="steel", cab="red", doors=True):
    z0, z1 = L.IN_Z0, L.N_FRONT
    sc.box(m, "Cabinet", (x0, L.CAB_Y0, z0 - 0.6), (x1, L.COUNTER_TOP0, z1 - 0.6), cab)
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, z1), top)
    if riser:
        sc.box(m, "Riser", (x0, L.WORK, z0), (x1, L.RISER_TOP, z0 + L.RISER), "steel_dark")
    if doors:
        _doors(sc, m, x0, x1, lambda a, b, y0, y1: mk.panel_z(sc, m, "CabinetDoor", z1 - 0.6 - 0.1, a, b, y0, y1,
                                                                "red_dark"), "x", z1 - 0.6 - 0.3)


def south_counter(sc, m, x0, x1, top="steel", cab="red", doors=True):
    z0, z1 = L.S_FRONT, L.IN_Z1
    sc.box(m, "Cabinet", (x0, L.CAB_Y0, z0 + 0.6), (x1, L.COUNTER_TOP0, z1 + 0.6), cab)
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, z1), top)
    if doors:
        _doors(sc, m, x0, x1, lambda a, b, y0, y1: mk.panel_z(sc, m, "CabinetDoor", z0 + 0.6 + 0.1, a, b, y0, y1,
                                                                "red_dark"), "x", z0 + 0.6 + 0.3)


def east_counter(sc, m, z0, z1, top="steel", cab="red", doors=True):
    x0, x1 = L.E_FRONT, L.IN_X1
    sc.box(m, "Cabinet", (x0 + 0.6, L.CAB_Y0, z0), (x1 + 0.6, L.COUNTER_TOP0, z1), cab)
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, z1), top)
    if doors:
        _doors(sc, m, z0, z1, lambda a, b, y0, y1: mk.panel_x(sc, m, "CabinetDoor", x0 + 0.6 - 0.1, y0, y1, a, b,
                                                                "red_dark"), "z", x0 + 0.6 - 0.3)


def _doors(sc, m, a0, a1, make, axis, front):
    """One recessed door panel per 4 studs of cabinet front, with a steel knob mesh."""
    w = a1 - a0
    n = max(1, int(round(w / 4)))
    step = w / n
    for k in range(n):
        a, b = a0 + k * step + 0.5, a0 + (k + 1) * step - 0.5
        a, b = math.floor(a * 2) / 2, math.ceil(b * 2) / 2
        if (b - a) % 1:
            b -= 0.5
        make(a, b, 0.8, 2.8)
        c = (a + b) / 2 + (b - a) / 2 - 0.5
        if axis == "x":
            pos = (c, 2.3, front)
        else:
            pos = (front, 2.3, c)
        knob = G.sphere(0.12, 6, 3, c=pos)
        sc.mesh(m, "Knob", "Counter__Knob", G.sphere(0.12, 6, 3), CF(pos), "steel", owner="Counter",
                material="Metal")


# ---------------------------------------------------------------- north wall

def back_door(sc):
    m = station(sc, "BackDoor")
    x0, x1, y0, y1 = L.DOOR_X0, L.DOOR_X1, L.DOOR_Y0, L.DOOR_Y1
    zo, zi = L.OUT_Z0, L.IN_Z0
    door = sc.box(m, "Door", (x0, y0, zo), (x1, 4.6, zi), "green_dark", collide=True)
    parts = [sc.box(m, "DoorTop", (x0, 6.2, zo), (x1, y1, zi), "green_dark"),
             sc.box(m, "DoorStile", (x0, 4.6, zo), (x0 + 1, 6.2, zi), "green_dark"),
             sc.box(m, "DoorStile", (x1 - 1, 4.6, zo), (x1, 6.2, zi), "green_dark"),
             mk.panel_z(sc, m, "Window", (zo + zi) / 2, x0 + 1, x1 - 1, 4.6, 6.2 - 0.0 + 0.0, "glass",
                        material="Glass", transparency=0.4, grid=False)]
    kick = sc.box(m, "KickPlate", (x0 + 0.5, y0 + 0.2, zi - 0.6), (x1 - 0.5, y0 + 1.0, zi + 0.4), "steel")
    kick.p["collide"] = False
    parts.append(kick)
    lever = G.Geo()
    for zz, sgn in ((zi, 1), (zo, -1)):
        lever.add(G.cyl(0.14, 0.3, 8, "z", (x1 - 0.6, 3.6, zz + sgn * 0.15)))
        lever.add(G.box(0.7, 0.16, 0.16, (x1 - 0.85, 3.6, zz + sgn * 0.32)))
    parts.append(mesh(sc, m, "Lever", lever, "steel", material="Metal"))
    weld_all(sc, door, parts)
    pivot(door, CF((x0, 3.8, zo)))
    moving(m, "Door", "hinged on its west edge (outer face); rotate the pivot +90 deg about Y to swing it OUT into "
                      "the yard (north). Window, stiles, kick plate and levers are welded to it")
    # inside head trim + exit sign
    sc.box(m, "HeadTrim", (x0, y1, zi), (x1, y1 + 0.4, zi + 1), "mustard")
    sc.box(m, "ExitSign", (x0 + 1, 7.8, zi), (x1 - 1, 8.6, zi + 1), "black")
    sc.box(m, "ExitLight", (x0 + 1.5, 7.9, zi + 0.4), (x1 - 1.5, 8.5, zi + 1.2), (60, 220, 110), material="Neon",
           collide=False, grid=False)
    # caged lamp over the door outside
    cage = G.Geo()
    for a in range(4):
        cage.add(G.box(0.08, 0.9, 0.08, (0.32 * math.cos(math.pi / 4 + a * math.pi / 2), 0,
                                         0.32 * math.sin(math.pi / 4 + a * math.pi / 2))))
    cage.add(G.ring(0.36, 0.28, 0.08, 8, c=(0, 0.45, 0)))
    cage.add(G.ring(0.36, 0.28, 0.08, 8, c=(0, -0.45, 0)))
    cage.add(G.box(0.2, 0.2, 0.9, (0, 0.45, 0.45)))
    lampc = (x0 + 2.0, y1 + 1.6, zo - 0.75)
    mesh(sc, m, "LampCage", cage, "black", frame=CF(lampc))
    bulb = sc.ball(m, "Bulb", 1.0, lampc, "bulb", material="Neon", collide=False, shadow=False)
    sc.light(bulb, "PointLight", "Light", "bulb", brightness=0.9, range_=16, shadows=True)
    stand(sc, m, (x0 + x1) / 2, L.IN_Z0 + 1.6, N)
    return m


def fridge(sc):
    m = station(sc, "Fridge")
    x0, x1 = L.FRIDGE
    z0, z1 = L.IN_Z0, L.IN_Z0 + 4
    sc.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "black")
    mk.panel_x(sc, m, "Side", x0 + 0.2, 1.2, 8.2, z0, z1, "steel")
    mk.panel_x(sc, m, "Side", x1 - 0.2, 1.2, 8.2, z0, z1, "steel")
    sc.box(m, "Back", (x0 + 0.5, 1.2, z0), (x1 - 0.5, 8.0, z0 + 1), "white")
    sc.box(m, "Header", (x0 - 0.5, 8.2, z0), (x1 + 0.5, 9.4, z1 + 1), "red")
    sc.box(m, "Badge", (x0 + 1, 8.4, z1 + 1), (x1 - 1, 9.2, z1 + 1.4), "mustard", grid=False)
    sc.box(m, "Light", (x0 + 0.5, 7.8, z1 - 1), (x1 - 0.5, 8.2, z1), "bulb_cool", material="Neon", collide=False)
    lt = m.children[-1]
    sc.light(lt, "SurfaceLight", "Light", "bulb_cool", brightness=1.2, range_=8, shadows=False, angle=80, face="Bottom")
    slots = []
    for y in (6.2, 4.6, 3.0):
        sc.box(m, "Shelf", (x0 + 0.5, y - 0.4, z0 + 1), (x1 - 0.5, y, z1), "steel_dark")
    # numbered for the stock the game puts there: Slot1/2 (dough, cheese) at eye level on the
    # second shelf, Slot3/4 (first toppings) on the third, Slot5/6 top, Slot7/8 bottom
    k = 1
    for y in (4.6, 3.0, 6.2, 1.2):
        for x in (x0 + 1.2, x1 - 1.2):
            slots.append(spot(sc, m, "Slot%d" % k, x, y, z1 - 1.2, N))
            k += 1
    # a strip-curtain hint: two cold "frost" strips on the sides of the opening
    stand(sc, m, (x0 + x1) / 2, L.N_FRONT + L.STAND_GAP, N)
    return m


def dough_station(sc):
    m = station(sc, "DoughStation")
    x0, x1 = L.DOUGH
    north_counter(sc, m, x0, x1)
    zb0 = L.IN_Z0 + L.RISER
    sc.box(m, "Board", (x0, L.WORK, zb0 - 0.0), (x1, L.WORK + 0.4, zb0 + 4.0), "wood_light")
    # flour dusting on the board
    rng = np.random.default_rng(31)
    dust = G.Geo()
    for _ in range(9):
        r = 1.4 * math.sqrt(rng.random())
        a = rng.random() * math.tau
        pts = G.circle_pts(0.25 + 0.35 * rng.random(), 7)
        dust.add(G.slab_poly(pts, 0.012, ((x0 + x1) / 2 + r * math.cos(a), L.WORK + 0.4, zb0 + 2.0 + r * math.sin(a))))
    mesh(sc, m, "FlourDust", dust, "flour")
    spot(sc, m, "Work", (x0 + x1) / 2, L.WORK + 0.4, zb0 + 2.0, N)
    # flour bin on the riser
    bin_c = (x0 + 1.0, L.RISER_TOP, L.IN_Z0 + 0.5)
    tub = G.lathe_loop([(0.0, 0.0), (0.5, 0.0), (0.56, 0.9), (0.5, 0.9), (0.45, 0.08), (0.0, 0.08)], 10)
    tub.weld()
    mesh(sc, m, "FlourBin", tub, "white", frame=CF(bin_c))
    flour = G.lathe([(0, 0.6), (0.48, 0.6), (0.3, 0.8), (0, 0.86)], 10)
    mesh(sc, m, "Flour", G.outward(flour), "flour", frame=CF(bin_c))
    scoop = G.Geo().add([G.cyl(0.18, 0.3, 8, "y", (0, 0.0, 0)), G.cyl(0.05, 0.5, 5, "x", (0.35, 0.05, 0))])
    mesh(sc, m, "Scoop", scoop, "steel", frame=CF((bin_c[0] + 0.1, bin_c[1] + 0.95, bin_c[2])) * CF(R=G.rz(25)),
         material="Metal")
    # rolling-pin rack on the wall
    sc.box(m, "PinRack", (x0, 5.8, L.IN_Z0), (x1, 6.2, L.IN_Z0 + 1), "wood")
    for x in (x0 + 0.5, x1 - 0.5):
        sc.wedge(m, "PinBracket", (1, 0.8, 1), (x, 5.4, L.IN_Z0 + 0.5), G.rx(180), "wood_dark")
    pin = I.get("RollingPin")
    I.place(sc, m, pin, CF(((x0 + x1) / 2 - 1.65 + 0.15, 6.2 + 0.34, L.IN_Z0 + 0.55), facing(E)))
    stand(sc, m, (x0 + x1) / 2, L.N_FRONT + L.STAND_GAP, N)
    return m


def sauce_station(sc):
    m = station(sc, "SauceStation")
    x0, x1 = L.SAUCE
    north_counter(sc, m, x0, x1)
    zc = L.IN_Z0 + L.RISER + 2.0
    xs, xc = x0 + 2.0, x0 + 6.0
    spot(sc, m, "WorkSauce", xs, L.WORK, zc, N)
    spot(sc, m, "WorkCheese", xc, L.WORK, zc, N)
    # burner + big pot on the riser behind WorkSauce
    pc = (xs + 0.3, L.RISER_TOP, L.IN_Z0 + 0.62)
    burner = G.Geo().add([G.cyl(0.85, 0.12, 12, "y", (0, 0.06, 0)), G.ring(0.6, 0.45, 0.06, 12, c=(0, 0.15, 0))])
    mesh(sc, m, "Burner", burner, "black", frame=CF(pc))
    pot = G.lathe_loop([(0.0, 0.12), (0.72, 0.12), (0.8, 0.2), (0.8, 1.45), (0.86, 1.52), (0.74, 1.52),
                        (0.7, 1.4), (0.7, 0.24), (0.0, 0.24)], 14)
    pot.weld()
    for sx in (-1, 1):
        pot.add(G.torus(0.2, 0.05, 8, 4, "z", (sx * 0.92, 1.25, 0)))
    mesh(sc, m, "Pot", G.outward(pot), "steel", frame=CF(pc), material="Metal")
    sauce = G.lathe([(0, 1.18), (0.71, 1.18), (0.71, 1.24), (0, 1.27)], 14, rmod=wobble(4, 0.01))
    mesh(sc, m, "Sauce", G.outward(sauce), "sauce", frame=CF(pc))
    # ladle hook on the wall, the ladle hanging from it
    hook = G.tube([(0, 0.0, 0.0), (0, 0.0, 0.45), (0, 0.18, 0.55), (0, 0.3, 0.45)], 0.05, 5)
    hook.add(G.box(0.4, 0.4, 0.08, (0, 0, 0.04)))
    hk = (x0 + 0.55, 8.2, L.IN_Z0)
    mesh(sc, m, "Hook", hook, "steel", frame=CF(hk), material="Metal")
    hang = np.array(((-1, 0, 0), (0, 0, 1), (0, 1, 0)), float)          # ladle: bowl down, opening to the room
    I.place(sc, m, I.get("Ladle"), CF((hk[0], hk[1] - 0.2, L.IN_Z0 + 0.8), hang))
    # cheese block on a little board + box grater behind WorkCheese
    sc.box(m, "CheeseBoard", (xc - 1.5, L.RISER_TOP, L.IN_Z0), (xc + 0.5, L.RISER_TOP + 0.4, L.IN_Z0 + 1), "wood")
    cheese, grater = I.get("CheeseBlock"), I.get("Grater")
    I.place(sc, m, cheese, CF((xc - 0.6, L.RISER_TOP + 0.4, L.IN_Z0 + 0.5)) * cheese.rest().inv())
    I.place(sc, m, grater, CF((xc + 1.2, L.RISER_TOP, L.IN_Z0 + 0.5)) * grater.rest().inv())
    stand(sc, m, (x0 + x1) / 2, L.N_FRONT + L.STAND_GAP, N)
    stand(sc, m, xs, L.N_FRONT + L.STAND_GAP, N, name="StandSauce")
    stand(sc, m, xc, L.N_FRONT + L.STAND_GAP, N, name="StandCheese")
    return m


def wobble(k, amp):
    return lambda a: 1.0 + amp * math.sin(k * a)


def chop_station(sc):
    m = station(sc, "ChopStation")
    x0, x1 = L.CHOP
    north_counter(sc, m, x0, x1)
    zb0 = L.IN_Z0 + L.RISER
    sc.box(m, "Board", (x0 + 0.5, L.WORK, zb0 + 0.5), (x1 - 0.5, L.WORK + 0.4, zb0 + 3.5), "wood")
    spot(sc, m, "Work", (x0 + x1) / 2, L.WORK + 0.4, zb0 + 2.0, N)
    # knife block (a wedge) on the riser, knife in it
    kb = sc.wedge(m, "KnifeBlock", (2, 1.6, 1), (x1 - 1.2, L.RISER_TOP + 0.8, L.IN_Z0 + 0.5), G.ry(180), "wood_dark")
    d = np.array((0.0, -1.0, -0.55))
    d /= np.linalg.norm(d)
    up = np.cross(np.cross(d, (1, 0, 0)), d)
    Z = -d
    Y = np.cross(Z, np.cross((0, 1, 0), Z))
    Y /= np.linalg.norm(Y)
    X = np.cross(Y, Z)
    R = np.column_stack((X, Y, Z))
    grip = np.array((x1 - 1.6, L.RISER_TOP + 1.75, L.IN_Z0 + 1.05))
    I.place(sc, m, I.get("Knife"), CF(grip, R))
    for k, dx in enumerate((0.45, 0.9)):
        sc.mesh(m, "KnifeHandle", "Knife__Grip", None, CF(grip + (dx, -0.08 * k, -0.05), R), "black",
                owner="Knife", kind="item")
    stand(sc, m, (x0 + x1) / 2, L.N_FRONT + L.STAND_GAP, N)
    return m


def topping_rail(sc):
    m = station(sc, "ToppingRail")
    x0, x1 = L.TOPPING
    north_counter(sc, m, x0, x1, riser=False)
    sc.box(m, "Rail", (x0, L.WORK, L.IN_Z0), (x1, L.RISER_TOP, L.IN_Z0 + L.RISER), "steel_dark")
    tub = G.lathe_loop([(0.0, 0.0), (0.5, 0.0), (0.5, 0.6), (0.44, 0.6), (0.44, 0.06), (0.0, 0.06)], 4,
                       phase=math.pi / 4)
    tub.weld()
    tub = tub.xf(S(0.42 / 0.5 * 1.414 * 0.5 / 0.5 * 1.0, 1, 1.0))
    lo, hi = tub.bbox()
    tub = tub.xf(S(0.9 / (hi[0] - lo[0]), 1, 0.9 / (hi[2] - lo[2])))
    floor_y = None
    for k in range(6):
        cx = x0 + 0.5 + k
        c = (cx, L.RISER_TOP, L.IN_Z0 + 0.5)
        sc.mesh(m, "Tub", "ToppingRail__Tub", tub, CF(c), "steel", owner="ToppingRail", material="Metal")
        spot(sc, m, "Tub%d" % (k + 1), cx, L.RISER_TOP + 0.06, L.IN_Z0 + 0.5, N)
    spot(sc, m, "Work", (x0 + x1) / 2 - 0.5, L.WORK, L.IN_Z0 + L.RISER + 2.0, N)
    stand(sc, m, (x0 + x1) / 2 - 0.5, L.N_FRONT + L.STAND_GAP, N)
    return m


# ---------------------------------------------------------------- east wall

OVEN_DECKS = ((2.2, 4.2), (5.0, 7.0))


def oven(sc):
    m = station(sc, "Oven")
    x0, x1 = L.OVEN_X0, L.IN_X1
    z0, z1 = L.OVEN
    (a0, a1), (b0, b1) = OVEN_DECKS
    oz0, oz1 = z0 + 1, z1 - 1          # door openings 5 wide
    sc.box(m, "Base", (x0, L.CAB_Y0, z0), (x1, a0, z1), "brick")
    for (y0, y1) in OVEN_DECKS:
        sc.box(m, "Pillar", (x0, y0, z0), (x1, y1, oz0), "brick")
        sc.box(m, "Pillar", (x0, y0, oz1), (x1, y1, z1), "brick")
    sc.box(m, "Course", (x0, a1, z0), (x1, b0, z1), "brick_dark")
    sc.box(m, "Course", (x0, b1, z0), (x1, b1 + 1.2, z1), "brick")
    sc.box(m, "Flue", (x0 + 1, b1 + 1.2, z0 + 1), (x1, L.CEIL, z1 - 1), "brick_dark")
    sc.box(m, "Breast", (x0, -0.2, L.BREAST[0]), (x1, L.CEIL, L.BREAST[1]), "brick")
    sc.box(m, "Trim", (x0 - 0.4, b1 + 1.2, z0 - 0.5), (x0 + 0.6, b1 + 1.6, z1 + 0.5), "black")
    sc.box(m, "Trim", (x0 - 0.4, a1, z0 - 0.5), (x0 + 0.6, a1 + 0.4, z1 + 0.5), "black")
    glows, slots = [], []
    for k, (y0, y1) in enumerate(OVEN_DECKS):
        g = sc.box(m, "Glow", (x0 + 0.4, y1 - 0.4, oz0), (x1 + 0.4, y1, oz1), "fire", material="Neon", collide=False)
        sc.light(g, "PointLight", "Light", "fire", brightness=1.6, range_=10, shadows=False)
        glows.append(g)
        sc.box(m, "Soot", (x1 - 0.1, y0, oz0), (x1 + 0.9, y1 - 0.4, oz1), "soot")
        slots.append(spot(sc, m, "Slot%d" % (k + 1), x0 + 0.4 + 1.8, y0, (oz0 + oz1) / 2, E))
    # drop-down doors: 0.4 plates hinged on their bottom-back edge
    hdl = G.Geo()
    for dz in (-1.8, 1.8):
        hdl.add(G.box(0.4, 0.14, 0.14, (-0.2, 0, dz)))
    hdl.add(G.cyl(0.09, 3.9, 8, "z", (-0.42, 0, 0)))
    for k, (y0, y1) in enumerate(OVEN_DECKS):
        d = mk.panel_x(sc, m, "Door%d" % (k + 1), x0 + 0.2, y0, y1, oz0, oz1, "black", surfaces="smooth")
        h = sc.mesh(m, "DoorHandle", "Oven__DoorHandle", hdl, CF((x0, y1 - 0.45, (oz0 + oz1) / 2)), "steel",
                    owner="Oven", material="Metal")
        weld_all(sc, d, [h])
        pivot(d, CF((x0 + 0.4, y0, (oz0 + oz1) / 2)))
        moving(m, "Door%d" % (k + 1), "drop-down door hinged on its bottom edge; rotate the pivot +90 deg about Z "
                                      "and it falls open towards the room, ending flush with the deck floor")
    gauge = G.Geo().add([G.cyl(0.42, 0.12, 12, "x", (0, 0, 0)), G.box(0.04, 0.3, 0.06, (-0.08, 0.1, 0.05))])
    mesh(sc, m, "Gauge", gauge, "white", frame=CF((x0 - 0.06, b1 + 0.6, z1 - 0.9)))
    # chimney: from the attic floor through the roof, with the Smoke attachment at the top
    cx0, cx1, cz0, cz1 = x0 + 1, x1, L.BREAST[0] + 1, L.BREAST[1]
    ch = sc.box(m, "Chimney", (cx0, L.CEIL_TOP, cz0), (cx1, 19.4, cz1), "brick")
    sc.box(m, "ChimneyCap", (cx0 - 0.5, 19.4, cz0 - 0.5), (cx1 + 0.5, 19.8, cz1 + 0.5), "brick_dark")
    sc.box(m, "ChimneyMouth", (cx0 + 0.5, 19.8, cz0 + 0.5), (cx1 - 0.5, 20.2, cz1 - 0.5), "soot")
    sc.attachment(ch, "Smoke", CF(((cx0 + cx1) / 2, 20.2, (cz0 + cz1) / 2)))
    stand(sc, m, x0 - L.STAND_GAP - 0.6, (oz0 + oz1) / 2, E)
    return m


def peel_rack(sc):
    m = station(sc, "PeelRack")
    z0, z1 = L.PEEL
    zc = (z0 + z1) / 2
    mk.panel_x(sc, m, "Backboard", L.IN_X1 - 0.2, 3.4, 8.4, z0, z1, "wood_dark")
    hooks = G.Geo()
    for x in (L.IN_X1 - 3.4, L.IN_X1 - 0.6):
        hooks.add(G.tube([(x, 4.5, zc), (x, 4.25, zc), (x + 0.12, 4.25, zc)], 0.06, 5))
    hooks.add(G.cyl(0.07, 3.0, 6, "x", (L.IN_X1 - 1.6, 4.25, zc)))
    hooks.add(G.box(0.8, 0.3, 0.3, (L.IN_X1 - 0.3, 4.25, zc)))
    cup = G.lathe_loop([(0.0, 0.0), (0.35, 0.0), (0.35, 0.5), (0.28, 0.5), (0.28, 0.06), (0.0, 0.06)], 8)
    cup.weld()
    hooks.add(cup.xf(T(L.IN_X1 - 1.95, L.FLOOR, zc)))
    hooks.add(G.box(1.9, 0.1, 0.2, (L.IN_X1 - 1.0, L.FLOOR + 0.25, zc)))
    mesh(sc, m, "Hooks", hooks, "steel", material="Metal")
    # the peel stands blade-up, blade edge-on to the wall
    peel = I.get("PizzaPeel")
    R = np.column_stack(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
    lo, hi = peel.bbox()
    grip_y = L.FLOOR + 0.5 + hi[2]                    # handle end just above the floor cup
    I.place(sc, m, peel, CF((L.IN_X1 - 1.95, grip_y, zc), R))
    stand(sc, m, L.E_FRONT - L.STAND_GAP, zc, E)
    return m


def cut_table(sc):
    m = station(sc, "CutTable")
    z0, z1 = L.CUT
    east_counter(sc, m, z0, z1)
    sc.box(m, "Board", (L.E_FRONT - 0.2, L.WORK, z0), (L.IN_X1 - 0.2, L.WORK + 0.4, z1), "wood")
    spot(sc, m, "Work", (L.E_FRONT + L.IN_X1) / 2 - 0.2, L.WORK + 0.4, (z0 + z1) / 2, E)
    rail = G.Geo().add([G.cyl(0.07, 3.2, 6, "z", (0, 0, 0))])
    for dz in (-1.4, 1.4):
        rail.add(G.box(0.3, 0.16, 0.16, (0.15, 0, dz)))
    rc = (L.IN_X1 - 0.3, 6.6, (z0 + z1) / 2)
    mesh(sc, m, "ToolRail", rail, "steel", frame=CF(rc), material="Metal")
    cutter = I.get("PizzaCutter")
    R = np.column_stack(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # hanging wheel-down, flat to the wall
    I.place(sc, m, cutter, CF((rc[0] - 0.15, rc[1] - 0.05, rc[2] + 0.6), R))
    stand(sc, m, L.E_FRONT - L.STAND_GAP, (z0 + z1) / 2, E)
    return m


def kitchen_bin(sc):
    m = station(sc, "Bin")
    c = (L.E_FRONT - 0.95, L.FLOOR, L.CUT[1])
    body = G.lathe([(0, 0.0), (0.66, 0.0), (0.76, 2.2), (0, 2.2)], 10)
    mesh(sc, m, "Body", G.outward(body), "steel_dark", frame=CF(c), collide=True)
    band = G.ring(0.78, 0.7, 0.3, 10, c=(0, 2.05, 0))
    mesh(sc, m, "Band", band, "black", frame=CF(c))
    lid = G.lathe([(0, 0.0), (0.8, 0.0), (0.8, 0.12), (0.55, 0.32), (0, 0.38)], 10)
    lid = G.outward(lid)
    lid.add(G.box(0.3, 0.12, 0.2, (-0.8, 0.08, 0)))
    lidp = mesh(sc, m, "Lid", lid, "steel", frame=CF((c[0], c[1] + 2.2, c[2])), collide=True)
    pivot(lidp, CF((c[0] + 0.8, c[1] + 2.2, c[2])))
    moving(m, "Lid", "hinged at the back (counter side); rotate the pivot -90 deg about Z to flip it up")
    pedal = G.box(0.5, 0.12, 0.7, (-0.85, 0.2, 0))
    mesh(sc, m, "Pedal", pedal, "black", frame=CF(c))
    stand(sc, m, c[0] - 1.8, c[2], E)
    return m


def box_station(sc):
    m = station(sc, "BoxStation")
    z0, z1 = L.BOX
    x0, x1 = L.E_FRONT, L.IN_X1
    # folding table: top on four legs, flat boxes stacked underneath
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, z1), "wood_light")
    sc.box(m, "Apron", (x0, L.COUNTER_TOP0 - 0.4, z0), (x0 + 1, L.COUNTER_TOP0, z1), "wood_dark")
    for (lx, lz) in ((x0, z0), (x1 - 1, z0), (x0, z1 - 1), (x1 - 1, z1 - 1)):
        sc.box(m, "Leg", (lx, L.CAB_Y0, lz), (lx + 1, L.COUNTER_TOP0 - 0.4, lz + 1), "wood_dark")
    stack = G.Geo()
    rng = np.random.default_rng(8)
    for k in range(9):
        stack.add(G.box(3.4, 0.16, 3.4).xf(T(0, 0.08 + 0.17 * k, 0) @ RY((rng.random() - 0.5) * 8)
                                          @ T((rng.random() - 0.5) * 0.2, 0, (rng.random() - 0.5) * 0.2)))
    mesh(sc, m, "FlatBoxes", stack, "cardboard", frame=CF(((x0 + x1) / 2 + 0.3, L.FLOOR, (z0 + z1) / 2)))
    spot(sc, m, "Work", (x0 + x1) / 2, L.WORK, (z0 + z1) / 2, E)
    stand(sc, m, x0 - L.STAND_GAP, (z0 + z1) / 2, E)
    return m


# ---------------------------------------------------------------- south wall

def register(sc):
    m = station(sc, "Register")
    x0, x1 = L.REGISTER
    south_counter(sc, m, x0, x1)
    tx0, tx1 = x0 + 0.5, x0 + 3.5
    tz0, tz1 = L.S_FRONT + 1.0, L.S_FRONT + 3.0
    sc.box(m, "TillBase", (tx0, L.WORK, tz0), (tx1, L.WORK + 1.2, tz1), "black")
    sc.wedge(m, "Keyboard", (3, 0.8, 1), ((tx0 + tx1) / 2, L.WORK + 1.6, tz0 + 0.5), np.eye(3), "grey")
    sc.box(m, "TillTop", (tx0, L.WORK + 1.2, tz0 + 1), (tx1, L.WORK + 2.0, tz1), "grey")
    sc.box(m, "Display", (tx0 + 1, L.WORK + 2.0, tz0 + 1), (tx1 - 1, L.WORK + 2.8, tz0 + 2), "black")
    sc.box(m, "DisplayGlow", (tx0 + 1.2, L.WORK + 2.2, tz0 + 0.95), (tx1 - 1.2, L.WORK + 2.6, tz0 + 1.05),
           (110, 230, 140), material="Neon", grid=False, collide=False)
    keys = G.Geo()
    for i in range(4):
        for j in range(3):
            keys.add(G.box(0.4, 0.12, 0.2, (-0.9 + 0.6 * i, 0.06, -0.25 + 0.3 * j)).xf(RX(-38)))
    mesh(sc, m, "Keys", keys, "cream", frame=CF(((tx0 + tx1) / 2, L.WORK + 1.62, tz0 + 0.5)))
    drawer = sc.box(m, "Drawer", (tx0 + 0.5, L.WORK + 0.2, tz0 - 0.1), (tx1 - 0.5, L.WORK + 0.6, tz1 - 0.1),
                    "mustard")
    cash = G.Geo()
    for i in range(3):
        cash.add(G.box(0.7, 0.12, 1.2, (-0.95 + 0.95 * i, 0, 0)))
    cm = mesh(sc, m, "DrawerCash", cash, (104, 150, 96), frame=CF(((tx0 + tx1) / 2, L.WORK + 0.66, (tz0 + tz1) / 2)))
    pull = mesh(sc, m, "DrawerPull", G.box(0.8, 0.12, 0.1), "black", frame=CF(((tx0 + tx1) / 2, L.WORK + 0.4,
                                                                                tz0 - 0.16)))
    weld_all(sc, drawer, [cm, pull])
    pivot(drawer, CF(((tx0 + tx1) / 2, L.WORK + 0.4, tz0 - 0.1)))
    moving(m, "Drawer", "slides straight out towards the player (-Z) by 1.2; the cash inside is welded to it")
    # tip jar
    tj = sc.model(m, "TipJar")
    jar = G.lathe([(0, 0.0), (0.4, 0.0), (0.42, 0.9), (0.34, 1.0), (0.34, 1.1), (0, 1.1)], 10)
    c = (x1 - 0.9, L.WORK, L.S_FRONT + 1.3)
    mesh(sc, tj, "Jar", G.outward(jar), (200, 225, 215), owner="TipJar", frame=CF(c), material="Glass",
         transparency=0.5)
    coins = G.Geo()
    for k in range(6):
        coins.add(G.cyl(0.14, 0.05, 8, "y", (0.12 * math.cos(k * 2.1), 0.05 + 0.055 * k, 0.12 * math.sin(k * 2.1))))
    mesh(sc, tj, "Coins", coins, "mustard", owner="TipJar", frame=CF(c), material="Metal")
    stand(sc, m, (x0 + x1) / 2, L.S_FRONT - L.STAND_GAP, S_)
    return m


def rules_board(sc):
    m = station(sc, "RulesBoard")
    x0, x1 = 5.0, 12.0
    sc.part(m, "Face", (7.0, 5.0, 0.2), CF(((x0 + x1) / 2, 6.9, L.IN_Z1 - 0.1)), "green_dark", material="SmoothPlastic",
            surfaces="smooth", grid=False)
    for x in (x0 + 0.4, x1 - 0.4):
        sc.part(m, "Pin", (0.4, 0.4, 0.4), CF((x, 9.0, L.IN_Z1 - 0.25)), "red", shape="Ball", grid=False,
                collide=False)
    stand(sc, m, (x0 + x1) / 2, L.S_FRONT - L.STAND_GAP - 0.6, S_)
    return m


def plushie_shelf(sc):
    m = station(sc, "PlushieShelf")
    x0, x1 = 12.0, 17.0
    sc.box(m, "Shelf", (x0, 6.2, L.IN_Z1 - 2), (x1, 6.6, L.IN_Z1), "wood")
    sc.box(m, "Lip", (x0, 6.6, L.IN_Z1 - 2), (x1, 7.0, L.IN_Z1 - 1.6), "wood_dark", grid=False)
    for x in (x0 + 0.5, x1 - 1.5):
        sc.wedge(m, "Bracket", (1, 1.2, 1), (x + 0.5, 5.6, L.IN_Z1 - 0.5), G.rx(180), "wood_dark")
    for k in range(4):
        spot(sc, m, "Slot%d" % (k + 1), x0 + 0.65 + 1.25 * k, 6.6, L.IN_Z1 - 0.9, N)
    stand(sc, m, (x0 + x1) / 2 - 1.0, L.S_FRONT - L.STAND_GAP, S_)
    return m


def serving_window(sc):
    m = station(sc, "ServingWindow")
    x0, x1 = L.WINDOW
    south_counter(sc, m, x0, x1)
    # outside ledge on brackets
    sc.box(m, "Ledge", (x0, L.WORK - 0.8, L.OUT_Z1), (x1, L.WORK, L.OUT_Z1 + 2), "steel")
    for x in (x0 + 1.0, x1 - 2.0):
        sc.wedge(m, "LedgeBracket", (1, 1.2, 2), (x + 0.5, L.WORK - 1.4, L.OUT_Z1 + 1), G.rx(180), "mustard")
    spot(sc, m, "Handover", 0.0, L.WORK, (L.S_FRONT + L.IN_Z1) / 2, S_)
    sc.marker(m, "Customer", CF((0.0, 0.0, L.QUEUE_Z), facing(N)))
    # desk bell
    bell = G.lathe([(0, 0.08), (0.42, 0.08), (0.4, 0.2), (0.3, 0.42), (0.12, 0.5), (0, 0.52)], 12)
    bell.add(G.cyl(0.06, 0.12, 6, "y", (0, 0.58, 0)))
    bc = (x1 - 1.3, L.WORK, L.S_FRONT + 1.0)
    mesh(sc, m, "Bell", G.outward(bell), "mustard", frame=CF(bc), material="Metal")
    mesh(sc, m, "BellBase", G.cyl(0.46, 0.08, 12, "y", (0, 0.04, 0)), "black", frame=CF(bc))
    # ticket printer
    tp = sc.model(m, "TicketPrinter")
    px0, px1 = x0 + 0.6, x0 + 2.6
    sc.box(tp, "Body", (px0, L.WORK, L.S_FRONT + 1.4), (px1, L.WORK + 1.2, L.S_FRONT + 3.4), "grey_dark")
    sc.box(tp, "Top", (px0, L.WORK + 1.2, L.S_FRONT + 2.4), (px1, L.WORK + 1.6, L.S_FRONT + 3.4), "grey")
    paper = G.Geo()
    paper.add(G.box(1.0, 0.02, 0.7, (0, 0.0, -0.35)).xf(RX(-25)))
    mesh(sc, tp, "Paper", paper, "paper", owner="TicketPrinter",
         frame=CF(((px0 + px1) / 2, L.WORK + 1.22, L.S_FRONT + 2.0)))
    sc.box(tp, "Led", (px1 - 0.6, L.WORK + 0.8, L.S_FRONT + 1.3), (px1 - 0.2, L.WORK + 1.0, L.S_FRONT + 1.5),
           (90, 255, 120), material="Neon", grid=False, collide=False)
    # ticket rail above the window, inside
    tr = sc.model(m, "TicketRail")
    sc.box(tr, "Rail", (x0 + 1, 8.4, L.IN_Z1 - 1), (x1 - 1, 8.8, L.IN_Z1), "steel")
    for k in range(5):
        spot(sc, tr, "Ticket%d" % (k + 1), -3.2 + 1.6 * k, 8.4, L.IN_Z1 - 1.05, N)
    # the roll-down shutter (open: up inside the box over the window)
    sh = []
    zs0 = L.OUT_Z1 + 0.2
    for k in range(9):
        y0 = L.WIN_Y1 + 0.4 * k
        dz = 0.0 if k % 2 == 0 else 0.1
        col = "steel_dark" if k == 0 else ("grey" if k % 2 else "steel")
        sh.append(sc.box(m, "Shutter" if k == 0 else "Slat", (x0, y0, zs0 + dz), (x1, y0 + 0.4, zs0 + 1 + dz), col))
    weld_all(sc, sh[0], sh[1:])
    sh[0].p["anchored"] = True
    sh[0].p["massless"] = False
    pivot(sh[0], CF((0.0, L.WIN_Y1, zs0 + 0.5)))
    moving(m, "Shutter", "starts OPEN (rolled up into the box over the window). Slide it straight down 3.6 to close: "
                         "pivot Y 7.0 = open, Y 3.4 = closed (resting on the ledge). The 8 slats are welded to it")
    stand(sc, m, 0.0, L.S_FRONT - L.STAND_GAP, S_)
    return m


def shutter_button(sc):
    m = station(sc, "ShutterButton")
    x = L.BUTTON_X
    base = sc.box(m, "Base", (x - 1, 4.4, L.IN_Z1 - 1), (x + 1, 6.4, L.IN_Z1), "mustard")
    stripes = G.Geo()
    for k in range(3):
        stripes.add(G.box(0.25, 2.3, 0.04).xf(T(x - 0.6 + 0.6 * k, 5.4, L.IN_Z1 - 1.02) @ RZ(40)))
    stripes = G.Geo().add(stripes)
    mesh(sc, m, "Stripes", G.box(1.7, 1.7, 0.04, (x, 5.4, L.IN_Z1 - 1.02)), "black")
    ring = G.ring(0.62, 0.5, 0.12, 12, "z", (x, 5.4, L.IN_Z1 - 1.08))
    mesh(sc, m, "Collar", ring, "grey_dark")
    dome = G.lathe([(0, 0.0), (0.5, 0.0), (0.52, 0.12), (0.44, 0.3), (0.22, 0.42), (0, 0.45)], 12).xf(RX(-90))
    btn = mesh(sc, m, "Button", G.outward(dome), "red", frame=CF((x, 5.4, L.IN_Z1 - 1.04)), collide=True)
    pivot(btn, CF((x, 5.4, L.IN_Z1 - 1.04)))
    moving(m, "Button", "presses in: move it +Z (towards the wall) by 0.2, then back")
    stand(sc, m, x, L.S_FRONT - 0.8, S_)
    return m


def cctv_desk(sc):
    m = station(sc, "CCTVDesk")
    x0, x1 = L.CCTV
    z0 = L.S_FRONT
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, L.IN_Z1), "wood_dark")
    for (a, b) in ((x0, x0 + 2), (x1 - 2, x1)):
        sc.box(m, "Pedestal", (a, L.CAB_Y0, z0 + 0.6), (b, L.COUNTER_TOP0, L.IN_Z1 + 0.6), "wood")
    sc.box(m, "Modesty", (x0 + 2, 1.0, L.IN_Z1 - 1), (x1 - 2, L.COUNTER_TOP0, L.IN_Z1), "wood")
    for k, (a, b) in enumerate(((x0, x0 + 3), (x1 - 3, x1))):
        mon = sc.model(m, "Monitor%d" % (k + 1))
        sc.box(mon, "Body", (a, L.WORK, z0 + 1.4), (b, L.WORK + 2.4, z0 + 3.4), "cream_dark")
        sc.box(mon, "Back", (a + 0.5 - 0.0, L.WORK + 0.4, z0 + 3.0), (b - 0.5, L.WORK + 2.0, z0 + 4.0), "cream_dark")
        sc.part(mon, "Screen", (2.4, 1.8, 0.2), CF(((a + b) / 2, L.WORK + 1.3, z0 + 1.3)), "screen",
                material="SmoothPlastic", surfaces="smooth", grid=False)
        knobs = G.Geo().add([G.cyl(0.1, 0.1, 6, "z", (0.9, 0, 0)), G.cyl(0.1, 0.1, 6, "z", (1.2, 0, 0))])
        sc.mesh(mon, "Knobs", "CCTVDesk__Knobs", knobs, CF(((a + b) / 2 - 0.0, L.WORK + 0.2, z0 + 1.35)), "black",
                owner="CCTVDesk")
    sb = sc.model(m, "SwitchBox")
    sc.box(sb, "Box", (x0 + 2, L.WORK, z0 + 0.4), (x0 + 4, L.WORK + 0.4, z0 + 1.4), "grey_dark")
    btns = G.Geo()
    for k in range(4):
        btns.add(G.box(0.3, 0.12, 0.3, (-0.6 + 0.4 * k, 0.06, 0)))
    sc.mesh(sb, "Buttons", "CCTVDesk__Buttons", btns, CF((x0 + 3, L.WORK + 0.4, z0 + 0.95)), "red", owner="CCTVDesk")
    sc.box(sb, "Lamp", (x0 + 2.2, L.WORK + 0.4, z0 + 0.5), (x0 + 2.6, L.WORK + 0.6, z0 + 0.7), (120, 255, 120),
           material="Neon", grid=False, collide=False)
    # wall phone above the desk, handset hanging on its side
    ph = sc.model(m, "Phone")
    px = (x0 + x1) / 2
    base = sc.box(ph, "Base", (px - 0.5, 6.6, L.IN_Z1 - 1), (px + 0.5, 8.2, L.IN_Z1), "red")
    dial = G.Geo().add([G.cyl(0.36, 0.06, 12, "z", (0, 0, 0))])
    for k in range(8):
        a = math.tau * k / 10 + 0.5
        dial.add(G.cyl(0.05, 0.04, 6, "z", (0.24 * math.cos(a), 0.24 * math.sin(a), -0.05)))
    sc.mesh(ph, "Dial", "Phone__Dial", dial, CF((px, 7.2, L.IN_Z1 - 1.03)), "white", owner="Phone")
    hs = G.Geo()
    hs.add(G.box(0.22, 1.1, 0.24, (0, 0, 0)))
    for sy in (-1, 1):
        hs.add(G.box(0.3, 0.36, 0.42, (0, sy * 0.62, -0.1)))
    hsp = sc.mesh(ph, "Handset", "Phone__Handset", hs, CF((px + 0.66, 7.5, L.IN_Z1 - 0.55)), "red", owner="Phone",
                  collide=False)
    pivot(hsp, hsp.p["cf"])
    moving(ph, "Handset", "free part: lift it off the hook (move it where you like); pivot at its centre")
    cord = G.tube([(px + 0.5, 6.7, L.IN_Z1 - 0.5), (px + 0.55, 6.1, L.IN_Z1 - 0.45), (px + 0.68, 5.9, L.IN_Z1 - 0.5),
                   (px + 0.75, 6.2, L.IN_Z1 - 0.5), (px + 0.68, 6.9, L.IN_Z1 - 0.55)], 0.05, 5)
    sc.mesh(ph, "Cord", "Phone__Cord", cord, CF(), "black", owner="Phone")
    stand(sc, m, (x0 + x1) / 2, L.S_FRONT - L.STAND_GAP, S_)
    return m


def sink(sc):
    m = station(sc, "Sink")
    x0, x1 = L.SINK
    z0, z1 = L.S_FRONT, L.IN_Z1
    hx0, hx1, hz0, hz1 = x0 + 1, x1 - 1, z0 + 1, z1 - 1
    sc.box(m, "Cabinet", (x0, L.CAB_Y0, z0 + 0.6), (x1, 2.2, z1 + 0.6), "red")
    sc.box(m, "Apron", (x0, 2.2, z0), (x1, L.COUNTER_TOP0, hz0), "steel")
    sc.box(m, "Back", (x0, 2.2, hz1), (x1, L.COUNTER_TOP0, z1), "steel")
    sc.box(m, "Side", (x0, 2.2, hz0), (hx0, L.COUNTER_TOP0, hz1), "steel")
    sc.box(m, "Side", (hx1, 2.2, hz0), (x1, L.COUNTER_TOP0, hz1), "steel")
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, z0), (x1, L.WORK, hz0), "steel")
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, hz1), (x1, L.WORK, z1), "steel")
    sc.box(m, "Top", (x0, L.COUNTER_TOP0, hz0), (hx0, L.WORK, hz1), "steel")
    sc.box(m, "Top", (hx1, L.COUNTER_TOP0, hz0), (x1, L.WORK, hz1), "steel")
    sc.box(m, "Basin", (hx0, 2.2, hz0), (hx1, 2.6, hz1), "steel_dark")
    sc.cylinder(m, "Drain", 0.4, 1, ((hx0 + hx1) / 2, 2.8, (hz0 + hz1) / 2), (0, 1, 0), "black")
    tap = G.tube([(0, 0, 0), (0, 0.9, 0), (0, 1.25, -0.25), (0, 1.1, -0.65), (0, 0.85, -0.7)], 0.09, 6)
    tap.add(G.cyl(0.2, 0.15, 8, "y", (0, 0.07, 0)))
    for sx in (-1, 1):
        tap.add(G.box(0.36, 0.12, 0.12, (sx * 0.35, 0.35, 0.05)))
    mesh(sc, m, "Faucet", tap, "steel", frame=CF(((hx0 + hx1) / 2, L.WORK, z1 - 0.45)), material="Metal")
    stand(sc, m, (x0 + x1) / 2, L.S_FRONT - L.STAND_GAP, S_)
    return m


def extinguisher(sc):
    """The FireExtinguisher is stock the players take: the station is its wall bracket in
    the corner over the sink, with a cradle it stands on and a Slot where it goes. The game
    stands the item on Slot (Slot faces into the room, so it hangs as it always did)."""
    m = station(sc, "Extinguisher")
    zc = L.S_FRONT + 1.6
    br = G.Geo().add([G.box(0.15, 0.4, 0.9, (0.07, 0, 0)), G.box(0.5, 0.1, 0.9, (0.3, -0.15, 0))])
    mesh(sc, m, "Bracket", br, "black", frame=CF((L.IN_X0, 6.8, zc)))
    sc.box(m, "Cradle", (L.IN_X0, 4.3, zc - 0.5), (L.IN_X0 + 1, 4.7, zc + 0.5), "black")
    fe = I.get("FireExtinguisher")
    held = CF((L.IN_X0 + 0.55, 6.75, zc), facing(E))          # where the item hangs (its Handle)
    slot = held * fe.rest()
    sc.marker(m, "Slot", CF((slot.p[0], 4.7, slot.p[2]), slot.R))
    st = np.array((-14.4, L.FLOOR, L.S_FRONT - L.STAND_GAP))
    d = np.array((slot.p[0], L.FLOOR, zc)) - st
    sc.marker(m, "Stand", CF(st, facing(d / np.linalg.norm(d))))
    return m


# ---------------------------------------------------------------- west wall

def storage_shelf(sc):
    m = station(sc, "StorageShelf")
    z0, z1 = L.STORAGE
    x0, x1 = L.IN_X0, L.IN_X0 + 2
    sc.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "wood_dark")
    mk.panel_z(sc, m, "Side", z0 + 0.2, x0, x1, 1.2 - 0.0, 9.2 - 0.0, "wood", surfaces="smooth")
    mk.panel_z(sc, m, "Side", z1 - 0.2, x0, x1, 1.2, 9.2, "wood", surfaces="smooth")
    for y in (4.0, 6.8, 9.2):
        sc.box(m, "Shelf", (x0, y - 0.4, z0), (x1, y, z1), "wood")
    # Slot1/2 (flour, sauce cans) on the middle shelf, Slot3/4 (flashlights) at the bottom, Slot5/6 top
    k = 1
    for y in (4.0, 1.2, 6.8):
        for z in (z1 - 1.0, z0 + 1.0):
            spot(sc, m, "Slot%d" % k, x0 + 1.0, y, z, W)
            k += 1
    stand(sc, m, x1 + L.STAND_GAP + 0.4, (z0 + z1) / 2, W)
    return m


def drinks_cooler(sc):
    m = station(sc, "DrinksCooler")
    z0, z1 = L.COOLER
    x0, x1 = L.IN_X0, L.IN_X0 + 3
    sc.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "black")
    mk.panel_z(sc, m, "Side", z0 + 0.2, x0, x1, 1.2, 8.2, "red")
    mk.panel_z(sc, m, "Side", z1 - 0.2, x0, x1, 1.2, 8.2, "red")
    sc.box(m, "Back", (x0, 1.2, z0 + 0.5), (x0 + 1, 7.6, z1 - 0.5), "white")
    sc.box(m, "Header", (x0, 7.6, z0), (x1, 8.8, z1), "red")
    sc.box(m, "Band", (x1, 7.8, z0 + 0.5), (x1 + 0.4, 8.6, z1 - 0.5), "white", grid=False)
    lt = sc.box(m, "Light", (x0 + 1, 7.2, z0 + 0.5), (x1, 7.6, z1 - 0.5), "bulb_cool", material="Neon", collide=False)
    sc.light(lt, "SurfaceLight", "Light", "bulb_cool", brightness=1.0, range_=6, shadows=False, angle=80, face="Bottom")
    for y in (6.0, 4.4, 2.8):
        sc.box(m, "Shelf", (x0 + 1, y - 0.4, z0 + 0.5), (x1, y, z1 - 0.5), "steel")
    k = 1
    for y in (6.0, 4.4, 2.8, 1.2):
        for z in (z1 - 1.0, (z0 + z1) / 2, z0 + 1.0):
            spot(sc, m, "Slot%d" % k, x0 + 2.0, y, z, W)
            k += 1
    door = mk.panel_x(sc, m, "Door", x1 + 0.2, 1.2, 7.2, z0, z1, "glass", material="Glass", transparency=0.55)
    frame = [sc.box(m, "DoorFrame", (x1 + 0.4, 1.2, z0), (x1 + 1.4, 1.6, z1), "red", grid=False),
             sc.box(m, "DoorFrame", (x1 + 0.4, 6.8, z0), (x1 + 1.4, 7.2, z1), "red", grid=False)]
    hdl = G.Geo().add([G.box(0.12, 2.0, 0.14, (0.25, 0, 0)), G.box(0.25, 0.12, 0.12, (0.12, 0.9, 0)),
                       G.box(0.25, 0.12, 0.12, (0.12, -0.9, 0))])
    frame.append(mesh(sc, m, "DoorHandle", hdl, "steel", frame=CF((x1 + 0.4, 4.2, z1 - 0.4)), material="Metal"))
    weld_all(sc, door, frame)
    pivot(door, CF((x1 + 0.4, 4.2, z0)))
    moving(m, "Door", "glass door hinged on its north edge; rotate the pivot +90 deg about Y to swing it open into "
                      "the room. Frame strips and handle are welded to it")
    stand(sc, m, x1 + L.STAND_GAP + 0.6, (z0 + z1) / 2, W)
    return m


def fuse_box(sc):
    m = station(sc, "FuseBox")
    z = L.FUSE_Z
    x0 = L.IN_X0
    sc.box(m, "Box", (x0, 4.6, z - 1), (x0 + 1, 6.6, z + 1), "grey")
    sc.box(m, "Sticker", (x0 + 1, 6.0, z - 0.6), (x0 + 1.2, 6.4, z + 0.4), "mustard", grid=False)
    sc.cylinder(m, "Hub", 0.4, 1, (x0 + 1.2, 5.4, z + 0.5), (1, 0, 0), "black")
    lev = G.Geo().add([G.box(0.16, 1.2, 0.16, (0, 0.6, 0)), G.sphere(0.2, 8, 4, c=(0, 1.25, 0))])
    lv = mesh(sc, m, "Lever", lev, "red", frame=CF((x0 + 1.5, 5.4, z + 0.5)), collide=True)
    pivot(lv, CF((x0 + 1.5, 5.4, z + 0.5)))
    moving(m, "Lever", "pointing up = ON. Rotate the pivot about X (the wall's normal): +120 deg swings it down = OFF")
    stand(sc, m, x0 + 1 + L.STAND_GAP + 0.6, z, W)
    return m


# ---------------------------------------------------------------- ceiling

def ceiling_lamp(sc, name, x, z):
    m = station(sc, name)
    top = L.CEIL
    cord = G.cyl(0.06, 1.5, 6, "y", (0, -0.75, 0))
    cord.add(G.cyl(0.3, 0.12, 8, "y", (0, -0.06, 0)))
    c = mesh(sc, m, "Cord", cord, "black", owner="CeilingLamp", frame=CF((x, top, z)), collide=False)
    shade = G.lathe_loop([(0.12, 0.0), (0.95, -0.7), (0.9, -0.75), (0.08, -0.06)], 12)
    s = mesh(sc, m, "Shade", shade, "green", owner="CeilingLamp", frame=CF((x, top - 1.5, z)))
    b = sc.ball(m, "Bulb", 1.0, (x, top - 2.0, z), "bulb", material="Neon", collide=False, shadow=False)
    sc.light(b, "PointLight", "Light", "bulb", brightness=1.4, range_=20, shadows=True)
    for p in (s, b):
        p.p["anchored"] = False
        p.p["massless"] = True
        sc.weld(c, p, "Weld")
    pivot(c, CF((x, top, z)))
    moving(m, "Cord", "optional sway: the Cord is the anchored root (pivot on the ceiling hook); Shade and Bulb are "
                      "welded to it, so tilting the pivot a few degrees swings the whole lamp")
    stand(sc, m, x, z + 1.5, N)
    return m


def hatch(sc):
    from map_shell import HATCH
    m = station(sc, "Hatch")
    hx0, hx1, hz0, hz1 = HATCH
    door = sc.box(m, "Door", (hx0, L.CEIL, hz0), (hx1, L.CEIL_TOP, hz1), "wood_light", collide=True)
    ring = G.Geo().add([G.torus(0.22, 0.05, 10, 4, "z", (0, -0.3, 0)), G.box(0.1, 0.12, 0.1, (0, -0.04, 0))])
    rp = mesh(sc, m, "PullRing", ring, "steel", frame=CF(((hx0 + hx1) / 2, L.CEIL, hz1 - 0.6)), material="Metal")
    weld_all(sc, door, [rp])
    pivot(door, CF(((hx0 + hx1) / 2, L.CEIL, hz0)))
    moving(m, "Door", "hinged along its north edge; rotate the pivot +90 deg about X and it swings down into the "
                      "room (a dark attic is above it)")
    for (a, b, c, d) in ((hx0 - 1, hx1 + 1, hz0 - 1, hz0), (hx0 - 1, hx1 + 1, hz1, hz1 + 1),
                         (hx0 - 1, hx0, hz0, hz1), (hx1, hx1 + 1, hz0, hz1)):
        sc.box(m, "Frame", (a, L.CEIL - 0.4, c), (b, L.CEIL, d), "wood_dark")
    stand(sc, m, (hx0 + hx1) / 2, hz1 + 1.6, N)
    return m


def build_inside(sc):
    sc.folder(sc.root, "Stations")
    for f in (back_door, fridge, dough_station, sauce_station, chop_station, topping_rail, oven, peel_rack,
              cut_table, kitchen_bin, box_station, register, rules_board, plushie_shelf, serving_window,
              shutter_button, cctv_desk, sink, extinguisher, storage_shelf, drinks_cooler, fuse_box, hatch):
        f(sc)
    ceiling_lamp(sc, "CeilingLamp1", -6.0, 0.5)
    ceiling_lamp(sc, "CeilingLamp2", 6.5, 2.5)
