import re
import os

with open('rock_paper_scissors.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Chunk 1: Imports
code = code.replace(
    'import time\n',
    'import time\nimport json\nimport os\n'
)

# Chunk 2: Splashes
code = code.replace(
    'title    = "PIXEL  RPS"\n    subtitle = "ROCK · PAPER · SCISSORS"',
    'title    = "PIXEL RPSLS"\n    subtitle = "ROCK · PAPER · SCISSORS · LIZARD · SPOCK"'
)

# Chunk 3: Splash sprites spin
code = code.replace(
    'angle_offset = (i * 2.094) + t * 0.6  # 120° apart, rotating',
    'angle_offset = (i * 1.2566) + t * 0.6  # 72° apart, rotating'
)

# Chunk 4: Pixels and Choices
old_pixels = '''SPRITES = {"rock": ROCK_PIXELS, "paper": PAPER_PIXELS, "scissors": SCISSORS_PIXELS}
COLORS  = {"rock": PIXEL_ORANGE, "paper": PIXEL_CYAN, "scissors": PIXEL_PURPLE}
CHOICES = ["rock", "paper", "scissors"]'''

new_pixels = '''LIZARD_PIXELS = [
    (2,0),(3,0),(4,0),(5,0),
    (1,1),(6,1),
    (1,2),(3,2),(6,2),
    (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),
    (0,4),(2,4),(4,4),
    (0,5),(2,5),(4,5),
    (2,6),(3,6),
    (2,7),(3,7),
]

SPOCK_PIXELS = [
    (1,0),(2,0),(5,0),(6,0),
    (1,1),(2,1),(5,1),(6,1),
    (1,2),(2,2),(5,2),(6,2),
    (1,3),(2,3),(3,3),(4,3),(5,3),(6,3),
    (0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),
    (0,5),(1,5),(6,5),(7,5),
    (0,6),(1,6),(6,6),(7,6),
    (1,7),(2,7),(3,7),(4,7),(5,7),(6,7),
]

SPRITES = {"rock": ROCK_PIXELS, "paper": PAPER_PIXELS, "scissors": SCISSORS_PIXELS, "lizard": LIZARD_PIXELS, "spock": SPOCK_PIXELS}
COLORS  = {"rock": PIXEL_ORANGE, "paper": PIXEL_CYAN, "scissors": PIXEL_PURPLE, "lizard": PIXEL_GREEN, "spock": PIXEL_YELLOW}
CHOICES = ["rock", "paper", "scissors", "lizard", "spock"]'''

code = code.replace(old_pixels, new_pixels)

# Chunk 5: Winner Logic
old_winner = '''def get_winner(p, c):
    if p == c:
        return "tie"
    wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    return "player" if wins[p] == c else "computer"'''

new_winner = '''def get_winner(p, c):
    if p == c:
        return "tie"
    wins = {
        "rock": ["scissors", "lizard"], 
        "paper": ["rock", "spock"], 
        "scissors": ["paper", "lizard"],
        "lizard": ["spock", "paper"],
        "spock": ["scissors", "rock"]
    }
    return "player" if c in wins[p] else "computer"

def get_counters(move):
    counters = []
    wins = {
        "rock": ["scissors", "lizard"], 
        "paper": ["rock", "spock"], 
        "scissors": ["paper", "lizard"],
        "lizard": ["spock", "paper"],
        "spock": ["scissors", "rock"]
    }
    for m, beats in wins.items():
        if move in beats:
            counters.append(m)
    return counters'''

code = code.replace(old_winner, new_winner)

# Chunk 6: GameScreen __init__
old_init = '''    def __init__(self):
        self.reset_scores()
        self.state = "choose"   # choose | reveal | result
        self.player_choice = None
        self.cpu_choice    = None
        self.result        = None
        self.anim_t        = 0
        self.result_msg    = ""
        self.result_color  = PIXEL_WHITE
        self.countdown     = 0
        self.shake         = 0

        # Buttons
        bw, bh = 220, 58
        y_btn  = HEIGHT - 110
        self.btns = {
            "rock":     PixelButton("🪨  ROCK",     WIDTH//2 - 250, y_btn, bw, bh, PIXEL_ORANGE),
            "paper":    PixelButton("📄  PAPER",    WIDTH//2,       y_btn, bw, bh, PIXEL_CYAN),
            "scissors": PixelButton("✂  SCISSORS", WIDTH//2 + 250, y_btn, bw, bh, PIXEL_PURPLE),
        }'''

new_init = '''    def __init__(self):
        self.ai_history = []
        self.ai_transitions = {c: {c2: 0 for c2 in CHOICES} for c in CHOICES}
        self.load_stats()
        self.reset_scores()
        self.state = "choose"   # choose | reveal | result
        self.player_choice = None
        self.cpu_choice    = None
        self.result        = None
        self.anim_t        = 0
        self.result_msg    = ""
        self.result_color  = PIXEL_WHITE
        self.countdown     = 0
        self.shake         = 0

        # Buttons
        bw, bh = 140, 50
        y_btn  = HEIGHT - 110
        self.btns = {
            "rock":     PixelButton("🪨 ROCK",     WIDTH//2 - 300, y_btn, bw, bh, PIXEL_ORANGE),
            "paper":    PixelButton("📄 PAPER",    WIDTH//2 - 150, y_btn, bw, bh, PIXEL_CYAN),
            "scissors": PixelButton("✂ SCISSORS", WIDTH//2,       y_btn, bw, bh, PIXEL_PURPLE),
            "lizard":   PixelButton("🦎 LIZARD",   WIDTH//2 + 150, y_btn, bw, bh, PIXEL_GREEN),
            "spock":    PixelButton("🖖 SPOCK",    WIDTH//2 + 300, y_btn, bw, bh, PIXEL_YELLOW),
        }

    def load_stats(self):
        self.player_stats = {"wins": 0, "losses": 0, "ties": 0, "level": 1, "xp": 0}
        if os.path.exists("stats.json"):
            try:
                with open("stats.json", "r") as f:
                    self.player_stats = json.load(f)
            except: pass

    def save_stats(self):
        with open("stats.json", "w") as f:
            json.dump(self.player_stats, f)
            
    def ai_predict_and_counter(self):
        if len(self.ai_history) < 2: return random.choice(CHOICES)
        prev = self.ai_history[-1]
        poss = self.ai_transitions[prev]
        max_freq = max(poss.values())
        if max_freq == 0: return random.choice(CHOICES)
        likely = [m for m, f in poss.items() if f == max_freq]
        pred = random.choice(likely)
        return random.choice(get_counters(pred))'''

code = code.replace(old_init, new_init)

# Chunk 7: Event handle AI logic
old_event = '''                    if snd_select: snd_select.play()
                    self.player_choice = name
                    self.cpu_choice    = random.choice(CHOICES)'''

new_event = '''                    if snd_select: snd_select.play()
                    self.player_choice = name
                    self.cpu_choice = self.ai_predict_and_counter()
                    if len(self.ai_history) > 0:
                        self.ai_transitions[self.ai_history[-1]][name] += 1
                    self.ai_history.append(name)'''

code = code.replace(old_event, new_event)

# Chunk 8: Result save stats
old_save = '''                if self.player_hp <= 0 or self.cpu_hp <= 0:
                    self.game_over = True
                    self.result_msg = "VICTORY!" if self.player_hp > 0 else "DEFEAT!"
                    self.result_color = WIN_COLOR if self.player_hp > 0 else LOSE_COLOR'''

new_save = '''                if self.player_hp <= 0 or self.cpu_hp <= 0:
                    self.game_over = True
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
                    self.save_stats()'''

code = code.replace(old_save, new_save)

# Chunk 9: Draw HUD
old_hud = '''        # Scores
        draw_text_center(surf, f"TIES: {self.score_ties}",  F_MED, PIXEL_YELLOW, WIDTH//2, 10)
        draw_text_center(surf, f"ROUND {self.rounds + 1}", F_TINY, PIXEL_GREY, WIDTH//2, 60)'''

new_hud = '''        # Scores
        lvl = self.player_stats["level"]
        xp = self.player_stats["xp"]
        draw_text_center(surf, f"LVL: {lvl} | XP: {xp}/100", F_TINY, PIXEL_CYAN, WIDTH//2, 15)
        draw_text_center(surf, f"TIES: {self.score_ties}",  F_MED, PIXEL_YELLOW, WIDTH//2, 35)
        draw_text_center(surf, f"ROUND {self.rounds + 1}", F_TINY, PIXEL_GREY, WIDTH//2, 65)'''

code = code.replace(old_hud, new_hud)

# Chunk 10: Idle sprites spacing
old_idle = '''            # Idle animated sprites
            for i, choice in enumerate(CHOICES):
                bob = int(math.sin(t * 2 + i * 1.5) * 6)
                cx  = [WIDTH//2 - 250, WIDTH//2, WIDTH//2 + 250][i]'''

new_idle = '''            # Idle animated sprites
            for i, choice in enumerate(CHOICES):
                bob = int(math.sin(t * 2 + i * 1.5) * 6)
                cx  = [WIDTH//2 - 300, WIDTH//2 - 150, WIDTH//2, WIDTH//2 + 150, WIDTH//2 + 300][i]'''

code = code.replace(old_idle, new_idle)

# Chunk 11: Subtitles
old_sub = '''            # Subtitle (what beat what)
            beats = {"rock": "crushes scissors", "paper": "covers rock",
                     "scissors": "cuts paper"}
            if self.result != "tie":
                winner = self.player_choice if p_win else self.cpu_choice
                sub = f"{winner.upper()} {beats[winner].upper()}"'''

new_sub = '''            # Subtitle (what beat what)
            beats = {
                "rock": {"scissors": "crushes", "lizard": "crushes"},
                "paper": {"rock": "covers", "spock": "disproves"},
                "scissors": {"paper": "cuts", "lizard": "decapitates"},
                "lizard": {"spock": "poisons", "paper": "eats"},
                "spock": {"scissors": "smashes", "rock": "vaporizes"}
            }
            if self.result != "tie":
                winner = self.player_choice if p_win else self.cpu_choice
                loser = self.cpu_choice if p_win else self.player_choice
                verb = beats[winner].get(loser, "beats")
                sub = f"{winner.upper()} {verb.upper()} {loser.upper()}"'''

code = code.replace(old_sub, new_sub)

with open('rock_paper_scissors.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patching complete!")
