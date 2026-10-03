"""Shared color palette. Index order is the contract between the generator,
the Roblox builder (PALETTE table) and Blender (palette texture cells)."""

# name: (r, g, b, roblox material)
COLORS = {
    # terrain
    "rock":        (124, 137, 214, "Plastic"),
    "rock_dark":   (100, 112, 192, "Plastic"),
    "rock_light":  (168, 178, 222, "Plastic"),
    "sand":        (236, 212, 128, "Plastic"),
    "sand_dark":   (222, 186, 92, "Plastic"),
    "reef_sand":   (236, 226, 160, "Plastic"),
    "reef_sand_dk": (242, 206, 88, "Plastic"),
    "grass":       (112, 182, 62, "Plastic"),
    "grass_dark":  (86, 156, 50, "Plastic"),
    "path":        (196, 172, 128, "Plastic"),
    "cobble":      (164, 160, 156, "Plastic"),
    "seabed":      (70, 96, 150, "Plastic"),
    "ocean":       (40, 112, 196, "Glass"),
    # plants
    "leaf":        (44, 124, 54, "Plastic"),
    "leaf_dark":   (30, 98, 42, "Plastic"),
    "trunk":       (112, 72, 42, "Plastic"),
    "seaweed":     (60, 176, 66, "Plastic"),
    "seaweed_dk":  (40, 140, 52, "Plastic"),
    "coral_root":  (140, 100, 82, "Plastic"),
    # built stuff
    "wood":        (152, 96, 56, "Plastic"),
    "wood_dark":   (104, 64, 36, "Plastic"),
    "plank":       (176, 116, 64, "Plastic"),
    "stone":       (142, 146, 162, "Plastic"),
    "stone_dark":  (112, 116, 132, "Plastic"),
    "cloth":       (238, 232, 218, "Plastic"),
    "cloth_brown": (140, 92, 54, "Plastic"),
    "flag_blue":   (66, 138, 222, "Plastic"),
    "metal":       (64, 64, 70, "Plastic"),
    "ship":        (98, 76, 66, "Plastic"),
    "ship_dark":   (72, 56, 48, "Plastic"),
    "fire":        (255, 136, 32, "Neon"),
    "fire_core":   (255, 222, 90, "Neon"),
    "glow":        (255, 204, 110, "Neon"),
    # detail shades (cliff facades, cobbles, ground clutter)
    "rock_gray":   (128, 134, 174, "Plastic"),
    "rock_deep":   (90, 100, 178, "Plastic"),
    "moss":        (100, 154, 58, "Plastic"),
    "moss_dark":   (74, 124, 46, "Plastic"),
    "grass_light": (146, 198, 70, "Plastic"),
    "leaf_light":  (72, 152, 60, "Plastic"),
    "sand_light":  (246, 228, 160, "Plastic"),
    "sand_wet":    (208, 180, 104, "Plastic"),
    "cobble_dark": (128, 124, 126, "Plastic"),
    "cobble_light": (188, 184, 174, "Plastic"),
    "path_dirt":   (150, 116, 78, "Plastic"),
    "cave_dark":   (28, 26, 40, "Plastic"),
    "flower_white": (246, 244, 236, "Plastic"),
    "mushroom_red": (212, 52, 46, "Plastic"),
    "barrel":      (132, 84, 46, "Plastic"),
    "rope":        (192, 162, 112, "Plastic"),
    "mesh_sand":   (246, 226, 112, "Plastic"),
    "mesh_rock":   (112, 138, 230, "Plastic"),
    # per-instance tint slots (resolved at build time)
    "accent":      (240, 110, 170, "Plastic"),
    "accent_dark": (190, 80, 130, "Plastic"),
}

NAMES = list(COLORS.keys())
INDEX = {n: i + 1 for i, n in enumerate(NAMES)}  # 1-based for Lua

CORAL_TINTS = {
    "Pink":   (240, 110, 170),
    "Orange": (240, 122, 40),
    "Yellow": (250, 210, 50),
    "Green":  (112, 210, 62),
    "Cyan":   (62, 182, 240),
    "Purple": (172, 92, 222),
}
TINT_NAMES = list(CORAL_TINTS.keys())


def darker(rgb, f=0.75):
    return tuple(int(c * f) for c in rgb)
