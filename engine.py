"""
SDF Engine Studio v3 - Surreal Zone Traversal Engine
Movement: Rotate to face direction, then thrust forward.
Features: Checkpoints, Zone System, Bouncy Materials, Audio, Squash/Stretch.

Controls:
  A / D / Left / Right : Rotate
  W / Up               : Thrust forward
  S / Down             : Brake
  SPACE                : Dash (in facing direction)
  ESC                  : Pause / Back to Menu
  R                    : Reduced Motion
  M                    : Mute
  F1                   : Debug Overlay
"""
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

# ===================== CONFIG =====================
WIDTH, HEIGHT = 960, 720
FPS = 60
SEED = 1337
MAX_PARTICLES = 80
MAX_TRAIL = 20
MAX_SHAPES = 32
MAX_CHECKPOINTS = 8

random.seed(SEED)
np.random.seed(SEED)

# ===================== GLSL SHADERS =====================
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aUv;
out vec2 vUv;
void main() {
    vUv = aUv;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = r"""
#version 330 core
out vec4 FragColor;
in vec2 vUv;

uniform vec2 uResolution;
uniform float uTime;
uniform vec2 uCamOffset;
uniform float uReduceMotion;

uniform vec2 uPlayerPos;
uniform vec2 uPlayerScale;
uniform float uPlayerRadius;
uniform float uPlayerAngle;

uniform vec4 uBoxes[32];
uniform vec3 uBoxColors[32];
uniform int  uBoxCount;

uniform vec4 uCircles[32];
uniform vec3 uCircleColors[32];
uniform int  uCircleCount;

uniform vec4 uLasers[8];
uniform float uLaserPhases[8];
uniform int  uLaserCount;

uniform vec3 uOrbs[16];
uniform int  uOrbCollected[16];
uniform int  uOrbCount;

uniform vec3 uCheckpoints[8];
uniform int  uCheckpointActive[8];
uniform int  uCheckpointCount;

uniform vec2 uGoalPos;
uniform float uGoalActive;

uniform vec3 uBgColor;

uniform vec4 uParticles[80];
uniform vec3 uParticleColors[80];
uniform int  uParticleCount;
uniform vec3 uTrail[20];
uniform int  uTrailCount;
uniform float uDamageFlash;
uniform float uLevelClearFlash;
uniform float uRespawnFlash;

float sdCircle(vec2 p, vec2 c, float r) { return length(p - c) - r; }
float sdBox(vec2 p, vec2 c, vec2 b) {
    vec2 d = abs(p - c) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}
float sdSegment(vec2 p, vec2 a, vec2 b, float r) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 0.0001), 0.0, 1.0);
    return length(pa - ba * h) - r;
}
float sdEllipse(vec2 p, vec2 c, vec2 ab) {
    vec2 d = p - c;
    ab = max(ab, vec2(0.001));
    float k1 = length(d / ab);
    float k2 = length(d / (ab * ab));
    return k1 * (k1 - 1.0) / max(k2, 0.001);
}

void main() {
    vec2 p = vUv * uResolution + uCamOffset;
    float t = uTime;

    float d = 1e9;
    float hazardD = 1e9;
    vec3 wallCol = vec3(0.0);

    // Arena boundaries
    float bD = sdBox(p, vec2(480.0, -30.0), vec2(530.0, 80.0));
    bD = min(bD, sdBox(p, vec2(480.0, 750.0), vec2(530.0, 80.0)));
    bD = min(bD, sdBox(p, vec2(-30.0, 360.0), vec2(80.0, 410.0)));
    bD = min(bD, sdBox(p, vec2(990.0, 360.0), vec2(80.0, 410.0)));
    d = min(d, bD);
    wallCol += vec3(0.9, 0.43, 0.86) * step(bD, d);

    for(int i=0; i<32; i++) {
        if(i >= uBoxCount) break;
        float boxD = sdBox(p, uBoxes[i].xy, uBoxes[i].zw);
        if(boxD < d) { d = boxD; wallCol = uBoxColors[i]; }
    }
    for(int i=0; i<32; i++) {
        if(i >= uCircleCount) break;
        float circD = sdCircle(p, uCircles[i].xy, uCircles[i].z);
        if(circD < d) { d = circD; wallCol = uCircleColors[i]; }
    }
    for(int i=0; i<8; i++) {
        if(i >= uLaserCount) break;
        float ang = t * uLasers[i].z + uLaserPhases[i];
        vec2 dir = vec2(cos(ang), sin(ang)) * uLasers[i].w;
        hazardD = min(hazardD, sdSegment(p, uLasers[i].xy - dir, uLasers[i].xy + dir, 6.0));
    }

    // Player body + nose
    float playerBodyD = sdEllipse(p, uPlayerPos, uPlayerScale * uPlayerRadius);
    vec2 beamDir = vec2(cos(uPlayerAngle), sin(uPlayerAngle));
    vec2 nosePos = uPlayerPos + beamDir * uPlayerRadius * 0.7;
    float noseD = sdCircle(p, nosePos, uPlayerRadius * 0.38);
    float playerD = min(playerBodyD, noseD);

    // Orbs
    float orbD = 1e9;
    for(int i=0; i<16; i++) {
        if(i >= uOrbCount) break;
        if(uOrbCollected[i] == 0) {
            float r = uOrbs[i].z + sin(t * 4.0 + float(i) * 1.5) * 2.0;
            orbD = min(orbD, sdCircle(p, uOrbs[i].xy, r));
        }
    }

    // Goal
    float goalD = 1e9;
    if(uGoalActive > 0.5) {
        goalD = sdCircle(p, uGoalPos, 28.0 + sin(t * 5.0) * 4.0);
    }

    // --- Compositing ---
    vec3 col = vec3(0.0);
    vec2 center = uResolution * 0.5;
    float distToCenter = length(p - center) / length(center);
    vec3 bgCol = mix(uBgColor * 0.8, uBgColor * 0.12, distToCenter);

    if(uReduceMotion < 0.5) {
        vec2 grid = abs(fract(p / 40.0) - 0.5);
        float gridLine = smoothstep(0.48, 0.5, max(grid.x, grid.y));
        bgCol += uBgColor * 0.4 * gridLine * 0.5;
    }
    col = bgCol;

    // Walls
    col += vec3(0.35, 0.82, 1.0) * exp(-max(d, 0.0) / 18.0) * 0.5;
    float contour = abs(sin((d + t * 8.0) * 3.14159 / 25.0));
    col += vec3(0.27, 0.43, 0.66) * smoothstep(0.9, 1.0, contour) * 0.6 * step(0.0, d);
    if(d < 0.0) {
        float depth = clamp(-d / 50.0, 0.0, 1.0);
        col = mix(wallCol, wallCol * 0.2, depth);
    }
    col += wallCol * exp(-d*d / 5.0) * 1.6;

    // Hazards
    col += vec3(1.0, 0.23, 0.23) * exp(-max(hazardD, 0.0) / 10.0) * 1.5;
    if(hazardD < 0.0) col = vec3(1.0, 0.2, 0.2);

    // Checkpoints
    for(int i=0; i<8; i++) {
        if(i >= uCheckpointCount) break;
        float cpD = sdCircle(p, uCheckpoints[i].xy, uCheckpoints[i].z);
        if(uCheckpointActive[i] > 0) {
            float pulse = 0.6 + 0.4 * sin(t * 3.0 + float(i) * 1.2);
            col += vec3(0.43, 0.82, 1.0) * exp(-max(cpD, 0.0) / 12.0) * pulse;
            float ring = abs(cpD) - 3.0;
            col += vec3(0.6, 0.95, 1.0) * exp(-abs(ring) / 2.5) * 0.6 * pulse;
        } else {
            col += vec3(0.35, 0.35, 0.45) * exp(-max(cpD, 0.0) / 12.0) * 0.5;
            col += vec3(0.4, 0.4, 0.5) * exp(-abs(cpD) / 2.5) * 0.25;
        }
    }

    // Orbs
    col += vec3(0.43, 1.0, 0.74) * exp(-max(orbD, 0.0) / 15.0) * 1.5;
    if(orbD < 0.0) col = vec3(0.43, 1.0, 0.74);

    // Trail
    for(int i=0; i<20; i++) {
        if(i >= uTrailCount) break;
        float td = length(p - uTrail[i].xy);
        float trailGlow = exp(-td / 12.0) * (1.0 - uTrail[i].z) * 0.4;
        col += vec3(1.0, 0.92, 0.43) * trailGlow;
    }

    // Particles
    for(int i=0; i<80; i++) {
        if(i >= uParticleCount) break;
        float pd = length(p - uParticles[i].xy);
        float glow = exp(-pd / max(uParticles[i].z, 1.0)) * uParticles[i].w;
        col += uParticleColors[i] * glow;
    }

    // Player direction beam
    vec2 beamEnd = uPlayerPos + beamDir * 48.0;
    float beamD = sdSegment(p, uPlayerPos, beamEnd, 2.0);
    col += vec3(1.0, 0.92, 0.43) * exp(-max(beamD, 0.0) / 3.0) * 0.35;

    // Player
    col += vec3(1.0, 0.92, 0.43) * exp(-max(playerD, 0.0) / 12.0) * 1.5;
    if(playerD < 0.0) col = vec3(1.0, 0.92, 0.43);

    // Goal
    if(uGoalActive > 0.5) {
        col += vec3(1.0, 0.35, 0.54) * exp(-max(goalD, 0.0) / 20.0) * 1.5;
        if(goalD < 0.0) col = vec3(1.0, 0.35, 0.54);
    }

    // --- Post-Processing ---
    if(uReduceMotion < 0.5) {
        vec2 uv = vUv * 2.0 - 1.0;
        float r2 = dot(uv, uv);
        uv *= 1.0 + r2 * 0.015;
        uv = uv * 0.5 + 0.5;
        float scan = sin(uv.y * uResolution.y * 3.1415 * 2.0) * 0.04 + 0.96;
        col *= scan;
        float vig = smoothstep(1.0, 0.2, length(uv - 0.5) * 1.4);
        col *= vig;
    }

    col = mix(col, vec3(1.0, 0.0, 0.0), uDamageFlash * 0.7);
    col = mix(col, vec3(0.4, 1.0, 0.6), uLevelClearFlash * 0.5);
    col = mix(col, vec3(0.3, 0.7, 1.0), uRespawnFlash * 0.5);
    col = col / (1.0 + col * 0.3);
    col = pow(col, vec3(0.85));

    FragColor = vec4(col, 1.0);
}
"""

# ===================== SDF MATH (CPU) =====================
def sd_circle(p, c, r): return float(np.linalg.norm(p - c)) - r
def sd_segment(p, a, b, r):
    pa = p - a; ba = b - a
    h = float(np.clip(np.dot(pa, ba) / max(float(np.dot(ba, ba)), 1e-6), 0.0, 1.0))
    return float(np.linalg.norm(pa - ba * h)) - r
def sd_box(p, c, b):
    d = abs(p - c) - b
    return float(np.linalg.norm(np.maximum(d, 0.0)) + min(max(d[0], d[1]), 0.0))

# ===================== AUDIO ENGINE =====================
class AudioEngine:
    def __init__(self):
        self.available = False
        self.muted = False
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self.available = True
            self.sr = 44100
            self._generate_sounds()
        except Exception:
            self.available = False

    def _make_sound(self, samples):
        stereo = np.column_stack([samples, samples])
        stereo = np.clip(stereo, -1.0, 1.0)
        return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

    def _generate_sounds(self):
        sr = self.sr
        t = np.linspace(0, 0.15, int(sr * 0.15))
        env = np.exp(-t * 12)
        wave = env * np.sin(2 * np.pi * (150 + 600 * (t / 0.15)) * t) * 0.25
        wave += env * (np.random.random(len(t)) - 0.5) * 0.15
        self.sounds = {'dash': self._make_sound(wave)}

        t = np.linspace(0, 0.25, int(sr * 0.25))
        env = np.exp(-t * 7)
        wave = env * np.sin(2 * np.pi * (523 + 440 * (t / 0.25)) * t) * 0.25
        wave += env * np.sin(2 * np.pi * (523 + 440 * (t / 0.25)) * 1.5 * t) * 0.12
        self.sounds['orb'] = self._make_sound(wave)

        t = np.linspace(0, 0.1, int(sr * 0.1))
        env = np.exp(-t * 15)
        wave = env * np.sin(2 * np.pi * 800 * t) * 0.2
        self.sounds['select'] = self._make_sound(wave)

        # Checkpoint sound - ascending chime
        t = np.linspace(0, 0.4, int(sr * 0.4))
        env = np.exp(-t * 4)
        wave = env * np.sin(2 * np.pi * 523 * t) * 0.15
        wave += env * np.sin(2 * np.pi * 659 * t) * 0.12
        wave += env * np.sin(2 * np.pi * 784 * t) * 0.1
        self.sounds['checkpoint'] = self._make_sound(wave)

        t = np.linspace(0, 0.12, int(sr * 0.12))
        env = np.exp(-t * 18)
        wave = env * np.sin(2 * np.pi * 300 * t) * 0.3
        wave += env * (np.random.random(len(t)) - 0.5) * 0.1
        self.sounds['bounce'] = self._make_sound(wave)

        t = np.linspace(0, 0.4, int(sr * 0.4))
        env = np.exp(-t * 5)
        wave = env * np.sin(2 * np.pi * (70 + 30 * np.sin(t * 15)) * t) * 0.4
        wave += env * (np.random.random(len(t)) - 0.5) * 0.25
        self.sounds['hit'] = self._make_sound(wave)

        t = np.linspace(0, 1.2, int(sr * 1.2))
        wave = np.zeros_like(t)
        notes = [523, 659, 784, 1047, 1319]
        for i, f in enumerate(notes):
            mask = (t >= i * 0.15) & (t < (i + 1) * 0.3)
            local_t = t[mask] - i * 0.15
            wave[mask] += np.sin(2 * np.pi * f * t[mask]) * np.exp(-local_t * 5) * 0.25
        self.sounds['win'] = self._make_sound(wave)

    def play(self, name, volume=1.0):
        if not self.available or self.muted: return
        if name in self.sounds:
            self.sounds[name].set_volume(volume)
            self.sounds[name].play()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

# ===================== LEVEL SYSTEM =====================
@dataclass
class Shape:
    center: np.ndarray
    color: tuple = (0.9, 0.43, 0.86)
    bounce: float = 0.0

@dataclass
class BoxShape(Shape):
    half_size: np.ndarray = field(default_factory=lambda: np.array([20.0, 20.0]))

@dataclass
class CircleShape(Shape):
    radius: float = 30.0

@dataclass
class MovingShape:
    shape: Shape
    pos1: np.ndarray
    pos2: np.ndarray
    speed: float = 1.0
    phase: float = 0.0
    def update(self, t):
        s = (math.sin(t * self.speed + self.phase) + 1.0) / 2.0
        self.shape.center = self.pos1 * (1.0 - s) + self.pos2 * s

@dataclass
class LevelData:
    name: str = "Untitled Zone"
    spawn: np.ndarray = field(default_factory=lambda: np.array([WIDTH/2, HEIGHT-100], dtype=np.float32))
    spawn_angle: float = -math.pi / 2
    goal: np.ndarray = field(default_factory=lambda: np.array([WIDTH/2, 100], dtype=np.float32))
    bg_color: tuple = (0.086, 0.117, 0.25)
    boxes: List[BoxShape] = field(default_factory=list)
    circles: List[CircleShape] = field(default_factory=list)
    lasers: List[Dict] = field(default_factory=list)
    orbs: List[np.ndarray] = field(default_factory=list)
    checkpoints: List[np.ndarray] = field(default_factory=list)
    moving_shapes: List[MovingShape] = field(default_factory=list)

class LevelLoader:
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> LevelData:
        lvl = LevelData(name=data.get("name", "Custom Zone"))
        lvl.spawn = np.array(data.get("spawn", [WIDTH/2, HEIGHT-100]), dtype=np.float32)
        lvl.spawn_angle = float(data.get("spawn_angle", -math.pi / 2))
        lvl.goal = np.array(data.get("goal", [WIDTH/2, 100]), dtype=np.float32)
        lvl.bg_color = tuple(data.get("bg_color", [0.086, 0.117, 0.25]))

        def parse_shape(s, cls, pos_key="pos"):
            kwargs = {
                'center': np.array(s[pos_key], dtype=np.float32),
                'color': tuple(s.get("color", [0.9, 0.43, 0.86])),
                'bounce': float(s.get("bounce", 0.0)),
            }
            if cls == BoxShape:
                kwargs['half_size'] = np.array(s["size"], dtype=np.float32) / 2.0
            else:
                kwargs['radius'] = float(s.get("radius", 30.0))
            return cls(**kwargs)

        for b in data.get("boxes", []):
            lvl.boxes.append(parse_shape(b, BoxShape))
        for c in data.get("circles", []):
            lvl.circles.append(parse_shape(c, CircleShape))

        for ms in data.get("moving_shapes", []):
            base_shape = parse_shape(ms, BoxShape if "size" in ms else CircleShape, pos_key="pos1")
            lvl.moving_shapes.append(MovingShape(
                shape=base_shape,
                pos1=np.array(ms["pos1"], dtype=np.float32),
                pos2=np.array(ms["pos2"], dtype=np.float32),
                speed=float(ms.get("speed", 1.0)),
                phase=float(ms.get("phase", 0.0))
            ))
            
        for l in data.get("lasers", []):
            lvl.lasers.append({
                "center": np.array(l["pos"], dtype=np.float32),
                "speed": float(l.get("speed", 1.0)),
                "length": float(l.get("length", 100.0)),
                "phase": float(l.get("phase", 0.0))
            })
        for o in data.get("orbs", []):
            lvl.orbs.append(np.array([o[0], o[1], 10.0], dtype=np.float32))
        for cp in data.get("checkpoints", []):
            r = cp[2] if len(cp) > 2 else 22.0
            lvl.checkpoints.append(np.array([cp[0], cp[1], r], dtype=np.float32))

        return lvl

    @staticmethod
    def update(level: LevelData, t):
        for ms in level.moving_shapes:
            ms.update(t)

    @staticmethod
    def evaluate_sdf(level: LevelData, p, t):
        if p[0] < 0 or p[0] > WIDTH or p[1] < 0 or p[1] > HEIGHT:
            return -10.0, False, None
        d = 1e9
        hit_obj = None

        for b in level.boxes:
            bd = sd_box(p, b.center, b.half_size)
            if bd < d: d = bd; hit_obj = b
        for c in level.circles:
            cd = sd_circle(p, c.center, c.radius)
            if cd < d: d = cd; hit_obj = c
        for ms in level.moving_shapes:
            if isinstance(ms.shape, BoxShape):
                bd = sd_box(p, ms.shape.center, ms.shape.half_size)
                if bd < d: d = bd; hit_obj = ms.shape
            else:
                cd = sd_circle(p, ms.shape.center, ms.shape.radius)
                if cd < d: d = cd; hit_obj = ms.shape

        hazard_d = 1e9
        for l in level.lasers:
            ang = t * l["speed"] + l["phase"]
            dir_vec = np.array([math.cos(ang), math.sin(ang)], dtype=np.float32) * l["length"]
            hazard_d = min(hazard_d, sd_segment(p, l["center"] - dir_vec, l["center"] + dir_vec, 6.0))

        if hazard_d < d:
            return hazard_d, True, None
        return d, False, hit_obj

    @staticmethod
    def normal_at(level: LevelData, p, t, eps=2.0):
        d0, _, _ = LevelLoader.evaluate_sdf(level, p, t)
        dx, _, _ = LevelLoader.evaluate_sdf(level, p + np.array([eps, 0], dtype=np.float32), t)
        dy, _, _ = LevelLoader.evaluate_sdf(level, p + np.array([0, eps], dtype=np.float32), t)
        n = np.array([dx - d0, dy - d0], dtype=np.float32)
        l = float(np.linalg.norm(n))
        return n / l if l > 1e-6 else np.array([0.0, -1.0], dtype=np.float32)

# ===================== ENGINE ENTITIES =====================
@dataclass
class Player:
    pos: np.ndarray
    angle: float = -math.pi / 2
    vel: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    radius: float = 12.0
    trail: list = field(default_factory=list)
    trail_timer: float = 0.0
    dash_cd: float = 0.0
    dash_time: float = 0.0
    invuln: float = 0.0
    hp: int = 3
    max_hp: int = 3
    scale: np.ndarray = field(default_factory=lambda: np.array([1.0, 1.0], dtype=np.float32))

    def update(self, dt, level: LevelData, t, rotate_input, thrust_input, brake_input, dash_pressed):
        events = []
        if dt <= 0: return events

        # --- Rotation (change direction) ---
        rot_speed = 3.5
        self.angle += rotate_input * rot_speed * dt

        # --- Dash ---
        if dash_pressed and self.dash_cd <= 0:
            forward = np.array([math.cos(self.angle), math.sin(self.angle)], dtype=np.float32)
            self.dash_time = 0.18
            self.dash_cd = 1.2
            self.invuln = max(self.invuln, 0.25)
            self.vel = forward * 700.0
            self.scale = np.array([1.3, 0.8], dtype=np.float32)
            events.append({"type": "dash", "pos": self.pos.copy()})

        self.dash_cd = max(0, self.dash_cd - dt)
        self.dash_time = max(0, self.dash_time - dt)
        self.invuln = max(0, self.invuln - dt)
        self.scale += (np.array([1.0, 1.0], dtype=np.float32) - self.scale) * min(1.0, dt * 10.0)

        # --- Thrust (go forward) ---
        forward = np.array([math.cos(self.angle), math.sin(self.angle)], dtype=np.float32)
        accel = 3500.0 if self.dash_time > 0 else 2200.0
        max_speed = 650.0 if self.dash_time > 0 else 380.0

        if thrust_input:
            self.vel = self.vel + forward * accel * dt

        # Friction / brake
        if brake_input:
            self.vel = self.vel * max(0.0, 1.0 - 8.0 * dt)
        else:
            friction = 4.0 if self.dash_time > 0 else 2.8
            self.vel = self.vel * max(0.0, 1.0 - friction * dt)

        speed = float(np.linalg.norm(self.vel))
        if speed > max_speed:
            self.vel = self.vel * (max_speed / speed)
            speed = max_speed

        # --- Collision ---
        remaining_dist = speed * dt
        dir_vec = self.vel / max(speed, 1e-6)
        safety = 0
        while remaining_dist > 0.1 and safety < 10:
            safety += 1
            d, is_hazard, hit_obj = LevelLoader.evaluate_sdf(level, self.pos, t)
            if d < self.radius:
                n = LevelLoader.normal_at(level, self.pos, t)
                if is_hazard and self.invuln <= 0:
                    events.append({"type": "hit", "pos": self.pos.copy(), "normal": n.copy()})
                    self._take_damage(n)
                    return events
                else:
                    push = (self.radius - d) + 0.5
                    self.pos = self.pos + n * push
                    vn = float(np.dot(self.vel, n))
                    if vn < 0:
                        impact = -vn
                        bounce_amt = getattr(hit_obj, 'bounce', 0.0) if hit_obj else 0.0
                        if bounce_amt > 0:
                            self.vel = self.vel - (1.0 + bounce_amt) * vn * n
                            events.append({"type": "bounce", "pos": self.pos.copy(), "normal": n.copy(), "impact": impact})
                            self.scale = np.array([1.0 + abs(n[0])*0.4, 1.0 - abs(n[0])*0.2], dtype=np.float32)
                        else:
                            self.vel = self.vel - (1.0 + 0.15) * vn * n
                            if impact > 30:
                                events.append({"type": "wall_hit", "pos": self.pos.copy(), "normal": n.copy(), "impact": impact})
                dir_vec = self.vel / max(float(np.linalg.norm(self.vel)), 1e-6)
                remaining_dist = float(np.linalg.norm(self.vel * dt))
            else:
                safe_dist = max(0.1, d - self.radius)
                move = min(remaining_dist, safe_dist)
                self.pos = self.pos + dir_vec * move
                remaining_dist -= move

        self.trail_timer += dt
        if self.trail_timer > 0.025:
            self.trail.append(self.pos.copy()); self.trail_timer = 0.0
        self.trail = self.trail[-MAX_TRAIL:]
        return events

    def _take_damage(self, n):
        self.hp -= 1
        self.invuln = 1.0
        self.vel = -n * 450.0
        self.dash_time = 0

    def get_trail_shader_data(self):
        count = len(self.trail)
        data = np.zeros((MAX_TRAIL, 3), dtype=np.float32)
        for i, pos in enumerate(self.trail):
            age = i / max(count - 1, 1)
            data[i] = [pos[0], pos[1], age]
        return data, count

@dataclass
class Camera:
    shake_amp: float = 0.0
    offset: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    def update(self, dt, reduce_motion=False):
        if reduce_motion:
            self.shake_amp = 0.0; self.offset[:] = 0; return
        self.shake_amp *= math.exp(-5.0 * dt)
        if self.shake_amp < 0.1: self.shake_amp = 0.0; self.offset[:] = 0
        else:
            t = pygame.time.get_ticks() / 1000.0
            self.offset[0] = (math.sin(t * 31.7) * 0.7 + math.sin(t * 47.3) * 0.3) * self.shake_amp
            self.offset[1] = (math.sin(t * 29.3) * 0.6 + math.sin(t * 53.1) * 0.4) * self.shake_amp
    def add_shake(self, amount, reduce_motion=False):
        if reduce_motion: return
        self.shake_amp = min(12.0, self.shake_amp + amount)

@dataclass
class Particle:
    pos: np.ndarray; vel: np.ndarray; life: float; max_life: float; size: float; color: tuple

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    def emit_burst(self, pos, count, color, speed_range=(50, 250), life_range=(0.3, 0.7), size_range=(3, 8)):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(*speed_range)
            vel = np.array([math.cos(ang), math.sin(ang)], dtype=np.float32) * spd
            life = random.uniform(*life_range)
            self.particles.append(Particle(
                pos=pos.copy() if isinstance(pos, np.ndarray) else np.array(pos, dtype=np.float32),
                vel=vel, life=life, max_life=life,
                size=random.uniform(*size_range), color=color
            ))
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]
    def update(self, dt):
        for p in self.particles:
            p.pos = p.pos + p.vel * dt
            p.vel = p.vel * max(0.0, 1.0 - 3.0 * dt)
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]
    def get_shader_data(self):
        count = len(self.particles)
        positions = np.zeros((MAX_PARTICLES, 4), dtype=np.float32)
        colors = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
        for i, p in enumerate(self.particles):
            positions[i] = [p.pos[0], p.pos[1], p.size, p.life / p.max_life]
            colors[i] = p.color
        return positions, colors, count

# ===================== OPENGL TEXT RENDERER =====================
class GLTextRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 48, bold=True)
        self.cache = {}
    def get_texture(self, text, font, color):
        key = (text, font, color)
        if key not in self.cache:
            surf = font.render(text, True, color).convert_alpha()
            data = pygame.image.tostring(surf, 'RGBA', True)
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.get_width(), surf.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            self.cache[key] = (tex, surf.get_width(), surf.get_height())
        return self.cache[key]
    def render(self, text, x, y, font=None, color=(255, 255, 255)):
        if font is None: font = self.font
        tex, w, h = self.get_texture(text, font, color)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        x0 = (x / WIDTH) * 2.0 - 1.0
        y0 = 1.0 - (y / HEIGHT) * 2.0
        x1 = ((x + w) / WIDTH) * 2.0 - 1.0
        y1 = 1.0 - ((y + h) / HEIGHT) * 2.0
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x1, y0)
        glTexCoord2f(1, 1); glVertex2f(x1, y1)
        glTexCoord2f(0, 1); glVertex2f(x0, y1)
        glEnd()
        glDisable(GL_TEXTURE_2D)
    def render_centered(self, text, cx, cy, font=None, color=(255, 255, 255)):
        if font is None: font = self.font
        tex, w, h = self.get_texture(text, font, color)
        self.render(text, cx - w // 2, cy - h // 2, font, color)

# ===================== ENGINE CORE =====================
class SDFEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption("Threshold - A Surreal Journey")
        self.clock = pygame.time.Clock()

        self.shader = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER))

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0
        ], dtype=np.float32)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        stride = vertices.itemsize * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))

        glUseProgram(self.shader)
        self.u = {name: glGetUniformLocation(self.shader, name) for name in [
            "uTime", "uResolution", "uCamOffset", "uReduceMotion",
            "uPlayerPos", "uPlayerScale", "uPlayerRadius", "uPlayerAngle",
            "uBoxes", "uBoxColors", "uBoxCount", "uCircles", "uCircleColors", "uCircleCount",
            "uLasers", "uLaserPhases", "uLaserCount", "uOrbs", "uOrbCollected", "uOrbCount",
            "uCheckpoints", "uCheckpointActive", "uCheckpointCount",
            "uGoalPos", "uGoalActive", "uBgColor",
            "uParticles", "uParticleColors", "uParticleCount",
            "uTrail", "uTrailCount", "uDamageFlash", "uLevelClearFlash", "uRespawnFlash"
        ]}

        self.text = GLTextRenderer()
        self.audio = AudioEngine()
        self.particles = ParticleSystem()
        self.camera = Camera()
        self.reduce_motion = False
        self.muted = False
        self.time = 0.0
        self.damage_flash = 0.0
        self.level_clear_flash = 0.0
        self.respawn_flash = 0.0
        self.hit_stop = 0.0
        self.frame_times = []
        self.state = "MENU"
        self.menu_idx = 0
        self.zone_title_timer = 0.0
        self.respawn_text_timer = 0.0
        self.debug_overlay = False

    def load_level(self, level_data: LevelData):
        self.level = level_data
        self.player = Player(pos=self.level.spawn.copy(), angle=self.level.spawn_angle)
        self.orbs_collected = [0] * len(self.level.orbs)
        self.collected_count = 0
        self.checkpoint_active = [0] * len(self.level.checkpoints)
        self.current_checkpoint = -1
        self.goal_active = (len(self.level.orbs) == 0)
        self.particles.particles.clear()
        self.camera.shake_amp = 0
        self.damage_flash = 0
        self.level_clear_flash = 0
        self.respawn_flash = 0
        self.hit_stop = 0
        self.zone_title_timer = 3.0
        self.respawn_text_timer = 0.0

    def run(self, levels: List[LevelData]):
        self.levels = levels
        self.current_level_idx = 0

        running = True
        while running:
            raw_dt = self.clock.tick(FPS) / 1000.0
            dt = min(raw_dt, 1/30)
            self.frame_times.append(raw_dt)
            if len(self.frame_times) > 120: self.frame_times.pop(0)

            for e in pygame.event.get():
                if e.type == pygame.QUIT: running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.state == "PLAYING": self.state = "PAUSED"
                        elif self.state == "PAUSED": self.state = "PLAYING"
                        elif self.state == "PAUSED": self.state = "MENU"
                        else: running = False
                    elif e.key == pygame.K_r: self.reduce_motion = not self.reduce_motion
                    elif e.key == pygame.K_m: self.muted = self.audio.toggle_mute()
                    elif e.key == pygame.K_F1: self.debug_overlay = not self.debug_overlay

                    if self.state == "MENU":
                        if e.key in (pygame.K_w, pygame.K_UP): self.menu_idx = (self.menu_idx - 1) % len(self.levels)
                        elif e.key in (pygame.K_s, pygame.K_DOWN): self.menu_idx = (self.menu_idx + 1) % len(self.levels)
                        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.current_level_idx = self.menu_idx
                            self.load_level(self.levels[self.menu_idx])
                            self.state = "PLAYING"
                            self.audio.play('select')
                    elif self.state == "PLAYING":
                        if e.key == pygame.K_SPACE:
                            if self.player.dash_cd <= 0: self.dash_pressed = True
                    elif self.state == "WIN":
                        if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                            next_idx = self.current_level_idx + 1
                            if next_idx >= len(self.levels):
                                self.state = "COMPLETE"
                            else:
                                self.current_level_idx = next_idx
                                self.menu_idx = next_idx
                                self.load_level(self.levels[next_idx])
                                self.state = "PLAYING"
                                self.audio.play('select')
                    elif self.state == "COMPLETE":
                        if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = "MENU"
                            self.audio.play('select')

            sim_dt = dt
            if self.hit_stop > 0:
                self.hit_stop -= dt
                sim_dt = 0

            self.time += dt
            self.zone_title_timer = max(0, self.zone_title_timer - dt)
            self.respawn_text_timer = max(0, self.respawn_text_timer - dt)
            self.camera.update(dt, self.reduce_motion)
            self.damage_flash = max(0, self.damage_flash - dt * 3)
            self.level_clear_flash = max(0, self.level_clear_flash - dt * 1.5)
            self.respawn_flash = max(0, self.respawn_flash - dt * 2)

            if self.state == "PLAYING":
                LevelLoader.update(self.level, self.time)
                self.update(sim_dt, dt)

            self.particles.update(sim_dt if self.state == "PLAYING" else dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def update(self, dt, real_dt):
        if dt <= 0: return
        keys = pygame.key.get_pressed()
        rotate_input = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        thrust_input = 1 if (keys[pygame.K_w] or keys[pygame.K_UP]) else 0
        brake_input = 1 if (keys[pygame.K_s] or keys[pygame.K_DOWN]) else 0

        events = self.player.update(dt, self.level, self.time, rotate_input, thrust_input, brake_input, getattr(self, 'dash_pressed', False))
        self.dash_pressed = False

        for ev in events:
            if ev["type"] == "dash":
                self.particles.emit_burst(ev["pos"], 8, (1.0, 0.92, 0.43), speed_range=(50, 150))
                self.audio.play('dash', 0.5)
            elif ev["type"] == "hit":
                self.camera.add_shake(12.0, self.reduce_motion)
                self.hit_stop = 0.12
                self.damage_flash = 1.0
                self.particles.emit_burst(ev["pos"], 20, (1.0, 0.2, 0.2))
                self.audio.play('hit', 0.8)
                if self.player.hp <= 0:
                    # --- Respawn at checkpoint ---
                    if self.current_checkpoint >= 0:
                        cp = self.level.checkpoints[self.current_checkpoint]
                        self.player.pos = cp[:2].copy()
                    else:
                        self.player.pos = self.level.spawn.copy()
                        self.player.angle = self.level.spawn_angle
                    self.player.hp = self.player.max_hp
                    self.player.vel = np.zeros(2, dtype=np.float32)
                    self.player.invuln = 2.0
                    self.respawn_flash = 1.0
                    self.respawn_text_timer = 1.5
                    self.particles.emit_burst(self.player.pos, 25, (0.43, 0.82, 1.0))
                    self.audio.play('checkpoint', 0.6)
            elif ev["type"] == "bounce":
                self.particles.emit_burst(ev["pos"], 8, (0.2, 0.9, 1.0), speed_range=(50, 150))
                self.audio.play('bounce', 0.4)
                self.camera.add_shake(min(ev["impact"] / 30, 4), self.reduce_motion)
            elif ev["type"] == "wall_hit":
                self.particles.emit_burst(ev["pos"], 4, (0.35, 0.82, 1.0), speed_range=(30, 80))

        # Brake particles
        if brake_input and float(np.linalg.norm(self.player.vel)) > 50:
            if random.random() < 0.4:
                forward = np.array([math.cos(self.player.angle), math.sin(self.player.angle)], dtype=np.float32)
                pos = self.player.pos - forward * 15 + np.array([random.uniform(-8, 8), random.uniform(-8, 8)], dtype=np.float32)
                self.particles.emit_burst(pos, 1, (1.0, 0.5, 0.2), speed_range=(20, 60), life_range=(0.2, 0.4), size_range=(2, 4))

        # Checkpoint collision
        for i, cp in enumerate(self.level.checkpoints):
            if self.checkpoint_active[i] == 0:
                if float(np.linalg.norm(self.player.pos - cp[:2])) < self.player.radius + cp[2]:
                    self.checkpoint_active[i] = 1
                    self.current_checkpoint = i
                    self.particles.emit_burst(cp[:2], 15, (0.43, 0.82, 1.0))
                    self.audio.play('checkpoint', 0.6)

        # Orb collision
        for i, orb in enumerate(self.level.orbs):
            if self.orbs_collected[i] == 0:
                if float(np.linalg.norm(self.player.pos - orb[:2])) < self.player.radius + orb[2]:
                    self.orbs_collected[i] = 1
                    self.collected_count += 1
                    self.particles.emit_burst(orb[:2], 10, (0.43, 1.0, 0.74))
                    self.audio.play('orb', 0.5)
                    if self.collected_count == len(self.level.orbs):
                        self.goal_active = True

        # Goal collision
        if self.goal_active:
            if float(np.linalg.norm(self.player.pos - self.level.goal)) < 25:
                self.state = "WIN"
                self.level_clear_flash = 1.0
                self.particles.emit_burst(self.player.pos, 40, (1.0, 0.35, 0.54))
                self.audio.play('win', 0.8)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        rm = 1.0 if self.reduce_motion else 0.0
        glUniform1f(self.u["uTime"], self.time)
        glUniform2f(self.u["uResolution"], WIDTH, HEIGHT)
        glUniform2f(self.u["uCamOffset"], self.camera.offset[0], self.camera.offset[1])
        glUniform1f(self.u["uReduceMotion"], rm)

        if self.state == "MENU":
            self._draw_menu()
            return

        glUniform2f(self.u["uPlayerPos"], self.player.pos[0], self.player.pos[1])
        glUniform2f(self.u["uPlayerScale"], self.player.scale[0], self.player.scale[1])
        glUniform1f(self.u["uPlayerRadius"], self.player.radius)
        glUniform1f(self.u["uPlayerAngle"], self.player.angle)
        glUniform1f(self.u["uDamageFlash"], self.damage_flash)
        glUniform1f(self.u["uLevelClearFlash"], self.level_clear_flash)
        glUniform1f(self.u["uRespawnFlash"], self.respawn_flash)
        glUniform3f(self.u["uBgColor"], self.level.bg_color[0], self.level.bg_color[1], self.level.bg_color[2])

        # Boxes
        all_boxes = self.level.boxes + [ms.shape for ms in self.level.moving_shapes if isinstance(ms.shape, BoxShape)]
        box_data = []; box_cols = []
        for b in all_boxes:
            box_data.extend([b.center[0], b.center[1], b.half_size[0], b.half_size[1]])
            box_cols.extend(b.color)
        glUniform4fv(self.u["uBoxes"], max(1, len(box_data)//4), box_data if box_data else [0,0,0,0])
        glUniform3fv(self.u["uBoxColors"], max(1, len(box_cols)//3), box_cols if box_cols else [0,0,0])
        glUniform1i(self.u["uBoxCount"], len(all_boxes))

        # Circles
        all_circs = self.level.circles + [ms.shape for ms in self.level.moving_shapes if isinstance(ms.shape, CircleShape)]
        circ_data = []; circ_cols = []
        for c in all_circs:
            circ_data.extend([c.center[0], c.center[1], c.radius, c.bounce])
            circ_cols.extend(c.color)
        glUniform4fv(self.u["uCircles"], max(1, len(circ_data)//4), circ_data if circ_data else [0,0,0,0])
        glUniform3fv(self.u["uCircleColors"], max(1, len(circ_cols)//3), circ_cols if circ_cols else [0,0,0])
        glUniform1i(self.u["uCircleCount"], len(all_circs))

        # Lasers
        las_data = []; las_phases = []
        for l in self.level.lasers:
            las_data.extend([l["center"][0], l["center"][1], l["speed"], l["length"]])
            las_phases.append(l["phase"])
        glUniform4fv(self.u["uLasers"], max(1, len(las_data)//4), las_data if las_data else [0,0,0,0])
        glUniform1fv(self.u["uLaserPhases"], max(1, len(las_phases)), las_phases if las_phases else [0.0])
        glUniform1i(self.u["uLaserCount"], len(self.level.lasers))

        # Orbs
        orb_data = []
        for o in self.level.orbs:
            orb_data.extend([o[0], o[1], o[2]])
        glUniform3fv(self.u["uOrbs"], max(1, len(orb_data)//3), orb_data if orb_data else [0,0,0])
        glUniform1iv(self.u["uOrbCollected"], max(1, len(self.orbs_collected)), self.orbs_collected if self.orbs_collected else [0])
        glUniform1i(self.u["uOrbCount"], len(self.level.orbs))

        # Checkpoints
        cp_data = []
        for cp in self.level.checkpoints:
            cp_data.extend([cp[0], cp[1], cp[2]])
        glUniform3fv(self.u["uCheckpoints"], max(1, len(cp_data)//3), cp_data if cp_data else [0,0,0])
        glUniform1iv(self.u["uCheckpointActive"], max(1, len(self.checkpoint_active)), self.checkpoint_active if self.checkpoint_active else [0])
        glUniform1i(self.u["uCheckpointCount"], len(self.level.checkpoints))

        glUniform1f(self.u["uGoalActive"], 1.0 if self.goal_active else 0.0)
        glUniform2f(self.u["uGoalPos"], self.level.goal[0], self.level.goal[1])

        trail_data, trail_count = self.player.get_trail_shader_data()
        glUniform3fv(self.u["uTrail"], MAX_TRAIL, trail_data.flatten())
        glUniform1i(self.u["uTrailCount"], trail_count)

        ppos, pcol, pcount = self.particles.get_shader_data()
        glUniform4fv(self.u["uParticles"], MAX_PARTICLES, ppos.flatten())
        glUniform3fv(self.u["uParticleColors"], MAX_PARTICLES, pcol.flatten())
        glUniform1i(self.u["uParticleCount"], pcount)

        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        self._draw_ui()

    def _draw_ui(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if self.state == "PLAYING":
            self.text.render_centered(f"ZONE {self.current_level_idx + 1}", WIDTH//2, 20, self.text.font, (255, 255, 255))
            self.text.render(f"HP: {'O' * self.player.hp}", 20, 20, self.text.font, (255, 235, 110))
            if len(self.level.orbs) > 0:
                self.text.render(f"ORBS: {self.collected_count} / {len(self.level.orbs)}", WIDTH-150, 20, self.text.font, (110, 255, 190))
            if self.goal_active:
                pulse = 0.7 + 0.3 * math.sin(self.time * 6)
                self.text.render_centered("GOAL ACTIVE", WIDTH//2, 50, self.text.font, (int(255*pulse), int(90*pulse), int(140*pulse)))

            # Zone title overlay (fade in/out)
            if self.zone_title_timer > 0:
                fade_in = min(1.0, (3.0 - self.zone_title_timer) * 2.0)
                fade_out = min(1.0, self.zone_title_timer / 1.0)
                alpha = fade_in * fade_out
                c = int(255 * alpha)
                self.text.render_centered(self.level.name, WIDTH//2, HEIGHT//2 - 80, self.text.font_big, (c, c, c))

            # Respawn text
            if self.respawn_text_timer > 0:
                alpha = min(1.0, self.respawn_text_timer / 1.5)
                c = int(255 * alpha)
                self.text.render_centered("RESPAWNING", WIDTH//2, HEIGHT//2 - 40, self.text.font_md, (int(100*c/255), int(200*c/255), c))

        elif self.state == "PAUSED":
            self.text.render_centered("PAUSED", WIDTH//2, HEIGHT//2 - 30, self.text.font_big, (255, 255, 255))
            self.text.render_centered("Press ESC to resume", WIDTH//2, HEIGHT//2 + 30, self.text.font, (200, 200, 200))
            self.text.render_centered("Press ESC again for Menu", WIDTH//2, HEIGHT//2 + 60, self.text.font, (200, 200, 200))
        elif self.state == "WIN":
            self.text.render_centered("ZONE COMPLETE", WIDTH//2, HEIGHT//2 - 30, self.text.font_big, (110, 255, 190))
            if self.current_level_idx + 1 < len(self.levels):
                self.text.render_centered("Press ENTER for next zone", WIDTH//2, HEIGHT//2 + 30, self.text.font, (200, 200, 200))
            else:
                self.text.render_centered("Press ENTER to finish", WIDTH//2, HEIGHT//2 + 30, self.text.font, (200, 200, 200))
        elif self.state == "COMPLETE":
            self.text.render_centered("JOURNEY COMPLETE", WIDTH//2, HEIGHT//2 - 30, self.text.font_big, (255, 215, 0))
            self.text.render_centered("You have traversed all zones.", WIDTH//2, HEIGHT//2 + 20, self.text.font_md, (200, 200, 200))
            self.text.render_centered("Press ENTER to return to menu", WIDTH//2, HEIGHT//2 + 70, self.text.font, (160, 160, 180))

        if self.debug_overlay:
            self._draw_debug()

        glDisable(GL_BLEND)

    def _draw_menu(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.text.render_centered("THRESHOLD", WIDTH//2, 80, self.text.font_big, (255, 100, 180))
        self.text.render_centered("A Surreal Journey Through Zones", WIDTH//2, 140, self.text.font_md, (180, 180, 220))
        self.text.render_centered("Select a Zone:", WIDTH//2, 200, self.text.font, (255, 255, 255))

        y = 250
        for i, lvl in enumerate(self.levels):
            color = (255, 235, 110) if i == self.menu_idx else (140, 140, 170)
            prefix = "> " if i == self.menu_idx else "  "
            self.text.render_centered(f"{prefix}{i+1}. {lvl.name}{prefix}", WIDTH//2, y, self.text.font_md, color)
            y += 48

        self.text.render_centered("A/D: Rotate  |  W: Thrust  |  S: Brake  |  SPACE: Dash", WIDTH//2, HEIGHT - 70, self.text.font, (160, 160, 180))
        self.text.render_centered("UP/DOWN: Navigate  |  ENTER: Play  |  ESC: Quit", WIDTH//2, HEIGHT - 40, self.text.font, (160, 160, 180))
        glDisable(GL_BLEND)

    def _draw_debug(self):
        avg_fps = len(self.frame_times) / max(sum(self.frame_times), 0.001) if self.frame_times else 0
        angle_deg = math.degrees(self.player.angle) % 360
        lines = [
            f"FPS: {avg_fps:.1f}",
            f"Zone: {self.level.name}",
            f"Pos: ({self.player.pos[0]:.1f}, {self.player.pos[1]:.1f})",
            f"Angle: {angle_deg:.1f} deg",
            f"Vel: ({self.player.vel[0]:.1f}, {self.player.vel[1]:.1f})",
            f"Speed: {float(np.linalg.norm(self.player.vel)):.1f}",
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"Checkpoint: {self.current_checkpoint}",
            f"Particles: {len(self.particles.particles)}",
        ]
        y = HEIGHT - len(lines) * 22 - 10
        for line in lines:
            self.text.render(line, WIDTH - 280, y, self.text.font, (100, 255, 100))
            y += 22