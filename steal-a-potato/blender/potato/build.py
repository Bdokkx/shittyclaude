"""Assemble the scene: PotatoBuild/PotatoMap (goes to Workspace) and PotatoBuild/PotatoKit (goes
to ReplicatedStorage).

    from potato import build; sc = build.build()
"""
import numpy as np

import spslib
from spsgeo import CF

from . import layout as L
from . import mound as MD
from . import structure
from . import yard
from .kit import Kit, facing
from .areas import meadow, dunes

AREA_MODULES = {1: meadow, 2: dunes}


def build(areas=None, kit=True, roots=True, seed=7, showcase=False):
    sc = spslib.Scene("PotatoBuild")
    k = Kit(sc)
    rng = np.random.default_rng(seed)
    pm = sc.model(sc.root, "PotatoMap")
    markers = sc.folder(pm, "Markers")
    yf = sc.folder(pm, "Yard")
    structure.yard_shell(k, yf)
    structure.gate(k, pm, markers)
    fields = sc.folder(pm, "Fields")
    shells = structure.fields_shell(k, fields, markers)
    sc.area_info = {}
    for n in range(1, L.N_AREAS + 1):
        af, am = shells[n]
        mod = AREA_MODULES.get(n) if areas is None or n in areas else None
        arng = np.random.default_rng(seed * 100 + n)
        a = mod.build(k, n, af, am, arng) if mod else None
        tucked = a.tucked if a else []
        avoid = [(x, z, r + 3.0) for (x, z, r) in (a.taken if a else [])]
        spots = MD.place(n, arng, tucked, avoid)
        for (x, z) in spots:
            MD.mound(k, am, CF((x, 0.0, z), facing(0.0, 1.0) if x < 0 else facing(0.0, 1.0)))
        sc.area_info[n] = dict(spots=spots, tucked=tucked, taken=a.taken if a else [])
    yard.build(k, pm, markers, rng)
    pm.p["primary"] = yf.find("Avenue")
    kf = sc.folder(sc.root, "PotatoKit")
    if showcase:                       # preview renders only
        from . import kitparts
        kitparts.showcase(k, kf)
    elif kit:
        from . import kitparts
        kitparts.build(k, kf)
    if roots:
        from . import roots as R
        R.build(k, kf)
    sc.kit = k
    return sc
