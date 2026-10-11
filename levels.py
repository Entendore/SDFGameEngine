"""
Level definitions for THRESHOLD - A Surreal Journey Through Zones.
Each zone has its own color palette, theme, and mechanic focus.
Movement is rotate-then-thrust: turn to face a direction, then commit.
"""
import math
from engine import LevelLoader, LevelData

# ===================== ZONE 1: THE AWAKENING =====================
ZONE_1 = {
    "name": "The Awakening",
    "spawn": [480, 620],
    "spawn_angle": -math.pi / 2,
    "goal": [480, 100],
    "bg_color": [0.04, 0.06, 0.12],
    "boxes": [
        {"pos": [180, 440], "size": [30, 200], "color": [0.25, 0.55, 0.85]},
        {"pos": [780, 440], "size": [30, 200], "color": [0.25, 0.55, 0.85]},
        {"pos": [480, 520], "size": [200, 25], "color": [0.25, 0.55, 0.85]},
        {"pos": [340, 280], "size": [120, 25], "color": [0.3, 0.5, 0.7]},
        {"pos": [620, 280], "size": [120, 25], "color": [0.3, 0.5, 0.7]},
    ],
    "circles": [
        {"pos": [480, 380], "radius": 45, "color": [0.2, 0.4, 0.6], "bounce": 0.8},
    ],
    "orbs": [
        [150, 350], [810, 350], [480, 200]
    ],
    "checkpoints": [
        [480, 360, 22]
    ],
}

# ===================== ZONE 2: THE GARDEN =====================
ZONE_2 = {
    "name": "The Garden",
    "spawn": [100, 620],
    "spawn_angle": 0.0,
    "goal": [860, 100],
    "bg_color": [0.04, 0.10, 0.06],
    "boxes": [
        {"pos": [300, 500], "size": [200, 25], "bounce": 1.6, "color": [0.2, 0.8, 0.4]},
        {"pos": [600, 350], "size": [200, 25], "bounce": 1.8, "color": [0.2, 0.8, 0.4]},
        {"pos": [200, 200], "size": [25, 120], "bounce": 1.4, "color": [0.2, 0.8, 0.4]},
        {"pos": [750, 500], "size": [25, 100], "color": [0.15, 0.6, 0.3]},
    ],
    "circles": [
        {"pos": [450, 200], "radius": 35, "bounce": 1.5, "color": [0.3, 0.9, 0.5]},
        {"pos": [820, 250], "radius": 30, "bounce": 1.3, "color": [0.3, 0.9, 0.5]},
    ],
    "moving_shapes": [
        {
            "pos1": [500, 450], "pos2": [500, 250], "speed": 1.5, "phase": 0.0,
            "size": [70, 25], "bounce": 1.2, "color": [0.9, 0.5, 0.2]
        },
        {
            "pos1": [150, 400], "pos2": [150, 300], "speed": 2.0, "phase": 1.0,
            "radius": 28, "bounce": 1.0, "color": [0.8, 0.3, 0.6]
        }
    ],
    "lasers": [
        {"pos": [700, 150], "speed": 1.0, "length": 80, "phase": 0.0}
    ],
    "orbs": [
        [150, 350], [480, 300], [810, 420], [350, 150]
    ],
    "checkpoints": [
        [300, 560, 22],
        [700, 250, 22]
    ],
}

# ===================== ZONE 3: THE INVERSION =====================
ZONE_3 = {
    "name": "The Inversion",
    "spawn": [480, 620],
    "spawn_angle": -math.pi / 2,
    "goal": [480, 100],
    "bg_color": [0.10, 0.03, 0.12],
    "boxes": [
        {"pos": [200, 500], "size": [30, 150], "color": [0.6, 0.3, 0.85]},
        {"pos": [760, 500], "size": [30, 150], "color": [0.6, 0.3, 0.85]},
        {"pos": [200, 200], "size": [30, 150], "color": [0.6, 0.3, 0.85]},
        {"pos": [760, 200], "size": [30, 150], "color": [0.6, 0.3, 0.85]},
        {"pos": [480, 360], "size": [100, 20], "bounce": 1.5, "color": [0.85, 0.7, 0.2]},
    ],
    "circles": [
        {"pos": [340, 360], "radius": 30, "bounce": 1.6, "color": [0.9, 0.6, 0.3]},
        {"pos": [620, 360], "radius": 30, "bounce": 1.6, "color": [0.9, 0.6, 0.3]},
    ],
    "moving_shapes": [
        {
            "pos1": [120, 400], "pos2": [120, 300], "speed": -2.5, "phase": 0.0,
            "radius": 32, "bounce": 1.3, "color": [0.9, 0.2, 0.9]
        },
        {
            "pos1": [840, 300], "pos2": [840, 400], "speed": -2.5, "phase": 0.0,
            "radius": 32, "bounce": 1.3, "color": [0.9, 0.2, 0.9]
        },
        {
            "pos1": [480, 500], "pos2": [480, 580], "speed": 3.0, "phase": 0.5,
            "size": [60, 20], "color": [0.5, 0.2, 0.7]
        }
    ],
    "lasers": [
        {"pos": [480, 300], "speed": 2.0, "length": 150, "phase": 0.0},
        {"pos": [480, 420], "speed": -2.0, "length": 150, "phase": math.pi / 2}
    ],
    "orbs": [
        [120, 200], [840, 200], [120, 500], [840, 500], [480, 360]
    ],
    "checkpoints": [
        [200, 400, 22],
        [760, 400, 22]
    ],
}

# ===================== ZONE 4: THE ABYSS =====================
ZONE_4 = {
    "name": "The Abyss",
    "spawn": [100, 620],
    "spawn_angle": 0.0,
    "goal": [860, 100],
    "bg_color": [0.01, 0.01, 0.03],
    "boxes": [
        {"pos": [350, 550], "size": [25, 100], "color": [0.3, 0.3, 0.4]},
        {"pos": [600, 400], "size": [25, 100], "color": [0.3, 0.3, 0.4]},
        {"pos": [250, 250], "size": [25, 80], "color": [0.3, 0.3, 0.4]},
        {"pos": [750, 200], "size": [25, 80], "color": [0.3, 0.3, 0.4]},
    ],
    "circles": [
        {"pos": [480, 500], "radius": 25, "bounce": 1.8, "color": [0.5, 0.2, 0.2]},
    ],
    "moving_shapes": [
        {
            "pos1": [200, 450], "pos2": [400, 450], "speed": 3.0, "phase": 0.0,
            "radius": 28, "color": [0.9, 0.2, 0.3]
        },
        {
            "pos1": [700, 350], "pos2": [500, 350], "speed": -3.5, "phase": 0.5,
            "radius": 28, "color": [0.9, 0.2, 0.3]
        },
        {
            "pos1": [400, 200], "pos2": [600, 200], "speed": 4.0, "phase": 1.0,
            "radius": 25, "color": [0.9, 0.2, 0.3]
        }
    ],
    "lasers": [
        {"pos": [350, 350], "speed": 3.0, "length": 120, "phase": 0.0},
        {"pos": [600, 250], "speed": -3.5, "length": 120, "phase": 1.0},
        {"pos": [480, 600], "speed": 2.5, "length": 100, "phase": 2.0}
    ],
    "orbs": [
        [150, 450], [480, 550], [810, 350], [480, 150]
    ],
    "checkpoints": [
        [250, 500, 22],
        [500, 350, 22],
        [750, 200, 22]
    ],
}

# ===================== ZONE 5: THE CONVERGENCE =====================
ZONE_5 = {
    "name": "The Convergence",
    "spawn": [100, 620],
    "spawn_angle": 0.0,
    "goal": [860, 100],
    "bg_color": [0.06, 0.03, 0.10],
    "boxes": [
        # Bouncy lower section
        {"pos": [250, 540], "size": [180, 22], "bounce": 1.8, "color": [0.2, 0.9, 0.4]},
        {"pos": [550, 480], "size": [22, 100], "bounce": 1.5, "color": [0.2, 0.9, 0.4]},
        # Middle maze
        {"pos": [350, 380], "size": [22, 80], "color": [0.6, 0.3, 0.85]},
        {"pos": [650, 380], "size": [22, 80], "color": [0.6, 0.3, 0.85]},
        {"pos": [500, 340], "size": [120, 22], "color": [0.6, 0.3, 0.85]},
        # Upper section
        {"pos": [250, 180], "size": [22, 100], "color": [0.3, 0.5, 0.8]},
        {"pos": [700, 220], "size": [120, 22], "bounce": 1.4, "color": [0.9, 0.6, 0.2]},
    ],
    "circles": [
        {"pos": [800, 500], "radius": 30, "bounce": 1.6, "color": [0.3, 0.9, 0.5]},
        {"pos": [150, 300], "radius": 28, "bounce": 1.4, "color": [0.9, 0.5, 0.3]},
        {"pos": [480, 220], "radius": 35, "bounce": 1.7, "color": [0.5, 0.3, 0.9]},
    ],
    "moving_shapes": [
        {
            "pos1": [400, 580], "pos2": [600, 580], "speed": 2.0, "phase": 0.0,
            "size": [60, 22], "bounce": 1.3, "color": [0.9, 0.4, 0.2]
        },
        {
            "pos1": [200, 420], "pos2": [200, 320], "speed": -2.5, "phase": 0.5,
            "radius": 30, "color": [0.9, 0.2, 0.9]
        },
        {
            "pos1": [800, 350], "pos2": [800, 250], "speed": 3.0, "phase": 1.0,
            "radius": 28, "bounce": 1.2, "color": [0.2, 0.8, 1.0]
        },
        {
            "pos1": [480, 120], "pos2": [680, 120], "speed": -2.0, "phase": 0.0,
            "size": [50, 20], "color": [0.85, 0.7, 0.2]
        }
    ],
    "lasers": [
        {"pos": [480, 440], "speed": 2.5, "length": 130, "phase": 0.0},
        {"pos": [350, 250], "speed": -3.0, "length": 100, "phase": 1.0},
        {"pos": [650, 150], "speed": 2.0, "length": 90, "phase": 2.0}
    ],
    "orbs": [
        [150, 580], [400, 460], [800, 580], [150, 200],
        [480, 280], [810, 150]
    ],
    "checkpoints": [
        [200, 500, 22],
        [480, 400, 22],
        [480, 200, 22],
        [760, 300, 22]
    ],
}


def get_all_levels() -> list:
    """Convert all zone dictionaries to LevelData objects."""
    zone_dicts = [ZONE_1, ZONE_2, ZONE_3, ZONE_4, ZONE_5]
    return [LevelLoader.from_dict(zd) for zd in zone_dicts]