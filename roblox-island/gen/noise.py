"""Tiny deterministic value noise shared by the asset and map generators."""
import math


def _hash(i, j, seed):
    h = (i * 374761393 + j * 668265263 + seed * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, seed):
    i, j = math.floor(x), math.floor(z)
    fx, fz = x - i, z - j
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash(i, j, seed), _hash(i + 1, j, seed)
    c, d = _hash(i, j + 1, seed), _hash(i + 1, j + 1, seed)
    top = a + (b - a) * sx
    return top + ((c + (d - c) * sx) - top) * sz


def fbm(x, z, seed, octaves=4):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += vnoise(x * freq, z * freq, seed + o * 17) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def weighted(rng, table):
    """table: list of (value, weight)"""
    r = rng.random() * sum(w for _, w in table)
    for v, w in table:
        r -= w
        if r <= 0:
            return v
    return table[-1][0]
