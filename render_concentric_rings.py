"""
CONCENTRIC ROTATING RINGS: RACE TO THE CENTER (SATISFYING ASMR)
Duration: 92.0 seconds (2,760 frames @ 30 FPS)
Format: 1080x1920 (9:16 Vertical)
Physics: Pymunk 2D Rigid Body + Radial Inward Gravity + Dynamic Swirl
Audio: 100% Real Recorded Tactile Marble Clacks (Zero Silent Collisions!)
Visuals: High-Contrast Cyber-Neon Concentric Arena, Fully Centered (Zero Confusing Scrolling!)
"""

import os
import sys
import math
import time
import subprocess
import wave
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymunk

sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================
WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_SECONDS = 92.0
TOTAL_FRAMES = int(TOTAL_SECONDS * FPS)  # 2760 frames
BALL_RADIUS = 15.0

# Arena Center (Centered in viewport below top HUD)
CX = 540
CY = 1140

# 7 Concentric Rings (From Outer R7 down to Inner R1, then Center Goal)
RING_RADII = [460, 405, 350, 295, 240, 185, 130]
NUM_RINGS = len(RING_RADII)

# Alternating rotation speeds (rad/s)
ROT_SPEEDS = [0.38, -0.42, 0.45, -0.48, 0.52, -0.55, 0.60]
# Escape gap segment counts out of 36 segments
GAP_SEGS = [5, 4, 4, 3, 3, 3, 3]

# Ring Neon Border Colors (Outer cool cyan -> inner fiery gold)
RING_COLORS = [
    (0, 242, 254),    # Ring 7: Electric Cyan
    (56, 239, 125),   # Ring 6: Emerald Lime
    (255, 220, 0),    # Ring 5: Solar Amber
    (255, 107, 0),    # Ring 4: Tangerine Orange
    (255, 0, 128),    # Ring 3: Vivid Magenta
    (168, 85, 247),   # Ring 2: Electric Violet
    (255, 215, 0),    # Ring 1: Pure Gold
]

# 8 Distinct Competitor Marbles
RACERS = [
    {"name": "RUBY",    "color": (255, 34, 68),   "hi": (255, 180, 190)},
    {"name": "SUNFIRE", "color": (255, 102, 0),   "hi": (255, 210, 160)},
    {"name": "AMBER",   "color": (255, 195, 0),   "hi": (255, 245, 180)},
    {"name": "LIME",    "color": (120, 255, 0),   "hi": (220, 255, 180)},
    {"name": "CYAN",    "color": (0, 212, 255),   "hi": (200, 245, 255)},
    {"name": "SKY",     "color": (41, 128, 255),  "hi": (190, 225, 255)},
    {"name": "PURPLE",  "color": (181, 23, 158),  "hi": (245, 190, 255)},
    {"name": "MAGENTA", "color": (247, 37, 133),  "hi": (255, 180, 220)},
]

# Fonts with robust cross-platform fallback (Windows + Linux / Ubuntu Actions)
def get_best_font(names, size):
    candidates = []
    for n in names:
        candidates.extend([
            f"C:/Windows/Fonts/{n}.ttf",
            f"/usr/share/fonts/truetype/dejavu/{n}.ttf",
            f"/usr/share/fonts/truetype/liberation/{n}.ttf",
            f"/usr/share/fonts/truetype/freefont/{n}.ttf",
            f"/usr/share/fonts/{n}.ttf"
        ])
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

font_title = get_best_font(["impact", "DejaVuSans-Bold", "arialbd", "LiberationSans-Bold"], 54)
font_subtitle = get_best_font(["arialbd", "DejaVuSans-Bold", "LiberationSans-Bold"], 22)
font_stage_badge = get_best_font(["impact", "DejaVuSans-Bold", "arialbd"], 28)
font_ball_label = get_best_font(["arialbd", "DejaVuSans-Bold", "LiberationSans-Bold"], 16)
font_winner_hero = get_best_font(["impact", "DejaVuSans-Bold", "arialbd"], 74)
font_winner_sub = get_best_font(["arialbd", "DejaVuSans-Bold", "LiberationSans-Bold"], 30)
font_hud_card = get_best_font(["arialbd", "DejaVuSans-Bold", "LiberationSans-Bold"], 18)

# =============================================================================
# 1. PHYSICS SIMULATION ENGINE
# =============================================================================
print("[*] Setting up Concentric Rings Physics Simulation...")
space = pymunk.Space()
space.gravity = (0, 0)  # Pure radial inward gravity
space.iterations = 10

ring_bodies = []
ring_shapes = []
SEGMENTS_PER_RING = 36

for r_idx, (radius, omega, gaps) in enumerate(zip(RING_RADII, ROT_SPEEDS, GAP_SEGS)):
    body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    body.position = (CX, CY)
    body.angular_velocity = omega
    space.add(body)
    ring_bodies.append(body)
    
    initial_gap_offset = (r_idx * 11) % SEGMENTS_PER_RING
    for s_i in range(SEGMENTS_PER_RING):
        if ((s_i + initial_gap_offset) % SEGMENTS_PER_RING) < gaps:
            continue
        a1 = (s_i / float(SEGMENTS_PER_RING)) * 2 * math.pi
        a2 = ((s_i + 1) / float(SEGMENTS_PER_RING)) * 2 * math.pi
        p1 = (radius * math.cos(a1), radius * math.sin(a1))
        p2 = (radius * math.cos(a2), radius * math.sin(a2))
        seg = pymunk.Segment(body, p1, p2, 9)
        seg.elasticity = 0.88
        seg.friction = 0.22
        seg.collision_type = 2  # Ring wall
        space.add(seg)
        ring_shapes.append((seg, r_idx))

# Outer containment wall (Radius 485px)
for s_i in range(SEGMENTS_PER_RING):
    a1 = (s_i / float(SEGMENTS_PER_RING)) * 2 * math.pi
    a2 = ((s_i + 1) / float(SEGMENTS_PER_RING)) * 2 * math.pi
    p1 = (CX + 485 * math.cos(a1), CY + 485 * math.sin(a1))
    p2 = (CX + 485 * math.cos(a2), CY + 485 * math.sin(a2))
    seg = pymunk.Segment(space.static_body, p1, p2, 10)
    seg.elasticity = 0.85
    seg.collision_type = 2
    space.add(seg)

# Sound & Collision Events
sound_events = []
current_sim_frame = 0

def on_ball_contact(sound_type, base_gain=1.0):
    def handler(arbiter, space, data):
        if not arbiter.is_first_contact:
            return True
        pts = arbiter.contact_point_set.points
        if pts:
            pos = pts[0].point_a
            impulse = arbiter.total_impulse.length
            sound_events.append({
                "frame": current_sim_frame,
                "type": sound_type,
                "x": pos[0],
                "y": pos[1],
                "intensity": min(1.8, max(0.3, (impulse / 100.0) * base_gain))
            })
        return True
    return handler

# Every collision generates real tactile sound!
space.on_collision(1, 1, begin=on_ball_contact("ball_clack", 1.4))
space.on_collision(1, 2, begin=on_ball_contact("ring_clack", 1.1))

class Marble:
    def __init__(self, idx, info, body, shape):
        self.idx = idx
        self.name = info["name"]
        self.color = info["color"]
        self.hi = info["hi"]
        self.body = body
        self.shape = shape
        self.ring = 7  # Starts in Outer Ring 7
        self.won = False
        self.win_frame = 0
        self.rank = 0

marbles = []
seed_val = int(os.environ.get("RANDOM_SEED", "42"))
np.random.seed(seed_val)

for idx, info in enumerate(RACERS):
    angle = (idx / 8.0) * 2 * math.pi + np.random.uniform(-0.06, 0.06)
    spawn_r = 472.0
    x = CX + spawn_r * math.cos(angle)
    y = CY + spawn_r * math.sin(angle)
    
    b = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0, BALL_RADIUS))
    b.position = (x, y)
    b.velocity = (np.random.uniform(-15, 15), np.random.uniform(-15, 15))
    s = pymunk.Circle(b, BALL_RADIUS)
    s.elasticity = 0.82
    s.friction = 0.15
    s.collision_type = 1
    space.add(b, s)
    marbles.append(Marble(idx, info, b, s))

print(f"[*] Spawned {len(marbles)} competitors in Outer Ring 7.")

frame_data_list = []
podium = []
winner = None
dt = 1.0 / 30.0
t_sim_0 = time.time()

for f in range(TOTAL_FRAMES):
    current_sim_frame = f
    
    # Apply continuous radial inward gravity + dynamic orbital swirl
    for m in marbles:
        dx = CX - m.body.position[0]
        dy = CY - m.body.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 5.0:
            nx = dx / dist
            ny = dy / dist
            # Inward gravity pull: calibrated for dramatic 80-second penetration
            inward_f = 270.0 + (460.0 - dist) * 0.25
            if dist < 190:
                inward_f += 90.0
            # Orbital swirl force: alternates slightly to maintain continuous movement
            tx = -ny
            ty = nx
            swirl_f = 45.0 * math.sin(f * 0.008 + m.body.position[0] * 0.02)
            
            # Apply force in WORLD space so marble roll rotation doesn't warp gravity
            m.body.force = (nx * inward_f + tx * swirl_f, ny * inward_f + ty * swirl_f)
            
            # Check ring layer transitions
            for r_lvl, r_boundary in enumerate(RING_RADII):
                ring_num = 6 - r_lvl
                if dist < r_boundary and ring_num < m.ring:
                    m.ring = ring_num
                    sound_events.append({
                        "frame": f,
                        "type": "ring_escape",
                        "x": m.body.position[0],
                        "y": m.body.position[1],
                        "ring_level": 7 - ring_num,
                        "intensity": 1.5
                    })
                    print(f"    [f={f:4d} ({f/30:4.1f}s)] {m.name} ESCAPED into Ring {ring_num} (dist: {dist:.1f})")
                    
            # Check Center Core Goal (Radius < 75px)
            if dist < 75 and not m.won:
                m.won = True
                m.win_frame = f
                finish_rank = len(podium) + 1
                m.rank = finish_rank
                podium.append({"rank": finish_rank, "name": m.name, "color": m.color, "frame": f})
                if finish_rank == 1:
                    winner = m
                print(f"**************************************************")
                print(f"[*] PODIUM #{finish_rank} FINISH AT FRAME {f} ({f/30:.1f}s): {m.name}!")
                print(f"**************************************************")
                sound_events.append({
                    "frame": f,
                    "type": "center_win",
                    "x": CX,
                    "y": CY,
                    "intensity": 2.5
                })

    # Step physics
    for _ in range(4):
        space.step(dt / 4)

    # Snapshot visible frame state
    marbles_snapshot = []
    for m in marbles:
        pos = m.body.position
        marbles_snapshot.append({
            "idx": m.idx,
            "name": m.name,
            "color": m.color,
            "hi": m.hi,
            "x": round(pos[0], 1),
            "y": round(pos[1], 1),
            "ring": m.ring,
            "won": m.won,
            "rank": m.rank
        })
        
    ring_angles = [round(b.angle, 4) for b in ring_bodies]
    podium_snapshot = [dict(p) for p in podium]
    
    frame_data_list.append({
        "f": f,
        "ring_angles": ring_angles,
        "marbles": marbles_snapshot,
        "podium": podium_snapshot,
        "winner_name": winner.name if winner else None,
        "winner_color": winner.color if winner else None,
        "winner_frame": winner.win_frame if winner else None
    })

print(f"[SUCCESS] Physics simulation finished in {time.time()-t_sim_0:.2f}s!")
print(f"Captured {len(sound_events)} distinct collision & escape sound events.")

# =============================================================================
# 2. AUDIO ENGINE: REAL ACOUSTIC RECORDED MARBLE CLACKS
# =============================================================================
print("[*] Compiling Master ASMR Soundtrack from Real Physical Acoustic Samples...")
SAMPLE_RATE = 48000
NUM_SAMPLES = int(TOTAL_SECONDS * SAMPLE_RATE)
left_buf = np.zeros(NUM_SAMPLES, dtype=np.float32)
right_buf = np.zeros(NUM_SAMPLES, dtype=np.float32)

def resample_np(data, target_len):
    x_old = np.linspace(0, 1, len(data))
    x_new = np.linspace(0, 1, target_len)
    return np.interp(x_new, x_old, data).astype(np.float32)

def resolve_audio(filename):
    for base in [".", "audio", "public/audio", "../public/audio", "../../public/audio"]:
        p = os.path.join(base, filename)
        if os.path.exists(p):
            return p
    return filename

# Load the 6 Real Marble Clack WAVs
clack_samples = []
for i in range(1, 7):
    clack_p = resolve_audio(f"real_clack_{i}.wav")
    if os.path.exists(clack_p):
        with wave.open(clack_p, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
            if wf.getframerate() != SAMPLE_RATE:
                data = resample_np(data, int(len(data) * (SAMPLE_RATE / wf.getframerate())))
            clack_samples.append(data)

print(f"[*] Loaded {len(clack_samples)} Real Acoustic Marble Clack samples.")

# Load Pop sample for Ring Escapes
pop_p = resolve_audio("sfx_pop_snatch.wav")
with wave.open(pop_p, "rb") as wf:
    raw = wf.readframes(wf.getnframes())
    pop_raw = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
    if wf.getframerate() != SAMPLE_RATE:
        pop_base = resample_np(pop_raw, int(len(pop_raw) * (SAMPLE_RATE / wf.getframerate())))
    else:
        pop_base = pop_raw

# Pre-generate 8 rising musical pitches for ring escapes (Ring 7 -> Ring 1)
ring_escape_pops = []
pentatonic = [1.0, 1.122, 1.26, 1.335, 1.498, 1.682, 1.888, 2.0]
for r in pentatonic:
    target_len = int(len(pop_base) / r)
    ring_escape_pops.append(resample_np(pop_base, target_len))

# Load Center Win Chime
chime_p = resolve_audio("sfx_chime.wav")
with wave.open(chime_p, "rb") as wf:
    raw = wf.readframes(wf.getnframes())
    chime_data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
    if wf.getframerate() != SAMPLE_RATE:
        chime_data = resample_np(chime_data, int(len(chime_data) * (SAMPLE_RATE / wf.getframerate())))

# Place sound events into stereo buffer
np.random.seed(42)
for ev in sound_events:
    f_idx = ev["frame"]
    ev_type = ev["type"]
    intensity = ev["intensity"]
    x_pos = ev.get("x", 540)
    
    pan = max(0.0, min(1.0, (x_pos - (CX - 480)) / 960.0))
    gain_l = math.cos(pan * math.pi * 0.5)
    gain_r = math.sin(pan * math.pi * 0.5)
    
    if ev_type in ("ball_clack", "ring_clack"):
        # Pick one of the 6 real acoustic clacks
        sample = clack_samples[np.random.randint(0, len(clack_samples))]
        sound = sample * intensity * 0.85
    elif ev_type == "ring_escape":
        lvl = min(len(ring_escape_pops) - 1, ev.get("ring_level", 0))
        sound = ring_escape_pops[lvl] * 1.1
    elif ev_type == "center_win":
        sound = chime_data * 1.35
    else:
        continue
        
    start_s = int((f_idx / float(FPS)) * SAMPLE_RATE)
    end_s = min(NUM_SAMPLES, start_s + len(sound))
    actual_len = end_s - start_s
    if actual_len > 0:
        left_buf[start_s:end_s] += sound[:actual_len] * gain_l
        right_buf[start_s:end_s] += sound[:actual_len] * gain_r

# Soft-Saturation Limiter (guarantees thick, punchy sound without harsh digital clipping)
print("[*] Applying Soft-Saturation Limiter to Audio Master...")
left_buf = np.tanh(left_buf * 1.6) * 0.82
right_buf = np.tanh(right_buf * 1.6) * 0.82

# Subtle 120 BPM Marimba Groove in background
bgm_path = resolve_audio("soundtrack_120bpm_educational.wav")
if os.path.exists(bgm_path):
    print(f"[*] Layering Subtle 120 BPM Marimba Groove: {bgm_path}")
    with wave.open(bgm_path, "rb") as wf:
        n_ch = wf.getnchannels()
        raw_bytes = wf.readframes(wf.getnframes())
    bgm_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32767.0
    bgm_l = bgm_data[0::2] if n_ch == 2 else bgm_data
    bgm_r = bgm_data[1::2] if n_ch == 2 else bgm_data
    bgm_len = len(bgm_l)
    for pos in range(0, NUM_SAMPLES, bgm_len):
        chunk_len = min(bgm_len, NUM_SAMPLES - pos)
        # Background music sits gently at 16% volume so marble clacks DOMINATE
        left_buf[pos:pos + chunk_len] += bgm_l[:chunk_len] * 0.16
        right_buf[pos:pos + chunk_len] += bgm_r[:chunk_len] * 0.16

master_wav = "renders/concentric_rings_master.wav"
os.makedirs(os.path.dirname(master_wav), exist_ok=True)
stereo_interleaved = np.empty((NUM_SAMPLES, 2), dtype=np.float32)
stereo_interleaved[:, 0] = left_buf
stereo_interleaved[:, 1] = right_buf

max_amp = np.max(np.abs(stereo_interleaved))
if max_amp > 0:
    stereo_interleaved = (stereo_interleaved / max_amp) * 0.95

with wave.open(master_wav, "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    raw_int16 = (stereo_interleaved * 32767.0).astype(np.int16)
    wf.writeframes(raw_int16.tobytes())

print(f"[SUCCESS] Master ASMR Audio saved to: {master_wav}")

# =============================================================================
# 3. HIGH-PERFORMANCE VIDEO RENDERER (PIL -> FFMPEG PIPE)
# =============================================================================
OUTPUT_MP4 = os.environ.get("OUTPUT_MP4", "renders/ConcentricRingsRace.mp4")
if os.path.dirname(OUTPUT_MP4):
    os.makedirs(os.path.dirname(OUTPUT_MP4), exist_ok=True)
if os.path.dirname(master_wav):
    os.makedirs(os.path.dirname(master_wav), exist_ok=True)
print(f"[*] Initializing FFmpeg Video Pipe -> {OUTPUT_MP4} (1080x1920 @ {FPS} FPS, CRF 26)...")

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-loglevel", "error",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",  # Video from stdin pipe
    "-i", master_wav,  # Master audio
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "26",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    OUTPUT_MP4
]

pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

# Pre-render 3D Glossy Marble Sprites
marble_sprites = {}
sprite_size = int(BALL_RADIUS * 2 + 16)
for r in RACERS:
    base_col = r["color"]
    hi_col = r["hi"]
    img = Image.new("RGBA", (sprite_size, sprite_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx_s, cy_s = sprite_size // 2, sprite_size // 2
    r_val = BALL_RADIUS
    
    # Outer dark shadow
    d.ellipse([cx_s - r_val, cy_s - r_val, cx_s + r_val, cy_s + r_val], fill=(int(base_col[0]*0.35), int(base_col[1]*0.35), int(base_col[2]*0.35), 255))
    # Concentric smooth gradient shading
    for s_step in range(int(r_val), 1, -1):
        ratio = s_step / r_val
        col = (
            int(base_col[0] * ratio + hi_col[0] * (1 - ratio)),
            int(base_col[1] * ratio + hi_col[1] * (1 - ratio)),
            int(base_col[2] * ratio + hi_col[2] * (1 - ratio)),
            255
        )
        d.ellipse([cx_s - s_step + (1 - ratio) * 4, cy_s - s_step - (1 - ratio) * 4, cx_s + s_step + (1 - ratio) * 4, cy_s + s_step - (1 - ratio) * 4], fill=col)
    # Bright specular reflection
    d.ellipse([cx_s - 5, cy_s - 8, cx_s + 1, cy_s - 3], fill=(255, 255, 255, 240))
    marble_sprites[r["name"]] = img

# Base Background Plate
bg_canvas = Image.new("RGB", (WIDTH, HEIGHT), (8, 12, 22))
bg_draw = ImageDraw.Draw(bg_canvas)
# Deep concentric gradient glow behind the arena
for glow_r in range(520, 20, -40):
    alpha_ratio = (520 - glow_r) / 520.0
    c_val = int(18 + alpha_ratio * 25)
    bg_draw.ellipse([CX - glow_r, CY - glow_r, CX + glow_r, CY + glow_r], outline=(c_val, c_val + 5, c_val + 18), width=3)

t_render_start = time.time()
print(f"[*] Rendering {TOTAL_FRAMES} frames...")

for idx_f, fd in enumerate(frame_data_list):
    f = fd["f"]
    ring_angles = fd["ring_angles"]
    marbles_f = fd["marbles"]
    winner_name = fd["winner_name"]
    winner_color = fd["winner_color"]
    winner_frame = fd["winner_frame"]
    
    frame_img = bg_canvas.copy()
    draw = ImageDraw.Draw(frame_img)
    
    # 1. Draw 7 Concentric Spinning Rings with Escape Gaps
    for r_idx, (radius, color, gaps) in enumerate(zip(RING_RADII, RING_COLORS, GAP_SEGS)):
        angle_rot = ring_angles[r_idx]
        initial_gap_offset = (r_idx * 11) % SEGMENTS_PER_RING
        
        for s_i in range(SEGMENTS_PER_RING):
            if ((s_i + initial_gap_offset) % SEGMENTS_PER_RING) < gaps:
                continue  # Gap opening!
            a1 = angle_rot + (s_i / float(SEGMENTS_PER_RING)) * 2 * math.pi
            a2 = angle_rot + ((s_i + 1) / float(SEGMENTS_PER_RING)) * 2 * math.pi
            p1 = (CX + radius * math.cos(a1), CY + radius * math.sin(a1))
            p2 = (CX + radius * math.cos(a2), CY + radius * math.sin(a2))
            
            # Thick vibrant neon ring track
            draw.line([p1, p2], fill=color, width=9)

    # Draw Outer Boundary Ring
    for s_i in range(SEGMENTS_PER_RING):
        a1 = (s_i / float(SEGMENTS_PER_RING)) * 2 * math.pi
        a2 = ((s_i + 1) / float(SEGMENTS_PER_RING)) * 2 * math.pi
        p1 = (CX + 485 * math.cos(a1), CY + 485 * math.sin(a1))
        p2 = (CX + 485 * math.cos(a2), CY + 485 * math.sin(a2))
        draw.line([p1, p2], fill=(40, 60, 95), width=6)

    # 2. Draw Golden Center Core Goal
    pulse_size = 55 + int(6 * math.sin(f * 0.12))
    draw.ellipse([CX - pulse_size, CY - pulse_size, CX + pulse_size, CY + pulse_size], fill=(30, 25, 10), outline=(255, 215, 0), width=5)
    draw.ellipse([CX - 22, CY - 22, CX + 22, CY + 22], fill=(255, 235, 50))
    draw.text((CX - 42, CY - 11), "CORE", font=font_stage_badge, fill=(10, 10, 10))

    # 3. Draw Competitor Marbles (Sprites + Dynamic Labels)
    for mb in marbles_f:
        mx, my = int(mb["x"]), int(mb["y"])
        sprite = marble_sprites[mb["name"]]
        frame_img.paste(sprite, (mx - sprite_size // 2, my - sprite_size // 2), sprite)
        # Marble name tag floating with clean contrast
        draw.text((mx + 18, my - 10), mb["name"], font=font_ball_label, fill=(255, 255, 255))

    # 4. Top HUD Zone (0 to 380px): Obsidian Glass Plate
    draw.rectangle([0, 0, WIDTH, 380], fill=(6, 9, 18))
    draw.line([(0, 380), (WIDTH, 380)], fill=(0, 242, 254), width=4)
    
    # Title & Core Hook
    draw.text((60, 32), "RACE TO THE CENTER CORE", font=font_title, fill=(255, 255, 255))
    draw.text((60, 92), "7 SPINNING RINGS - WHICH COLOR ESCAPES FIRST?!", font=font_subtitle, fill=(0, 242, 254))
    
    # Live Leaderboard Grid (8 Racer Cards with current Ring level)
    for idx_r, r_info in enumerate(RACERS):
        rx = 60 + (idx_r % 4) * 242
        ry = 135 + (idx_r // 4) * 110
        m_state = next((m for m in marbles_f if m["name"] == r_info["name"]), None)
        cur_ring = m_state["ring"] if m_state else 7
        
        m_rank = m_state["rank"] if m_state else 0
        
        # Highlight card based on podium rank or ring depth
        if m_rank == 1:
            card_border = (255, 215, 0)
            card_bg = (45, 38, 12)
            ring_text = "1st GOLD!"
            ring_col = (255, 215, 0)
        elif m_rank == 2:
            card_border = (220, 225, 235)
            card_bg = (30, 34, 44)
            ring_text = "2nd SILVER"
            ring_col = (220, 225, 235)
        elif m_rank == 3:
            card_border = (205, 127, 50)
            card_bg = (38, 26, 18)
            ring_text = "3rd BRONZE"
            ring_col = (205, 127, 50)
        elif m_rank > 3:
            card_border = (60, 180, 100)
            card_bg = (18, 32, 24)
            ring_text = f"FINISH #{m_rank}"
            ring_col = (80, 250, 140)
        else:
            card_border = (255, 215, 0) if cur_ring <= 2 else r_info["color"]
            card_bg = (28, 26, 16) if cur_ring <= 2 else (16, 22, 36)
            ring_text = f"RING {cur_ring}"
            ring_col = (255, 215, 0) if cur_ring <= 2 else (0, 242, 254)
        
        draw.rectangle([rx, ry, rx + 225, ry + 95], fill=card_bg, outline=card_border, width=2)
        draw.ellipse([rx + 12, ry + 16, rx + 36, ry + 40], fill=r_info["color"])
        draw.text((rx + 46, ry + 16), r_info["name"], font=font_hud_card, fill=(255, 255, 255))
        draw.text((rx + 46, ry + 48), ring_text, font=font_hud_card, fill=ring_col)

    # 5. Core Finisher Shockwaves (Dynamic 1-second pulse on finish)
    podium_f = fd.get("podium", [])
    for p_item in podium_f:
        frames_since_fin = f - p_item["frame"]
        if 0 <= frames_since_fin <= 35:
            pulse_r = int(frames_since_fin * 14)
            wave_col = (255, 215, 0) if p_item["rank"] == 1 else (0, 242, 254)
            draw.ellipse([CX - pulse_r, CY - pulse_r, CX + pulse_r, CY + pulse_r], outline=wave_col, width=4)

    # 6. Grand Finale Victory Podium (Last 10 Seconds: detik 82.0 to 92.0)
    if f >= 2460 and len(podium_f) > 0:
        p1 = podium_f[0]
        draw.rectangle([90, 840, 990, 1340], fill=(8, 12, 24), outline=(255, 215, 0), width=6)
        draw.text((220, 875), "OFFICIAL RACE PODIUM", font=font_stage_badge, fill=(255, 215, 0))
        
        # 1st Gold Champion
        draw.text((150, 940), f"1st GOLD:    {p1['name']}", font=font_title, fill=(255, 215, 0))
        
        # 2nd Silver
        if len(podium_f) > 1:
            p2 = podium_f[1]
            draw.text((150, 1020), f"2nd SILVER:  {p2['name']}", font=font_stage_badge, fill=(220, 225, 235))
            
        # 3rd Bronze
        if len(podium_f) > 2:
            p3 = podium_f[2]
            draw.text((150, 1080), f"3rd BRONZE:  {p3['name']}", font=font_stage_badge, fill=(205, 127, 50))
            
        # 4th / 5th
        if len(podium_f) > 3:
            p4 = podium_f[3]
            draw.text((150, 1140), f"4th PLACE:   {p4['name']}", font=font_ball_label, fill=(180, 190, 205))
            
        draw.text((150, 1230), "DID YOUR COLOR MAKE THE PODIUM?", font=font_winner_sub, fill=(0, 242, 254))

    pipe.stdin.write(frame_img.tobytes())
    
    if f % 300 == 0 or f == TOTAL_FRAMES - 1:
        fps_curr = (f + 1) / (time.time() - t_render_start)
        print(f"    [Frame {f:4d}/{TOTAL_FRAMES}] ({f/30:4.1f}s) | Winner: {winner_name} | Speed: {fps_curr:4.1f} fps")

pipe.stdin.close()
pipe.wait()

print(f"[SUCCESS] Video rendered successfully in {time.time()-t_render_start:.1f}s!")
print(f"Output: {OUTPUT_MP4} ({os.path.getsize(OUTPUT_MP4)/(1024*1024):.2f} MB)")
