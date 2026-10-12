"""Classic R6 bodies for batch 2, in Roblox space (feet on the ground at the origin, facing -Z).

Every rigged character uses exactly the R6 part names, Motor6D names, parents and
C0/C1 frames, so one set of R6 animations plays on players, customers, the Watcher and
the Inspector. Bigger characters scale the joint offsets with the parts; the joint
frames keep the standard R6 orientations, so rotations play the same.

    RootJoint        HumanoidRootPart -> Torso   C0 = C1 = Angles(-90, 0, 180)
    Neck             Torso -> Head               C0 (0, TH/2, 0)        C1 (0, -HH/2, 0)
    Right Shoulder   Torso -> Right Arm          C0 (TW/2, TH/2 - k, 0) C1 (-AW/2, AL/2 - k, 0)
    Left Shoulder    Torso -> Left Arm           mirrored
    Right Hip        Torso -> Right Leg          C0 (TW/2, -TH/2, 0)    C1 (LW/2, LH/2, 0)
    Left Hip         Torso -> Left Leg           mirrored

(standard R6: TW 2, TH 2, AW 1, AL 2, LW 1, LH 2, HH 1, k 0.5)
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

R_ROOT = np.array(((-1, 0, 0), (0, 0, 1), (0, 1, 0)), float)      # RootJoint, Neck
R_RIGHT = np.array(((0, 0, 1), (0, 1, 0), (-1, 0, 0)), float)     # Right Shoulder, Right Hip
R_LEFT = np.array(((0, 0, -1), (0, 1, 0), (1, 0, 0)), float)      # Left Shoulder, Left Hip
R_GRIP = G.rx(-90)                                                 # Left/RightGripAttachment

HEAD_SCALE = 1.25        # the classic head: SpecialMesh MeshType Head, Scale 1.25


class Body:
    """Part sizes of an R6 body. `k` is how far below the torso top the shoulder pivots."""

    def __init__(self, torso=(2, 2, 1), arm=(1, 2, 1), leg=(1, 2, 1), head=(2, 1, 1), k=0.5):
        self.torso, self.arm, self.leg, self.head = (tuple(float(v) for v in x) for x in (torso, arm, leg, head))
        self.k = float(k)

    @staticmethod
    def scaled(s, arm_len=1.0, width=1.0, depth=1.0, limb_w=1.0, head=1.0):
        """R6 scaled by s in height; width/depth scale the torso and legs on top of s,
        limb_w the arm thickness, arm_len the arm length, head the head part."""
        return Body(torso=(2 * s * width, 2 * s, s * depth), arm=(s * limb_w, 2 * s * arm_len, s * depth * limb_w),
                    leg=(s * width, 2 * s, s * depth), head=(2 * s * head, s * head, s * head), k=0.5 * s)

    # -- where everything goes (standing pose, origin = feet centre on the ground)
    def cfs(self, origin=CF()):
        TW, TH, TD = self.torso
        AW, AL, AD = self.arm
        LW, LH, LD = self.leg
        HW, HH, HD = self.head
        ty = LH + TH / 2
        loc = {
            "HumanoidRootPart": (0, ty, 0), "Torso": (0, ty, 0), "Head": (0, LH + TH + HH / 2, 0),
            "Left Arm": (-(TW / 2 + AW / 2), LH + TH - AL / 2, 0), "Right Arm": (TW / 2 + AW / 2, LH + TH - AL / 2, 0),
            "Left Leg": (-(TW / 2 - LW / 2), LH / 2, 0), "Right Leg": (TW / 2 - LW / 2, LH / 2, 0),
        }
        return {k: origin * CF(v) for k, v in loc.items()}

    def size(self, name):
        return {"HumanoidRootPart": self.torso, "Torso": self.torso, "Head": self.head, "Left Arm": self.arm,
                "Right Arm": self.arm, "Left Leg": self.leg, "Right Leg": self.leg}[name]

    def joints(self):
        """(name, part0, part1, C0 relative to part0)."""
        TW, TH, TD = self.torso
        k = self.k
        return [("RootJoint", "HumanoidRootPart", "Torso", CF((0, 0, 0), R_ROOT)),
                ("Neck", "Torso", "Head", CF((0, TH / 2, 0), R_ROOT)),
                ("Right Shoulder", "Torso", "Right Arm", CF((TW / 2, TH / 2 - k, 0), R_RIGHT)),
                ("Left Shoulder", "Torso", "Left Arm", CF((-TW / 2, TH / 2 - k, 0), R_LEFT)),
                ("Right Hip", "Torso", "Right Leg", CF((TW / 2, -TH / 2, 0), R_RIGHT)),
                ("Left Hip", "Torso", "Left Leg", CF((-TW / 2, -TH / 2, 0), R_LEFT))]

    def attachments(self):
        """The standard R6 accessory / tool attachments, scaled: (part, name, local CF)."""
        TW, TH, TD = self.torso
        AW, AL, AD = self.arm
        LW, LH, LD = self.leg
        hs = self.head[1] / 1.0                     # head scale relative to the classic head
        out = [("HumanoidRootPart", "RootAttachment", CF()),
               ("Head", "FaceCenterAttachment", CF()), ("Head", "FaceFrontAttachment", CF((0, 0, -0.6 * hs))),
               ("Head", "HairAttachment", CF((0, 0.6 * hs, 0))), ("Head", "HatAttachment", CF((0, 0.6 * hs, 0))),
               ("Torso", "BodyBackAttachment", CF((0, 0, TD / 2))), ("Torso", "BodyFrontAttachment", CF((0, 0, -TD / 2))),
               ("Torso", "LeftCollarAttachment", CF((-TW / 2, TH / 2, 0))), ("Torso", "NeckAttachment", CF((0, TH / 2, 0))),
               ("Torso", "RightCollarAttachment", CF((TW / 2, TH / 2, 0))),
               ("Torso", "WaistBackAttachment", CF((0, -TH / 2, TD / 2))),
               ("Torso", "WaistCenterAttachment", CF((0, -TH / 2, 0))),
               ("Torso", "WaistFrontAttachment", CF((0, -TH / 2, -TD / 2))),
               ("Left Arm", "LeftShoulderAttachment", CF((0, AL / 2, 0))),
               ("Left Arm", "LeftGripAttachment", CF((0, -AL / 2, 0), R_GRIP)),
               ("Right Arm", "RightShoulderAttachment", CF((0, AL / 2, 0))),
               ("Right Arm", "RightGripAttachment", CF((0, -AL / 2, 0), R_GRIP)),
               ("Left Leg", "LeftFootAttachment", CF((0, -LH / 2, 0))),
               ("Right Leg", "RightFootAttachment", CF((0, -LH / 2, 0)))]
        return out

    def head_dims(self):
        """What the classic head mesh looks like on this Head part: (width, height, depth)."""
        HW, HH, HD = self.head
        return (HEAD_SCALE * HW / 2, HEAD_SCALE * HH, HEAD_SCALE * HD)


PARTS = ("HumanoidRootPart", "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg")


def head_geo(w=1.25, h=1.25, d=1.25, n=16):
    """Preview stand-in for the classic head mesh: a cylinder with well-rounded rims."""
    r, hh = w / 2, h / 2
    rc = 0.4 * min(r, hh)
    prof = [(0.0, -hh)]
    for k in range(4):
        a = math.pi / 2 * k / 3
        prof.append((r - rc + rc * math.sin(a), -hh + rc - rc * math.cos(a)))
    for k in range(4):
        a = math.pi / 2 * k / 3
        prof.append((r - rc + rc * math.cos(a), hh - rc + rc * math.sin(a)))
    prof.append((0.0, hh))
    g = G.lathe(prof, n, sz=d / w)
    return G.outward(g)


def build(sc, parent, name, body, origin=CF(), colors=None, material="Plastic", humanoid=True,
          attachments=True, transparency=None):
    """Make the R6 Model: the seven parts, the six Motor6Ds (in Part0, as in Roblox), the
    standard attachments, a Humanoid with an Animator. HumanoidRootPart is anchored and
    invisible; everything else hangs off it on the joints, unanchored."""
    colors = colors or {}
    m = sc.model(parent, name)
    cfs = body.cfs(origin)
    parts = {}
    for pn in PARTS:
        root = pn == "HumanoidRootPart"
        tr = 1.0 if root else (transparency or {}).get(pn, 0.0)
        parts[pn] = sc.part(m, pn, body.size(pn), cfs[pn], colors.get(pn, (163, 162, 165)), material=material,
                            transparency=tr, anchored=root, collide=pn in ("Torso", "Head"),
                            touch=True, query=not root, shadow=not root, massless=False, surfaces="smooth", grid=False)
    sc.special_mesh(parts["Head"], "Head", (HEAD_SCALE,) * 3)
    for jn, p0, p1, c0 in body.joints():
        sc.motor(parts[p0], parts[p1], jn, parts[p0].p["cf"] * c0, parent=parts[p0])
    if attachments:
        for pn, an, lcf in body.attachments():
            sc.attachment(parts[pn], an, parts[pn].p["cf"] * lcf)
    if humanoid:
        sc.humanoid(m)
    m.p["primary"] = parts["HumanoidRootPart"]
    return m, parts
