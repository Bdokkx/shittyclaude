"""A brick rig: groups of bricks welded to a main part, the main parts joined by Motor6Ds.

Group(rig, name, part0, hinge) makes the group's main part (named `name`, the Motor6D's Part1)
and its Motor6D (named `joint`, parented to the main part). Bricks added to a group are children
of its main part, welded to it. Joint frames have model axes, so clips read the same on any rig
built this way.

Rig.world(X) gives every part's world CFrame for joint transforms X ({joint name: 4x4}), and
write_clip() turns baked frames into a KeyframeSequence (rbxtool JSON) whose poses are named after
the joints' Part1s, nested Part0 -> Part1 (Roblox's own rule).
"""
import copy
import os
import sys

import numpy as np

from spsgeo import CF

from .bricks import Bricks, hexc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "folk-valley-animations", "tools"))
import anim as A  # noqa: E402

from .roots_anim import MARKER_PROPS  # noqa: E402

FPS = 30


class Rig:
    def __init__(self, sc, parent, name, base=None, root_size=(2.0, 0.4, 2.0)):
        self.sc = sc
        self.base = base if base is not None else CF()
        self.m = sc.model(parent, name)
        self.b = Bricks(sc, self.base, anchored=False, massless=True)
        h = root_size[1]
        self.root = sc.part(self.m, "Root", root_size, self.base * CF((0.0, h / 2, 0.0)), (255, 255, 255),
                            material="SmoothPlastic", transparency=1.0, anchored=True, collide=False, touch=False,
                            query=False, shadow=False, massless=False, grid=False, surfaces="smooth",
                            pivot=CF((0.0, -h / 2, 0.0)))
        self.m.p["primary"] = self.root
        self.groups = {"Root": self.root}
        self.motors = []          # (joint, part0, part1, hinge local)
        self.welds = []

    def group(self, name, part0, hinge, joint, size=(0.2, 0.2, 0.2), pos=None, R=None, color="ffffff",
              material="SmoothPlastic", visible=False):
        """The group's main part: an invisible holder at the hinge, or (visible=True) a real brick."""
        p0 = self.groups[part0] if isinstance(part0, str) else part0
        if visible:
            p = self.b.part(self.m, name, size, pos, R, color, material=material)
        else:
            p = self.b.part(self.m, name, (0.2, 0.2, 0.2), hinge if pos is None else pos, None, "ffffff",
                            material="SmoothPlastic", transparency=1.0, shadow=False)
        self.groups[name] = p
        self.motors.append((joint, p0, p, CF(np.asarray(hinge, float))))
        return p

    def brick(self, group, name, size, pos, R=None, color="ffffff", material="Plastic", **kw):
        g = self.groups[group] if isinstance(group, str) else group
        p = self.b.part(g, name, size, pos, R, color, material=material, **kw)
        self.welds.append((g, p))
        return p

    def plate(self, group, name, size, pos, R=None, color="1e1a22", material="SmoothPlastic"):
        g = self.groups[group] if isinstance(group, str) else group
        p = self.b.plate(g, name, size, pos, R, color, material=material)
        self.welds.append((g, p))
        return p

    def part(self, name, size, pos, R=None, color="ffffff", **kw):
        """A part straight under the model, not part of any group (e.g. the invisible Prompt)."""
        return self.b.part(self.m, name, size, pos, R, color, **kw)

    def finish(self):
        for p0, p1 in self.welds:
            self.sc.weld(p0, p1, name="Weld")
        for joint, p0, p1, hinge in self.motors:
            self.sc.motor(p0, p1, joint, self.base * hinge, parent=p1)
        self.sc.anim_controller(self.m)
        return self.m


# ---------------------------------------------------------------- posing from a built model

class Pose:
    def __init__(self, model):
        self.model = model
        self.motors = {}
        self.by_joint = {}
        self.welded = {}
        for n in model.walk():
            for c in n.children:
                if c.kind == "Motor":
                    self.motors[id(c.p["part1"])] = (c.name, c.p["part0"], c.p["part1"], c.p["hinge"])
                    self.by_joint[c.name] = (c.p["part0"], c.p["part1"])
                elif c.kind == "Weld":
                    self.welded[id(c.p["part1"])] = c.p["part0"]
        self.root = model.p["primary"]

    def tree(self):
        """{part0 name: [part1 names]} in the order the joints were made, and part1 -> joint name."""
        t, joint_of = {}, {}
        for n in self.model.walk():
            for c in n.children:
                if c.kind == "Motor":
                    t.setdefault(c.p["part0"].name, []).append(c.p["part1"].name)
                    joint_of[c.p["part1"].name] = c.name
        return t, joint_of

    def world(self, X=None):
        X = X or {}
        out = {id(self.root): (self.root, self.root.p["cf"])}

        def solve(part):
            key = id(part)
            if key in out:
                return out[key][1]
            if key in self.motors:
                name, p0, p1, hinge = self.motors[key]
                w0 = solve(p0)
                C0 = p0.p["cf"].inv() * hinge
                C1 = p1.p["cf"].inv() * hinge
                T = X.get(name)
                Tcf = CF() if T is None else CF(T[:3, 3], T[:3, :3])
                w = w0 * C0 * Tcf * C1.inv()
            elif key in self.welded:
                p0 = self.welded[key]
                w = solve(p0) * (p0.p["cf"].inv() * part.p["cf"])
            elif part.p.get("anchored"):
                w = part.p["cf"]                   # anchored on its own (e.g. the Prompt): stays put
            else:
                raise KeyError(part.name)
            out[key] = (part, w)
            return w
        for n in self.model.walk():
            if n.kind == "Part":
                solve(n)
        return out


# ---------------------------------------------------------------- KeyframeSequences

class Clip:
    def __init__(self, name, length, loop, priority, fn, markers=(), fps=FPS):
        self.name, self.length, self.loop, self.priority, self.fn = name, length, loop, priority, fn
        self.markers = list(markers)
        self.fps = fps

    def times(self):
        n = int(round(self.length * self.fps))
        return [i / self.fps for i in range(n + 1)]

    def bake(self):
        out = []
        for t in self.times():
            X = {}
            self.fn(X, (t % self.length) if (self.loop and t < self.length - 1e-9) else (0.0 if self.loop else t))
            out.append(X)
        return out


def moving(frames):
    out = set()
    for X in frames:
        for j, m in X.items():
            if not np.allclose(m, np.eye(4), atol=1e-6):
                out.add(j)
    return out


def write_clip(model, clip, frames):
    """frames: [{joint: 4x4}]. Poses are named after each joint's Part1 (Roblox's rule)."""
    P = Pose(model)
    tree, joint_of = P.tree()
    parent = {c: p for p, cs in tree.items() for c in cs}
    part_of = {j: p1 for p1, j in joint_of.items()}
    used = {part_of[j] for j in moving(frames)}
    need = set(used)
    for p in list(used):
        q = parent.get(p)
        while q and q != "Root":
            need.add(q)
            q = parent.get(q)
    props = copy.deepcopy(A.KS_PROPS)
    props["Loop"] = {"Bool": bool(clip.loop)}
    props["Priority"] = {"Enum": int(clip.priority)}
    props["AuthoredHipHeight"] = {"Float32": 0.0}
    times = clip.times()
    marks = {}
    for t, name in clip.markers:
        i = int(np.argmin([abs(t - x) for x in times]))
        marks.setdefault(i, []).append(name)
    kfs = []
    for i, X in enumerate(frames):
        def pose(b):
            kids = [pose(c) for c in tree.get(b, []) if c in need]
            if b == "Root":
                return A._pose(b, (0, 0, 0), np.array([1.0, 0, 0, 0]), kids, weight=0.0)
            m = X.get(joint_of[b], np.eye(4))
            return A._pose(b, m[:3, 3], A.mat_to_quat(m[:3, :3]), kids)
        kp = copy.deepcopy(A.KF_PROPS)
        kp["Time"] = {"Float32": round(float(times[i]), 5)}
        kids = [pose("Root")]
        for name in marks.get(i, []):
            kids.append({"class": "KeyframeMarker", "name": name, "ref": A._ref(), "props": copy.deepcopy(MARKER_PROPS),
                         "children": []})
        kfs.append({"class": "Keyframe", "name": "Keyframe", "ref": A._ref(), "props": kp, "children": kids})
    return {"class": "KeyframeSequence", "name": clip.name, "ref": A._ref(), "props": props, "children": kfs}


def folder_json(name, items):
    return {"class": "Folder", "name": name, "ref": A._ref(),
            "props": {"Attributes": {"Attributes": {}}, "Tags": {"Tags": []}}, "children": items}


__all__ = ["Rig", "Pose", "Clip", "write_clip", "folder_json", "moving", "hexc"]
