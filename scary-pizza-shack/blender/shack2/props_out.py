"""Prop models for the outside, in the same mesh language as inside (chunky, bevelled, 6..12
sided, nothing thinner than 0.15). Each returns [(part name, colour, Geo[, options])] in its
own space: origin on the ground it stands on (or the wall it hangs on), +Y up, +Z its front."""
import math

import numpy as np

import spsgeo as G
from spsgeo import T, RX, RY, RZ

from .kit import bevel_box, ccyl, cfrustum, chamfer_slab, irregular, prop, rod
from .outkit import catenary, chainlink, corrugated, flat_pole


def _cyl_y(r, y0, y1, n=10, b=0.05, x=0.0, z=0.0):
    return ccyl(r, y1 - y0, n, "y", (x, (y0 + y1) / 2, z), b)


def _lathe(profile, n=10):
    return G.outward(G.lathe(profile, n, phase=math.pi / n))


def _face_slab(pts, h, b=0.06):
    """A front-view outline (x, y) given thickness h along Z (centred), front edge chamfered."""
    return chamfer_slab([(x, -y) for (x, y) in pts], h, b).xf(G.M(G.rx(90))).xf(T(0, 0, -h / 2))


GLASS = {"material": "Glass", "transparency": 0.5}
NEON = {"material": "Neon"}


# ---------------------------------------------------------------- street furniture

@prop("PostBin")
def post_bin(rng):
    """A round litter bin hung on a short post, a lid with a slot, a sticker on the side."""
    post = _cyl_y(0.15, 0.0, 3.2, 8)
    body = _lathe([(0.0, 1.0), (0.55, 1.0), (0.62, 1.1), (0.62, 2.7), (0.0, 2.7)], 10)
    lid = _lathe([(0.0, 2.7), (0.68, 2.7), (0.68, 2.9), (0.4, 3.05), (0.0, 3.1)], 10)
    band = _lathe([(0.63, 2.2), (0.66, 2.2), (0.66, 2.45), (0.63, 2.45)], 10)
    return [("Post", "galv_dark", post), ("Body", "bin_green", body.xf(T(0, 0, 0.6))),
            ("Lid", "bin_black", lid.xf(T(0, 0, 0.6))), ("Band", "mustard", band.xf(T(0, 0, 0.6)))]


@prop("LitterBin")
def litter_bin(rng):
    """A round steel litter bin with a domed lid, dented, a bag edge showing."""
    body = _lathe([(0.0, 0.0), (0.7, 0.0), (0.78, 0.15), (0.78, 2.4), (0.0, 2.4)], 10)
    lid = _lathe([(0.0, 2.4), (0.85, 2.4), (0.85, 2.6), (0.5, 2.9), (0.0, 2.95)], 10)
    bag = _lathe([(0.7, 2.25), (0.82, 2.25), (0.82, 2.45), (0.7, 2.45)], 10)
    ribs = G.Geo()
    for y in (0.6, 1.6):
        ribs.add(_lathe([(0.78, y), (0.84, y), (0.84, y + 0.2), (0.78, y + 0.2)], 10))
    return [("Body", "galv", body), ("Lid", "galv_dark", lid), ("Bag", "black", bag), ("Ribs", "galv_dark", ribs)]


@prop("Bench")
def bench(rng):
    """A park bench: five weathered slats on two cast-iron ends with armrests."""
    slats = G.Geo()
    for i in range(3):
        slats.add(bevel_box(5.0, 0.15, 0.4, 0.04, c=(0, 1.6, -0.5 + 0.45 * i)))
    for i in range(2):
        slats.add(bevel_box(5.0, 0.4, 0.15, 0.04, c=(0, 2.25 + 0.5 * i, -0.85)).xf(T(0, 0, 0)))
    ends = G.Geo()
    for x in (-2.2, 2.2):
        ends.add(G.tube([(x, 0.0, 0.5), (x, 1.5, 0.3), (x, 1.5, -0.7), (x, 0.0, -0.8)], 0.12, 6))
        ends.add(G.tube([(x, 1.5, -0.85), (x, 3.1, -0.95)], 0.12, 6))
        ends.add(G.tube([(x, 2.2, 0.4), (x, 2.2, -0.9)], 0.12, 6))
    return [("Slats", "wood", slats), ("Ends", "black", ends)]


@prop("Bollard")
def bollard(rng):
    """A concrete bollard with a reflective band and a chipped top."""
    b = _lathe([(0.0, 0.0), (0.45, 0.0), (0.42, 2.4), (0.3, 2.7), (0.0, 2.75)], 10)
    band = _lathe([(0.43, 1.9), (0.47, 1.9), (0.46, 2.2), (0.42, 2.2)], 10)
    return [("Bollard", "concrete", b), ("Band", "reflector", band)]


@prop("WheelStop")
def wheel_stop(rng):
    """A precast concrete wheel stop, chipped at one end, two rusty pins."""
    g = G.Geo()
    g.add(chamfer_slab([(-2.5, -0.3), (2.3, -0.3), (2.5, -0.1), (2.5, 0.3), (-2.5, 0.3)], 0.5, 0.12))
    pins = G.Geo()
    for x in (-1.6, 1.6):
        pins.add(_cyl_y(0.1, 0.45, 0.58, 6, x=x))
    return [("Stop", "concrete2", g), ("Pins", "rust", pins)]


@prop("OilStain")
def oil_stain(rng):
    """A dark oil stain soaked into the ground (a plate let in, only its top shows)."""
    pts = irregular(rng, 1.4, 9, 0.35)
    return [("Stain", "oil", chamfer_slab(pts, 0.15, 0.04).xf(T(0, -0.13, 0)))]


@prop("Puddle")
def puddle(rng):
    """Rain water in a dip: a dark glossy plate, a lighter wet rim."""
    pts = [(x * 1.0, z * 0.7) for (x, z) in irregular(rng, 2.0, 10, 0.25)]
    rim = [(x * 1.18, z * 1.18) for (x, z) in pts]
    return [("Rim", "mud", chamfer_slab(rim, 0.15, 0.04).xf(T(0, -0.13, 0))),
            ("Water", "water", chamfer_slab(pts, 0.15, 0.04).xf(T(0, -0.11, 0)), {"material": "Glass",
                                                                                   "transparency": 0.15})]


@prop("Litter")
def litter(rng):
    """A drift of litter: a crushed cup, a burger box, a can, two wrappers."""
    g, red, can = G.Geo(), G.Geo(), G.Geo()
    for i in range(3):
        x, z = rng.uniform(-1.2, 1.2), rng.uniform(-0.8, 0.8)
        g.add(bevel_box(0.4, 0.15, 0.3, 0.04, c=(x, 0.075, z)).xf(RY(rng.uniform(0, 90))))
    red.add(cfrustum(0.22, 0.3, 0.6, 8, "x", (0.4, 0.25, 0.6), 0.04))
    can.add(ccyl(0.18, 0.5, 8, "z", (-0.8, 0.18, -0.4), 0.04))
    return [("Wrappers", "paper", g), ("Cup", "red", red), ("Can", "label_green", can)]


@prop("PicnicTable")
def picnic_table(rng):
    """A weathered picnic table with fixed benches on A-frame legs, one board loose."""
    top, legs = G.Geo(), G.Geo()
    for i in range(4):
        top.add(bevel_box(7.0, 0.3, 0.75, 0.05, c=(0, 3.15, -1.15 + 0.77 * i)))
    for sz in (-1, 1):
        top.add(bevel_box(7.0, 0.3, 0.9, 0.05, c=(0, 1.75, sz * 2.4)))
    top.add(bevel_box(6.8, 0.3, 0.75, 0.05, c=(0.1, 3.2, 1.2)).xf(RZ(1.5)))
    for x in (-2.6, 2.6):
        for sz in (-1, 1):
            legs.add(G.tube([(x, 0.0, sz * 2.4), (x, 3.0, sz * 0.4)], 0.18, 6))
        legs.add(bevel_box(0.3, 0.3, 5.6, 0.05, c=(x, 1.45, 0)))
    return [("Top", "wood", top), ("Legs", "wood_dark", legs)]


@prop("Payphone")
def payphone(rng):
    """A payphone on a post under its steel hood: the handset on a cord, a keypad, the
    PHONE sign (a Board on the hood is the station's job)."""
    post = bevel_box(0.4, 3.75, 0.4, 0.06, c=(0, 1.875, -0.3))
    hood = G.Geo()
    hood.add(bevel_box(1.9, 0.2, 1.4, 0.05, c=(0, 6.3, 0.3)))
    for sx in (-1, 1):
        hood.add(bevel_box(0.2, 2.6, 1.4, 0.05, c=(sx * 0.85, 5.0, 0.3)))
    hood.add(bevel_box(1.9, 2.6, 0.2, 0.05, c=(0, 5.0, -0.35)))
    box = bevel_box(1.0, 1.8, 0.6, 0.08, c=(0, 4.5, 0.0))
    keys = G.Geo()
    for i in range(3):
        for j in range(4):
            keys.add(bevel_box(0.15, 0.15, 0.15, 0.03, c=(-0.2 + 0.2 * i, 4.2 + 0.2 * j, 0.33)))
    hs = G.Geo()
    hs.add(bevel_box(0.25, 1.0, 0.3, 0.08, c=(-0.62, 4.6, 0.15)))
    cord = G.tube([(-0.62, 4.05, 0.15), (-0.5, 3.6, 0.3), (-0.3, 3.75, 0.35), (-0.1, 3.9, 0.3)], 0.075, 4)
    return [("Post", "galv_dark", post), ("Hood", "galv", hood), ("Box", "grey_dark", box), ("Keys", "steel_light", keys),
            ("Handset", "black", hs), ("Cord", "black", cord)]


@prop("NewsBox")
def news_box(rng):
    """A newspaper vending box on four legs: blue body, a window on the front, a coin slot."""
    body = bevel_box(1.8, 2.0, 1.4, 0.12, c=(0, 2.0, 0))
    lid = bevel_box(1.9, 0.2, 1.5, 0.05, c=(0, 3.1, 0))
    legs = G.Geo()
    for sx in (-1, 1):
        for sz in (-1, 1):
            legs.add(bevel_box(0.15, 1.0, 0.15, 0.03, c=(sx * 0.75, 0.5, sz * 0.55)))
    window = bevel_box(1.3, 0.9, 0.15, 0.03, c=(0, 2.35, 0.68))
    paper = bevel_box(1.1, 0.7, 0.15, 0.02, c=(0, 2.3, 0.6))
    slot = bevel_box(0.3, 0.3, 0.15, 0.03, c=(0.6, 1.45, 0.72))
    return [("Body", "label_blue", body), ("Lid", "label_blue", lid), ("Legs", "black", legs),
            ("Paper", "paper_old", paper), ("Window", "glass", window, GLASS), ("Slot", "steel_light", slot)]


@prop("IceChest")
def ice_chest(rng):
    """An ICE chest freezer outside the shop: white, a blue band, frost on the lid seal."""
    body = bevel_box(3.6, 2.6, 1.8, 0.15, c=(0, 1.45, 0))
    lid = bevel_box(3.7, 0.3, 1.9, 0.1, c=(0, 2.9, 0))
    band = bevel_box(3.65, 0.6, 1.85, 0.05, c=(0, 2.1, 0))
    feet = G.Geo()
    for sx in (-1, 1):
        feet.add(bevel_box(0.4, 0.15, 1.6, 0.04, c=(sx * 1.5, 0.075, 0)))
    hinge = bevel_box(0.5, 0.2, 0.15, 0.04, c=(1.2, 2.8, -0.97))
    return [("Body", "label_white", body), ("Lid", "label_white", lid), ("Band", "label_blue", band),
            ("Feet", "black", feet), ("Latch", "steel", hinge)]


@prop("VendingMachine")
def vending(rng):
    """A drinks machine: red body, the lit front panel, a column of buttons, the can slot."""
    body = bevel_box(3.0, 6.0, 2.4, 0.15, c=(0, 3.15, 0))
    front = bevel_box(1.9, 4.2, 0.15, 0.04, c=(-0.4, 3.6, 1.2))
    btns = G.Geo()
    for i in range(6):
        btns.add(bevel_box(0.35, 0.3, 0.15, 0.04, c=(1.0, 2.6 + 0.5 * i, 1.22)))
    slot = bevel_box(1.6, 0.6, 0.4, 0.06, c=(-0.4, 0.95, 1.05))
    plinth = bevel_box(2.8, 0.3, 2.2, 0.05, c=(0, 0.15, 0))
    return [("Body", "vending_red", body), ("Front", (255, 236, 210), front, NEON), ("Buttons", "steel_light", btns),
            ("Slot", "black", slot), ("Plinth", "charcoal", plinth)]


@prop("BugZapper")
def bug_zapper(rng):
    """A bug zapper hanging from a bracket: a cage round a blue tube, a drip tray under it."""
    cage = G.Geo()
    for i in range(8):
        a = math.tau * i / 8
        cage.add(rod((0.42 * math.cos(a), 0.2, 0.42 * math.sin(a)), (0.42 * math.cos(a), 1.6, 0.42 * math.sin(a)),
                     0.075, 4))
    cage.add(_cyl_y(0.5, 1.6, 1.8, 10))
    cage.add(_cyl_y(0.5, 0.0, 0.2, 10))
    hook = G.tube([(0, 1.8, 0), (0, 2.3, 0), (0.2, 2.55, 0)], 0.075, 4)
    tube = _cyl_y(0.2, 0.25, 1.55, 8)
    return [("Cage", "charcoal", cage), ("Hook", "steel_dark", hook), ("Tube", (110, 150, 255), tube, NEON)]


@prop("StringLightPole")
def string_light_pole(rng):
    """A timber post set in a tyre full of concrete, with a hook for the string lights."""
    pole = flat_pole(9.0, 0.3, 0.25, 8)
    tyre = _lathe([(0.55, 0.0), (0.95, 0.05), (1.0, 0.35), (0.9, 0.6), (0.55, 0.62)], 10)
    fill = _cyl_y(0.6, 0.0, 0.5, 10)
    hook = G.tube([(0.25, 8.6, 0), (0.55, 8.6, 0), (0.6, 8.85, 0)], 0.075, 4)
    return [("Pole", "pole_wood", pole), ("Tyre", "tyre", tyre), ("Fill", "concrete_dark", fill), ("Hook", "steel_dark", hook)]


@prop("PlanterBarrel")
def planter_barrel(rng):
    """Half a whisky barrel with dry earth and a dead shrub in it."""
    barrel = _lathe([(0.0, 0.0), (1.0, 0.0), (1.12, 0.6), (1.05, 1.3), (0.95, 1.3), (0.95, 0.15), (0.0, 0.15)], 12)
    hoops = G.Geo()
    for y in (0.25, 1.05):
        hoops.add(_lathe([(1.08, y), (1.16, y), (1.15, y + 0.15), (1.07, y + 0.15)], 12))
    earth = _cyl_y(0.93, 0.9, 1.15, 10)
    twigs = G.Geo()
    for i in range(5):
        a = math.tau * i / 5 + 0.3
        twigs.add(rod((0, 1.1, 0), (0.6 * math.cos(a), 2.3 + 0.2 * (i % 2), 0.6 * math.sin(a)), 0.075, 4))
    return [("Barrel", "wood_dark", barrel), ("Hoops", "iron", hoops), ("Earth", "mud", earth), ("Twigs", "deadwood", twigs)]


# ---------------------------------------------------------------- the shack's walls and roof

@prop("SandBucket")
def sand_bucket(rng):
    """A red fire bucket of sand by the back door."""
    b = _lathe([(0.0, 0.0), (0.45, 0.0), (0.58, 1.0), (0.48, 1.0), (0.4, 0.15), (0.0, 0.15)], 10)
    sand = _cyl_y(0.5, 0.6, 0.9, 10)
    handle = G.tube([(-0.58, 0.95, 0), (-0.4, 1.4, 0), (0.4, 1.4, 0), (0.58, 0.95, 0)], 0.075, 4)
    return [("Bucket", "fuel_red", b), ("Sand", "sand", sand), ("Handle", "steel_dark", handle)]


@prop("GasBottles")
def gas_bottles(rng):
    """Two propane bottles chained in a steel cage against the wall."""
    bt = G.Geo()
    for x in (-0.6, 0.6):
        bt.add(_lathe([(0.0, 0.0), (0.5, 0.0), (0.55, 0.3), (0.55, 2.4), (0.35, 2.75), (0.15, 2.8), (0.0, 2.8)], 10)
               .xf(T(x, 0, 0)))
    valves = G.Geo()
    for x in (-0.6, 0.6):
        valves.add(_cyl_y(0.15, 2.8, 3.1, 6, x=x))
    cage = G.Geo()
    for y in (0.2, 1.4, 2.6):
        cage.add(rod((-1.3, y, 0.65), (1.3, y, 0.65), 0.075, 4))
    for x in (-1.3, 1.3):
        cage.add(rod((x, 0.0, 0.65), (x, 2.8, 0.65), 0.075, 4))
        cage.add(rod((x, 2.8, 0.65), (x, 2.8, -0.65), 0.075, 4))
    return [("Bottles", "steel_light", bt), ("Valves", "brass", valves), ("Cage", "charcoal", cage)]


@prop("ElectricMeter")
def electric_meter(rng):
    """The electricity meter in its box on the wall, a dial window, the conduit stub."""
    box = bevel_box(1.4, 2.0, 0.6, 0.08, c=(0, 0, 0.3))
    door = bevel_box(1.3, 1.9, 0.15, 0.04, c=(0, 0, 0.62))
    win = _cyl_y(0.35, 0.0, 0.15, 10).xf(RX(90)).xf(T(0, 0.35, 0.72))
    seal = bevel_box(0.15, 0.3, 0.15, 0.03, c=(0.5, -0.6, 0.72))
    return [("Box", "grey", box), ("Door", "grey_light", door), ("Window", "glass", win, GLASS), ("Seal", "red", seal)]


@prop("RoofAC")
def roof_ac(rng):
    """A rooftop air conditioner on rails: louvred sides, the fan grille on top."""
    body = bevel_box(4.0, 2.2, 3.0, 0.15, c=(0, 1.5, 0))
    louv = G.Geo()
    for i in range(6):
        louv.add(bevel_box(3.6, 0.15, 0.15, 0.03, c=(0, 0.75 + 0.25 * i, 1.52)))
    rails = G.Geo()
    for z in (-1.1, 1.1):
        rails.add(bevel_box(4.6, 0.4, 0.4, 0.06, c=(0, 0.2, z)))
    grille = G.Geo()
    grille.add(G.torus(1.0, 0.1, 12, 4, "y", (0, 2.65, 0)))
    for a in (0, 45, 90, 135):
        grille.add(bevel_box(2.0, 0.15, 0.15, 0.03, c=(0, 2.65, 0)).xf(RY(a)))
    return [("Body", "grey_light", body), ("Louvres", "grey", louv), ("Rails", "galv_dark", rails),
            ("Grille", "charcoal", grille)]


@prop("RoofVent")
def roof_vent(rng):
    """A mushroom vent on its upstand."""
    base = bevel_box(1.2, 0.4, 1.2, 0.06, c=(0, 0.2, 0))
    pipe = _cyl_y(0.35, 0.4, 1.4, 8)
    cap = _lathe([(0.0, 1.35), (0.7, 1.35), (0.6, 1.6), (0.0, 1.75)], 8)
    return [("Base", "galv_dark", base), ("Pipe", "galv", pipe), ("Cap", "galv", cap)]


@prop("TVAerial")
def tv_aerial(rng):
    """An old Yagi TV aerial on a lashed mast, slightly bent, pointing at a town far away."""
    mast = _cyl_y(0.12, 0.0, 7.0, 6)
    boom = rod((0, 6.6, -1.6), (0, 6.6, 1.8), 0.08, 4)
    els = G.Geo()
    for i, z in enumerate(np.linspace(-1.4, 1.6, 6)):
        w = 1.6 - 0.15 * i
        els.add(rod((-w / 2, 6.6, z), (w / 2, 6.6 + (0.15 if i == 4 else 0.0), z), 0.075, 4))
    stays = G.Geo()
    for a in (30, 150, 270):
        r = math.radians(a)
        stays.add(rod((0, 4.0, 0), (2.6 * math.cos(r), 0.05, 2.6 * math.sin(r)), 0.075, 4))
    foot = bevel_box(0.8, 0.3, 0.8, 0.05, c=(0, 0.15, 0))
    return [("Mast", "galv", mast), ("Boom", "galv", boom), ("Elements", "galv", els), ("Stays", "galv_dark", stays),
            ("Foot", "galv_dark", foot)]


@prop("WallLadder")
def wall_ladder(rng):
    """A galvanised fixed ladder up the back wall to the roof, with hoops at the top."""
    g = G.Geo()
    for x in (-0.7, 0.7):
        g.add(rod((x, 0.0, 0.5), (x, 14.0, 0.5), 0.1, 6))
        g.add(rod((x, 3.0, 0.0), (x, 3.0, 0.5), 0.08, 4))
        g.add(rod((x, 10.0, 0.0), (x, 10.0, 0.5), 0.08, 4))
    for y in np.arange(0.8, 13.6, 0.8):
        g.add(rod((-0.7, y, 0.5), (0.7, y, 0.5), 0.075, 4))
    for y in (11.0, 12.6):
        g.add(G.tube([(-0.7, y, 0.5), (-0.9, y, 1.3), (0.0, y, 1.6), (0.9, y, 1.3), (0.7, y, 0.5)], 0.075, 4))
    return [("Ladder", "galv", g)]


@prop("HoseReel")
def hose_reel(rng):
    """A wall hose reel with the green hose wound on it and the nozzle hanging."""
    bracket = bevel_box(0.8, 1.2, 0.3, 0.05, c=(0, 0, 0.15))
    drum = ccyl(0.7, 0.6, 12, "z", (0, 0, 0.6), 0.06)
    hose = G.torus(0.6, 0.15, 12, 6, "z", (0, 0, 0.6))
    hang = G.tube([(0.6, -0.1, 0.65), (0.75, -0.9, 0.7), (0.6, -1.5, 0.75)], 0.12, 6)
    nozzle = ccyl(0.15, 0.4, 6, "y", (0.6, -1.7, 0.75), 0.03)
    return [("Bracket", "steel_dark", bracket), ("Drum", "grey", drum), ("Hose", "label_green", hose),
            ("Hang", "label_green", hang), ("Nozzle", "brass", nozzle)]


# ---------------------------------------------------------------- the yard

@prop("Pallet")
def pallet(rng):
    """A wooden pallet (4 x 4): deck boards on three runners, one board split."""
    g = G.Geo()
    for i in range(5):
        g.add(bevel_box(4.0, 0.15, 0.6, 0.03, c=(0, 0.48, -1.65 + 0.82 * i)))
    for x in (-1.7, 0.0, 1.7):
        g.add(bevel_box(0.5, 0.4, 4.0, 0.04, c=(x, 0.2, 0)))
    g.add(bevel_box(1.6, 0.15, 0.6, 0.03, c=(1.2, 0.56, 1.65)).xf(RZ(4)))
    return [("Pallet", "wood_light", g)]


@prop("Crate")
def crate(rng):
    """A slatted wooden crate (studded lid: a built surface), stencil band."""
    g = G.Geo()
    for i in range(3):
        g.add(bevel_box(2.4, 0.5, 2.4, 0.05, c=(0, 0.3 + 0.62 * i, 0)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.add(bevel_box(0.3, 1.9, 0.3, 0.04, c=(sx * 1.1, 0.95, sz * 1.1)))
    lid = bevel_box(2.5, 0.2, 2.5, 0.05, c=(0, 1.95, 0))
    band = bevel_box(1.4, 0.4, 0.15, 0.03, c=(0, 1.0, 1.23))
    return [("Crate", "wood", g), ("Lid", "wood_light", lid), ("Stencil", "black", band)]


@prop("TyreStack")
def tyre_stack(rng):
    """Old tyres, three stacked and one leaning on them."""
    t = G.Geo()
    for i in range(3):
        t.add(G.torus(0.95, 0.4, 12, 6, "y", (rng.uniform(-0.1, 0.1), 0.4 + 0.8 * i, rng.uniform(-0.1, 0.1))))
    t.add(G.torus(0.95, 0.4, 12, 6, "z", (0, 0, 0)).xf(RX(-18)).xf(T(0.2, 1.3, 1.6)))
    return [("Tyres", "tyre", t)]


@prop("BrokenChair")
def broken_chair(rng):
    """A plastic garden chair on its back, one leg snapped off and lying beside it."""
    seat = bevel_box(1.6, 0.2, 1.5, 0.08, c=(0, 0, 0))
    back = bevel_box(1.6, 1.6, 0.2, 0.08, c=(0, 0.8, -0.7))
    legs = G.Geo()
    for (x, z, ln) in ((-0.65, 0.6, 1.5), (0.65, 0.6, 1.5), (0.65, -0.6, 1.5), (-0.65, -0.6, 0.6)):
        legs.add(rod((x, -0.1, z), (x, -0.1 - ln, z), 0.1, 6))
    chair = G.Geo()
    chair.add(seat)
    chair.add(back)
    chair.add(legs)
    chair = chair.xf(RX(-100)).xf(T(0, 0.9, 0))
    snapped = rod((1.4, 0.12, 0.6), (2.2, 0.12, 0.9), 0.1, 6)
    return [("Chair", "label_white", chair), ("Leg", "label_white", snapped)]


@prop("DogBowl")
def dog_bowl(rng):
    """An empty steel dog bowl, and the chain from its stake, lying in the dirt."""
    bowl = _lathe([(0.0, 0.0), (0.45, 0.0), (0.6, 0.35), (0.5, 0.35), (0.38, 0.08), (0.0, 0.08)], 10)
    stake = G.Geo()
    stake.add(_cyl_y(0.12, 0.0, 0.6, 6, x=1.6, z=-0.8))
    stake.add(G.torus(0.2, 0.075, 8, 4, "y", (1.6, 0.6, -0.8)))
    chain = G.Geo()
    pts = [(1.6, 0.55, -0.8), (1.1, 0.08, -0.4), (0.6, 0.08, 0.3), (0.1, 0.08, 1.0), (-0.6, 0.08, 1.3)]
    chain.add(G.tube(pts, 0.075, 4))
    for i in range(8):
        t = i / 7
        p = np.array(pts[0]) * (1 - t) + np.array(pts[-1]) * t
        chain.add(G.torus(0.15, 0.075, 6, 4, "x" if i % 2 else "z", (p[0], 0.15, p[2])))
    collar = G.torus(0.35, 0.1, 10, 4, "y", (-0.75, 0.1, 1.35))
    return [("Bowl", "steel", bowl), ("Stake", "steel_dark", stake), ("Chain", "steel_dark", chain),
            ("Collar", "red", collar)]


@prop("FuelCan")
def fuel_can(rng):
    """A red jerry can: three handles, the spout cap, stamped panels."""
    body = bevel_box(0.9, 1.5, 0.5, 0.1, c=(0, 0.75, 0))
    panel = G.Geo()
    for sz in (-1, 1):
        panel.add(G.extrude([(-0.35, -0.5), (0.35, -0.5), (0.0, 0.5)], 0.15, "z", (0, 0.7, sz * 0.25)))
    handles = G.Geo()
    for x in (-0.25, 0.0, 0.25):
        handles.add(rod((x, 1.5, -0.15), (x, 1.5, 0.15), 0.075, 4))
        handles.add(rod((x, 1.5, 0.0), (x, 1.68, 0.0), 0.075, 4))
    spout = _cyl_y(0.12, 1.45, 1.75, 6, x=0.38)
    return [("Can", "fuel_red", body), ("Panels", "red_dark", panel), ("Handles", "fuel_red", handles),
            ("Spout", "black", spout)]


@prop("CableReel")
def cable_reel(rng):
    """An extension lead on its reel, half unwound, the socket box on the end."""
    reel = G.Geo()
    for z in (-0.35, 0.35):
        reel.add(ccyl(0.75, 0.15, 12, "z", (0, 0.8, z), 0.04))
    reel.add(ccyl(0.4, 0.6, 10, "z", (0, 0.8, 0), 0.04))
    frame = G.Geo()
    for z in (-0.5, 0.5):
        frame.add(G.tube([(-0.6, 0.0, z), (0.0, 0.85, z), (0.6, 0.0, z)], 0.075, 4))
    frame.add(rod((0, 0.85, -0.55), (0, 0.85, 0.55), 0.08, 4))
    wound = ccyl(0.62, 0.55, 12, "z", (0, 0.8, 0), 0.04)
    return [("Reel", "fuel_red", reel), ("Frame", "charcoal", frame), ("Lead", "mustard", wound)]


@prop("OilDrum")
def oil_drum(rng):
    """A steel drum, a rust stain down one side, ribs, the bung on top."""
    d = _lathe([(0.0, 0.0), (0.95, 0.0), (1.0, 0.1), (1.0, 2.9), (0.95, 3.0), (0.0, 3.0)], 12)
    ribs = G.Geo()
    for y in (1.0, 2.0):
        ribs.add(_lathe([(1.0, y - 0.075), (1.05, y - 0.075), (1.05, y + 0.075), (1.0, y + 0.075)], 12))
    bung = _cyl_y(0.15, 3.0, 3.15, 6, x=0.5)
    rust = bevel_box(0.6, 1.2, 0.15, 0.04, c=(0, 1.6, 0.98))
    return [("Drum", "label_blue", d), ("Ribs", "label_blue", ribs), ("Bung", "steel_dark", bung), ("Rust", "rust", rust)]


@prop("Wheelbarrow")
def wheelbarrow(rng):
    """A tipped-over wheelbarrow with a flat tyre."""
    tray = G.Geo()
    tray.add(chamfer_slab([(-1.0, -1.4), (1.0, -1.4), (1.3, 1.2), (-1.3, 1.2)], 0.15, 0.04))
    for sx in (-1, 1):
        tray.add(bevel_box(0.15, 0.9, 2.6, 0.04, c=(sx * 1.15, 0.45, 0)).xf(RZ(sx * -12)))
    tray.add(bevel_box(2.6, 0.9, 0.15, 0.04, c=(0, 0.45, 1.25)))
    hands = G.Geo()
    for sx in (-1, 1):
        hands.add(rod((sx * 0.8, 0.0, 0.8), (sx * 1.0, 0.0, -2.8), 0.1, 6))
    wheel = ccyl(0.55, 0.3, 10, "x", (0, -0.2, 1.9), 0.06)
    g = G.Geo()
    g.add(tray)
    g.add(hands)
    return [("Tray", "trim_green", g.xf(RZ(95)).xf(T(0.2, 1.4, 0))), ("Wheel", "tyre", wheel.xf(RZ(95)).xf(T(0.2, 1.4, 0)))]


@prop("LogPile")
def log_pile(rng):
    """Split oak for the oven, stacked against the wall under a corrugated lean-to sheet."""
    logs, ends = G.Geo(), G.Geo()
    for row in range(4):
        for i in range(6 - (row % 2)):
            x = -2.5 + i * 1.0 + 0.5 * (row % 2)
            y = 0.4 + row * 0.75
            logs.add(ccyl(0.38, 2.0, 7, "z", (x, y, 0), 0.06))
            ends.add(ccyl(0.3, 0.15, 7, "z", (x, y, 1.0), 0.03))
    roof = corrugated(6.6, 2.8, 0.8, 0.15).xf(RX(-12)).xf(T(0, 3.8, 0.1))
    posts = G.Geo()
    for x in (-3.1, 3.1):
        posts.add(bevel_box(0.3, 3.8, 0.3, 0.04, c=(x, 1.9, 1.15)))
    return [("Logs", "trunk", logs), ("Ends", "wood_pale", ends), ("Sheet", "galv_dark", roof), ("Posts", "wood_dark", posts)]


@prop("Weeds")
def weeds(rng):
    """A clump of tall weeds and a thistle along a fence line."""
    g, heads = G.Geo(), G.Geo()
    for i in range(9):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.0, 0.8)
        h = rng.uniform(0.8, 2.2)
        x, z = r * math.cos(a), r * math.sin(a)
        g.add(G.tube([(x, 0.0, z), (x * 1.3, h * 0.6, z * 1.3 + 0.1), (x * 1.5 + 0.1, h, z * 1.5)], 0.075, 4))
        if i % 3 == 0:
            heads.add(_lathe([(0, 0), (0.2, 0.1), (0.15, 0.3), (0, 0.35)], 6).xf(T(x * 1.5 + 0.1, h, z * 1.5)))
    return [("Stems", "grass_dry", g), ("Heads", "deadwood", heads)]


@prop("Cone")
def cone(rng):
    """A traffic cone, scuffed, one reflective band."""
    c = _lathe([(0.0, 0.2), (0.45, 0.2), (0.12, 2.0), (0.0, 2.0)], 10)
    base = bevel_box(1.1, 0.2, 1.1, 0.05, c=(0, 0.1, 0))
    band = _lathe([(0.3, 0.9), (0.34, 0.9), (0.26, 1.25), (0.22, 1.25)], 10)
    return [("Cone", "reflector", c), ("Base", "black", base), ("Band", "sign_white", band)]


@prop("Tarp")
def tarp(rng):
    """A blue tarp thrown over a lumpy stack, tied down with rope, a corner flapping up."""
    g = G.Geo()
    g.add(G.blob(1.0, 9, 5, (1.6, 0.9, 1.2), 0.12, int(rng.integers(0, 100)), (0, 0.85, 0), 0.0))
    rope = G.Geo()
    for z in (-0.5, 0.5):
        rope.add(G.tube([(-1.65, 0.0, z), (-1.2, 1.15, z), (0.0, 1.62, z), (1.2, 1.15, z), (1.65, 0.0, z)], 0.075, 4))
    return [("Tarp", "tarp_blue", g), ("Rope", "jute", rope)]


@prop("MileMarker")
def mile_marker(rng):
    """A green mile post by the road."""
    post = bevel_box(0.5, 2.6, 0.3, 0.05, c=(0, 1.3, 0))
    plate = bevel_box(0.6, 1.0, 0.15, 0.04, c=(0, 2.0, 0.2))
    return [("Post", "galv_dark", post), ("Plate", "sign_green", plate)]


@prop("Mailbox")
def mailbox(rng):
    """A rural mailbox on a leaning post at the farm track, its flag down."""
    post = bevel_box(0.4, 3.6, 0.4, 0.05, c=(0, 1.8, 0)).xf(RZ(4))
    box = G.Geo()
    box.add(bevel_box(0.8, 0.6, 1.6, 0.08, c=(0.1, 3.9, 0)))
    box.add(ccyl(0.4, 1.6, 10, "z", (0.1, 4.2, 0), 0.06))
    flag = bevel_box(0.15, 0.6, 0.3, 0.03, c=(0.55, 4.0, -0.3))
    return [("Post", "wood_dark", post), ("Box", "grey", box), ("Flag", "red", flag)]


@prop("Tufts")
def tufts(rng):
    """Grass tufts in a darker green, in a ragged ring."""
    g = G.Geo()
    for i in range(7):
        a = math.tau * i / 7 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.3, 1.0)
        x, z = r * math.cos(a), r * math.sin(a)
        for j in range(3):
            b = math.tau * j / 3 + i
            g.add(rod((x, 0.0, z), (x + 0.25 * math.cos(b), rng.uniform(0.6, 1.0), z + 0.25 * math.sin(b)), 0.075, 4))
    return [("Tufts", "grass2", g)]
