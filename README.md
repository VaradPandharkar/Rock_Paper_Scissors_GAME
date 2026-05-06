⚔️ PIXEL RPS — Rock Paper Scissors
A retro pixel-art Rock · Paper · Scissors game built with Python and Pygame, featuring animated sprites, sound effects, an AI opponent, multiple game modes, and optional hand gesture recognition via camera.

🎮 Features

🪨 Classic Rock · Paper · Scissors gameplay
🎨 Retro pixel-art sprites with animated idle states
🤖 AI opponent with Markov chain prediction (learns your patterns!)
🔊 Sound effects for win / lose / tie / select
🎵 Intro music on launch
🧬 4 Game Modes:

Standard 1v1
Hardcore (harder AI + double damage)
Endless survival
Local multiplayer (sequential turns)


📷 Optional hand gesture recognition via webcam (MediaPipe)
🏆 XP & Level system with persistent stats saved to stats.json
✨ Particle effects, scanline overlay, CRT-style visuals


📁 Project Structure
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

🎮 Controls
ActionControlSelect moveClick a buttonNext roundClick Next RoundNew matchClick New MatchBack to menuClick Back

📷 Camera / Gesture Mode (Optional)
If opencv-python and mediapipe are installed, the Multiplayer mode supports real-time hand gesture detection via webcam. Both players show their hand to the camera simultaneously.
Gestures supported: ✊ Rock · 🖐 Paper · ✌️ Scissors

🤖 AI System
The AI uses a Markov chain transition model — it tracks which move you played after each previous move and predicts your next one, then plays the counter. The more you play, the smarter it gets!

🏆 XP & Leveling
OutcomeXP EarnedWin+20 XPLoss+5 XPLevel UpEvery 100 XP
Stats are saved automatically to stats.json.

🛠️ Built With
Python
Pygame-CE

👥 Team
Name                Role
Varad             Developer
Pratham           Developer
Dnyanesh           Report
Kamana             Report

Feel free to fork, star ⭐, and contribute!
