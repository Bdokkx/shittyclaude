"""October props: pumpkins and jack-o'-lanterns, hay bales, a scarecrow, corn stalks, fallen leaves.
Same conventions as props.py: built in the current local frame, origin on the ground, front = -Z."""
import math
import random

ORANGE = ("#FF8A1F", "#F07412", "#FFA23F")
STEM = "#5B7A2E"
VINE = "#4F8A2E"
LEAF = "#5E9E34"
GLOW = "#FFC93C"
HAY = ("#E8C25A", "#D9AE45")
TWINE = "#B98F32"
SOIL = ("#5A3A22", "#6E4A2C")
LEAVES = ("#E8622A", "#F2A22A", "#C9402A", "#FFC23D")
PURPLE = "#5B2A86"


def pumpkin(m, s=1.0, seed=0, carved=False, light=True, colors=ORANGE):
    """Ribbed pumpkin ~2.6*s wide: core, two crossing lobes, top cap, curly stem and a leaf.
    carved=True adds a glowing jack-o'-lantern face on the front (-Z) with an optional PointLight.
    Returns the core part (use it as the model's PrimaryPart)."""
    rng = random.Random(seed)
    h = 1.9 * s
    core = m.box((0, h / 2, 0), (2.2 * s, h, 2.2 * s), colors[0])
    core["name"] = "Body"
    m.box((0, h * 0.46, 0), (2.7 * s, h * 0.8, 1.5 * s), colors[1])
    m.box((0, h * 0.46, 0), (1.5 * s, h * 0.8, 2.7 * s), colors[1])
    m.box((0, h * 0.5, 0), (2.4 * s, h * 0.7, 2.4 * s), colors[2], ry=45)
    m.box((0, h + 0.05 * s, 0), (1.3 * s, 0.25 * s, 1.3 * s), colors[1])
    with m.ctx(collide=False, shadow=False):
        m.box((0.05 * s, h + 0.45 * s, 0), (0.35 * s, 0.8 * s, 0.35 * s), STEM, rz=rng.uniform(-14, 14))
        m.box((0.45 * s, h + 0.2 * s, 0.3 * s), (0.9 * s, 0.12 * s, 0.6 * s), LEAF, ry=rng.uniform(0, 90), rz=-12)
        if carved:
            zf = -1.36 * s
            for x in (-0.42, 0.42):
                m.box((x * s, h * 0.66, zf), (0.42 * s, 0.42 * s, 0.1), GLOW, mat="Neon", rz=45)
            m.box((0, h * 0.45, zf), (0.3 * s, 0.3 * s, 0.1), GLOW, mat="Neon", rz=45)       # nose
            m.box((0, h * 0.24, zf), (1.1 * s, 0.26 * s, 0.1), GLOW, mat="Neon",
                  light=("PointLight", 1.4, 12, "#FFB347") if light else None)
            for x in (-0.3, 0.3):                                                     # teeth gaps
                m.box((x * s, h * 0.32, zf - 0.02), (0.18 * s, 0.14 * s, 0.1), colors[1])
    return core


def pumpkin_pile(m, seed, n=3, carved_first=True):
    """One big pumpkin with smaller ones leaning against it."""
    rng = random.Random(seed)
    pumpkin(m, 1.1, seed, carved=carved_first)
    for k in range(n - 1):
        a = rng.uniform(0, 6.28) if k == 0 else a + rng.uniform(1.6, 2.6)
        with m.at((math.cos(a) * 2.3, 0, math.sin(a) * 2.3), ry=rng.uniform(0, 90)):
            pumpkin(m, rng.uniform(0.5, 0.7), seed * 3 + k)


def hay_bale(m, ry=0, w=4.2, top=None, seed=0):
    """Rectangular bale with twine bands; top: callable placed on top (a pumpkin, a lantern...)."""
    with m.at((0, 0, 0), ry=ry):
        m.box((0, 1.1, 0), (w, 2.2, 2.6), HAY[0])
        m.box((0, 1.1, 0), (w - 0.6, 2.3, 2.7), HAY[1])
        for x in (-w / 4, w / 4):
            m.box((x, 1.1, 0), (0.25, 2.35, 2.75), TWINE)
        with m.ctx(collide=False, shadow=False):
            rng = random.Random(seed)
            for k in range(4):                          # loose straws
                m.box((rng.uniform(-w / 2, w / 2), 2.25, rng.uniform(-1, 1)), (0.12, 0.12, 1.2), HAY[0],
                      ry=rng.uniform(0, 180), rz=rng.uniform(-10, 10))
        if top:
            with m.at((0, 2.2, 0)):
                top(m)


def scarecrow(m, seed=0):
    """Post + crossbar, plaid shirt, patched trousers, sack head with a pointy hat, straw hands."""
    wood = "#6B4226"
    m.box((0, 3.5, 0), (0.6, 7.0, 0.6), wood)
    m.box((0, 5.4, 0), (5.6, 0.5, 0.5), wood)
    with m.ctx(collide=False):
        m.box((0, 4.6, 0), (2.4, 2.4, 1.3), "#C9402A")                 # shirt
        for x in (-0.6, 0.6):
            m.box((x, 4.6, -0.68), (0.2, 2.4, 0.05), "#8E2A1E")
        m.box((0, 4.2, -0.68), (2.4, 0.2, 0.05), "#8E2A1E")
        for s in (-1, 1):
            m.box((s * 2.0, 5.4, 0), (1.8, 0.9, 0.9), "#C9402A")      # sleeves
            m.box((s * 3.05, 5.3, 0), (0.5, 0.7, 0.6), HAY[0], rz=-s * 20)
        m.box((0, 3.1, 0), (2.2, 0.8, 1.2), "#3E5C99")                 # trousers
        for x in (-0.6, 0.6):
            m.box((x, 2.2, 0), (0.9, 1.6, 1.0), "#3E5C99")
            m.box((x, 1.3, 0), (0.6, 0.5, 0.6), HAY[0])
        m.box((0.6, 2.4, -0.52), (0.5, 0.5, 0.05), "#E8C25A")          # patch
        m.box((0, 6.5, 0), (1.8, 1.8, 1.6), "#E8D3A0")                 # sack head
        m.box((0, 5.75, 0), (1.2, 0.3, 1.2), TWINE)
        for x in (-0.4, 0.4):
            m.box((x, 6.75, -0.82), (0.32, 0.32, 0.05), "#2A1E14")
        m.box((0, 6.15, -0.82), (0.9, 0.14, 0.05), "#2A1E14")
        m.box((0, 7.5, 0), (3.0, 0.25, 3.0), "#3A2A1E")                # hat
        m.box((0, 8.1, 0), (1.6, 1.0, 1.6), "#3A2A1E")
        m.box((0.2, 8.85, 0.1), (0.9, 0.7, 0.9), "#3A2A1E", rz=-18)
        m.box((0, 7.75, 0), (1.7, 0.3, 1.7), PURPLE)


def corn_stalk(m, seed, h=None):
    rng = random.Random(seed)
    h = h or rng.uniform(5.5, 7.5)
    with m.ctx(collide=False):
        m.box((0, h / 2, 0), (0.4, h, 0.4), "#C9B458", rz=rng.uniform(-4, 4))
        for k in range(3):
            y = h * (0.35 + 0.2 * k)
            a = rng.uniform(0, 180)
            with m.at((0, y, 0), ry=a):
                m.box((0.9, 0.2, 0), (1.8, 0.12, 0.45), "#B8A24A", rz=-25)
        m.box((0.3, h * 0.6, 0), (0.45, 1.3, 0.45), "#F2C23D", rz=-15)  # cob
        m.box((0, h + 0.4, 0), (0.25, 0.9, 0.25), "#D9B85A")


def leaf_litter(m, seed, n=None):
    """A few flat fallen leaves overlapping on the ground."""
    rng = random.Random(seed)
    n = n or rng.randint(4, 7)
    with m.ctx(collide=False, shadow=False):
        for k in range(n):
            a = rng.uniform(0, 6.28)
            r = rng.uniform(0, 1.3)
            m.box((math.cos(a) * r, 0.06 + 0.03 * k, math.sin(a) * r), (0.9, 0.06, 0.6), rng.choice(LEAVES),
                  ry=rng.uniform(0, 180))


def soil_row(m, length, seed):
    """Raised tilled soil strip along X, centred on the origin."""
    rng = random.Random(seed)
    m.box((0, 0.2, 0), (length, 0.4, 2.2), SOIL[0])
    with m.ctx(collide=False, shadow=False):
        x = -length / 2 + 1.0
        while x < length / 2 - 1.0:
            m.box((x, 0.45, rng.uniform(-0.4, 0.4)), (1.4, 0.12, 0.8), SOIL[1], ry=rng.uniform(-20, 20))
            x += rng.uniform(1.8, 2.6)
