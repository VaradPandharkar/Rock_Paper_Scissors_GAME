# ⚔️ PIXEL RPS — Rock Paper Scissors

A retro pixel-art **Rock · Paper · Scissors** game built with Python and Pygame, featuring animated sprites, sound effects, an AI opponent, multiple game modes, and optional hand gesture recognition via camera.

---

## 🎮 Features

- 🪨 Classic **Rock · Paper · Scissors** gameplay
- 🎨 Retro **pixel-art sprites** with animated idle states
- 🤖 **AI opponent** with Markov chain prediction (learns your patterns!)
- 🔊 Sound effects for win / lose / tie / select
- 🎵 Intro music on launch
- 🧬 **4 Game Modes:**
  - Standard 1v1
  - Hardcore (harder AI + double damage)
  - Endless survival
  - Local multiplayer (sequential turns)
- 📷 Optional **hand gesture recognition** via webcam (MediaPipe)
- 🏆 **XP & Level system** with persistent stats saved to `stats.json`
- ✨ Particle effects, scanline overlay, CRT-style visuals

---

## 📁 Project Structure

```
Rock_Paper_scissors_Game/
├── rock_paper_scissors.py   # Main game
├── patch_game.py            # Upgrade to Lizard & Spock variant
├── make_sounds.py           # Generate sound files
├── hand_landmarker.task     # MediaPipe hand model
├── select.wav
├── win.wav
├── lose.wav
├── tie.wav
├── intro.mp3
└── stats.json               # Auto-generated on first run


## 🎮 Controls

| Action | Control |
|---|---|
| Select move | Click a button |
| Next round | Click **Next Round** |
| New match | Click **New Match** |
| Back to menu | Click **Back** |

---

## 📷 Camera / Gesture Mode (Optional)

If `opencv-python` and `mediapipe` are installed, the **Multiplayer** mode supports real-time hand gesture detection via webcam. Both players show their hand to the camera simultaneously.

Gestures supported: ✊ Rock · 🖐 Paper · ✌️ Scissors

---

## 🤖 AI System

The AI uses a **Markov chain transition model** — it tracks which move you played after each previous move and predicts your next one, then plays the counter. The more you play, the smarter it gets!

---

## 🏆 XP & Leveling

| Outcome | XP Earned |
|---|---|
| Win | +20 XP |
| Loss | +5 XP |
| Level Up | Every 100 XP |

Stats are saved automatically to `stats.json`.

---

## 🛠️ Built With

- [Python](https://www.python.org/)
- [Pygame-CE](https://pyga.me/)
- [MediaPipe](https://mediapipe.dev/) *(optional)*
- [OpenCV](https://opencv.org/) *(optional)*

---

## 👥 Team

| Name | Role |
|---|---|
| **Varad** | Developer |
| **Pratham Wasu** | Developer |
| **Dnyanesh** | Report |
| **Kamana** | Report |

Feel free to fork, star ⭐, and contribute!
