"""Batch 2, section C: InspectorCar, DeliveryTruck, Van.

Vehicle space: the ground is y = 0, the middle of the vehicle is x = z = 0, the front points
along -Z. PrimaryPart `Base` lies on the ground under the middle; its pivot is on the
ground, so `vehicle:PivotTo(marker.CFrame)` stands the wheels on the marker's surface.
Every Part is anchored (the vehicles are moved with PivotTo); small things that move with a
moving piece (hub caps, door handles) are welded to it. Boxy parts are studded bricks on
the brick grid; thin upright panels are 0.4 plates turned on their side; curved and thin
details are meshes.
"""
import math

import numpy as np

import mk
import spsgeo as G
from assets_common import moving, pivot
from spsgeo import CF, T, RX, RY, RZ, S

VC = {
    "car_black": (22, 22, 25), "glass_dark": (16, 18, 22), "chrome": (200, 202, 208), "tyre": (28, 28, 30),
    "whitewall": (232, 230, 222), "head": (255, 244, 212), "tail": (196, 26, 26), "beacon": (180, 22, 22),
    "cream": (240, 228, 196), "red": (196, 40, 32), "dark": (44, 44, 48), "hub": (160, 162, 168),
    "glass": (160, 196, 214), "seat": (58, 58, 64), "wood": (160, 104, 62), "wood_dark": (112, 70, 42),
    "cardboard": (196, 160, 112), "steel": (120, 124, 130), "sign": (30, 30, 34), "amber": (255, 170, 40),
}


def c(k):
    return VC[k] if isinstance(k, str) else k


class VB:
    """Adds parts to a vehicle Model in vehicle space (origin = a translation)."""

    def __init__(self, sc, m, origin, owner):
        assert np.allclose(origin.R, np.eye(3)), "vehicles are built facing -Z"
        self.sc, self.m, self.o, self.owner = sc, m, np.asarray(origin.p, float), owner

    def box(self, name, lo, hi, col, **kw):
        return self.sc.box(self.m, name, self.o + lo, self.o + hi, c(col), **kw)

    def wedge(self, name, size, center, R, col, **kw):
        return self.sc.wedge(self.m, name, size, self.o + center, R, c(col), **kw)

    def panel_x(self, name, x_mid, y0, y1, z0, z1, col, **kw):
        return mk.panel_x(self.sc, self.m, name, x_mid + self.o[0], y0 + self.o[1], y1 + self.o[1], z0 + self.o[2],
                          z1 + self.o[2], c(col), **kw)

    def panel_z(self, name, z_mid, x0, x1, y0, y1, col, **kw):
        return mk.panel_z(self.sc, self.m, name, z_mid + self.o[2], x0 + self.o[0], x1 + self.o[0], y0 + self.o[1],
                          y1 + self.o[1], c(col), **kw)

    def part(self, name, size, center, col, R=None, **kw):
        kw.setdefault("grid", False)
        return self.sc.part(self.m, name, size, CF(self.o + center, R), c(col), **kw)

    def mesh(self, pname, geo, col, frame=CF(), mesh_name=None, **kw):
        kw.setdefault("collide", False)
        return self.sc.mesh(self.m, pname, mesh_name or self.owner + "__" + pname, geo, CF(self.o) * frame, c(col),
                            owner=self.owner, **kw)

    def weld_to(self, root, parts):
        for p in parts:
            p.p["anchored"] = False
            p.p["massless"] = True
            self.sc.weld(root, p, "Weld")

    def cf(self, p=(0, 0, 0), R=None):
        return CF(self.o + p, R)


def base(v, length):
    b = v.part("Base", (4, 0.4, min(8, length)), (0, 0.2, 0), (255, 255, 255), material="SmoothPlastic",
               transparency=1.0, collide=False, touch=False, query=False, shadow=False, surfaces="smooth")
    pivot(b, v.cf((0, 0, 0)))
    v.m.p["primary"] = b
    return b


def wheel(v, center, r, w, hub_mesh, hub_col="chrome", extra=None):
    """Cylinder Wheel (axis along X, pivot on the axle) with a hub mesh welded to it."""
    wpart = v.part("Wheel", (w, 2 * r, 2 * r), center, "tyre", shape="Cylinder", material="Plastic",
                   surfaces="smooth")
    welded = [v.mesh("Hub", None, hub_col, CF(center), mesh_name=hub_mesh, material="Metal")]
    if extra:
        welded.append(v.mesh(extra[0], None, extra[1], CF(center), mesh_name=extra[2]))
    v.weld_to(wpart, welded)
    return wpart


def hub_geo(r, w, lugs=5, cap=0.55):
    g = G.cyl(r * cap, w + 0.06, 12, "x")
    for k in range(lugs):
        a = math.tau * k / lugs
        for sx in (-1, 1):
            g.add(G.cyl(0.07, 0.06, 6, "x", (sx * (w / 2 + 0.05), r * cap * 0.55 * math.sin(a),
                                              r * cap * 0.55 * math.cos(a))))
    return g


def headlight(v, center, size, R=None, face="Front", round_=False):
    if round_:
        p = v.part("Headlight", (0.2, size, size), center, "head", R=G.ry(90), shape="Cylinder", material="Neon",
                   collide=False, surfaces="smooth")
        face = "Right"
    else:
        p = v.part("Headlight", size, center, "head", R=R, material="Neon", collide=False, surfaces="smooth")
    v.sc.light(p, "SpotLight", "Light", (255, 238, 200), brightness=2.0, range_=40, shadows=True, angle=70,
               face=face)
    return p


def taillight(v, center, size):
    return v.part("TailLight", size, center, "tail", material="Neon", collide=False, surfaces="smooth")


# ---------------------------------------------------------------- the Inspector's car

DOOR_Z = (-2.6, 0.6)            # the driver's door, between the door lines (the driver sits on the left, -X)
DOOR_OPEN = -70.0


def driver_door(sc, v, m, K):
    """The driver's door, an openable Model (the shack's Opens contract): the panel from the
    sill to the waist with its piece of chrome strip and its handle, hinged on its front edge
    and swinging out to the left. Papa_CarDoor (on the map) is where he stands once out."""
    d = sc.model(m, "DriverDoor")
    sc.attr(d, "Opens", "Swing")
    sc.attr(d, "OpenAngle", DOOR_OPEN)
    sc.attr(d, "OpenSound", "Metal")
    dv = VB(sc, d, CF(v.o), v.owner)
    z0, z1 = DOOR_Z
    panel = dv.part("Panel", (1, 2.8, z1 - z0 - 0.06), (-3.5, 2.2, (z0 + z1) / 2), K)
    t = G.Geo()
    t.add(G.box(0.06, 0.14, z1 - z0 - 0.1, (-4.03, 2.95, (z0 + z1) / 2)))
    t.add(G.box(0.06, 0.06, 0.5, (-4.03, 3.25, z1 - 0.6)))
    dv.mesh("DoorTrim", t, "chrome", material="Metal")
    pivot(panel, v.cf((-4.0, 0.8, z0)))
    d.p["primary"] = panel
    moving(m.name, "DriverDoor", "an openable Model: Opens Swing, OpenAngle %g about its pivot's Y (the hinge on "
                                 "the door's front edge); open = DriverDoor:PivotTo(closed * CFrame.Angles(0, "
                                 "math.rad(OpenAngle), 0))" % DOOR_OPEN)
    return d


def inspector_car(sc, parent, origin=CF(), name="InspectorCar"):
    """A long black 1960s saloon: 8 wide, 19 long (bumper to bumper), 6.5 tall to the beacon."""
    m = sc.model(parent, name)
    v = VB(sc, m, origin, "InspectorCar")
    base(v, 19)
    K = "car_black"
    v.box("Body", (-3, 0.8, -8.5), (3, 2.8, 8.5), K)
    for sx in (-1, 1):
        x0, x1 = (3, 4) if sx > 0 else (-4, -3)
        if sx > 0:
            v.box("Sill", (x0, 0.8, -4), (x1, 2.8, 4), K)
        else:                                           # the driver's door fills the gap between
            v.part("Sill", (1, 2.0, DOOR_Z[0] + 4), (-3.5, 1.8, (DOOR_Z[0] - 4) / 2), K)
            v.part("Sill", (1, 2.0, 4 - DOOR_Z[1]), (-3.5, 1.8, (DOOR_Z[1] + 4) / 2), K)
        v.box("Corner", (x0, 0.8, -8.5), (x1, 2.8, -7.5), K)
        v.box("Corner", (x0, 0.8, 7.5), (x1, 2.8, 8.5), K)
        v.wedge("Fin", (1, 0.8, 3), (sx * 3.5, 4.0, 7.0), None, K)
    v.box("Deck", (-3, 2.8, -8.5), (4, 3.6, 8.5), K)
    v.part("Deck", (1, 0.8, DOOR_Z[0] + 8.5), (-3.5, 3.2, (DOOR_Z[0] - 8.5) / 2), K)
    v.part("Deck", (1, 0.8, 8.5 - DOOR_Z[1]), (-3.5, 3.2, (DOOR_Z[1] + 8.5) / 2), K)
    driver_door(sc, v, m, K)
    v.box("Cabin", (-3, 3.6, -3), (3, 5.6, 3), "glass_dark", material="SmoothPlastic")
    v.wedge("Windscreen", (6, 2.0, 1), (0, 4.6, -3.5), None, "glass_dark", material="SmoothPlastic")
    v.wedge("RearWindow", (6, 2.0, 1), (0, 4.6, 3.5), G.ry(180), "glass_dark", material="SmoothPlastic")
    v.box("Roof", (-3, 5.6, -3.5), (3, 6.0, 3.5), K)
    for z0, z1 in ((-9.5, -8.5), (8.5, 9.5)):
        v.box("Bumper", (-4, 1.2, z0), (4, 2.0, z1), "chrome", material="Metal")
    # pillars (body colour) and chrome details
    pil = G.Geo()
    for sx in (-1, 1):
        pil.add(G.box(0.14, 2.0, 0.5, (sx * 3.07, 4.6, 0.0)))
        for zz, sgn in ((-3.0, -1), (3.0, 1)):
            a = G.box(0.14, 2.24, 0.3, (0, 0, 0)).xf(RX(-sgn * 26.6))
            pil.add(a.xf(T(sx * 3.07, 4.6, zz + sgn * 0.5)))
    v.mesh("Pillars", pil, K)
    trim = G.Geo()
    trim.add(G.box(0.06, 0.14, 16.6, (4.03, 2.95, 0)))
    trim.add(G.box(0.06, 0.06, 0.5, (4.03, 3.25, -1.2)))               # door handles
    trim.add(G.box(0.06, 0.06, 0.5, (4.03, 3.25, 1.8)))
    for (za, zb) in ((-8.3, DOOR_Z[0]), (DOOR_Z[1], 8.3)):              # the driver's side, less the door
        trim.add(G.box(0.06, 0.14, zb - za - 0.04, (-4.03, 2.95, (za + zb) / 2)))
    trim.add(G.box(0.06, 0.06, 0.5, (-4.03, 3.25, 1.8)))
    grille = G.Geo().add([G.box(4.8, 0.08, 0.1, (0, 2.0 + 0.16 * k, -8.55)) for k in range(5)])
    grille.add(G.box(0.1, 0.8, 0.1, (-2.4, 2.32, -8.55)))
    grille.add(G.box(0.1, 0.8, 0.1, (2.4, 2.32, -8.55)))
    grille.add(G.box(0.1, 0.8, 0.1, (0.0, 2.32, -8.55)))
    v.mesh("Trim", trim, "chrome", material="Metal")
    v.mesh("Grille", grille, "chrome", material="Metal")
    lines = G.Geo()
    for sx in (-1, 1):
        for zz in (-2.6, 0.6):
            lines.add(G.box(0.04, 1.9, 0.06, (sx * 4.02, 1.85, zz)))
    v.mesh("DoorLines", lines, (10, 10, 12))
    for sx in (-1, 1):
        headlight(v, (sx * 3.2, 2.4, -8.6), 0.8, round_=True)
        taillight(v, (sx * 3.4, 3.2, 8.6), (1.0, 0.6, 0.2))
    bc = v.part("Beacon", (0.5, 0.7, 0.7), (0, 6.25, 0.5), "beacon", R=G.rz(90), shape="Cylinder", material="Neon",
                collide=False, surfaces="smooth")
    sc.light(bc, "PointLight", "Light", (255, 40, 30), brightness=2.0, range_=16, shadows=False)
    rimg = G.cyl(0.5, 0.08, 10, "y", (0, 6.04, 0.5))
    v.mesh("BeaconBase", rimg, "chrome", material="Metal")
    hub = "InspectorCar__Hub"
    sc.geom(hub, hub_geo(1.4, 1.0), owner="InspectorCar")
    ww = "InspectorCar__Whitewall"
    sc.geom(ww, G.ring(1.12, 0.78, 1.04, 16, "x"), owner="InspectorCar")
    for zz in (-5.5, 5.5):
        for sx in (-1, 1):
            wheel(v, (sx * 3.5, 1.4, zz), 1.4, 1.0, hub, extra=("Whitewall", "whitewall", ww))
    moving(name, "Wheel x4", "cylinders on their axles: spin each about its own X axis "
                            "(wheel.CFrame = wheel.CFrame * CFrame.Angles(a, 0, 0)); Hub and Whitewall are welded on")
    return m


# ---------------------------------------------------------------- the depot's box truck

def delivery_truck(sc, parent, origin=CF(), name="DeliveryTruck"):
    """Cream cab and box with a red stripe: 9 wide, 24 long, 11.6 tall."""
    m = sc.model(parent, name)
    v = VB(sc, m, origin, "DeliveryTruck")
    base(v, 24)
    CR = "cream"
    v.box("Bumper", (-4.5, 1.2, -12), (4.5, 2.0, -11), "dark")
    v.box("Nose", (-2.5, 1.2, -11), (2.5, 4.4, -8), CR)
    for sx in (-1, 1):
        x0, x1 = (2.5, 4.5) if sx > 0 else (-4.5, -2.5)
        v.box("NoseSide", (x0, 1.2, -11), (x1, 4.4, -9), CR)
        v.box("Fender", (x0, 3.2, -9), (x1, 4.4, -5), CR)
        v.box("Step", (x0, 1.6, -5), (x1, 2.8, -4), "dark")
    v.box("Hood", (-4.5, 4.4, -11), (4.5, 4.8, -9), CR)
    v.wedge("Windscreen", (9, 3.6, 1), (0, 6.6, -9.5), None, (60, 74, 86), material="SmoothPlastic")
    v.box("Cab", (-4.5, 4.4, -9), (4.5, 8.4, -4), CR)
    v.box("CabFloor", (-2.5, 1.2, -8), (2.5, 4.4, -4), "dark")
    v.box("CabRoof", (-4.5, 8.4, -10), (4.5, 8.8, -4), CR)
    v.box("Chassis", (-2, 1.2, -4), (2, 2.8, 11), "dark")
    v.box("BoxFloor", (-4.5, 2.8, -4), (4.5, 3.2, 11), "dark")
    v.panel_z("BoxFront", -3.8, -4.5, 4.5, 3.2, 11.2, CR)
    for sx in (-1, 1):
        v.panel_x("BoxSide", sx * 4.3, 3.2, 11.2, -4, 11, CR)
    v.box("BoxRoof", (-4.5, 11.2, -4), (4.5, 11.6, 11), CR)
    v.panel_z("Header", 11.2, -4.5, 4.5, 10.2, 11.2, CR)
    v.box("RearBumper", (-4.5, 1.6, 11), (4.5, 2.4, 12), "dark")
    # the roll-up door: one ribbed mesh so it can be squashed upwards
    door = G.Geo()
    for k in range(10):
        y0 = 3.2 + 0.7 * k
        door.add(G.box(8.2, 0.6, 0.16, (0, y0 + 0.35, 10.88)))
        door.add(G.box(8.1, 0.1, 0.1, (0, y0 + 0.02, 10.9)))
    door.add(G.box(1.2, 0.18, 0.12, (0, 3.9, 10.76)))
    rd = v.mesh("RearDoor", door, (236, 232, 222), collide=True)
    pivot(rd, v.cf((0, 10.2, 10.88)))
    moving(name, "RearDoor", "roll-up door, pivot on its top edge. It slides up 7.0 to open, but straight up it "
                             "would come out through the roof, so roll it: tween Size.Y from 7.0 down to 0.6 and "
                             "keep the top edge (the pivot) where it is; it is one ribbed mesh, so the ribs squash "
                             "like a door rolling up")
    sc.attr(rd, "OpenTravel", 7.0)
    # stripe, sign boards, windows, details
    stripe = G.Geo()
    for sx in (-1, 1):
        stripe.add(G.box(0.06, 0.8, 15.0, (sx * 4.53, 4.6, 3.5)))
        stripe.add(G.box(0.06, 0.8, 5.0, (sx * 4.53, 5.6, -6.5)))
    stripe.add(G.box(8.96, 0.8, 0.06, (0, 5.6, -9.03)))
    v.mesh("Stripe", stripe, "red")
    for nm, sx in (("SideL", -1), ("SideR", 1)):
        v.part(nm, (13, 3.2, 0.2), (sx * 4.6, 7.8, 3.5), (250, 246, 234), R=G.facing((sx, 0, 0)),
               material="SmoothPlastic", surfaces="smooth")
    win = G.Geo()
    for sx in (-1, 1):
        win.add(G.box(0.06, 1.8, 3.0, (sx * 4.53, 7.0, -6.7)))
    v.mesh("Windows", win, (60, 74, 86), material="SmoothPlastic")
    grille = G.Geo().add([G.box(4.2, 0.12, 0.1, (0, 2.3 + 0.3 * k, -11.05)) for k in range(6)])
    v.mesh("Grille", grille, "chrome", material="Metal")
    mir = G.Geo()
    for sx in (-1, 1):
        mir.add(G.box(0.7, 0.08, 0.08, (sx * 4.85, 7.6, -8.6)))
        mir.add(G.box(0.18, 1.2, 0.5, (sx * 5.25, 7.3, -8.6)))
    v.mesh("Mirrors", mir, "dark")
    for sx in (-1, 1):
        headlight(v, (sx * 3.5, 3.4, -11.1), (1.2, 0.8, 0.2))
        taillight(v, (sx * 3.6, 2.0, 12.1), (1.2, 0.6, 0.2))
    hub = "DeliveryTruck__Hub"
    sc.geom(hub, hub_geo(1.6, 1.2, 6), owner="DeliveryTruck")
    for sx in (-1, 1):
        wheel(v, (sx * 3.9, 1.6, -7.2), 1.6, 1.2, hub, "hub")
        wheel(v, (sx * 3.9, 1.6, 7.0), 1.6, 1.2, hub, "hub")
        wheel(v, (sx * 2.7, 1.6, 7.0), 1.6, 1.2, hub, "hub")
    moving(name, "Wheel x6", "cylinders on their axles (twin wheels at the back): spin about their own X axis")
    return m


# ---------------------------------------------------------------- the crew van (lobby party room)

VAN_IN = dict(x0=-3.8, x1=3.8, y0=1.6, y1=9.8, z0=-2.0, z1=9.0)     # the cargo box inside


def van(sc, parent, origin=CF(), name="Van"):
    """8.4 wide, 19 long (plus bumpers and the ramp), 10.2 to the roof, 10.6 at the sign header."""
    m = sc.model(parent, name)
    v = VB(sc, m, origin, "Van")
    base(v, 19)
    CR, RD = "cream", "red"
    # -- cargo box: floor (round the rear wheels), walls (round the arches), bulkhead, roof, housings
    v.box("Floor", (-3, 0.4, -2), (3, 1.6, 10), "wood")
    for sx in (-1, 1):
        x0, x1 = (3, 4) if sx > 0 else (-4, -3)
        v.box("Floor", (x0, 0.4, -2), (x1, 1.6, 5), "wood")
        v.box("Floor", (x0, 0.4, 8), (x1, 1.6, 10), "wood")
        v.panel_x("Wall", sx * 4.0, 0.8, 9.8, -3, 4, CR)
        v.panel_x("Wall", sx * 4.0, 2.8, 9.8, 4, 9, CR)
        x0, x1 = (2.8, 3.8) if sx > 0 else (-3.8, -2.8)
        v.box("WheelHousing", (x0, 1.6, 4), (x1, 3.2, 9), "dark")
    v.box("Bulkhead", (-4, 0.6, -3), (4, 9.8, -2), CR, surfaces="smooth")
    v.box("Roof", (-4, 9.8, -2), (4, 10.2, 9), RD)
    v.panel_z("Header", 9.2, -4, 4, 7.6, 10.6, CR)
    # -- back doors, shut; pivots on the outer hinges
    for nm, x0, x1, hx, ang in (("DoorL", -4.2, -0.2, -4.2, -135), ("DoorR", 0.2, 4.2, 4.2, 135)):
        d = v.panel_z(nm, 9.2, x0, x1, 1.6, 7.6, CR, collide=True)
        welded = []
        hd = G.Geo().add([G.box(0.16, 0.9, 0.12, (0, 0, 0)), G.box(0.16, 0.12, 0.2, (0, 0.39, -0.06)),
                          G.box(0.16, 0.12, 0.2, (0, -0.39, -0.06))])
        welded.append(v.mesh("DoorHandle", hd, "chrome", CF(((x0 + x1) / 2 + (1.4 if hx < 0 else -1.4), 4.4, 9.48)),
                             mesh_name="Van__DoorHandle", material="Metal"))
        stripe = G.box(4.0, 0.8, 0.06, (0, 0, 0))
        welded.append(v.mesh("Stripe", stripe, RD, CF(((x0 + x1) / 2, 3.4, 9.43)), mesh_name="Van__DoorStripe"))
        if nm == "DoorR":
            welded.append(v.mesh("Seam", G.box(0.5, 6.0, 0.06, (0, 0, 0)), CR, CF((0.0, 4.6, 9.43)),
                                 mesh_name="Van__DoorSeam"))
        v.weld_to(d, welded)
        pivot(d, v.cf((hx, 4.6, 9.4)))
        sc.attr(d, "OpenAngle", ang)
        moving(name, nm, "back door, modelled shut, pivot on its outer hinge (x %+.1f, back face); "
                         "rotate the pivot %+d deg about +Y (attribute OpenAngle) to swing it open "
                         "round the side; handle and stripe are welded to it" % (hx, ang))
    v.part("Gate", (7.6, 6.0, 0.4), (0, 4.6, 9.2), (255, 255, 255), material="SmoothPlastic", transparency=1.0,
           collide=False, touch=False, query=False, shadow=False, surfaces="smooth")
    v.part("Zone", (7.6, 8.2, 11.0), (0, 5.7, 3.5), (255, 255, 255), material="SmoothPlastic", transparency=1.0,
           collide=False, touch=True, query=False, shadow=False, surfaces="smooth")
    v.part("Sign", (8.4, 2.4, 0.2), (0, 9.2, 9.5), "sign", R=G.facing((0, 0, 1)), material="SmoothPlastic",
           surfaces="smooth")
    v.wedge("Ramp", (6, 1.6, 4), (0, 0.8, 12.0), G.ry(180), "steel", material="DiamondPlate")
    for sx in (-1, 1):
        taillight(v, (sx * 3.5, 1.0, 10.1), (0.8, 0.6, 0.2))
    # -- cab: nose, fenders, floor, windscreen, glass, roof, seats
    v.box("Bumper", (-4, 0.8, -10), (4, 1.6, -9), "dark")
    v.box("Nose", (-3, 0.8, -9), (3, 4.0, -6), CR)
    for sx in (-1, 1):
        x0, x1 = (3, 4) if sx > 0 else (-4, -3)
        v.box("NoseSide", (x0, 0.8, -9), (x1, 4.0, -8), CR)
        v.box("Fender", (x0, 2.8, -8), (x1, 4.0, -5), CR)
        v.box("Sill", (x0, 0.8, -5), (x1, 2.8, -3), CR)
        v.panel_x("CabDoor", sx * 3.8, 1.6, 3.6, -5, -3, CR)
        v.panel_x("RoofRail", sx * 3.8, 6.6, 7.6, -6, -3, CR)
    glass = G.Geo()
    for sx in (-1, 1):
        glass.add(G.box(0.1, 3.0, 3.0, (sx * 3.85, 5.1, -4.5)))
    v.mesh("CabWindows", glass, "glass", material="Glass", transparency=0.5)
    v.box("CabFloor", (-3, 0.8, -6), (3, 2.0, -3), "dark")
    v.wedge("Windscreen", (8, 3.6, 2), (0, 5.8, -7), None, "glass", material="Glass", transparency=0.5)
    v.box("CabRoof", (-4, 7.6, -7), (4, 8.0, -3), RD)
    seat = G.Geo().add([G.box(1.8, 0.6, 1.8, (0, 0.3, 0)), G.box(1.8, 2.2, 0.5, (0, 1.4, 0.75)).xf(RX(-8)),
                        G.box(1.2, 0.6, 0.4, (0, 2.8, 0.95))])
    for nm, sx in (("SeatL", -1), ("SeatR", 1)):
        v.mesh(nm, seat, "seat", CF((sx * 1.8, 2.0, -4.0)), mesh_name="Van__Seat")
    dash = G.Geo().add([G.box(7.2, 0.9, 1.0, (0, 0.45, 0)), G.box(7.2, 0.3, 0.6, (0, 0.95, 0.3))])
    v.mesh("Dashboard", dash, "dark", CF((0, 3.6, -6.4)))
    whl = G.torus(0.42, 0.06, 12, 4, "z").xf(RX(-30))
    whl.add(G.cyl(0.06, 0.9, 6, "z", (0, -0.2, 0.4)).xf(RX(-30)))
    v.mesh("SteeringWheel", whl, (30, 30, 34), CF((-1.8, 4.5, -5.6)))
    # -- outside details: stripe, sign boards, grille, mirrors
    stripe = G.Geo()
    for sx in (-1, 1):
        stripe.add(G.box(0.06, 0.8, 11.9, (sx * 4.23, 3.4, 3.05)))
        stripe.add(G.box(0.06, 0.8, 5.6, (sx * 4.03, 3.4, -6.2)))
    stripe.add(G.box(7.96, 0.8, 0.06, (0, 3.4, -9.03)))
    v.mesh("Stripe", stripe, RD)
    for nm, sx in (("SideL", -1), ("SideR", 1)):
        v.part(nm, (10, 2.4, 0.2), (sx * 4.3, 6.4, 3.0), (250, 246, 234), R=G.facing((sx, 0, 0)),
               material="SmoothPlastic", surfaces="smooth")
    grille = G.Geo().add([G.box(3.6, 0.12, 0.1, (0, 1.9 + 0.3 * k, -9.05)) for k in range(4)])
    v.mesh("Grille", grille, "chrome", material="Metal")
    mir = G.Geo()
    for sx in (-1, 1):
        mir.add(G.box(0.6, 0.08, 0.08, (sx * 4.3, 6.4, -5.8)))
        mir.add(G.box(0.16, 1.0, 0.45, (sx * 4.65, 6.2, -5.8)))
    v.mesh("Mirrors", mir, "dark")
    for sx in (-1, 1):
        headlight(v, (sx * 2.2, 3.2, -9.1), (1.2, 0.8, 0.2))
    # -- inside: lamp, crates and pizza boxes against the front wall
    lamp = sc.model(m, "VanLamp")
    lv = VB(sc, lamp, origin, "Van")
    lv.mesh("Housing", G.Geo().add([G.cyl(0.6, 0.12, 10, "y", (0, 0, 0)), G.cyl(0.08, 0.2, 6, "y", (0, 0.12, 0))]),
            "dark", CF((0, 9.74, 3.5)))
    bulb = lv.part("Bulb", (0.9, 0.9, 0.9), (0, 9.4, 3.5), (255, 230, 180), shape="Ball", material="Neon",
                   collide=False, shadow=False, surfaces="smooth")
    sc.light(bulb, "PointLight", "Light", (255, 214, 160), brightness=1.4, range_=16, shadows=True)
    v.box("Crate", (-3.8, 1.6, -2), (-1.8, 3.6, 0), "wood")
    v.box("Crate", (-3.6, 3.6, -2), (-1.6, 5.6, 0), "wood_dark")
    v.box("Crate", (-1.6, 1.6, -2), (0.4, 3.2, 0), "wood")
    slats = G.Geo()
    for (x0, y0, x1, y1) in ((-3.8, 1.6, -1.8, 3.6), (-3.6, 3.6, -1.6, 5.6), (-1.6, 1.6, 0.4, 3.2)):
        for y in (y0 + 0.5, y1 - 0.5):
            slats.add(G.box(x1 - x0 - 0.2, 0.18, 0.06, ((x0 + x1) / 2, y, 0.03)))
    v.mesh("CrateSlats", slats, "wood_dark")
    for k in range(5):
        v.box("PizzaBox", (0.8 + 0.1 * (k % 2), 1.6 + 0.4 * k, -2), (3.8 - 0.1 * ((k + 1) % 2), 2.0 + 0.4 * k, 1),
              "cardboard", grid=False)
    hub = "Van__Hub"
    sc.geom(hub, hub_geo(1.4, 1.2), owner="Van")
    for zz in (-6.5, 6.5):
        for sx in (-1, 1):
            wheel(v, (sx * 3.6, 1.4, zz), 1.4, 1.2, hub, "hub")
    moving(name, "Wheel x4", "cylinders on their axles: spin about their own X axis")
    return m
