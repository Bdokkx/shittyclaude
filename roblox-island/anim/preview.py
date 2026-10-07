"""Tiny software renderer for R6 previews (no Blender needed): flat-shaded blocky character, ground shadow,
painter's sort. Used to make before/after GIFs and contact sheets of the animations."""
import math

from PIL import Image, ImageDraw, ImageFont

from r6 import CF, SIZES, fk

COLORS = {"Head": (245, 205, 48), "Torso": (13, 105, 172), "Right Arm": (245, 205, 48), "Left Arm": (245, 205, 48),
          "Right Leg": (164, 189, 71), "Left Leg": (164, 189, 71)}
FACE = (35, 35, 35)
LIGHT = (0.45, 0.8, -0.4)
BG = (226, 232, 240)
GROUND = (200, 208, 220)

BOX_FACES = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1
    return tuple(x / n for x in v)


class Camera:
    def __init__(self, eye, target, size=(320, 320), fov=34):
        self.eye, self.size = eye, size
        f = _norm(tuple(target[i] - eye[i] for i in range(3)))
        r = _norm((-f[2], 0, f[0]))                                       # forward x up
        u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])   # right x forward
        self.f, self.r, self.u = f, r, u
        self.k = size[1] / 2 / math.tan(math.radians(fov) / 2)

    def project(self, p):
        d = tuple(p[i] - self.eye[i] for i in range(3))
        z = sum(d[i] * self.f[i] for i in range(3))
        x = sum(d[i] * self.r[i] for i in range(3))
        y = sum(d[i] * self.u[i] for i in range(3))
        return (self.size[0] / 2 + x / z * self.k, self.size[1] / 2 - y / z * self.k), z


def draw_frame(transforms, cam, label=None, root=None, font=None):
    img = Image.new("RGB", cam.size, BG)
    dr = ImageDraw.Draw(img)
    # ground grid + shadow
    for g in range(-6, 7, 2):
        a, _ = cam.project((g, 0, -6))
        b, _ = cam.project((g, 0, 6))
        dr.line([a, b], fill=GROUND)
        a, _ = cam.project((-6, 0, g))
        b, _ = cam.project((6, 0, g))
        dr.line([a, b], fill=GROUND)
    world = fk(transforms, root or CF((0, 3, 0)))
    sh = [cam.project((math.cos(a) * 1.6 + world["Torso"].p[0], 0.01, math.sin(a) * 1.0 + world["Torso"].p[2]))[0]
          for a in [i * math.pi / 12 for i in range(24)]]
    dr.polygon(sh, fill=(185, 192, 205))
    polys = []
    for part, col in COLORS.items():
        w = world[part]
        sx, sy, sz = (s / 2 for s in SIZES[part])
        corners = [w.point((x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
        for idx, n in BOX_FACES:
            wn = tuple(sum(w.R[i][k] * n[k] for k in range(3)) for i in range(3))
            c = tuple(sum(corners[j][i] for j in idx) / 4 for i in range(3))
            to_eye = tuple(cam.eye[i] - c[i] for i in range(3))
            if sum(wn[i] * to_eye[i] for i in range(3)) <= 0:
                continue
            pts = [cam.project(corners[j]) for j in idx]
            depth = sum(p[1] for p in pts) / 4
            lit = 0.55 + 0.45 * max(0.0, sum(wn[i] * LIGHT[i] for i in range(3)) / 1.07)
            polys.append((depth, [p[0] for p in pts], tuple(int(ch * lit) for ch in col), part, n, w))
    polys.sort(key=lambda x: -x[0])
    for depth, pts, col, part, n, w in polys:
        dr.polygon(pts, fill=col, outline=tuple(int(c * 0.7) for c in col))
        if part == "Head" and n == (0, 0, -1):      # simple face so you can see where it looks
            for ex in (-0.22, 0.22):
                e, _ = cam.project(w.point((ex, 0.12, -0.61)))
                dr.ellipse([e[0] - 2, e[1] - 3, e[0] + 2, e[1] + 3], fill=FACE)
            m0, _ = cam.project(w.point((-0.2, -0.2, -0.61)))
            m1, _ = cam.project(w.point((0.2, -0.2, -0.61)))
            dr.line([m0, m1], fill=FACE, width=2)
    if label:
        dr.text((8, 6), label, fill=(40, 48, 64), font=font)
    return img


def default_cam(size=(320, 320)):
    return Camera((6.5, 4.2, -9.5), (0, 2.4, 0), size)


def frames(sampler, length, fps=30, loops=1, cam=None, label=None, font=None):
    cam = cam or default_cam()
    n = max(2, int(round(length * fps * loops)))
    return [draw_frame(sampler((i / fps) % length if length > 0 else 0), cam, label, font=font) for i in range(n)]


def save_gif(path, imgs, fps=30):
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0, disposal=2)


def side_by_side(a, b):
    out = []
    n = max(len(a), len(b))
    for i in range(n):
        fa, fb = a[i % len(a)], b[i % len(b)]
        im = Image.new("RGB", (fa.width + fb.width + 4, fa.height), (255, 255, 255))
        im.paste(fa, (0, 0))
        im.paste(fb, (fa.width + 4, 0))
        out.append(im)
    return out


def font(size=16):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()
