"""Reports pairs of differently-coloured boxes in an asset whose faces lie in the
same plane, face the same way and overlap -> visible z-fighting in Roblox."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gen"))
from assets import ASSETS

def ov(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0) > 1e-6

bad = 0
for name, a in ASSETS.items():
    bx = a["boxes"]
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            p, q = bx[i], bx[j]
            if p[6] == q[6]:
                continue
            for ax in range(3):
                o = [k for k in range(3) if k != ax]
                if not all(ov(p[k], p[k + 3], q[k], q[k + 3]) for k in o):
                    continue
                for side in (0, 3):
                    ground = min(b[1] for b in bx)
                    if ax == 1 and side == 0 and abs(q[1] - ground) < 1e-6:
                        continue  # both resting on the ground: hidden
                    if abs(p[ax + side] - q[ax + side]) < 1e-6:
                        bad += 1
                        print(f"{name}: box {i} ({p[6]}) & {j} ({q[6]}) share {'xyz'[ax]}{'-+'[side//3]} face")
print("z-fight pairs:", bad)
