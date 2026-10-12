"""Everything outside the shack: ground, front pavement, road, ditch, the back yard
with its fence and gate, the outside stations (Generator, Dumpster, YardGate,
StreetLamp, YardLamp, BusStop, RoadSign), the old billboard, the pine forest and
all the markers of section C."""
import math

import numpy as np

import layout as L
import map_items as I
import map_stations as MS
import mk
import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

N, S_, E, W = (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)
F = G.facing

PATH = [((8.0, 12.0), (-72.0, L.YARD_Z[0] - 1)), ((6.0, 10.0), (-94.0, -72.0)), ((4.0, 8.0), (-115.0, -94.0))]


def build(sc):
    out = sc.folder(sc.root, "Outside")
    ground(sc, sc.folder(out, "Ground"))
    road(sc, sc.folder(out, "Road"))
    yard(sc, sc.folder(out, "Yard"))
    front(sc, sc.folder(out, "Front"))
    billboard(sc, sc.model(out, "Billboard"))
    cams(sc, sc.folder(out, "Cameras"))
    generator(sc)
    dumpster(sc)
    yard_gate(sc)
    street_lamp(sc)
    yard_lamp(sc)
    bus_stop(sc)
    road_sign(sc)
    trees = forest(sc, sc.folder(out, "Trees"))
    markers(sc, trees)


# ---------------------------------------------------------------- ground

def ground(sc, f):
    X0, X1, Z0, Z1 = L.GROUND
    regions = [
        (L.YARD_X[0], L.YARD_X[1], L.YARD_Z[0], L.YARD_Z[1], "gravel"),
        (L.OUT_X0, L.OUT_X1, L.OUT_Z0, L.OUT_Z1, "pave"),
        (L.APRON_X[0], L.APRON_X[1], L.OUT_Z1, L.SIDEWALK_Z[0], "pave"),
        (X0, X1, L.SIDEWALK_Z[0], L.KERB_N[0], "pave"),
        (X0, X1, L.KERB_N[0], L.KERB_N[1], "kerb"),
        (X0, X1, L.ROAD[0], L.ROAD[1], "road"),
        (X0, X1, L.KERB_S[0], L.KERB_S[1], "kerb"),
        (X0, X1, L.DITCH[0], L.DITCH[1], "ditch"),
    ]
    for (xa, xb), (za, zb) in PATH:
        regions.append((xa, xb, za, zb, "dirt"))
    regions.append((L.GATE_X[0], L.GATE_X[1], L.YARD_Z[0] - 1, L.YARD_Z[0], "dirt"))
    cols = {"grass": "grass", "gravel": "gravel", "pave": "pave", "kerb": "kerb", "dirt": "dirt"}
    for x0, x1, z0, z1, k in mk.partition((X0, X1, Z0, Z1), regions, "grass"):
        if k == "road":
            continue                                  # built by road()
        if k == "ditch":
            sc.box(f, "Ditch", (x0, -2.8, z0), (x1, -L.DITCH_DEPTH, z1), "grass_dark")
            continue
        sc.box(f, "Ground", (x0, -1.2, z0), (x1, 0.0, z1), cols[k])
    # ditch slopes (wedges): high edges at the kerb side and the forest side
    zm = (L.DITCH[0] + L.DITCH[1]) / 2
    h = L.DITCH_DEPTH
    sc.wedge(f, "DitchBank", (X1 - X0, h, zm - L.DITCH[0]), ((X0 + X1) / 2, -h / 2, (L.DITCH[0] + zm) / 2),
             G.ry(180), "grass_dark")
    sc.wedge(f, "DitchBank", (X1 - X0, h, L.DITCH[1] - zm), ((X0 + X1) / 2, -h / 2, (zm + L.DITCH[1]) / 2),
             np.eye(3), "grass_dark")
    # a puddle of dark water along the bottom
    sc.box(f, "DitchWater", (X0 + 1, -h - 0.4 + 0.2, zm - 1), (X1 - 1, -h + 0.2, zm + 1), (30, 40, 44), material="Glass",
           transparency=0.2, collide=False, grid=True)


def road(sc, f):
    X0, X1 = L.GROUND[0], L.GROUND[1]
    y1 = L.ROAD_Y
    sc.box(f, "Asphalt", (X0, y1 - 1.2, L.LANE_N[0]), (X1, y1, L.LANE_N[1]), "asphalt")
    sc.box(f, "Asphalt", (X0, y1 - 1.2, L.LANE_S[0]), (X1, y1, L.LANE_S[1]), "asphalt")
    # worn dashed centre line: 6 long, 6 gaps, some dashes faded away
    rng = np.random.default_rng(14)
    za, zb = L.CENTRE
    x = X0
    gap_start = X0
    while x < X1 - 1e-6:
        dash = 6.0 if x + 12 <= X1 else None
        if dash and rng.random() > 0.18:
            if x > gap_start:
                sc.box(f, "Asphalt", (gap_start, y1 - 1.2, za), (x, y1, zb), "asphalt")
            length = 6.0 if rng.random() > 0.3 else float(rng.integers(3, 6))
            sc.box(f, "CentreLine", (x, y1 - 1.2, za), (x + length, y1, zb), "road_line")
            gap_start = x + length
        x += 12.0
    if gap_start < X1:
        sc.box(f, "Asphalt", (gap_start, y1 - 1.2, za), (X1, y1, zb), "asphalt")
    # kerb stones a plate proud of the road
    # (the kerb strips themselves are ground pieces at Y 0)


# ---------------------------------------------------------------- yard, fence

FENCE_Z = L.YARD_Z[0]          # inner face of the north fence


def yard(sc, f):
    x0, x1 = L.YARD_X
    z0, z1 = L.YARD_Z
    planks = sc.folder(f, "Fence")
    k = 0

    def plank(a0, a1, along, fixed0, fixed1, idx):
        tall = 7.2 if idx % 2 == 0 else 6.4
        col = "fence" if idx % 3 else "fence2"
        if along == "x":
            sc.box(planks, "Plank", (a0, -0.2, fixed0), (a1, -0.2 + tall, fixed1), col)
        else:
            sc.box(planks, "Plank", (fixed0, -0.2, a0), (fixed1, -0.2 + tall, a1), col)

    # north fence (with the gate gap), west and east fences (corners included), short south runs to the shack
    for a in np.arange(x0, x1, 2.0):
        if L.GATE_X[0] <= a < L.GATE_X[1]:
            continue
        plank(a, a + 2, "x", FENCE_Z - 1, FENCE_Z, k)
        k += 1
    for xf in (x0 - 1, x1):
        for a in np.arange(FENCE_Z - 1, z1 - 1, 2.0):
            plank(a, a + 2, "z", xf, xf + 1, k)
            k += 1
    for (a0, a1) in ((x0 - 1, L.OUT_X0 - 1), (L.OUT_X1 + 1, x1 + 1)):
        for a in np.arange(a0, a1, 2.0):
            plank(a, min(a + 2, a1), "x", z1 - 1, z1, k)
            k += 1
    # rails and posts on the yard side (same colour so their faces may meet)
    rails = sc.folder(f, "FenceRails")
    for y in (1.2, 5.2):
        sc.box(rails, "Rail", (x0, y, FENCE_Z), (L.GATE_X[0] - 1, y + 0.8, FENCE_Z + 1), "fence_dark")
        sc.box(rails, "Rail", (L.GATE_X[1] + 1, y, FENCE_Z), (x1, y + 0.8, FENCE_Z + 1), "fence_dark")
        sc.box(rails, "Rail", (x0, y, z0 + 1), (x0 + 1, y + 0.8, z1 - 1), "fence_dark")
        sc.box(rails, "Rail", (x1 - 1, y, z0 + 1), (x1, y + 0.8, z1 - 1), "fence_dark")
    for xp in list(np.arange(x0, x1 + 1, 8.0)) + [L.GATE_X[0] - 1, L.GATE_X[1]]:
        if L.GATE_X[0] - 1 < xp < L.GATE_X[1] + 1 and xp not in (L.GATE_X[0] - 1, L.GATE_X[1]):
            continue
        xp = min(max(xp, x0), x1 - 1)
        sc.box(rails, "Post", (xp, -0.2, FENCE_Z), (xp + 1, 7.4, FENCE_Z + 1), "fence_dark")
    for zp in np.arange(z0 + 8, z1 - 1, 8.0):
        sc.box(rails, "Post", (x0, -0.2, zp), (x0 + 1, 7.4, zp + 1), "fence_dark")
        sc.box(rails, "Post", (x1 - 1, -0.2, zp), (x1, 7.4, zp + 1), "fence_dark")
    # delivery pad inside the gate
    pad = sc.model(f, "DeliveryPad")
    px0, px1, pz0, pz1 = 6.0, 14.0, FENCE_Z + 1.0, FENCE_Z + 9.0
    sc.box(pad, "Slab", (px0, 0.0, pz0), (px1, 0.4, pz1), "concrete")
    for (a, b, c, d) in ((px0, px1, pz0, pz0 + 1), (px0, px1, pz1 - 1, pz1), (px0, px0 + 1, pz0 + 1, pz1 - 1),
                         (px1 - 1, px1, pz0 + 1, pz1 - 1)):
        sc.box(pad, "Paint", (a, 0.4, c), (b, 0.8, d), "mustard", collide=False)
    # paving from the back door to the pad
    for zz in np.arange(L.OUT_Z0 - 3, pz1 + 1, -3.0):
        sc.box(f, "Paver", (-15.0, 0.0, zz - 2), (-13.0, 0.4, zz), "concrete")
    # clutter: pallets and a tyre
    for (cx, cz, yaw) in ((-24.0, -16.0, 10), (-23.0, -19.5, -5)):
        pal = sc.model(f, "Pallet")
        R = G.ry(yaw)
        for k2 in range(3):
            sc.boxr(pal, "Slat", (4, 0.4, 1), (cx, 0.2 + 0.0, cz - 1.2 + 1.2 * k2), R, "wood_dark")
        sc.boxr(pal, "Deck", (4, 0.4, 4), (cx, 0.6, cz), R, "wood")


# ---------------------------------------------------------------- front

def front(sc, f):
    # bench against the front wall, west of the window, and a litter bin
    b = sc.model(f, "Bench")
    bx0, bx1, bz = -13.0, -9.0, L.OUT_Z1
    for x in (bx0, bx1 - 1):
        sc.box(b, "Leg", (x, -0.2, bz + 0.5), (x + 1, 1.8, bz + 1.5), "black")
    sc.box(b, "Seat", (bx0 - 0.5, 1.8, bz + 0.5), (bx1 + 0.5, 2.2, bz + 2.5), "green")
    sc.box(b, "Back", (bx0 - 0.5, 2.2, bz + 0.2), (bx1 + 0.5, 4.2, bz + 1.2), "green")
    lb = sc.model(f, "LitterBin")
    body = G.lathe([(0, 0), (0.7, 0), (0.78, 2.6), (0, 2.6)], 10)
    c = (-15.5, 0.0, L.OUT_Z1 + 1.4)
    sc.mesh(lb, "Body", "LitterBin__Body", G.outward(body), CF(c), "bin_green", owner="LitterBin", collide=True)
    sc.mesh(lb, "Rim", "LitterBin__Rim", G.ring(0.84, 0.66, 0.22, 10, c=(0, 2.6, 0)), CF(c), "black",
            owner="LitterBin")
    # a few bollards along the kerb so the queue reads as a waiting area
    for x in (-7.0, 7.0):
        sc.cylinder(f, "Bollard", 2.4, 1, (x, 1.0, L.SIDEWALK_Z[1] - 1.0), (0, 1, 0), "mustard")


def cams(sc, f):
    """Visible CCTV cameras (decor) next to the Cam markers."""
    body = G.Geo().add([G.box(0.6, 0.6, 1.4, (0, 0, 0)), G.box(0.8, 0.12, 1.6, (0, 0.36, 0.1)),
                        G.cyl(0.18, 0.15, 8, "z", (0, 0, -0.75))])
    arm = G.Geo().add([G.box(0.16, 0.16, 0.9, (0, 0.5, 0.9)), G.box(0.5, 0.5, 0.16, (0, 0.5, 1.4))])
    for name, pos, target in CAMS:
        R = G.look_at(pos, target).R
        # the prop sits just behind the marker
        cf = CF(pos, R) * CF((0, 0.0, 0.9))
        sc.mesh(f, "Camera", "CCTVCamera__Body", body, cf, "cream_dark", owner="CCTVCamera")
        sc.mesh(f, "Mount", "CCTVCamera__Mount", arm, cf, "grey_dark", owner="CCTVCamera")


# camera markers: (name, position, look-at)
CAMS = [
    ("Cam_Front", (5.4, 8.6, L.OUT_Z1 + 2.4), (0.0, 4.0, L.QUEUE_Z + 1.5)),
    ("Cam_Back", (-8.7, 10.2, 21.1), (0.0, 4.2, L.OUT_Z1 + 0.5)),
    ("Cam_Yard", (0.0, 9.6, L.OUT_Z0 - 0.7), (0.0, 0.0, -36.0)),
    ("Cam_Road", (24.6, 17.6, 21.6), (70.0, 4.0, 30.0)),
]


# ---------------------------------------------------------------- outside stations

def generator(sc):
    m = MS.station(sc, "Generator")
    cx, cz = -20.0, -34.0
    # lean-to: four posts, a sloping roof of three tilted plates
    for (x, z, h) in ((cx - 4, cz - 4, 7.6), (cx + 3, cz - 4, 6.4), (cx - 4, cz + 3, 7.6), (cx + 3, cz + 3, 6.4)):
        sc.box(m, "Post", (x, -0.2, z), (x + 1, -0.2 + h, z + 1), "wood_dark")
    slope = math.degrees(math.atan2(1.2, 8.0))
    for k, z in enumerate((cz - 4.5, cz - 1.5, cz + 1.5)):
        sc.boxr(m, "Roof", (9, 0.4, 3), (cx - 0.0, 6.95, z + 1.5), G.rz(-slope), "rust" if k % 2 else "grey")
    sc.box(m, "Pad", (cx - 3, 0.0, cz - 3), (cx + 3, 0.4, cz + 3), "concrete")
    base = CF((cx, 0.4, cz))
    # the generator itself, facing east (the yard)
    body = G.Geo()
    body.add(G.box(2.2, 1.0, 1.6, (0, 1.9, 0)))                   # fuel tank
    body.add(G.box(1.2, 0.5, 0.9, (-0.3, 2.6, 0)))                 # tank top
    mesh_b = MS.mesh(sc, m, "Body", body, "mustard", frame=base, collide=True)
    frame = G.Geo()
    for x in (-1.2, 1.2):
        for z in (-0.85, 0.85):
            frame.add(G.box(0.16, 1.4, 0.16, (x, 0.7, z)))
        frame.add(G.box(0.16, 0.16, 1.86, (x, 1.4, 0)))
        frame.add(G.box(0.16, 0.16, 1.86, (x, 0.08, 0)))
    for z in (-0.85, 0.85):
        frame.add(G.box(2.56, 0.16, 0.16, (0, 1.4, z)))
        frame.add(G.box(2.56, 0.16, 0.16, (0, 0.08, z)))
    MS.mesh(sc, m, "Frame", frame, "black", frame=base, collide=True)
    eng = G.Geo().add([G.box(1.3, 1.1, 1.2, (-0.2, 0.75, 0)), G.cyl(0.42, 0.5, 10, "x", (0.75, 0.8, 0))])
    for k in range(4):
        eng.add(G.box(0.9, 0.06, 1.25, (-0.2, 0.5 + 0.18 * k, 0)))
    MS.mesh(sc, m, "Engine", eng, "grey", frame=base)
    muff = G.cyl(0.25, 1.0, 8, "z", (-0.85, 1.05, 0.65))
    MS.mesh(sc, m, "Muffler", muff, "steel_dark", frame=base, material="Metal")
    panel = G.box(0.1, 0.6, 0.8, (1.2, 1.0, 0))
    MS.mesh(sc, m, "Panel", panel, "black", frame=base)
    cap = MS.mesh(sc, m, "FuelCap", G.cyl(0.2, 0.18, 8, "y", (0.5, 2.94, 0.3)), "red", frame=base, collide=True)
    MS.pivot(cap, base * CF((0.5, 2.85, 0.3)))
    MS.moving(m, "FuelCap", "screw cap on the tank: turn it about Y and lift it off (pivot = cap centre)")
    hdl = G.Geo().add([G.box(0.16, 0.16, 0.5, (0, 0, 0)), G.box(0.08, 0.08, 0.3, (-0.15, 0, 0)).xf(RY(90))])
    hp = MS.mesh(sc, m, "Handle", hdl, "black", frame=base * CF((1.12, 0.85, 0.0)), collide=True)
    MS.pivot(hp, base * CF((1.0, 0.85, 0.0)))
    MS.moving(m, "Handle", "pull-cord handle: pull it out along +X (east) up to 1.5 and let it snap back")
    bulb = sc.ball(m, "Bulb", 1.0, base * np.array((1.3, 1.25, -0.25)), (90, 40, 30), material="SmoothPlastic",
                   collide=False, shadow=False)
    bulb.p["size"] = (0.4, 0.4, 0.4)
    bulb.p["grid"] = False
    sc.attachment(mesh_b, "Exhaust", base * CF((-0.85, 1.05, 1.18), G.facing(S_)))
    MS.stand(sc, m, cx + 2.6, cz, W, y=0.4)
    sc.attr(m, "BulbOnColor", "255,70,40")
    return m


def dumpster(sc):
    m = MS.station(sc, "Dumpster")
    cx, cz = 20.0, -31.0
    base = CF((cx, 0.0, cz))
    # body: tapered skip, open side west; hinge for the lid at the back (east)
    body = G.Geo()
    rings = [[(sx * 1.9, 0.5, sz * 3.0) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
             [(sx * 2.0 + (0.4 if sx < 0 else 0), 3.6, sz * 3.1) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]]
    body.add(G.outward(G.loft(rings)))
    for z in (-1.5, 0.0, 1.5):
        body.add(G.box(0.2, 2.8, 0.3, (-2.15, 2.05, z)).xf(T(0, 0, 0) @ RZ(-6)))
    MS.mesh(sc, m, "Body", body, "bin_green", frame=base, collide=True)
    wheels = G.Geo()
    for x in (-1.5, 1.5):
        for z in (-2.6, 2.6):
            wheels.add(G.cyl(0.3, 0.25, 8, "z", (x, 0.3, z)))
    MS.mesh(sc, m, "Wheels", wheels, "black", frame=base)
    lid = G.box(4.6, 0.2, 6.4, (-0.3, 0.1, 0))
    lid.add(G.box(0.2, 0.4, 6.4, (-2.5, -0.1, 0)))
    lp = MS.mesh(sc, m, "Lid", lid, "black", frame=base * CF((0.0, 3.62, 0.0)), collide=True)
    MS.pivot(lp, base * CF((2.0, 3.7, 0.0)))
    MS.moving(m, "Lid", "hinged along the back (east) top edge; rotate the pivot -100 deg about Z to throw it open")
    # two wheelie bins north of it
    bb = G.Geo().add([G.outward(G.loft([[(sx * 0.7, 0.2, sz * 0.75) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
                                        [(sx * 0.8, 2.8, sz * 0.85) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]]))])
    bb.add(G.cyl(0.25, 0.2, 8, "z", (0.6, 0.25, -0.65)))
    bb.add(G.cyl(0.25, 0.2, 8, "z", (0.6, 0.25, 0.65)))
    blid = G.box(1.8, 0.16, 1.9, (0, 0, 0))
    for k, (bx, bz, col) in enumerate(((17.0, -26.5, "grey_dark"), (19.5, -26.5, "bin_green"))):
        wb = sc.model(m, "WheelieBin%d" % (k + 1))
        f = CF((bx, 0.0, bz), G.ry(90))
        sc.mesh(wb, "Body", "WheelieBin__Body", bb, f, col, owner="WheelieBin", collide=True)
        lp2 = sc.mesh(wb, "Lid", "WheelieBin__Lid", blid, f * CF((0, 2.88, 0)), "black", owner="WheelieBin",
                      collide=True)
        MS.pivot(lp2, CF((bx, 2.88, bz + 0.95)))
    MS.moving(m, "WheelieBin1/2.Lid", "hinged at the back edge; rotate the pivot about X to lift")
    bag = I.get("TrashBag")
    for k in range(3):
        rest = bag.rest()
        I.place(sc, m, bag, CF((cx - 3.0 + 0.3 * k, 0.0, cz - 2.0 + 1.6 * k), G.ry(40 * k)) * rest.inv())
    MS.stand(sc, m, cx - 4.2, cz, E, y=0.0)
    return m


def yard_gate(sc):
    m = MS.station(sc, "YardGate")
    gx0, gx1 = L.GATE_X
    z0, z1 = FENCE_Z - 1, FENCE_Z
    for x in (gx0 - 1, gx1):
        sc.box(m, "GatePost", (x, -0.2, z0 - 0.5), (x + 1, 8.2, z1 + 0.5), "fence_dark")
    gate = sc.box(m, "Gate", (gx0, 0.4, z0), (gx0 + 2, 6.8, z1), "fence")
    parts = [sc.box(m, "GatePlank", (gx0 + 2, 0.4, z0), (gx1, 6.8, z1), "fence2"),
             sc.box(m, "GateRail", (gx0, 1.6, z1), (gx1, 2.4, z1 + 1), "fence_dark", collide=False),
             sc.box(m, "GateRail", (gx0, 5.2, z1), (gx1, 6.0, z1 + 1), "fence_dark", collide=False)]
    L_ = math.hypot(gx1 - gx0, 3.6)
    ang = math.degrees(math.atan2(3.6, gx1 - gx0))
    parts.append(sc.boxr(m, "GateBrace", (4, 0.8, 1), ((gx0 + gx1) / 2, 3.8, z1 + 0.5), G.rz(ang), "fence_dark",
                         collide=False))
    latch = G.Geo().add([G.box(0.6, 0.3, 0.2, (0, 0, 0)), G.torus(0.2, 0.06, 8, 4, "z", (0.2, -0.3, 0))])
    parts.append(MS.mesh(sc, m, "Latch", latch, "steel_dark", frame=CF((gx1 - 0.4, 3.8, z1 + 1.15)), material="Metal"))
    MS.weld_all(sc, gate, parts)
    MS.pivot(gate, CF((gx0, 3.6, z0)))
    MS.moving(m, "Gate", "hinged on the west post; rotate the pivot +90 deg about Y to swing it OUT (north) onto "
                         "the dirt path. Second plank, rails, brace and latch are welded to it")
    MS.stand(sc, m, (gx0 + gx1) / 2, z1 + 3.0, N, y=0.4)
    return m


def street_lamp(sc):
    m = MS.station(sc, "StreetLamp")
    x, z = -9.0, 21.6
    sc.box(m, "Base", (x - 1, -0.2, z - 1), (x + 1, 1.0, z + 1), "grey_dark")
    sc.cylinder(m, "Pole", 10.8, 1, (x, 6.4, z), (0, 1, 0), "grey_dark")
    sc.box(m, "Arm", (x - 0.5, 11.2, z - 3.5), (x + 0.5, 11.6, z + 0.5), "grey_dark")
    head = G.Geo().add([G.box(1.2, 0.5, 2.0, (0, 0.25, 0)), G.frustum(0.75, 0.45, 0.5, 8, "y", (0, -0.25, 0))])
    hc = (x, 11.0, z - 3.0)
    MS.mesh(sc, m, "Head", head, "grey_dark", frame=CF(hc))
    b = sc.ball(m, "Bulb", 1.0, (hc[0], hc[1] - 0.45, hc[2]), "bulb", material="Neon", collide=False, shadow=False)
    sc.light(b, "SpotLight", "Light", "bulb", brightness=2.0, range_=28, shadows=True, angle=110, face="Bottom")
    MS.stand(sc, m, x + 2.0, z - 1.0, N, y=0.0)
    return m


def yard_lamp(sc):
    m = MS.station(sc, "YardLamp")
    x, z = 3.0, -27.0
    sc.box(m, "Pole", (x - 0.5, -0.2, z - 0.5), (x + 0.5, 11.8, z + 0.5), "wood_dark")
    sc.box(m, "CrossArm", (x - 2.0, 10.6, z - 0.5), (x + 2.0, 11.0, z + 0.5), "wood_dark")
    sc.box(m, "Arm", (x - 0.5, 9.8, z + 0.5), (x + 0.5, 10.2, z + 2.5), "grey_dark")
    head = G.Geo().add([G.frustum(0.9, 0.3, 0.7, 10, "y", (0, 0, 0)), G.cyl(0.3, 0.3, 8, "y", (0, 0.5, 0))])
    hc = (x, 9.5, z + 2.2)
    MS.mesh(sc, m, "Head", head, "green", frame=CF(hc))
    b = sc.ball(m, "Bulb", 1.0, (hc[0], hc[1] - 0.35, hc[2]), "bulb", material="Neon", collide=False, shadow=False)
    sc.light(b, "SpotLight", "Light", "bulb", brightness=2.2, range_=30, shadows=True, angle=120, face="Bottom")
    # a cable sagging to the back wall of the shack
    pts = [(x, 10.8, z), (x - 4, 9.9, z + 5.5), (x - 8, 9.6, z + 11), (x - 10, 10.0, L.OUT_Z0 - 0.3)]
    sc.mesh(m, "Cable", "YardLamp__Cable", G.tube(pts, 0.06, 5), CF(), "black", owner="YardLamp")
    MS.stand(sc, m, x - 1.5, z + 3.0, N, y=0.0)
    return m


def bus_stop(sc):
    m = MS.station(sc, "BusStop")
    x0, x1 = 37.0, 43.0
    z0, z1 = L.SIDEWALK_Z[0], L.SIDEWALK_Z[0] + 3.0
    for x in (x0, x1 - 1):
        for z in (z0, z1 - 1):
            sc.box(m, "Post", (x, 0.0, z), (x + 1, 7.2, z + 1), "steel_dark")
    sc.box(m, "Roof", (x0 - 0.5, 7.2, z0 - 0.5), (x1 + 0.5, 7.6, z1 + 0.5), "grey_dark")
    mk.panel_z(sc, m, "BackPanel", z0 + 0.5, x0 + 1, x1 - 1, 1.2, 7.2 - 0.0 - 0.0 + 0.0, "glass", material="Glass",
               transparency=0.6)
    mk.panel_x(sc, m, "SidePanel", x0 + 0.5, 1.2, 7.2, z0 + 1, z1 - 1, "glass", material="Glass", transparency=0.6)
    sc.box(m, "Seat", (x0 + 1, 1.8, z0 + 1), (x1 - 1, 2.2, z0 + 2), "red")
    for x in (x0 + 1, x1 - 2):
        sc.box(m, "SeatLeg", (x, -0.2, z0 + 1), (x + 1, 1.8, z0 + 2), "steel_dark")
    tube = sc.box(m, "Light", (x0 + 1, 6.8, z0 + 1), (x1 - 1, 7.2, z0 + 2), "bulb_cool", material="Neon",
                  collide=False)
    sc.light(tube, "PointLight", "Light", "bulb_cool", brightness=0.8, range_=12, shadows=False)
    sc.box(m, "Timetable", (x1 - 0.5, 2.8, z0 + 1.2), (x1 + 0.5, 5.2, z1 - 0.2), "white", grid=False)
    # bus stop flag on a pole at the kerb
    sc.cylinder(m, "SignPole", 8.0, 1, (x0 - 2.5, 3.8, L.SIDEWALK_Z[1] - 0.8), (0, 1, 0), "steel_dark")
    flag = G.Geo().add([G.cyl(1.1, 0.16, 16, "z", (0, 0, 0)), G.box(1.0, 0.5, 0.18, (0, 0, 0.02))])
    MS.mesh(sc, m, "Flag", flag, "sign_blue", frame=CF((x0 - 2.5, 7.4, L.SIDEWALK_Z[1] - 0.8)))
    MS.stand(sc, m, (x0 + x1) / 2, z0 + 2.6, N, y=0.0)
    return m


def road_sign(sc):
    m = MS.station(sc, "RoadSign")
    x0, x1 = 21.0, 31.0
    z0 = L.SIDEWALK_Z[0] + 1.5
    for x in (x0 + 1, x1 - 2):
        sc.box(m, "Post", (x, -0.4, z0), (x + 1, 8.4, z0 + 1), "grey_dark")
    sc.box(m, "Board", (x0, 8.4, z0), (x1, 13.2, z0 + 1), "red")
    sc.box(m, "BoardTrim", (x0 - 0.5, 13.2, z0 - 0.5), (x1 + 0.5, 13.6, z0 + 1.5), "mustard")
    sc.box(m, "BoardTrim", (x0 - 0.5, 8.0, z0 - 0.5), (x1 + 0.5, 8.4, z0 + 1.5), "mustard")
    # arrow pointing west to the shack, on both faces: a bar and a two-wedge head
    for zmid in (z0 + 1.3, z0 - 0.3):
        sc.box(m, "Arrow", (x0 + 4, 10.4, zmid - 0.5), (x1 - 2, 11.2, zmid + 0.5), "cream")
        sc.wedge(m, "ArrowHead", (1, 0.8, 2), (x0 + 3.0, 11.2, zmid), G.ry(90), "cream")
        sc.wedge(m, "ArrowHead", (1, 0.8, 2), (x0 + 3.0, 10.4, zmid), G.ry(90) @ G.rz(180), "cream")
    # pizza-slice mascot standing on the board: stepped slice, pepperoni, arms, head on top
    mx = (x0 + x1) / 2
    zm0, zm1 = z0, z0 + 1
    rows = [(1, 13.6, 14.8), (2, 14.8, 16.0), (2, 16.0, 17.2), (3, 17.2, 18.4), (4, 18.4, 19.6)]
    for w, y0, y1 in rows:
        sc.box(m, "Slice", (mx - w / 2, y0, zm0), (mx + w / 2, y1, zm1), "cheese")
    sc.box(m, "Crust", (mx - 2.5, 19.6, zm0 - 0.0), (mx + 2.5, 20.8, zm1 + 0.0), "crust")
    for (dx, y) in ((-0.6, 18.8), (0.8, 17.8), (0.0, 16.4)):
        sc.cylinder(m, "Pepperoni", 0.4, 1, (mx + dx, y, zm1 + 0.2), (0, 0, 1), "pepperoni")
    sc.boxr(m, "Arm", (2, 0.8, 1), (mx - 2.6, 18.9, (zm0 + zm1) / 2), G.rz(-30), "cheese")
    sc.boxr(m, "Arm", (2, 0.8, 1), (mx + 2.6, 19.4, (zm0 + zm1) / 2), G.rz(40), "cheese")
    head = sc.box(m, "Head", (mx - 1, 20.8, zm0), (mx + 1, 22.8, zm1 + 1), "dough")
    face = G.Geo()
    for sx in (-0.45, 0.45):
        face.add(G.cyl(0.18, 0.06, 8, "z", (sx, 0.35, 0)))
    smile = [(0.6 * math.cos(a), -0.15 + 0.35 * math.sin(a)) for a in np.linspace(math.radians(200), math.radians(340), 7)]
    for (a, b) in zip(smile, smile[1:]):
        L_ = math.hypot(b[0] - a[0], b[1] - a[1])
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        face.add(G.box(L_ + 0.04, 0.1, 0.06).xf(T((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0) @ RZ(ang)))
    fp = MS.mesh(sc, m, "Face", face, "black", frame=CF((mx, 21.8, zm1 + 1.02)))
    hat = G.Geo().add([G.cyl(0.8, 0.9, 10, "y", (0, 0.45, 0)), G.sphere(0.95, 10, 5, scale=(1, 0.6, 1), c=(0, 1.1, 0))])
    hp = MS.mesh(sc, m, "Hat", hat, "white", frame=CF((mx, 22.8, (zm0 + zm1 + 1) / 2)))
    MS.weld_all(sc, head, [fp, hp])
    MS.pivot(head, CF((mx, 20.8, (zm0 + zm1 + 1) / 2)))
    MS.moving(m, "Head", "the mascot's head: rotate the pivot (neck, bottom centre) about Y to turn it; face and hat "
                         "are welded on")
    MS.stand(sc, m, mx, z0 - 2.0, S_, y=0.0)
    return m


# ---------------------------------------------------------------- billboard

def billboard(sc, m):
    x0, x1, z = -38.0, -24.0, 61.0
    for x in (x0 + 2, x1 - 3):
        sc.box(m, "Leg", (x, -0.2, z), (x + 1, 7.8, z + 1), "wood_dark")
        sc.boxr(m, "Strut", (1, 6.0, 1), (x + 0.5, 3.0, z + 2.2), G.rx(-28), "wood_dark")
    sc.box(m, "Board", (x0, 7.6, z - 1), (x1, 15.6, z), "billboard")
    sc.box(m, "BoardTop", (x0 - 0.5, 15.6, z - 1.5), (x1 + 0.5, 16.0, z + 0.5), "wood_dark")
    # faded ad: a slice of pizza and stripes, one panel missing
    sc.box(m, "AdStripe", (x0 + 1, 13.6, z - 1.4), (x1 - 1, 14.8, z - 0.4), (150, 70, 60))
    sc.wedge(m, "AdSlice", (1, 4.8, 5), (x0 + 4.5, 10.4, z - 0.9), G.ry(90), (210, 180, 110))
    sc.box(m, "AdCrust", (x0 + 2, 12.4, z - 1.3), (x0 + 7, 13.2, z - 0.3), (170, 120, 80))
    sc.box(m, "AdText", (x0 + 8, 11.6, z - 1.3), (x1 - 1, 12.4, z - 0.3), (120, 110, 100))
    sc.box(m, "AdText", (x0 + 8, 10.0, z - 1.3), (x1 - 3, 10.8, z - 0.3), (120, 110, 100))
    sc.box(m, "Gap", (x1 - 4, 8.0, z - 1.2), (x1 - 1, 10.0, z - 0.2), (40, 40, 40))
    flap = G.box(2.4, 2.2, 0.06).xf(RX(-25) @ RZ(8))
    MS.mesh(sc, m, "Flap", flap, "billboard", owner="Billboard", frame=CF((x1 - 2.6, 9.4, z - 1.35)))
    lamp = G.Geo().add([G.box(0.4, 0.4, 1.4, (0, 0, -0.6)), G.frustum(0.3, 0.5, 0.5, 8, "z", (0, 0.15, -1.4))])
    for x in (x0 + 4, x1 - 4):
        MS.mesh(sc, m, "Spot", lamp, "grey_dark", owner="Billboard", frame=CF((x, 7.4, z - 1.2), G.rx(30)))


# ---------------------------------------------------------------- forest

VARIANTS = {
    # name: [(width, y0, y1)] leaf slabs (trunk added separately), trunk height
    "Tall": ([(10, 4.6, 7.0), (8, 7.0, 9.4), (6, 9.4, 11.8), (4, 11.8, 14.2), (2, 14.2, 16.6)], 7.2),
    "Medium": ([(10, 3.4, 4.6), (8, 4.6, 7.0), (6, 7.0, 9.4), (4, 9.4, 11.8), (2, 11.8, 13.0)], 5.2),
    "Wide": ([(12, 3.8, 6.2), (10, 6.2, 8.6), (8, 8.6, 11.0), (6, 11.0, 13.4), (4, 13.4, 15.8)], 6.4),
}


def clear_zone(x, z):
    """True where no tree may stand."""
    if L.SIDEWALK_Z[0] - 4 < z < L.DITCH[1] + 4:          # road corridor, sidewalk to ditch
        return True
    if -46 < x < 46 and -60 < z < 22:                    # shack, front, yard and margin
        return True
    if 31 < x < 50 and 10 < z < 22:                       # bus stop
        return True
    if -44 < x < -18 and 56 < z < 68:                     # billboard
        return True
    for (xa, xb), (za, zb) in PATH:
        if xa - 4 < x < xb + 4 and za - 2 < z < zb + 2:
            return True
    return False


def forest(sc, f):
    rng = np.random.default_rng(1234)

    def min_dist(x, z):
        # nearer the clearing the trees thin out
        dx = max(0.0, abs(x) - 46)
        dz = max(0.0, -60 - z, z - 22)
        d = math.hypot(dx, dz)
        return 15.0 - 5.0 * min(1.0, d / 60.0)

    def accept(x, z):
        return not clear_zone(x, z)

    pts = mk.scatter_poisson(rng, (-148, 148, -98, 98), 210, min_dist, accept, tries=80000)
    trees = []
    names = list(VARIANTS) + ["Dead"]
    for i, (x, z) in enumerate(pts):
        k = rng.random()
        var = "Dead" if k < 0.1 else names[int(rng.integers(0, 3))]
        yaw = float(rng.uniform(0, 90))
        R = G.ry(yaw)
        sink = -0.2 - 0.4 * int(rng.integers(0, 2))
        t = sc.model(f, "Pine" if var != "Dead" else "DeadPine")
        if var == "Dead":
            h = 14.4
            sc.boxr(t, "Trunk", (2, h, 2), (x, sink + h / 2, z), R, "trunk_dark")
            for j, (y, L_, a) in enumerate(((6.4, 4, 20), (8.0, 3, 300), (9.2, 3, 140), (11.6, 3, 250))):
                d = np.array((math.cos(math.radians(a + yaw)), 0, math.sin(math.radians(a + yaw))))
                Rb = G.facing(d) @ G.rx(-25)
                c = np.array((x, sink + y, z)) + d * (L_ / 2 + 0.6)
                sc.boxr(t, "Branch", (1, 0.8, L_), c, Rb, "trunk_dark")
            sc.boxr(t, "Snag", (1, 2.4, 1), (x + 0.3, sink + h + 1.0, z), R @ G.rz(14), "trunk_dark")
        else:
            slabs, th = VARIANTS[var]
            sc.boxr(t, "Trunk", (2, th, 2), (x, sink + th / 2, z), R, "trunk")
            col = ("pine", "pine2", "pine3")[int(rng.integers(0, 3))]
            for j, (w, y0, y1) in enumerate(slabs):
                c2 = col if j % 2 == 0 else ("pine3" if col != "pine3" else "pine")
                sc.boxr(t, "Leaves", (w, y1 - y0, w), (x, sink + (y0 + y1) / 2, z), R, c2)
        trees.append((x, z, var))
    return trees


# ---------------------------------------------------------------- markers (section C)

def markers(sc, trees):
    mf = sc.root.get("Markers")

    def mark(name, pos, d=None, R=None):
        sc.marker(mf, name, CF(pos, R if R is not None else F(d)))

    for k in range(3):
        mark("Queue%d" % (k + 1), (0.0, 0.0, L.QUEUE_Z + 4.0 * k), N)
    mark("Spawn_RoadWest", (-145.0, 0.0, 21.0), E)
    mark("Spawn_RoadEast", (145.0, 0.0, 21.0), W)
    mark("Spawn_BusStop", (40.0, 0.0, 21.0), W)
    for name, pos, target in CAMS:
        mark(name, pos, R=G.look_at(pos, target).R)
    lane = (L.LANE_N[0] + L.LANE_N[1]) / 2
    mark("Car_Start", (140.0, L.ROAD_Y, lane), W)
    mark("Car_Stop", (0.0, L.ROAD_Y, lane), W)
    mark("Car_End", (-140.0, L.ROAD_Y, lane), W)
    mark("Truck_Stop", (10.0, 0.0, -58.0), S_)
    mark("Delivery_Drop", (10.0, 0.4, FENCE_Z + 5.0), N)
    mark("Inspector_Rise", (-0.5, L.FLOOR, 0.5), S_)
    for k, x in enumerate((-20.0, -14.0, -8.0, -2.0)):
        mark("Inspection_Stand%d" % (k + 1), (x, 0.0, FENCE_Z + 2.0), N)
    # on the open floor (not against the fridge), each looking at the serving window
    for k, (x, z) in enumerate(((-11.0, -2.2), (-9.2, -3.6), (-7.4, -2.2), (-5.6, -3.6))):
        mark("PlayerSpawn%d" % (k + 1), (x, L.FLOOR, z), (0.0 - x, 0.0, L.IN_Z1 - z))
    mark("Watcher_Window", (L.OUT_X0 - 2.5, 0.0, (L.SIDE_Z0 + L.SIDE_Z1) / 2), E)
    # forest spawns and tree-line markers: just inside the first trees, facing the shack
    def nearest_gap(dirx, dirz, start, step=2.0):
        """Walk out from the shack along a direction until the first tree; stop 3 inside it."""
        d = np.array((dirx, dirz), float)
        d /= np.linalg.norm(d)
        p = np.array(start, float)
        for _ in range(200):
            p = p + d * step
            near = min(trees, key=lambda t: (t[0] - p[0]) ** 2 + (t[1] - p[1]) ** 2)
            if math.hypot(near[0] - p[0], near[1] - p[1]) < 7.0:
                return p + d * 3.0
        return p
    tl = [((-1, -0.35), (-30, -20)), ((-0.3, -1), (-12, -48)), ((0.45, -1), (24, -48)), ((1, -0.2), (30, -20)),
          ((1, 0.15), (30, 8)), ((-0.25, 1), (-12, 58))]
    for k, (dv, start) in enumerate(tl):
        p = nearest_gap(dv[0], dv[1], start)
        mark("TreeLine%d" % (k + 1), (p[0], 0.0, p[1]), (-p[0], 0, -p[1]))
    ps = nearest_gap(0.0, 1.0, (-8, 58))
    mark("Spawn_ForestSouth", (ps[0], 0.0, ps[1] + 6.0), N)
    pn = nearest_gap(0.0, -1.0, (-6, -50))
    mark("Spawn_ForestNorth", (pn[0], 0.0, pn[1] - 6.0), S_)
