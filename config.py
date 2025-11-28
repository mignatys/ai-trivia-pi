"""
config.py
---------
Centralized configuration and constants for the Trivia Game.
All paths are relative to the project root.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------------------
# PATHS (relative to project root)
# -----------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SOUNDS_DIR = os.path.join(PROJECT_ROOT, "sounds")
TTS_MODELS_DIR = os.path.join(PROJECT_ROOT, "tts_models")
QUESTIONS_DIR = os.path.join(PROJECT_ROOT, "questions")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")

# Game data and prompts
GAME_QUESTIONS_FILE = os.path.join(QUESTIONS_DIR, "game_questions.json")
QUESTION_PROMPT_FILE = os.path.join(PROMPTS_DIR, "question")
ANSWER_PROMPT_FILE = os.path.join(PROMPTS_DIR, "answer")

# Pre-generated sound effects
SOUND_CORRECT = os.path.join(SOUNDS_DIR, "correct.wav")
SOUND_WRONG = os.path.join(SOUNDS_DIR, "wrong.wav")
SOUND_TIMER_WARNING = os.path.join(SOUNDS_DIR, "warning.wav")
SOUND_TICK = os.path.join(SOUNDS_DIR, "tick.wav")

# Background music and main voiceovers
INTRO_MUSIC = os.path.join(SOUNDS_DIR, "grand_intro.wav")
BACKGROUND_MUSIC = os.path.join(SOUNDS_DIR, "intro_bg.wav")

# Piper TTS model
DEFAULT_TTS_MODEL = os.path.join(TTS_MODELS_DIR, "ru_RU-ruslan-medium.onnx")

# TTS output folder
TTS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tts_cache")

# TTS pre-generated voice over
TTS_DEFAULT_DIR = os.path.join(PROJECT_ROOT, "tts_default")
TTS_QUESTION_ERROR = os.path.join(TTS_DEFAULT_DIR, "question_error.wav")
TTS_HINT_ERROR = os.path.join(TTS_DEFAULT_DIR, "hint_error.wav")
TTS_HOST_INTRO_ERROR = os.path.join(TTS_DEFAULT_DIR, "host_intro_error.wav")
TTS_CORRECT_ANSWER = os.path.join(TTS_DEFAULT_DIR, "correct_answer.wav")
TTS_WRONG_ANSWER = os.path.join(TTS_DEFAULT_DIR, "wrong_answer.wav")
TTS_INCOMPLETE_ANSWER = os.path.join(TTS_DEFAULT_DIR, "incomplete_answer.wav")
TTS_NO_ANSWER = os.path.join(TTS_DEFAULT_DIR, "no_answer.wav")
TTS_HINT_1 = os.path.join(TTS_DEFAULT_DIR, "first_hint.wav")
TTS_HINT_2 = os.path.join(TTS_DEFAULT_DIR, "second_hint.wav")
TTS_HINT_3 = os.path.join(TTS_DEFAULT_DIR, "third_hint.wav")
TTS_WRONG_TEAM_ANSWERING = os.path.join(TTS_DEFAULT_DIR, "wrong_team_answering.wav")
TTS_INTERMEDIATE_SCORE = os.path.join(TTS_DEFAULT_DIR, "wrong_team_answering.wav")
TTS_FINALE_SCORE = os.path.join(TTS_DEFAULT_DIR, "final_score.wav")
TTS_GAME_SCORE = os.path.join(TTS_DEFAULT_DIR, "game_score.wav")
TTS_BONUS_QUESTION = os.path.join(TTS_DEFAULT_DIR, "bonus_question.wav")
TTS_GAME_DRAW = os.path.join(TTS_DEFAULT_DIR, "game_draw.wav")
TTS_NEW_GAME = os.path.join(TTS_DEFAULT_DIR, "new_game.wav")

TTS_INTRO = os.path.join(TTS_DEFAULT_DIR, "voice_intro.wav")
TTS_GENERATING_GAME = os.path.join(TTS_DEFAULT_DIR, "generating_game.wav")
TTS_GAME_READY = os.path.join(TTS_DEFAULT_DIR, "game_ready.wav")

# Ensure directories exist
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TTS_DEFAULT_DIR, exist_ok=True)


# -----------------------------------------
# API KEYS
# -----------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# -----------------------------------------
# PERFORMANCE CONFIG
# -----------------------------------------

TTS_WORKER_COUNT = 2 # Number of parallel threads for TTS generation
INITIAL_QUESTION_COUNT = 1 # Number of questions to generate before game starts


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
STATE_WAITING_DIFFICULTY = "WAITING_DIFFICULTY"
STATE_QUESTION_ACTIVE = "QUESTION_ACTIVE"
STATE_ANSWERING = "ANSWERING"
STATE_HINT_ACTIVE = "HINT_ACTIVE"
STATE_ROUND_OVER = "ROUND_OVER"
STATE_GAME_END = "GAME_END"
STATE_GAME_OVER_WAITING_RESTART = "GAME_OVER_WAITING_RESTART"
STATE_PAUSED = "PAUSED"


# -----------------------------------------
# WEB INTERFACE CONFIG
# -----------------------------------------

WEB_PORT = 8080
#WEB_HOST = "0.0.0.0"

# -----------------------------------------
# Defualt voice over text
# -----------------------------------------

DEFAULT_VOICE_LINES = {
    TTS_INTRO: "Привет! Меня зовут Михаил, и я рад приветствовать вас на нашем квизе..! Сегодня нас ждут интересные вопросы, острый ум и, конечно же, море веселья. Готовы проверить свои знания ??? Тогда давайте начнем!",
    TTS_QUESTION_ERROR: "Хм, кажется я профукал следующий вопрос, придется пропустить",
    TTS_HINT_ERROR: "Забыл подсказку, ладно, пропустим",
    TTS_HOST_INTRO_ERROR: "Хотел остроумно пошутить перед вопросом, но забыл что хотел сказать, переходим к вопросу",
    TTS_CORRECT_ANSWER: "Это правельный ответ!",
    TTS_WRONG_ANSWER: "К сожалению ответ неверный, продолжаем",
    TTS_INCOMPLETE_ANSWER: "Ответ неполный ",
    TTS_NO_ANSWER: "К сожалению ни одна из команд не смогла дать нам верный ответ, а теперь внимание верный ответ",
    TTS_HINT_1: "Первая подсказка",
    TTS_HINT_2: "Вторая подсказка",
    TTS_HINT_3: "Третья подсказка",
    TTS_WRONG_TEAM_ANSWERING: "Не так быстро, вы уже дали не верный ответ, сейчас отвечает команда соперников",
    TTS_FINALE_SCORE: "Друзья, мы подошли к фиральному вопросу нашей викторины, команда {team_one} заработала {score_one} очков, а команда {team_two} заработала {score_two} очков. Готовы к финальному вопросу?",
    TTS_GAME_SCORE: "Это был последний вопрос нашей игры, команда {winner} выиграла со счетом {winner_score} очков, а команда {loser} заработала {loser_score} очков.",
    TTS_INTERMEDIATE_SCORE: "Друзья, мы сиграли половину игры, текущие результаты следующие: команда {team_one} заработала {score_one} очков, а команда {team_two} заработала {score_two} очков",
    TTS_BONUS_QUESTION: "По результатам десяти вопросов у нас ничья. Сейчас разыграем финальный бонусный вопрос,",
    TTS_GAME_DRAW: "Это была отчаянная борьба, и по результатам игры, победила дружба!",
    TTS_NEW_GAME: "Чтобы начать новую игру, нажмите кнопку"
}
