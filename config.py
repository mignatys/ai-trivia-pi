"""
config.py
---------
Centralized configuration and constants for the Trivia Game.
All paths are relative to the project root.
"""

import os

# -----------------------------------------
# PATHS (relative to project root)
# -----------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SOUNDS_DIR = os.path.join(PROJECT_ROOT, "sounds")
TTS_MODELS_DIR = os.path.join(PROJECT_ROOT, "tty_models")
QUESTIONS_DIR = os.path.join(PROJECT_ROOT, "questions")

# Pre-generated sound effects
SOUND_CORRECT = os.path.join(SOUNDS_DIR, "correct.wav")
SOUND_WRONG = os.path.join(SOUNDS_DIR, "wrong.wav")
SOUND_TIMER_WARNING = os.path.join(SOUNDS_DIR, "warning.wav")
SOUND_TICK = os.path.join(SOUNDS_DIR, "tick.wav")

# Background music (boot only)
BACKGROUND_MUSIC = os.path.join(SOUNDS_DIR, "bgm_intro.wav")

# Piper TTS model
DEFAULT_TTS_MODEL = os.path.join(TTS_MODELS_DIR, "ru_RU-denis-medium.onnx")

# TTS output folder
TTS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tts_cache")

# Ensure directories exist
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


# -----------------------------------------
# GPIO PIN CONFIG
# -----------------------------------------

BUTTON_PIN = 17  # You can change later


# -----------------------------------------
# GAME TIMERS (seconds)
# -----------------------------------------

QUESTION_TIME = 60        # time for players to think
ANSWER_WINDOW = 15        # time to press button to answer
HINT_COUNT = 3

LONG_PRESS_THRESHOLD = 1      # seconds
DOUBLE_PRESS_WINDOW = 0.35    # if needed in future


# -----------------------------------------
# GAME STATE CONSTANTS
# -----------------------------------------

STATE_WAITING_TOPIC = "WAITING_TOPIC"
STATE_QUESTION_ACTIVE = "QUESTION_ACTIVE"
STATE_ANSWER_PENDING = "ANSWER_PENDING"
STATE_HINT_ACTIVE = "HINT_ACTIVE"
STATE_GAME_END = "GAME_END"
STATE_PAUSED = "PAUSED"


# -----------------------------------------
# WEB INTERFACE CONFIG
# -----------------------------------------

WEB_PORT = 8080
WEB_HOST = "0.0.0.0"

