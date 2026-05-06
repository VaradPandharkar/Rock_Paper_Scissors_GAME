import pygame
import time

pygame.init()
pygame.mixer.init()

try:
    sound = pygame.mixer.Sound("intro.mp3")
    print("Sound loaded successfully.")
except Exception as e:
    print(f"Error loading Sound: {e}")

try:
    pygame.mixer.music.load("intro.mp3")
    print("Music loaded successfully.")
except Exception as e:
    print(f"Error loading Music: {e}")

pygame.quit()
