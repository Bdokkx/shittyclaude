"""Everything that opens, one contract.

An openable is a Model holding every part that moves (and only those). Its PrimaryPart's
pivot (so the Model's pivot) sits on the hinge or slide line, and the Model is built SHUT.
Attributes on the Model:

  Opens      "Swing" or "Slide"
  OpenAngle  Swing: degrees about the pivot's Y (signed; the sign that takes the door away
             from whoever stands at it, into the room)
  OpenAxis   "X" for a lid or a drop-down door: OpenAngle is then about the pivot's X
  OpenOffset Slide: Vector3 in the pivot's space (a drawer: 0, 0, 1.8, straight out)
  OpenSound  "Cabinet", "Drawer", "Fridge", "Metal", "Lid" or "Locker"
  Locked     true when it will not open (yet)
  OpenLabel  the prompt text, where "Open" is not the right word

Open = Model:PivotTo(closed * CFrame.Angles(0, rad(OpenAngle), 0)) (or about X), or
closed * CFrame.new(OpenOffset) for a slide. A marker named Stash is where an item can be
put: inside a drawer Model it rides with the drawer; in a cupboard it stays put and its
attribute Behind names the door Model in front of it."""
import numpy as np

import spsgeo as G
from spsgeo import CF

SOUNDS = ("Cabinet", "Drawer", "Fridge", "Metal", "Lid", "Locker")


def opener(k, parent, name, kind, sound, angle=None, axis=None, offset=None, locked=False, label=None):
    assert kind in ("Swing", "Slide") and sound in SOUNDS, (name, kind, sound)
    m = k.sc.model(parent, name)
    k.attr(m, "Opens", kind)
    if kind == "Swing":
        assert angle is not None, name
        k.attr(m, "OpenAngle", float(round(angle, 3)))
        if axis:
            assert axis in ("X", "Y"), axis
            if axis == "X":
                k.attr(m, "OpenAxis", "X")
    else:
        assert offset is not None and len(offset) == 3, name
        k.attr(m, "OpenOffset", tuple(float(round(v, 4)) for v in offset))
    k.attr(m, "OpenSound", sound)
    if locked:
        k.attr(m, "Locked", True)
    if label:
        k.attr(m, "OpenLabel", label)
    return m


def hinge(m, part, world_cf):
    """Make `part` the Model's PrimaryPart with its pivot (the Model's pivot) at world_cf."""
    assert part.parent is m or any(a is m for a in _ancestors(part)), (m.name, part.name)
    m.p["primary"] = part
    part.p["pivot"] = part.p["cf"].inv() * world_cf


def _ancestors(n):
    while n.parent is not None:
        n = n.parent
        yield n


def is_openable(m):
    return m.kind == "Model" and "Opens" in (m.p.get("attrs") or {})


def world_pivot(m):
    prim = m.p["primary"]
    return prim.p["cf"] * prim.p["pivot"]


def open_tf(m, f=1.0):
    """World transform taking the shut Model to f of the way open (new = tf * old)."""
    a = m.p["attrs"]
    P = world_pivot(m)
    if a["Opens"] == "Slide":
        off = np.asarray(a["OpenOffset"], float) * f
        return CF(P.R @ off)
    ang = a["OpenAngle"] * f
    R = G.rx(ang) if a.get("OpenAxis") == "X" else G.ry(ang)
    return P * CF(R=R) * P.inv()


def stash(k, parent, cf_, size, behind=None):
    """A Stash marker: item spawn place on the floor of a cupboard / drawer, looking out;
    StashSize = the clear space there (width, height, depth)."""
    mk = k.sc.marker(parent, "Stash", cf_)
    k.attr(mk, "StashSize", tuple(float(round(v, 2)) for v in size))
    if behind:
        k.attr(mk, "Behind", behind)
    return mk


def apply_open(sc, match="all", f=1.0):
    """Leave the openables open in the scene (for renders): match = 'all' or comma-separated
    path fragments."""
    keys = None if match in ("all", "1", "") else match.split(",")
    for m in [m for m in sc.nodes("Model") if is_openable(m)]:
        path = m.path()
        if keys is not None and not any(k_ in path for k_ in keys):
            continue
        T_ = open_tf(m, f)
        for n in m.walk():
            if n.kind in ("Part", "MeshPart", "Marker") and n is not m:
                n.p["cf"] = T_ * n.p["cf"]


def adopt(k, parent, name, part, others, kind, sound, **kw):
    """Make an openable Model `name` under `parent` out of parts already built: `part` (its
    pivot already on the hinge) becomes the PrimaryPart, `others` ride with it. Welds between
    them go (the Model moves as one) and everything stays anchored."""
    om = opener(k, parent, name, kind, sound, **kw)
    for n in [part] + list(others):
        n.parent.children.remove(n)
        n.parent = om
        om.children.append(n)
        n.children = [c for c in n.children if c.kind != "Weld"]
        n.p["anchored"] = True
        n.p["massless"] = False
    assert part.p.get("pivot") is not None, name
    om.p["primary"] = part
    return om


def from_prop(k, prop_model, name, part_names, hinge_cf, kind, sound, **kw):
    """Turn named parts of a prop Model into an openable child Model hinged at hinge_cf (world)."""
    parts = [c for c in prop_model.children if c.name in part_names]
    assert parts, (prop_model.name, part_names)
    first = next(c for c in parts if c.name == part_names[0])
    first.p["pivot"] = first.p["cf"].inv() * hinge_cf
    if prop_model.p.get("primary") in parts:
        rest_ = [c for c in prop_model.children if c not in parts and c.kind in ("Part", "MeshPart")]
        prop_model.p["primary"] = rest_[0] if rest_ else None
    return adopt(k, prop_model, name, first, [c for c in parts if c is not first], kind, sound, **kw)
