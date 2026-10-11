"""
THRESHOLD - A Surreal Journey Through Zones

A game about traversal through dreamlike spaces.
Movement is deliberate: rotate to face a direction, then commit by thrusting forward.
Each zone has its own palette, rhythm, and personality.
Collect orbs to activate the goal. Touch checkpoints to anchor your soul.
If you fall, you respawn at your last checkpoint — the journey never ends, it only loops.

Run: python main.py
Requires: pygame, numpy, PyOpenGL
"""
from engine import SDFEngine
from levels import get_all_levels


def main():
    levels = get_all_levels()
    engine = SDFEngine()
    engine.run(levels)


if __name__ == "__main__":
    main()