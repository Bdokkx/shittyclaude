"""Improve every animation in the game's Sequences folder and add weapon hold / equip
animations, then write the folder back out (same names, same settings).

    python tools/improve.py <in.json> <out.json> [--previews=<dir>]

1. Every animation is re-sampled at 30 fps on a smooth curve through its original key
   poses (28 of them were authored with Constant easing, so they snapped from key to
   key), loops are closed, and each key is written Linear.
2. Polish by kind: locomotion gets a step bob, a steadier head and livelier arms;
   idles breathe and look around; attacks put more body into the swing.
3. New: SwordHold / DaggerHold / HammerHold (looping idle stances with the weapon) and
   SwordEquip / DaggerEquip / HammerEquip (short draw flourishes ending in the hold).
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim  # noqa: E402
from anim import JOINTS, euler_quat, quat_mul, slerp  # noqa: E402

FPS = 30
IDENT = np.array([1.0, 0, 0, 0])

LOCOMOTION = {"Walk", "Sprint", "CatcherRun", "CatcherRunSword", "CatcherRunDagger", "CatcherRunHammer"}
UNARMED_RUNS = {"Walk", "Sprint", "CatcherRun"}
IDLES = {"Idle", "NpcPete", "NpcWanda"}
ATTACKS = {"SwordSwing1", "SwordSwing2", "SwordSwing3", "DaggerSwing1", "DaggerSwing2", "DaggerSwing3",
           "HammerSwing1", "HammerSwing2", "HammerSwing3", "Slash", "Stab", "Smash", "Pounce"}
WEAPON_OF = {"Sword": "Sword", "Dagger": "Dagger", "Hammer": "Hammer", "Slash": "Sword", "Stab": "Dagger",
             "Smash": "Hammer"}


def weapon_for(name):
    for k, v in WEAPON_OF.items():
        if k in name:
            return v
    return None


# ---------------------------------------------------------------- sampled-motion helpers

def bake(a):
    ts = anim.frame_times(a.length, FPS)
    return ts, {j: [arr.copy() for arr in anim.sample(tr, ts, a.loop, a.length)] for j, tr in a.tracks.items()}


def rot(smp, ts, joint, fn):
    """Post-multiply a joint's rotation by euler angles fn(t) (degrees, joint-local)."""
    if joint not in smp:
        return
    q = smp[joint][1]
    for i, t in enumerate(ts):
        q[i] = quat_mul(q[i], euler_quat(*fn(t)))


def move(smp, ts, joint, fn):
    if joint not in smp:
        return
    p = smp[joint][0]
    for i, t in enumerate(ts):
        p[i] = p[i] + np.asarray(fn(t), dtype=float)


def amplify(smp, joint, k):
    """Exaggerate a joint's motion around its average pose."""
    if joint not in smp:
        return
    p, q = smp[joint]
    mean_q = q.sum(0)
    mean_q /= np.linalg.norm(mean_q)
    mean_p = p.mean(0)
    for i in range(len(q)):
        rel = quat_mul(np.array([mean_q[0], -mean_q[1], -mean_q[2], -mean_q[3]]), q[i])
        rel = slerp(IDENT, rel, k) if np.dot(rel, IDENT) >= 0 else slerp(IDENT, -rel, k)
        q[i] = quat_mul(mean_q, rel)
        p[i] = mean_p + (p[i] - mean_p) * k


def swing_angle(q, axis=2):
    """Signed rotation (degrees) about one local axis, for gentle analysis."""
    return math.degrees(2 * math.atan2(q[axis + 1], q[0]))


# ---------------------------------------------------------------- polish passes

def polish_locomotion(name, ts, smp, L):
    w = 2 * math.pi / L
    if "Right Leg" in smp:
        legs = np.array([swing_angle(q) for q in smp["Right Leg"][1]])
        span = max(np.ptp(legs), 1e-3)
        mid = (legs.max() + legs.min()) / 2
        torso_z = smp["Torso"][0][:, 2]
        if np.ptp(torso_z) < 0.08:                   # add a step bob: low when the legs are apart
            bob = 0.10 if "Sprint" in name or "Run" in name else 0.06
            for i in range(len(ts)):
                s = (legs[i] - mid) / (span / 2)
                smp["Torso"][0][i][2] += bob * (0.5 - s * s)
    if name in UNARMED_RUNS:
        for j in ("Right Arm", "Left Arm"):
            amplify(smp, j, 1.18)
        for j in ("Right Leg", "Left Leg"):
            amplify(smp, j, 1.06)
    # steadier head: take back part of the torso's yaw and roll, and nod with the steps
    if "Head" in smp and "Torso" in smp:
        tq = smp["Torso"][1]
        mean = tq.sum(0) / np.linalg.norm(tq.sum(0))
        for i, t in enumerate(ts):
            rel = quat_mul(np.array([mean[0], -mean[1], -mean[2], -mean[3]]), tq[i])
            yaw, roll = swing_angle(rel, 2), swing_angle(rel, 1)
            smp["Head"][1][i] = quat_mul(smp["Head"][1][i], euler_quat(2.0 * math.sin(2 * w * t), -0.45 * roll,
                                                                        -0.45 * yaw))
    if name in ("Sprint", "CatcherRun"):
        rot(smp, ts, "Torso", lambda t: (3.0, 0, 0))     # a touch more forward lean


def polish_idle(name, ts, smp, L):
    breaths = max(1, round(L / 1.6))
    wb = 2 * math.pi * breaths / L
    w = 2 * math.pi / L
    move(smp, ts, "Torso", lambda t: (0, 0, 0.035 * math.sin(wb * t)))
    rot(smp, ts, "Torso", lambda t: (-1.2 * math.sin(wb * t), 0, 0))
    rot(smp, ts, "Right Arm", lambda t: (2.0 * (0.5 + 0.5 * math.sin(wb * t)), 0, 1.5 * math.sin(w * t)))
    rot(smp, ts, "Left Arm", lambda t: (-2.0 * (0.5 + 0.5 * math.sin(wb * t)), 0, 1.5 * math.sin(w * t + 1.0)))
    looks = max(1, round(L / 3.2))
    wl = 2 * math.pi * looks / L
    rot(smp, ts, "Head", lambda t: (1.5 * math.sin(wb * t + 0.6), 0, 9.0 * math.sin(wl * t)))


def polish_attack(name, ts, smp, L):
    amplify(smp, "Torso", 1.25)          # more body behind the swing
    amplify(smp, "Head", 1.15)
    amplify(smp, "Right Arm", 1.06)


# ---------------------------------------------------------------- new: weapon holds and equips

def avg_pose(a, joint):
    ts, smp = bake(a)
    p, q = smp[joint]
    m = q.sum(0)
    return p.mean(0), m / np.linalg.norm(m)


def make_hold(name, base, L, style):
    """Looping idle stance holding the weapon the way the hunter runs hold it."""
    ts = anim.frame_times(L, FPS)
    w = 2 * math.pi / L
    wb = 2 * w                                             # two breaths per loop
    smp = {j: [np.zeros((len(ts), 3)), np.tile(IDENT, (len(ts), 1))] for j in JOINTS}
    rp, rq = base["Right Arm"]
    for i, t in enumerate(ts):
        br = math.sin(wb * t)
        if style == "Sword":
            torso = euler_quat(3 + 1.2 * br, 0, 10)
            tz = 0.03 * br
            head = euler_quat(-2 + 1.2 * math.sin(wb * t + 0.6), 0, -9 + 4 * math.sin(w * t))
            larm = euler_quat(-8 - 2 * br, 0, -16 + 3 * math.sin(w * t + 1))
            rleg, lleg = euler_quat(5, 0, -7), euler_quat(-5, 0, -9)
            rarm = quat_mul(rq, euler_quat(2.5 * math.sin(w * t), 0, 3 * br))
        elif style == "Dagger":
            bounce = abs(math.sin(wb * t))
            torso = euler_quat(11 + 2 * br, 0, 14)
            tz = 0.05 * bounce - 0.02
            head = euler_quat(-9 + 1.5 * br, 0, -12 + 5 * math.sin(w * t))
            larm = euler_quat(-14, 0, -42 + 5 * math.sin(wb * t + 0.8))
            rleg, lleg = euler_quat(8, 0, -14), euler_quat(-8, 0, -16)
            rarm = quat_mul(rq, euler_quat(3 * math.sin(wb * t), 0, 5 * math.sin(wb * t + 0.4)))
        else:  # Hammer: resting on the shoulder, weight back
            torso = euler_quat(-4 + 1.5 * br, 0, 6)
            tz = 0.035 * br
            head = euler_quat(1 + 1.5 * math.sin(wb * t + 0.6), 0, -6 + 5 * math.sin(w * t))
            larm = euler_quat(-6 - 2 * br, 0, 6 * math.sin(w * t + 0.5))
            rleg, lleg = euler_quat(6, 0, -4), euler_quat(-6, 0, -6)
            rarm = quat_mul(rq, euler_quat(2 * math.sin(w * t), 0, 2.5 * br))
        smp["Torso"][1][i], smp["Torso"][0][i] = torso, (0, 0, tz)
        smp["Head"][1][i] = head
        smp["Right Arm"][1][i], smp["Right Arm"][0][i] = rarm, rp
        smp["Left Arm"][1][i] = larm
        smp["Right Leg"][1][i] = rleg
        smp["Left Leg"][1][i] = lleg
    a = anim.Anim(name, L, True, 1, {})
    return a, ts, smp


def make_equip(name, hold_smp, style, L=0.55):
    """A short draw: arm down -> flourish -> the hold pose (frame 0 of the hold)."""
    end = {j: (hold_smp[j][0][0], hold_smp[j][1][0]) for j in JOINTS}
    rq_end = end["Right Arm"][1]
    if style == "Sword":        # pull up and twirl overhead, then settle into the hold
        keys = [(0.0, euler_quat(0, 0, 10)), (0.16, euler_quat(-10, -60, 120)), (0.27, euler_quat(-6, -150, 165)),
                (0.38, quat_mul(rq_end, euler_quat(0, 0, 14))), (L, rq_end)]
        torso_keys = [(0.0, euler_quat(0, 0, 0)), (0.2, euler_quat(-4, 0, 16)), (0.38, euler_quat(5, 0, 8)),
                      (L, end["Torso"][1])]
    elif style == "Dagger":     # flick it up and spin it in the hand
        keys = [(0.0, euler_quat(0, 0, 10)), (0.10, euler_quat(0, 0, 70)), (0.18, euler_quat(0, 110, 85)),
                (0.26, euler_quat(0, 220, 85)), (0.34, euler_quat(0, 330, 80)), (0.42, quat_mul(rq_end, euler_quat(0, 0, -8))),
                (L, rq_end)]
        torso_keys = [(0.0, euler_quat(0, 0, 0)), (0.18, euler_quat(4, 0, 6)), (L, end["Torso"][1])]
    else:                       # heave it up and thump it onto the shoulder with a little bounce
        keys = [(0.0, euler_quat(0, 0, -10)), (0.18, euler_quat(0, 0, 60)), (0.32, quat_mul(rq_end, euler_quat(0, 0, 22))),
                (0.42, quat_mul(rq_end, euler_quat(0, 0, -8))), (L, rq_end)]
        torso_keys = [(0.0, euler_quat(8, 0, 0)), (0.18, euler_quat(-8, 0, 4)), (0.32, euler_quat(-2, 0, 6)),
                      (0.42, euler_quat(2, 0, 6)), (L, end["Torso"][1])]
    ts = anim.frame_times(L, FPS)
    tracks = {}

    def tr(keys, pos_end=None):
        times = [k[0] for k in keys]
        quats = [k[1] for k in keys]
        pos = [np.zeros(3) for _ in keys]
        if pos_end is not None:
            pos[-1] = np.asarray(pos_end, dtype=float)
        return anim.Track(times, pos, quats)
    tracks["Right Arm"] = tr(keys, end["Right Arm"][0])
    tracks["Torso"] = tr(torso_keys, end["Torso"][0])
    for j in ("Head", "Left Arm", "Right Leg", "Left Leg"):
        tracks[j] = anim.Track([0.0, L * 0.45, L], [np.zeros(3), np.zeros(3), end[j][0]],
                               [IDENT, slerp(IDENT, end[j][1], 0.8), end[j][1]])
    a = anim.Anim(name, L, False, 2, tracks)
    ts, smp = bake(a)
    return a, ts, smp


# ---------------------------------------------------------------- main

def main(src, dst, preview_dir=None):
    data = json.load(open(src))
    folder = data[0]
    out_children, results = [], []
    originals = {c["name"]: anim.read_sequence(c) for c in folder["children"] if c["class"] == "KeyframeSequence"}
    for c in folder["children"]:
        if c["class"] != "KeyframeSequence":
            out_children.append(c)
            continue
        a = originals[c["name"]]
        ts, smp = bake(a)
        if a.name in LOCOMOTION:
            polish_locomotion(a.name, ts, smp, a.length)
        elif a.name in IDLES:
            polish_idle(a.name, ts, smp, a.length)
        elif a.name in ATTACKS:
            polish_attack(a.name, ts, smp, a.length)
        if a.loop:                         # exact loop closure after the polish passes
            for j in smp:
                smp[j][0][-1] = smp[j][0][0]
                smp[j][1][-1] = smp[j][1][0]
        out_children.append(anim.write_sequence(a, smp, FPS, ts))
        results.append((a, ts, smp, weapon_for(a.name)))
    # new weapon holds and equips, held the way the hunter runs hold each weapon
    for style, run, L in (("Sword", "CatcherRunSword", 2.4), ("Dagger", "CatcherRunDagger", 1.6),
                          ("Hammer", "CatcherRunHammer", 2.8)):
        if style == "Hammer":
            # the hammer run swings it around, so its average is mid-swing: rest it on the shoulder instead
            base = {"Right Arm": (np.zeros(3), euler_quat(16, -10, 138))}
        else:
            base = {"Right Arm": avg_pose(originals[run], "Right Arm")}
        a, ts, smp = make_hold(style + "Hold", base, L, style)
        out_children.append(anim.write_sequence(a, smp, FPS, ts))
        results.append((a, ts, smp, style))
        e, ets, esmp = make_equip(style + "Equip", smp, style)
        out_children.append(anim.write_sequence(e, esmp, FPS, ets))
        results.append((e, ets, esmp, style))
    folder = dict(folder)
    folder["children"] = out_children
    json.dump([folder], open(dst, "w"))
    print("wrote", dst, len(out_children), "sequences")
    if preview_dir:
        import render
        from PIL import Image
        os.makedirs(preview_dir, exist_ok=True)
        cam = render.Camera(px=220)
        strips = []
        for a, ts, smp, weapon in results:
            step = max(1, int(round(FPS / 15)))
            idx = list(range(0, len(ts), step))
            sub = {j: (smp[j][0][idx], smp[j][1][idx]) for j in smp}
            frames = render.frames_for(a, sub, ts[idx], cam, weapon)
            render.save_gif(frames, os.path.join(preview_dir, a.name + ".gif"), FPS / step)
            strips.append(render.filmstrip(frames, 8, "%s  %.2fs%s" % (a.name, a.length, "  loop" if a.loop else "")))
        for k in range(0, len(strips), 8):
            chunk = strips[k:k + 8]
            sheet = Image.new("RGB", (max(s.width for s in chunk), sum(s.height for s in chunk)))
            y = 0
            for s in chunk:
                sheet.paste(s, (0, y))
                y += s.height
            sheet.save(os.path.join(preview_dir, "strips_%02d.png" % (k // 8)))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    o = dict(x[2:].split("=", 1) for x in sys.argv[1:] if x.startswith("--") and "=" in x)
    main(a[0], a[1], o.get("previews"))
