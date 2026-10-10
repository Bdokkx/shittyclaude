"""Tiny software renderer for R6 animations: poses the classic R6 rig with the
standard Motor6D offsets, draws its boxes (plus an optional weapon in the right
hand, held by the standard tool grip) and writes GIFs and filmstrips."""
import math

import numpy as np
from PIL import Image, ImageDraw

from anim import quat_to_mat


def cf(pos, rows):
    m = np.eye(4)
    m[:3, :3] = np.array(rows, dtype=float)
    m[:3, 3] = pos
    return m


ROT_ROOT = [[-1, 0, 0], [0, 0, 1], [0, 1, 0]]
ROT_R = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
ROT_L = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
# joint: (parent, C0, C1, part size)
RIG = {
    "Torso": ("HRP", cf((0, 0, 0), ROT_ROOT), cf((0, 0, 0), ROT_ROOT), (2, 2, 1)),
    "Head": ("Torso", cf((0, 1, 0), ROT_ROOT), cf((0, -0.5, 0), ROT_ROOT), (1.2, 1.2, 1.2)),
    "Right Arm": ("Torso", cf((1, 0.5, 0), ROT_R), cf((-0.5, 0.5, 0), ROT_R), (1, 2, 1)),
    "Left Arm": ("Torso", cf((-1, 0.5, 0), ROT_L), cf((0.5, 0.5, 0), ROT_L), (1, 2, 1)),
    "Right Leg": ("Torso", cf((1, -1, 0), ROT_R), cf((0.5, 1, 0), ROT_R), (1, 2, 1)),
    "Left Leg": ("Torso", cf((-1, -1, 0), ROT_L), cf((-0.5, 1, 0), ROT_L), (1, 2, 1)),
}
COLORS = {"Torso": (13, 105, 172), "Head": (245, 205, 48), "Right Arm": (245, 205, 48), "Left Arm": (245, 205, 48),
          "Right Leg": (164, 189, 71), "Left Leg": (164, 189, 71)}
GRIP = cf((0, -1, 0), [[1, 0, 0], [0, 0, 1], [0, -1, 0]])      # standard RightGrip C0 (tool Grip = identity)


def pose_world(joint_xf):
    """{joint: 4x4 Transform} -> {part: 4x4 world matrix} (HumanoidRootPart at (0, 3, 0))."""
    world = {"HRP": cf((0, 3, 0), np.eye(3))}
    for j in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"):
        parent, c0, c1, _ = RIG[j]
        world[j] = world[parent] @ c0 @ joint_xf.get(j, np.eye(4)) @ np.linalg.inv(c1)
    return world


def xf(pos, quat):
    m = np.eye(4)
    m[:3, :3] = quat_to_mat(quat)
    m[:3, 3] = pos
    return m


def box_faces(m, size, color, eps=0.0):
    sx, sy, sz = (s / 2 + eps for s in size)
    c = np.array([[x, y, z, 1] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)], dtype=float)
    w = (m @ c.T).T[:, :3]
    faces = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]
    out = []
    for idx, n in faces:
        nw = m[:3, :3] @ np.array(n, dtype=float)
        out.append(([w[i] for i in idx], nw, color))
    return out


def weapon_boxes(handle, kind):
    """Simple stand-in shapes for a weapon in Handle space (+Y along the weapon, +X the edge)."""
    b = []
    if kind == "Sword":
        b += [((0, -0.45, 0), (0.28, 1.0, 0.28), (110, 70, 40)), ((0, 0.55, 0), (1.3, 0.2, 0.3), (90, 96, 116)),
              ((0, 2.55, 0), (0.6, 3.8, 0.16), (214, 222, 236))]
    elif kind == "Dagger":
        b += [((0, -0.35, 0), (0.26, 0.85, 0.26), (60, 40, 30)), ((0, 0.45, 0), (0.8, 0.16, 0.26), (90, 96, 116)),
              ((0, 1.65, 0), (0.5, 2.2, 0.14), (214, 222, 236))]
    elif kind == "Hammer":
        b += [((0, 1.0, 0), (0.28, 4.4, 0.28), (150, 100, 52)), ((0, 3.6, 0), (2.0, 1.1, 1.0), (120, 128, 146))]
    out = []
    for c, size, col in b:
        m = handle @ cf(c, np.eye(3))
        out += box_faces(m, size, col)
    return out


class Camera:
    def __init__(self, yaw=-28.0, pitch=12.0, center=(0, 3.2, 0), height=8.0, px=300):
        f = np.array([math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), -math.sin(math.radians(pitch)),
                      math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))])
        self.f = f / np.linalg.norm(f)                       # looking toward +Z: we see the character's front
        self.r = np.cross(self.f, (0, 1, 0))
        self.r /= np.linalg.norm(self.r)
        self.u = np.cross(self.r, self.f)
        self.c = np.array(center, dtype=float)
        self.scale = px / height
        self.px = px

    def proj(self, p):
        d = np.asarray(p) - self.c
        return (self.px / 2 + d.dot(self.r) * self.scale, self.px / 2 - d.dot(self.u) * self.scale), d.dot(self.f)


LIGHT = np.array([-0.45, 0.8, -0.55])
LIGHT /= np.linalg.norm(LIGHT)


def draw(world, cam, weapon=None, bg=(116, 146, 196)):
    img = Image.new("RGB", (cam.px, cam.px), bg)
    d = ImageDraw.Draw(img)
    # ground shadow
    gy = cam.proj((0, 0, 0))[0][1]
    d.ellipse((cam.px / 2 - 0.9 * cam.scale, gy - 0.25 * cam.scale, cam.px / 2 + 0.9 * cam.scale, gy + 0.25 * cam.scale),
              fill=tuple(int(v * 0.8) for v in bg))
    faces = []
    for j, m in world.items():
        if j == "HRP":
            continue
        faces += box_faces(m, RIG[j][3], COLORS[j])
    if weapon:
        faces += weapon_boxes(world["Right Arm"] @ GRIP, weapon)
    drawn = []
    for pts, n, col in faces:
        if n.dot(cam.f) >= 0:          # back face
            continue
        pp = [cam.proj(p) for p in pts]
        depth = sum(z for _, z in pp) / 4
        shade = 0.55 + 0.45 * max(0.0, float(n.dot(LIGHT)))
        drawn.append((depth, [xy for xy, _ in pp], tuple(int(c * shade) for c in col)))
    for depth, poly, col in sorted(drawn, key=lambda x: -x[0]):
        d.polygon(poly, fill=col, outline=tuple(int(c * 0.55) for c in col))
    # face on the head (front = -Z)
    h = world["Head"]
    for ex in (-0.22, 0.22):
        p, z = cam.proj((h @ np.array([ex, 0.12, -0.61, 1]))[:3])
        if (h[:3, :3] @ np.array([0, 0, -1])).dot(cam.f) < 0:
            d.ellipse((p[0] - 2.5, p[1] - 3.5, p[0] + 2.5, p[1] + 3.5), fill=(30, 30, 34))
    return img


def frames_for(anim, samples, times, cam, weapon=None):
    out = []
    for i in range(len(times)):
        joint_xf = {j: xf(samples[j][0][i], samples[j][1][i]) for j in samples}
        out.append(draw(pose_world(joint_xf), cam, weapon))
    return out


def save_gif(frames, path, fps):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)


def filmstrip(frames, n=8, label=None):
    idx = np.linspace(0, len(frames) - 1, n).round().astype(int)
    w, h = frames[0].size
    strip = Image.new("RGB", (w * n, h + (28 if label else 0)), (24, 26, 34))
    for k, i in enumerate(idx):
        strip.paste(frames[i], (k * w, 28 if label else 0))
    if label:
        ImageDraw.Draw(strip).text((8, 6), label, fill=(255, 255, 255))
    return strip
