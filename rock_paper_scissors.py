import pygame
import random
import sys
import math
import time
import json
import os

try:
    import cv2
    import mediapipe as mp
    import threading
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception:
    pygame.mixer.init()

import array
def _synth(freq, dur=0.1, vol=0.1):
    try:
        init = pygame.mixer.get_init()
        if not init: return None
        sr, _, ch = init
        ns = int(dur * sr)
        b = array.array('h', [0]*(ns*ch))
        for i in range(ns):
            t = i / sr
            # Simple square wave
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            env = max(0, 1.0 - (i / ns))
            s = int(32767 * vol * val * env)
            if ch == 2:
                b[2*i] = s; b[2*i+1] = s
            else:
                b[i] = s
        return pygame.mixer.Sound(buffer=b)
    except Exception: return None

snd_blip = _synth(1200, 0.05, 0.1)
snd_whoosh = _synth(200, 1.5, 0.15)

try:
    snd_select = pygame.mixer.Sound(os.path.join(BASE_DIR, "select.wav"))
    snd_win    = pygame.mixer.Sound(os.path.join(BASE_DIR, "win.wav"))
    snd_lose   = pygame.mixer.Sound(os.path.join(BASE_DIR, "lose.wav"))
    snd_tie    = pygame.mixer.Sound(os.path.join(BASE_DIR, "tie.wav"))
    # Pre-load intro sound if it exists
    intro_path = os.path.join(BASE_DIR, "intro.mp3")
    if os.path.exists(intro_path):
        snd_intro = intro_path
    else:
        snd_intro = None
except Exception:
    # Fallback to synth if files not found
    snd_select = _synth(600, 0.1, 0.2)
    snd_win    = _synth(800, 0.4, 0.2)
    snd_lose   = _synth(150, 0.5, 0.2)
    snd_tie    = _synth(400, 0.3, 0.2)
    snd_intro  = None

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
FPS = 60

# Pixel palette (Girigo monochrome theme)
BG_DARK      = (0, 0, 0)
BG_MID       = (15, 15, 15)
PIXEL_GREEN  = (255, 255, 255)
PIXEL_CYAN   = (220, 220, 220)
PIXEL_YELLOW = (180, 180, 180)
PIXEL_RED    = (150, 150, 150)
PIXEL_PURPLE = (200, 200, 200)
PIXEL_WHITE  = (255, 255, 255)
PIXEL_GREY   = (80, 80, 80)
PIXEL_ORANGE = (240, 240, 240)
PIXEL_TEAL   = (120, 120, 120)
WIN_COLOR    = (255, 255, 255)
LOSE_COLOR   = (100, 100, 100)
TIE_COLOR    = (180, 180, 180)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("⚔ PIXEL RPS ⚔")
clock = pygame.time.Clock()

global_sound_on = True

# ── Pixel font helper ────────────────────────────────────────────────────────
def get_font(size):
    """Return a monospace/pixel-ish font."""
    for name in ("Courier New", "Courier", "monospace"):
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

# Pre-load fonts
F_HUGE   = get_font(72)
F_BIG    = get_font(48)
F_MED    = get_font(32)
F_SMALL  = get_font(22)
F_TINY   = get_font(16)

# ── Draw helpers ────────────────────────────────────────────────────────────
def draw_pixel_border(surf, rect, color, thickness=3):
    """Draw a chunky pixel-style border without corner dots."""
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x, y, w, h), thickness)

def draw_scanlines(surf, alpha=30):
    """Retro CRT scanline overlay."""
    line_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(line_surf, (0, 0, 0, alpha), (0, y), (WIDTH, y))
    surf.blit(line_surf, (0, 0))

def draw_grid_bg(surf, t):
    """Animated scrolling grid background."""
    surf.fill(BG_DARK)
    offset = int(t * 0.4) % 40
    for x in range(-40, WIDTH + 40, 40):
        pygame.draw.line(surf, (20, 20, 50), (x + offset, 0), (x + offset, HEIGHT), 1)
    for y in range(-40, HEIGHT + 40, 40):
        pygame.draw.line(surf, (20, 20, 50), (0, y + offset), (WIDTH, y + offset), 1)

def draw_text_shadow(surf, text, font, color, x, y, shadow_color=(0,0,0), offset=3):
    s = font.render(text, False, shadow_color)
    surf.blit(s, (x + offset, y + offset))
    t = font.render(text, False, color)
    surf.blit(t, (x, y))
    return t.get_rect(topleft=(x, y))

def draw_text_center(surf, text, font, color, cx, y):
    s = font.render(text, False, color)
    surf.blit(s, (cx - s.get_width()//2, y))

# ── Pixel art sprites (drawn with rects) ────────────────────────────────────
SCALE = 6  # each "pixel" = 6×6 px

def draw_pixel_sprite(surf, pixels, color, ox, oy, scale=SCALE):
    for (px, py) in pixels:
        pygame.draw.rect(surf, color,
                         (ox + px * scale, oy + py * scale, scale, scale))

# Rock  – 7×7 grid
ROCK_PIXELS = [
    (2,0),(3,0),(4,0),
    (1,1),(2,1),(3,1),(4,1),(5,1),
    (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
    (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),
    (0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),
    (1,5),(2,5),(3,5),(4,5),(5,5),
    (2,6),(3,6),(4,6),
]

# Paper – 7×8 grid
PAPER_PIXELS = [
    (1,0),(2,0),(3,0),(4,0),(5,0),
    (1,1),(5,1),
    (1,2),(2,2),(3,2),(4,2),(5,2),
    (1,3),(5,3),
    (1,4),(2,4),(3,4),(4,4),(5,4),
    (1,5),(5,5),
    (1,6),(2,6),(3,6),(4,6),(5,6),
    (0,7),(1,7),(2,7),(3,7),(4,7),(5,7),(6,7),
]

# Scissors – 8×8 grid
SCISSORS_PIXELS = [
    (0,0),(1,0),(6,0),(7,0),
    (0,1),(1,1),(6,1),(7,1),
    (1,2),(2,2),(5,2),(6,2),
    (2,3),(3,3),(4,3),(5,3),
    (3,4),(4,4),
    (2,5),(3,5),(4,5),(5,5),
    (1,6),(2,6),(5,6),(6,6),
    (0,7),(1,7),(6,7),(7,7),
]

SPRITES = {"rock": ROCK_PIXELS, "paper": PAPER_PIXELS, "scissors": SCISSORS_PIXELS}
COLORS  = {"rock": PIXEL_ORANGE, "paper": PIXEL_CYAN, "scissors": PIXEL_PURPLE}
CHOICES = ["rock", "paper", "scissors"]

COMMENTARY_WIN = [
    "A brilliant move!", "Wow, did you read its mind?",
    "Flawless victory!", "The CPU is crying.",
    "Another one bites the dust!"
]
COMMENTARY_LOSE = [
    "Ouch! Saw that coming.", "Are you even trying?",
    "Pathetic fleshling...", "Calculated failure.",
    "Better luck next time."
]
COMMENTARY_DRAW = [
    "Great minds think alike.", "A boring tie.",
    "It's a standoff!", "Neither has the upper hand.",
    "Yawn... a tie."
]

def parse_ascii_sprite(ascii_str):
    pixels = []
    lines = [line for line in ascii_str.split('\n') if line.strip("\r")]
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == 'X':
                pixels.append((x, y))
    return pixels

SPEAKER_ON_ASCII = """
  X   X 
 XX   X 
XXX X X 
 XX   X 
  X   X 
"""
SPEAKER_OFF_ASCII = """
  X     
 XX X X 
XXX  X  
 XX X X 
  X     
"""
SPEAKER_ON_PIXELS = parse_ascii_sprite(SPEAKER_ON_ASCII)
SPEAKER_OFF_PIXELS = parse_ascii_sprite(SPEAKER_OFF_ASCII)

class SoundIconButton:
    def __init__(self, cx, cy, scale=3):
        self.rect = pygame.Rect(cx - 20, cy - 20, 40, 40)
        self.scale = scale
        self.hover = False
    def update(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)
    def draw(self, surf, is_on):
        bg = (40, 40, 80) if self.hover else BG_MID
        pygame.draw.rect(surf, bg, self.rect)
        draw_pixel_border(surf, self.rect, PIXEL_CYAN if is_on else PIXEL_GREY, 2)
        pixels = SPEAKER_ON_PIXELS if is_on else SPEAKER_OFF_PIXELS
        color = PIXEL_YELLOW if is_on else PIXEL_RED
        ox = self.rect.centerx - (8 * self.scale) // 2 + 5
        oy = self.rect.centery - (5 * self.scale) // 2
        for (px, py) in pixels:
            pygame.draw.rect(surf, color, (ox + px * self.scale, oy + py * self.scale, self.scale, self.scale))
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

BACK_ARROW_ASCII = """
   X    
  XX    
 XXXXXXX
  XX    
   X    
"""
BACK_ARROW_PIXELS = parse_ascii_sprite(BACK_ARROW_ASCII)

class BackIconButton:
    def __init__(self, cx, cy, scale=3):
        self.rect = pygame.Rect(cx - 20, cy - 20, 40, 40)
        self.scale = scale
        self.hover = False
    def update(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)
    def draw(self, surf):
        bg = (60, 40, 60) if self.hover else BG_MID
        pygame.draw.rect(surf, bg, self.rect)
        draw_pixel_border(surf, self.rect, PIXEL_PURPLE if self.hover else PIXEL_GREY, 2)
        color = PIXEL_WHITE
        ox = self.rect.centerx - (7 * self.scale) // 2
        oy = self.rect.centery - (5 * self.scale) // 2
        for (px, py) in BACK_ARROW_PIXELS:
            pygame.draw.rect(surf, color, (ox + px * self.scale, oy + py * self.scale, self.scale, self.scale))
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class CameraTracker:
    def __init__(self):
        self.running = False
        self.cap = None
        self.thread = None
        self.detector = None
        self.p1_gesture = None
        self.p2_gesture = None
        self.frame_surf = None
        self.lock = threading.Lock()
        self._prepare_detector()

    def _prepare_detector(self):
        if not CAMERA_AVAILABLE: return
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            task_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_landmarker.task')
            base_options = mp_python.BaseOptions(model_asset_path=task_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                running_mode=vision.RunningMode.IMAGE
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Error initializing detector: {e}")

    def start(self):
        if not CAMERA_AVAILABLE or self.running: return
        with self.lock:
            self.p1_gesture = None
            self.p2_gesture = None
            self.frame_surf = None
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        with self.lock:
            self.p1_gesture = None
            self.p2_gesture = None
            self.frame_surf = None

    def get_gesture(self, hand_landmarks):
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        fingers_up = 0
        for tip, pip in zip(tips, pips):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                fingers_up += 1
        
        if fingers_up <= 1: return "rock"
        elif fingers_up == 2: return "scissors"
        elif fingers_up >= 3: return "paper"
        return None

    def _loop(self):
        if not self.detector:
            self._prepare_detector()
            if not self.detector:
                self.running = False
                return
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.running = False
            return

        while self.running:
            success, image = self.cap.read()
            if not success:
                pygame.time.wait(30)
                continue

            image = cv2.flip(image, 1)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            results = self.detector.detect(mp_image)

            p1_g = None
            p2_g = None

            if results.hand_landmarks:
                hands_list = []
                for hl in results.hand_landmarks:
                    class DummyHL:
                        def __init__(self, landmarks):
                            self.landmark = landmarks
                    
                    dummy = DummyHL(hl)
                    x = hl[0].x
                    g = self.get_gesture(dummy)
                    hands_list.append((x, g, hl))
                
                hands_list.sort(key=lambda item: item[0])
                if len(hands_list) == 1:
                    if hands_list[0][0] < 0.5:
                        p1_g = hands_list[0][1]
                    else:
                        p2_g = hands_list[0][1]
                elif len(hands_list) >= 2:
                    p1_g = hands_list[0][1]
                    p2_g = hands_list[1][1]
                    
                for _, _, hl in hands_list:
                    for pt in hl:
                        px = int(pt.x * image_rgb.shape[1])
                        py = int(pt.y * image_rgb.shape[0])
                        cv2.circle(image_rgb, (px, py), 5, (0, 255, 0), -1)

            image_rgb = cv2.resize(image_rgb, (WIDTH, HEIGHT))
            surf = pygame.surfarray.make_surface(image_rgb.swapaxes(0, 1))

            with self.lock:
                self.p1_gesture = p1_g
                self.p2_gesture = p2_g
                self.frame_surf = surf

            pygame.time.wait(30)

NAMASTE_ASCII_F1 = """
                  XX XX                  
                  XX XX                  
                  XX XX                  
                 XXX XXX                 
                 XXX XXX                 
                 XXX XXX                 
                XXXX XXXX                
                XXXX XXXX                
                XXXX XXXX                
               XXXXX XXXXX               
               XXXXX XXXXX               
              XXXXXX XXXXXX              
              XXXXXX XXXXXX              
             XXXXXXX XXXXXXX             
             XXXXXXX XXXXXXX             
            XXXXXXXX XXXXXXXX            
            XXXXXXXX XXXXXXXX            
           XXXXXXXXX XXXXXXXXX           
           XXXXXXXXX XXXXXXXXX           
          XXXXXXXXXX XXXXXXXXXX          
          XXXXXXXXXX XXXXXXXXXX          
         XXXXXXXXXXX XXXXXXXXXXX         
         XXXXXXXXXXX XXXXXXXXXXX         
        XXXXXXXXXXXX XXXXXXXXXXXX        
        XXXXXXXXXXXX XXXXXXXXXXXX        
       XXXXXXXXXXXXX XXXXXXXXXXXXX       
       XXXXXXXXXXXXX XXXXXXXXXXXXX       
      XXXXXXXXXXXXXX XXXXXXXXXXXXXX      
      XXXXXXXXXXXXXX XXXXXXXXXXXXXX      
     XXXXXXXXXXXXXXX XXXXXXXXXXXXXXX     
     XXXXXXXXXXXXXXX XXXXXXXXXXXXXXX     
    XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXX    
    XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXX    
   XXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX   
   XXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX   
  XXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXX  
  XXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXX  
 XXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXX 
 XXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXX 
 XXX  XXXXXXXXXXXXXX XXXXXXXXXXXXXX  XXX 
 XXXX  XXXXXXXXXXXXX XXXXXXXXXXXXX  XXXX 
 XXXXX  XXXXXXXXXXX   XXXXXXXXXXX  XXXXX 
 XXXXXX  XXXXXXXXXX   XXXXXXXXXX  XXXXXX 
 XXXXXXX  XXXXXXXX     XXXXXXXX  XXXXXXX 
  XXXXXX  XXXXXXX       XXXXXXX  XXXXXX  
  X XXXX  XXXXXX         XXXXXX  XXXX X  
    XXXX  XXXXX           XXXXX  XXXX    
    X XX  XXXX             XXXX  XX X    
      X   XXX               XXX   X      
          XXX               XXX          
          X X               X X          
"""

NAMASTE_ASCII_F2 = """
                  XX XX                  
                  XX XX                  
                  XX XX                  
                 XXX XXX                 
                 XXX XXX                 
                 XXX XXX                 
                XXXX XXXX                
                XXXX XXXX                
                XXXX XXXX                
               XXXXX XXXXX               
               XXXXX XXXXX               
              XXXXXX XXXXXX              
              XXXXXX XXXXXX              
             XXXXXXX XXXXXXX             
             XXXXXXX XXXXXXX             
            XXXXXXXX XXXXXXXX            
            XXXXXXXX XXXXXXXX            
           XXXXXXXXX XXXXXXXXX           
           XXXXXXXXX XXXXXXXXX           
          XXXXXXXXXX XXXXXXXXXX          
          XXXXXXXXXX XXXXXXXXXX          
         XXXXXXXXXXX XXXXXXXXXXX         
         XXXXXXXXXXX XXXXXXXXXXX         
        XXXXXXXXXXXX XXXXXXXXXXXX        
        XXXXXXXXXXXX XXXXXXXXXXXX        
       XXXXXXXXXXXXX XXXXXXXXXXXXX       
       XXXXXXXXXXXXX XXXXXXXXXXXXX       
      XXXXXXXXXXXXXX XXXXXXXXXXXXXX      
      XXXXXXXXXXXXXX XXXXXXXXXXXXXX      
     XXXXXXXXXXXXXXX XXXXXXXXXXXXXXX     
     XXXXXXXXXXXXXXX XXXXXXXXXXXXXXX     
    XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXX    
    XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXX    
   XXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX   
   XXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX   
  XXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXX  
  XXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXX  
 XXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXX 
 XXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXX 
 XXX  XXXXXXXXXXXXXX XXXXXXXXXXXXXX  XXX 
 XXXX  XXXXXXXXXXXXX XXXXXXXXXXXXX  XXXX 
 XXXXX  XXXXXXXXXXX   XXXXXXXXXXX  XXXXX 
 XXXXXX  XXXXXXXXXX   XXXXXXXXXX  XXXXXX 
 XXXXXXX  XXXXXXXX     XXXXXXXX  XXXXXXX 
  XXXXXX  XXXXXXX       XXXXXXX  XXXXXX  
  X XXXX  XXXXXX         XXXXXX  XXXX X  
    XXXX  XXXXX           XXXXX  XXXX    
     XXX  XXXX             XXXX  XXX     
      XX  XXX               XXX  XX      
       X  XXX               XXX  X       
          X X               X X          
"""

NAMASTE_F1 = parse_ascii_sprite(NAMASTE_ASCII_F1)
NAMASTE_F2 = parse_ascii_sprite(NAMASTE_ASCII_F2)

def get_winner(p, c):
    if p == c:
        return "tie"
    wins = {
        "rock": ["scissors"], 
        "paper": ["rock"], 
        "scissors": ["paper"]
    }
    return "player" if c in wins[p] else "computer"

def get_counters(move):
    counters = []
    wins = {
        "rock": ["scissors"], 
        "paper": ["rock"], 
        "scissors": ["paper"]
    }
    for m, beats in wins.items():
        if move in beats:
            counters.append(m)
    return counters

# ── Stars background ─────────────────────────────────────────────────────────
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
          random.uniform(0.3, 1.5)) for _ in range(120)]

def draw_stars(surf, t):
    for sx, sy, sp in stars:
        bri = int(128 + 127 * math.sin(t * sp * 0.8))
        col = (bri//3, bri//3, bri)
        pygame.draw.rect(surf, col, (sx, sy, 2, 2))

# ── Particles ────────────────────────────────────────────────────────────────
class FloatingText:
    def __init__(self, x, y, text, color, font):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = font
        self.life = 1.5
        self.vy = -2

    def update(self):
        self.y += self.vy
        self.life -= 0.02

    def draw(self, surf):
        if self.life > 0:
            rend = self.font.render(self.text, False, self.color)
            rend.set_alpha(int(255 * min(1, self.life * 2)))
            surf.blit(rend, (int(self.x) - rend.get_width()//2, int(self.y) - rend.get_height()//2))

floating_texts = []

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.life = 1.0
        self.size = random.randint(4, 10)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 0.025
    def draw(self, surf):
        if self.life > 0:
            alpha_size = int(self.size * self.life)
            if alpha_size > 0:
                pygame.draw.rect(surf, self.color,
                                 (int(self.x), int(self.y), alpha_size, alpha_size))

particles = []

def burst_particles(x, y, color, n=40):
    for _ in range(n):
        particles.append(Particle(x, y, color))

# ── Button ────────────────────────────────────────────────────────────────────
class PixelButton:
    def __init__(self, label, cx, cy, w=180, h=56, color=PIXEL_CYAN):
        self.label = label
        self.rect  = pygame.Rect(cx - w//2, cy - h//2, w, h)
        self.color = color
        self.hover = False
        self.pressed = False

    def update(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)

    def draw(self, surf):
        bg = BG_MID
        if self.pressed:
            bg = (40, 40, 80)
        elif self.hover:
            bg = (30, 30, 60)
        pygame.draw.rect(surf, bg, self.rect)
        draw_pixel_border(surf, self.rect, self.color, 3)
        col = PIXEL_WHITE if self.hover else self.color
        draw_text_center(surf, self.label, F_MED, col,
                         self.rect.centerx, self.rect.centery - F_MED.get_height()//2)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return True
        if event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False
        return False

# ════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ════════════════════════════════════════════════════════════════════════════
def splash_screen():
    start = time.time()

    # Build title letters for stagger animation
    title    = "PIXEL RPS"
    subtitle = "ROCK · PAPER · SCISSORS"
    letters_dropped = [False] * len(title)
    
    if snd_intro and global_sound_on:
        snd_intro.set_volume(0.6)
        snd_intro.play(-1)

    while True:
        t = time.time() - start
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if t > 1.0:
                    if snd_intro: snd_intro.stop()
                    return  # skip remaining splash

        # Background
        draw_grid_bg(screen, t * 60)
        draw_stars(screen, t)

        # Pulsing glow circle
        pulse = 0.5 + 0.5 * math.sin(t * 3)
        for r in range(160, 40, -20):
            alpha = int(pulse * 30 * (1 - r/160))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*PIXEL_CYAN, alpha), (r, r), r)
            screen.blit(s, (WIDTH//2 - r, HEIGHT//2 - r - 60))

        # Animated namaste hands in the center
        namaste_bob = int(math.sin(t * 4) * 8)
        namaste_frame = NAMASTE_F1 if int(t * 4) % 2 == 0 else NAMASTE_F2
        namaste_color = PIXEL_WHITE
        namaste_scale = 3
        namaste_w = 40 * namaste_scale
        namaste_h = 51 * namaste_scale
        namaste_ox = WIDTH//2 - namaste_w//2
        namaste_oy = HEIGHT//2 - 60 - namaste_h//2 + namaste_bob
        draw_pixel_sprite(screen, namaste_frame, namaste_color, namaste_ox, namaste_oy, namaste_scale)

        # Animated sprites spinning in
        for i, choice in enumerate(CHOICES):
            angle_offset = (i * 1.2566) + t * 0.6  # 72° apart, rotating
            rx = WIDTH//2 + int(math.cos(angle_offset) * 180)
            ry = HEIGHT//2 - 60 + int(math.sin(angle_offset) * 70)
            sprite_w = 8 * SCALE
            ox = rx - sprite_w//2
            oy = ry - sprite_w//2
            draw_pixel_sprite(screen, SPRITES[choice], COLORS[choice], ox, oy)

        # Title drop-in per character
        total_w = sum(F_HUGE.render(c, False, PIXEL_WHITE).get_width() for c in title)
        cx_start = WIDTH//2 - total_w//2
        for i, ch in enumerate(title):
            delay = i * 0.12
            progress = max(0, min(1, (t - delay) / 0.4))
            
            if progress == 1.0 and not letters_dropped[i]:
                if snd_blip and ch.strip() and global_sound_on: snd_blip.play()
                letters_dropped[i] = True

            # ease-out
            ease = 1 - (1 - progress) ** 3
            drop_y = int(60 + (1 - ease) * (-150))
            glyph_color_list = [PIXEL_CYAN, PIXEL_GREEN, PIXEL_YELLOW,
                                 PIXEL_PURPLE, PIXEL_WHITE, PIXEL_ORANGE,
                                 PIXEL_CYAN, PIXEL_GREEN, PIXEL_YELLOW, PIXEL_WHITE]
            col = glyph_color_list[i % len(glyph_color_list)]
            rend = F_HUGE.render(ch, False, col)
            screen.blit(rend, (cx_start, drop_y))
            cx_start += rend.get_width()

        # Subtitle fade-in
        sub_alpha = min(255, int(255 * max(0, (t - 1.2) / 0.6)))
        sub_surf  = F_MED.render(subtitle, False, PIXEL_TEAL)
        sub_surf.set_alpha(sub_alpha)
        screen.blit(sub_surf, (WIDTH//2 - sub_surf.get_width()//2, 148))

        # "PRESS ANY KEY" blink
        if t > 2.5 and int(t * 2) % 2 == 0:
            draw_text_center(screen, "▶  PRESS ANY KEY TO START  ◀",
                             F_SMALL, PIXEL_YELLOW, WIDTH//2, HEIGHT - 70)

        draw_scanlines(screen)
        pygame.display.flip()

# ════════════════════════════════════════════════════════════════════════════
# GAME SCREEN
# ════════════════════════════════════════════════════════════════════════════
class GameScreen:
    def __init__(self):
        self.ai_history = []
        self.ai_transitions = {c: {c2: 0 for c2 in CHOICES} for c in CHOICES}
        self.load_stats()
        self.reset_scores()
        self.state = "mode_select"   # mode_select | choose | reveal | result
        self.player_choice = None
        self.cpu_choice    = None
        self.result        = None
        self.anim_t        = 0
        self.result_msg    = ""
        self.result_color  = PIXEL_WHITE
        self.countdown     = 0
        self.shake         = 0
        self.commentary    = ""
        self.p1_temp       = None
        self.p2_temp       = None

        self.modes = ["CLASSIC", "HARDCORE", "SURVIVAL", "MULTIPLAYER"]
        self.mode_idx = 0
        
        # Mode Selection Buttons
        self.mode_btns = [
            PixelButton("CLASSIC", WIDTH//2 - 130, HEIGHT//2 - 30, 240, 50, PIXEL_CYAN),
            PixelButton("HARDCORE", WIDTH//2 + 130, HEIGHT//2 - 30, 240, 50, PIXEL_RED),
            PixelButton("SURVIVAL", WIDTH//2 - 130, HEIGHT//2 + 40, 240, 50, PIXEL_YELLOW),
            PixelButton("MULTIPLAYER", WIDTH//2 + 130, HEIGHT//2 + 40, 240, 50, PIXEL_PURPLE),
        ]
        
        self.sound_btn = SoundIconButton(WIDTH - 30, HEIGHT - 30, scale=3)
        self.hud_y_offset = -100

        self.cam_tracker = CameraTracker() if CAMERA_AVAILABLE else None

        # Buttons
        bw, bh = 140, 50
        y_btn  = HEIGHT - 110
        self.btns = {
            "rock":     PixelButton("🪨 ROCK",     WIDTH//2 - 200, y_btn, bw, bh, PIXEL_ORANGE),
            "paper":    PixelButton("📄 PAPER",    WIDTH//2,       y_btn, bw, bh, PIXEL_CYAN),
            "scissors": PixelButton("✂ SCISSORS", WIDTH//2 + 200, y_btn, bw, bh, PIXEL_PURPLE),
        }
        self.play_again_btn = PixelButton("▶  PLAY AGAIN", WIDTH//2, HEIGHT - 60, 260, 52, PIXEL_GREEN)
        self.back_btn = BackIconButton(30, HEIGHT - 30, scale=3)

    def load_stats(self):
        self.player_stats = {"wins": 0, "losses": 0, "ties": 0, "level": 1, "xp": 0}
        self.stats_file = os.path.join(BASE_DIR, "stats.json")
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    self.player_stats = json.load(f)
            except: pass

    def save_stats(self):
        try:
            with open(self.stats_file, "w") as f:
                json.dump(self.player_stats, f)
        except: pass
            
    def ai_predict_and_counter(self):
        if len(self.ai_history) < 2: return random.choice(CHOICES)
        prev = self.ai_history[-1]
        poss = self.ai_transitions[prev]
        max_freq = max(poss.values())
        if max_freq == 0: return random.choice(CHOICES)
        likely = [m for m, f in poss.items() if f == max_freq]
        pred = random.choice(likely)
        
        # Hardcore mode tries to double-guess
        if self.modes[self.mode_idx] == "HARDCORE":
            return random.choice(CHOICES)
            
        return random.choice(get_counters(pred))

    def reset_scores(self):
        self.score_player = 0
        self.score_cpu    = 0
        self.score_ties   = 0
        self.rounds       = 0
        self.player_hp    = 100
        self.cpu_hp       = 100
        self.p1_temp      = None
        self.p2_temp      = None
        self.game_over    = False

    def handle_event(self, event, t):
        global global_sound_on
        if self.sound_btn.is_clicked(event):
            global_sound_on = not global_sound_on
            if snd_select and global_sound_on: snd_select.play()
            
        if self.state == "mode_select":
            for i, btn in enumerate(self.mode_btns):
                if btn.is_clicked(event):
                    if snd_select and global_sound_on: snd_select.play()
                    self.mode_idx = i
                    self.reset_scores()
                    self.state = "choose"
                    if self.modes[self.mode_idx] == "MULTIPLAYER" and self.cam_tracker:
                        self.cam_tracker.start()
        elif self.state == "choose" and not self.game_over:
            if self.back_btn.is_clicked(event):
                if snd_select and global_sound_on: snd_select.play()
                if self.cam_tracker: self.cam_tracker.stop()
                self.state = "mode_select"
                self.reset_scores()
                
            for name, btn in self.btns.items():
                if btn.is_clicked(event):
                    if snd_select and global_sound_on: snd_select.play()
                    if self.modes[self.mode_idx] == "MULTIPLAYER":
                        if not CAMERA_AVAILABLE:
                            if not self.p1_temp:
                                self.p1_temp = name
                            elif not self.p2_temp:
                                self.p2_temp = name
                                self.player_choice = self.p1_temp
                                self.cpu_choice = self.p2_temp
                                self.state = "reveal"
                                self.anim_t = 0
                    else:
                        self.player_choice = name
                        self.cpu_choice = self.ai_predict_and_counter()
                        if len(self.ai_history) > 0:
                            self.ai_transitions[self.ai_history[-1]][name] += 1
                        self.ai_history.append(name)
                        self.state = "reveal"
                        self.anim_t = 0


        elif self.state == "result" or self.game_over:
            if self.play_again_btn.is_clicked(event):
                if self.game_over:
                    self.state = "mode_select"
                else:
                    self.state = "choose"
                    if self.modes[self.mode_idx] == "MULTIPLAYER" and self.cam_tracker:
                        self.cam_tracker.start()
                self.player_choice = None
                self.cpu_choice    = None
                self.p1_temp       = None
                self.p2_temp       = None
                self.game_over     = False

    def update(self, dt, t):
        mx, my = pygame.mouse.get_pos()
        self.sound_btn.update(mx, my)
        if self.state == "mode_select":
            for btn in self.mode_btns:
                btn.update(mx, my)
        elif self.state == "choose":
            self.back_btn.update(mx, my)
            for btn in self.btns.values():
                btn.update(mx, my)
                
            if self.modes[self.mode_idx] == "MULTIPLAYER" and CAMERA_AVAILABLE and self.cam_tracker and self.cam_tracker.running:
                with self.cam_tracker.lock:
                    g1, g2 = self.cam_tracker.p1_gesture, self.cam_tracker.p2_gesture
                if g1 and g2:
                    if snd_select and global_sound_on: snd_select.play()
                    self.player_choice = g1
                    self.cpu_choice = g2
                    self.state = "reveal"
                    self.anim_t = 0
                    self.cam_tracker.stop()
        elif self.state == "result":
            self.play_again_btn.update(mx, my)

        # Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)
        for ft in floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                floating_texts.remove(ft)

        if self.shake > 0:
            self.shake -= dt * 8

        if self.state == "reveal":
            self.anim_t += dt
            if self.anim_t >= 1.5:
                # Determine result
                self.result = get_winner(self.player_choice, self.cpu_choice)
                self.rounds += 1
                if self.result == "player":
                    self.commentary = random.choice(COMMENTARY_WIN)
                    if snd_win and global_sound_on: snd_win.play()
                    self.score_player += 1
                    dmg = random.randint(15, 25)
                    crit = random.random() < 0.2
                    if crit: dmg *= 2
                    self.cpu_hp = max(0, self.cpu_hp - dmg)
                    self.result_msg   = "CRITICAL WIN!" if crit else "YOU WIN!"
                    if self.modes[self.mode_idx] == "MULTIPLAYER":
                        self.result_msg = "CRITICAL P1 WIN!" if crit else "P1 WINS!"
                    self.result_color = WIN_COLOR
                    burst_particles(WIDTH//4,   HEIGHT//2 - 40, PIXEL_GREEN, 60)
                    burst_particles(3*WIDTH//4, HEIGHT//2 - 40, PIXEL_RED, 20)
                    self.shake = 0.8 if crit else 0.4
                    floating_texts.append(FloatingText(3*WIDTH//4, HEIGHT//2 - 60, f"-{dmg}", PIXEL_RED, F_BIG))
                    if crit:
                        floating_texts.append(FloatingText(3*WIDTH//4, HEIGHT//2 - 100, "CRIT!", PIXEL_YELLOW, F_BIG))
                elif self.result == "computer":
                    self.commentary = random.choice(COMMENTARY_LOSE)
                    if snd_lose and global_sound_on: snd_lose.play()
                    self.score_cpu += 1
                    dmg = random.randint(25, 40) if self.modes[self.mode_idx] == "HARDCORE" else random.randint(15, 25)
                    crit = random.random() < 0.2
                    if crit: dmg *= 2
                    self.player_hp = max(0, self.player_hp - dmg)
                    self.result_msg  = "CRITICAL LOSS!" if crit else "CPU WINS!"
                    if self.modes[self.mode_idx] == "MULTIPLAYER":
                        self.result_msg = "CRITICAL P2 WIN!" if crit else "P2 WINS!"
                    self.result_color = LOSE_COLOR
                    burst_particles(3*WIDTH//4, HEIGHT//2 - 40, PIXEL_RED, 60)
                    burst_particles(WIDTH//4,   HEIGHT//2 - 40, PIXEL_RED, 20)
                    self.shake = 0.8 if crit else 0.4
                    floating_texts.append(FloatingText(WIDTH//4, HEIGHT//2 - 60, f"-{dmg}", PIXEL_RED, F_BIG))
                    if crit:
                        floating_texts.append(FloatingText(WIDTH//4, HEIGHT//2 - 100, "CRIT!", PIXEL_YELLOW, F_BIG))
                else:
                    self.commentary = random.choice(COMMENTARY_DRAW)
                    if snd_tie and global_sound_on: snd_tie.play()
                    self.score_ties += 1
                    self.result_msg  = "TIE GAME!"
                    self.result_color = TIE_COLOR
                    burst_particles(WIDTH//2,   HEIGHT//2 - 40, PIXEL_YELLOW, 40)
                    
                if self.cpu_hp <= 0 and self.modes[self.mode_idx] == "SURVIVAL":
                    self.cpu_hp = 100
                    self.player_stats["xp"] += 50
                    self.result_msg = "CPU DEFEATED! NEXT OPPONENT!"
                    self.game_over = False
                elif self.player_hp <= 0 or self.cpu_hp <= 0:
                    self.game_over = True
                    if self.modes[self.mode_idx] == "MULTIPLAYER":
                        self.result_msg = "PLAYER 1 WINS!" if self.player_hp > 0 else "PLAYER 2 WINS!"
                        self.result_color = PIXEL_GREEN if self.player_hp > 0 else PIXEL_RED
                    else:
                        self.result_msg = "VICTORY!" if self.player_hp > 0 else "DEFEAT!"
                        self.result_color = WIN_COLOR if self.player_hp > 0 else LOSE_COLOR
                    if self.player_hp > 0:
                        self.player_stats["wins"] += 1
                        self.player_stats["xp"] += 20
                    else:
                        self.player_stats["losses"] += 1
                        self.player_stats["xp"] += 5
                    if self.player_stats["xp"] >= 100:
                        self.player_stats["level"] += 1
                        self.player_stats["xp"] -= 100
                    self.save_stats()
                self.state  = "result"
                self.anim_t = 0

    def draw_health_bar(self, surf, x, y, w, h, hp, max_hp, color, name_label):
        draw_pixel_border(surf, (x, y, w, h), PIXEL_GREY, 2)
        pygame.draw.rect(surf, (40, 0, 0), (x+2, y+2, w-4, h-4))
        fill_w = max(0, int((hp / max_hp) * (w-4)))
        pygame.draw.rect(surf, color, (x+2, y+2, fill_w, h-4))
        lbl = F_TINY.render(f"{name_label}: {hp}/{max_hp}", False, PIXEL_WHITE)
        surf.blit(lbl, (x + w//2 - lbl.get_width()//2, y - 20))

    def draw_hud(self, surf, t, offset_y=0):
        # Top bar
        pygame.draw.rect(surf, BG_MID, (0, offset_y, WIDTH, 90))
        draw_pixel_border(surf, (0, offset_y, WIDTH, 90), PIXEL_GREY, 2)

        # Health bars
        bar_w = 200
        bar_h = 20
        p1_label = "P1 HP" if self.modes[self.mode_idx] == "MULTIPLAYER" else "PLAYER HP"
        p2_label = "P2 HP" if self.modes[self.mode_idx] == "MULTIPLAYER" else "CPU HP"
        self.draw_health_bar(surf, 40, 45 + offset_y, bar_w, bar_h, self.player_hp, 100, PIXEL_GREEN, p1_label)
        self.draw_health_bar(surf, WIDTH - 40 - bar_w, 45 + offset_y, bar_w, bar_h, self.cpu_hp, 100, PIXEL_RED, p2_label)

        # Scores
        if self.modes[self.mode_idx] != "MULTIPLAYER":
            lvl = self.player_stats["level"]
            xp = self.player_stats["xp"]
            draw_text_center(surf, f"LVL: {lvl} | XP: {xp}/100", F_TINY, PIXEL_CYAN, WIDTH//2, 15 + offset_y)
        else:
            draw_text_center(surf, "LOCAL MULTIPLAYER", F_TINY, PIXEL_PURPLE, WIDTH//2, 15 + offset_y)
            
        draw_text_center(surf, f"TIES: {self.score_ties}",  F_MED, PIXEL_YELLOW, WIDTH//2, 35 + offset_y)
        draw_text_center(surf, f"ROUND {self.rounds + 1}", F_TINY, PIXEL_GREY, WIDTH//2, 65 + offset_y)

    def draw_sprite_card(self, surf, choice, label, cx, cy, scale=SCALE, highlight=False):
        sw = 8 * scale
        sh = 8 * scale
        pad = 20
        rx, ry = cx - sw//2 - pad, cy - sh//2 - pad
        rw, rh = sw + pad*2,        sh + pad*2

        bg_col = (30, 30, 60) if not highlight else (40, 60, 40)
        pygame.draw.rect(surf, bg_col, (rx, ry, rw, rh))
        draw_pixel_border(surf, (rx, ry, rw, rh),
                          WIN_COLOR if highlight else PIXEL_GREY, 3)

        ox = cx - sw//2 + (8 - len(SPRITES[choice][0])) * scale // 2
        oy = cy - sh//2
        draw_pixel_sprite(surf, SPRITES[choice], COLORS[choice], cx - sw//2, cy - sh//2, scale)

        lbl = F_SMALL.render(label.upper(), False, PIXEL_WHITE)
        surf.blit(lbl, (cx - lbl.get_width()//2, cy + sh//2 + pad + 4))

    def draw(self, surf, t):
        # Shake offset
        sx = int(math.sin(t * 40) * self.shake * 8) if self.shake > 0 else 0
        sy = int(math.cos(t * 50) * self.shake * 6) if self.shake > 0 else 0

        # Background
        drawn_cam = False
        if self.state == "choose" and self.modes[self.mode_idx] == "MULTIPLAYER" and self.cam_tracker and self.cam_tracker.running:
            with self.cam_tracker.lock:
                frame = self.cam_tracker.frame_surf
            if frame:
                surf.blit(frame, (0, 0))
                # Add a dark overlay so text is visible
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(100)
                overlay.fill((0, 0, 0))
                surf.blit(overlay, (0, 0))
                drawn_cam = True

        if not drawn_cam:
            draw_grid_bg(surf, t * 60)
            draw_stars(surf, t)

        if self.state != "mode_select":
            self.hud_y_offset = min(0, self.hud_y_offset + 5)
            self.draw_hud(surf, t, self.hud_y_offset)
        else:
            self.hud_y_offset = -100

        self.sound_btn.draw(surf, global_sound_on)

        vs_y    = HEIGHT//2 - 60
        card_y  = HEIGHT//2 - 30
        scale_v = SCALE + 1

        if self.state == "mode_select":
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            col   = tuple(int(a + (b-a)*pulse) for a,b in zip(PIXEL_GREY, PIXEL_WHITE))
            draw_text_center(surf, "SELECT GAME MODE", F_BIG, col, WIDTH//2, 120)
            
            desc = ["STANDARD 1v1 MATCH", "HARDCORE AI & DOUBLE DAMAGE", "ENDLESS BATTLE - SURVIVE!", "LOCAL 1v1 - SEQUENTIAL TURNS!"]
            for i, btn in enumerate(self.mode_btns):
                btn.draw(surf)
                if btn.hover:
                    draw_text_center(surf, desc[i], F_SMALL, PIXEL_YELLOW, WIDTH//2, HEIGHT - 100)
                    
        elif self.state == "choose":
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            col   = tuple(int(a + (b-a)*pulse) for a,b in zip(PIXEL_GREY, PIXEL_WHITE))
            
            if self.modes[self.mode_idx] == "MULTIPLAYER":
                if CAMERA_AVAILABLE and self.cam_tracker and self.cam_tracker.running:
                    draw_text_center(surf, "HOLD GESTURES TO CAMERA", F_BIG, col, WIDTH//2 + sx, 110 + sy + self.hud_y_offset)
                    
                    with self.cam_tracker.lock:
                        p1_g, p2_g = self.cam_tracker.p1_gesture, self.cam_tracker.p2_gesture
                        
                    if p1_g:
                        draw_text_center(surf, f"P1: {p1_g.upper()}", F_BIG, PIXEL_GREEN, WIDTH//4, HEIGHT//2)
                    else:
                        draw_text_center(surf, "P1: SHOW HAND", F_MED, PIXEL_GREY, WIDTH//4, HEIGHT//2)
                        
                    if p2_g:
                        draw_text_center(surf, f"P2: {p2_g.upper()}", F_BIG, PIXEL_RED, 3*WIDTH//4, HEIGHT//2)
                    else:
                        draw_text_center(surf, "P2: SHOW HAND", F_MED, PIXEL_GREY, 3*WIDTH//4, HEIGHT//2)
                        
                    draw_pixel_border(surf, (WIDTH//2 - 2, 100, 4, HEIGHT), PIXEL_GREY, 2)
                else:
                    if not self.p1_temp:
                        draw_text_center(surf, "PLAYER 1'S TURN (P2 LOOK AWAY!)", F_BIG, col, WIDTH//2 + sx, 110 + sy + self.hud_y_offset)
                    else:
                        draw_text_center(surf, "PLAYER 2'S TURN (P1 LOOK AWAY!)", F_BIG, col, WIDTH//2 + sx, 110 + sy + self.hud_y_offset)

                    for btn in self.btns.values():
                        btn.draw(surf)
            else:
                draw_text_center(surf, "CHOOSE YOUR WEAPON!", F_BIG, col, WIDTH//2 + sx, 110 + sy + self.hud_y_offset)

            show_ui = True
            if self.modes[self.mode_idx] == "MULTIPLAYER" and CAMERA_AVAILABLE and self.cam_tracker and self.cam_tracker.running:
                show_ui = False
                
            if show_ui:
                # Idle animated sprites
                for i, choice in enumerate(CHOICES):
                    bob = int(math.sin(t * 2 + i * 1.5) * 6)
                    cx  = [WIDTH//2 - 200, WIDTH//2, WIDTH//2 + 200][i]
                    draw_pixel_sprite(surf, SPRITES[choice], COLORS[choice],
                                      cx - 4*scale_v, 180 + bob + self.hud_y_offset, scale_v)
                    lbl = F_SMALL.render(choice.upper(), False, COLORS[choice])
                    surf.blit(lbl, (cx - lbl.get_width()//2, 180 + 8*scale_v + 8 + self.hud_y_offset))
    
                # Buttons
                for btn in self.btns.values():
                    btn.draw(surf)
                
            self.back_btn.draw(surf)

        elif self.state == "reveal":
            progress = min(1.0, self.anim_t / 1.5)
            # Player card slides in from left
            px = int(WIDTH//4 * progress + (WIDTH//4)*(1-progress) - WIDTH//4*(1-progress))
            # Simpler: slide from off-screen
            p_x = int(-100 + (WIDTH//4 + 100) * progress)
            c_x = int(WIDTH + 100 - (WIDTH//4 + 100 + (WIDTH - WIDTH*3//4)) * progress)
            c_x = int(WIDTH + 100 - (100 + WIDTH//4) * progress)

            # Actually let's just ease from sides
            ease = 1 - (1 - progress) ** 3
            p_cx = int(-80 + (WIDTH//4 + 80) * ease)
            c_cx = int(WIDTH + 80 - (WIDTH//4 + 80) * ease)

            draw_pixel_sprite(surf, SPRITES[self.player_choice],
                              COLORS[self.player_choice],
                              p_cx - 4*scale_v, card_y - 4*scale_v, scale_v)
            lbl = F_SMALL.render("YOU", False, PIXEL_GREEN)
            surf.blit(lbl, (p_cx - lbl.get_width()//2, card_y + 5*scale_v + 4))

            # CPU – question mark until revealed
            if progress < 0.8:
                q_surf = F_HUGE.render("?", False, PIXEL_GREY)
                surf.blit(q_surf, (c_cx - q_surf.get_width()//2,
                                   card_y - q_surf.get_height()//2))
            else:
                draw_pixel_sprite(surf, SPRITES[self.cpu_choice],
                                  COLORS[self.cpu_choice],
                                  c_cx - 4*scale_v, card_y - 4*scale_v, scale_v)
                lbl2 = F_SMALL.render("CPU", False, PIXEL_RED)
                surf.blit(lbl2, (c_cx - lbl2.get_width()//2, card_y + 5*scale_v + 4))

            # VS label
            vs = F_BIG.render("VS", False, PIXEL_YELLOW)
            surf.blit(vs, (WIDTH//2 - vs.get_width()//2, card_y - vs.get_height()//2))

        elif self.state == "result":
            # Player card
            p_win = self.result == "player"
            c_win = self.result == "computer"
            p_cx  = WIDTH//4 + sx
            c_cx  = 3*WIDTH//4 + sx

            draw_pixel_sprite(surf, SPRITES[self.player_choice],
                              COLORS[self.player_choice],
                              p_cx - 4*scale_v + sx, card_y - 4*scale_v + sy, scale_v)
            p_label = "P1" if self.modes[self.mode_idx] == "MULTIPLAYER" else "YOU"
            plbl = F_SMALL.render(p_label, False, WIN_COLOR if p_win else PIXEL_GREY)
            surf.blit(plbl, (p_cx - plbl.get_width()//2 + sx, card_y + 5*scale_v + 4 + sy))

            draw_pixel_sprite(surf, SPRITES[self.cpu_choice],
                              COLORS[self.cpu_choice],
                              c_cx - 4*scale_v + sx, card_y - 4*scale_v + sy, scale_v)
            c_label = "P2" if self.modes[self.mode_idx] == "MULTIPLAYER" else "CPU"
            clbl = F_SMALL.render(c_label, False, WIN_COLOR if c_win else PIXEL_GREY)
            surf.blit(clbl, (c_cx - clbl.get_width()//2 + sx, card_y + 5*scale_v + 4 + sy))

            # VS
            vs = F_BIG.render("VS", False, PIXEL_YELLOW)
            surf.blit(vs, (WIDTH//2 - vs.get_width()//2, card_y - vs.get_height()//2))

            # Result banner
            pulse = 0.6 + 0.4 * math.sin(self.anim_t * 5)
            scale_factor = 1 + 0.08 * math.sin(self.anim_t * 6)
            banner = F_BIG.render(self.result_msg, False, self.result_color)
            bw_s = int(banner.get_width() * scale_factor)
            bh_s = int(banner.get_height() * scale_factor)
            banner_scaled = pygame.transform.scale(banner, (bw_s, bh_s))
            surf.blit(banner_scaled, (WIDTH//2 - bw_s//2, 110))

            # Particles
            for p in particles:
                p.draw(surf)

            # Subtitle (what beat what)
            beats = {
                "rock": {"scissors": "crushes"},
                "paper": {"rock": "covers"},
                "scissors": {"paper": "cuts"}
            }
            if self.result != "tie":
                winner = self.player_choice if p_win else self.cpu_choice
                loser = self.cpu_choice if p_win else self.player_choice
                verb = beats[winner].get(loser, "beats")
                sub = f"{winner.upper()} {verb.upper()} {loser.upper()}"
                draw_text_center(surf, sub, F_SMALL, PIXEL_WHITE, WIDTH//2, 170)
                
            # Random Commentary
            if self.commentary:
                draw_text_center(surf, f'"{self.commentary}"', F_SMALL, PIXEL_CYAN, WIDTH//2, 195)

            if self.game_over:
                self.play_again_btn.label = "▶  NEW MATCH"
            else:
                self.play_again_btn.label = "▶  NEXT ROUND"
            self.play_again_btn.draw(surf)

        # Particles (always on top in choose/reveal)
        if self.state != "result":
            for p in particles:
                p.draw(surf)

        for ft in floating_texts:
            ft.draw(surf)

        draw_scanlines(surf)

# ── Main loop ────────────────────────────────────────────────────────────────
def main():
    try:
        splash_screen()

        game = GameScreen()
        t    = 0.0

        while True:
            dt = clock.tick(FPS) / 1000
            t += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pass # Ignore ESC to prevent accidental game closures
                game.handle_event(event, t)

            game.update(dt, t)
            game.draw(screen, t)
            pygame.display.flip()
    except Exception as e:
        import traceback
        crash_log_path = os.path.join(BASE_DIR, "crash.log")
        with open(crash_log_path, "w") as f:
            traceback.print_exc(file=f)
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()
