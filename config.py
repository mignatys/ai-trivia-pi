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
# DEVELOPMENT FLAGS
# -----------------------------------------
# Set to False to skip regeneration of existing files for faster testing
OVERWRITE_EXISTING_QUESTIONS = False
OVERWRITE_EXISTING_TTS = False
# Force synchronous TTS generation for testing
FORCE_SYNC_TTS_GENERATION = True

# -----------------------------------------
# PATHS (relative to project root)
# -----------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SOUNDS_DIR = os.path.join(PROJECT_ROOT, "sounds")
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
GENERATING_MUSIC = os.path.join(SOUNDS_DIR, "generating_bg.wav")

# TTS output folder
TTS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tts_cache")

# TTS pre-generated voice over paths
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
TTS_BONUS_QUESTION = os.path.join(TTS_DEFAULT_DIR, "bonus_question.wav")
TTS_GAME_DRAW = os.path.join(TTS_DEFAULT_DIR, "game_draw.wav")
TTS_NEW_GAME = os.path.join(TTS_DEFAULT_DIR, "new_game.wav")
TTS_INTRO = os.path.join(TTS_DEFAULT_DIR, "voice_intro.wav")
TTS_GENERATING_GAME = os.path.join(TTS_DEFAULT_DIR, "generating_game.wav")
TTS_GAME_READY = os.path.join(TTS_DEFAULT_DIR, "game_ready.wav")
TTS_WRONG_TEAM = os.path.join(TTS_DEFAULT_DIR, "wrong_team.wav")
TTS_TOPIC = os.path.join(TTS_DEFAULT_DIR, "topic.wav")
TTS_DIFICULTY = os.path.join(TTS_DEFAULT_DIR, "difficulty.wav")

# Ensure directories exist
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)
os.makedirs(TTS_DEFAULT_DIR, exist_ok=True)


# -----------------------------------------
# DYNAMIC TEXT TEMPLATES
# -----------------------------------------

SCORE_ANNOUNCEMENT_TEMPLATES = {
    "INTERMEDIATE": "Друзья, мы сыграли половину игры. Текущие результаты следующие: команда {team_one} заработала {score_one} очков, а команда {team_two} заработала {score_two} очков.",
    "FINALE": "Друзья, мы подошли к финальному вопросу нашей викторины. Команда {team_one} заработала {score_one} очков, а команда {team_two} заработала {score_two} очков. Готовы к финальному вопросу?",
    "GAME_OVER": "Это был последний вопрос нашей игры. Команда {winner} выиграла со счётом {winner_score} очков, а команда {loser} заработала {loser_score} очков.",
    "WRONG_TEAM": "Такой команды у нас нет. Назовите свою команду, а потом дайте ответ на вопрос. Сегодня играют {team_one} и {team_two}."
}

# -----------------------------------------
# DEFAULT VOICE LINES (for generation script)
# -----------------------------------------

DEFAULT_VOICE_LINES = {
    TTS_TOPIC: "Нажмите красную кнопку и назовите тему квиза",
    TTS_DIFICULTY: "Нажмите кнопку и выберите уровень сложности, легко, средне, или сложно",
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
    TTS_BONUS_QUESTION: "По результатам десяти вопросов у нас ничья. Сейчас разыграем финальный бонусный вопрос,",
    TTS_GAME_DRAW: "Это была отчаянная борьба, и по результатам игры, победила дружба!",
    TTS_NEW_GAME: "Чтобы начать новую игру, нажмите кнопку.",
    TTS_GENERATING_GAME: "Превосходно! Тема выбрана. Сейчас я погуглю вам вопросы, погуляю с собакой, и мы сразу начнем. А пока — сделайте пару отжиманий извилинами! Они нам будут нужны в тонусе.",
    TTS_GAME_READY: "Ну что, команды, я придумал вам интересные вопросы! Если вы готовы — жмите кнопку, и мы начинаем!"
}

# -----------------------------------------
# API KEYS, PERFORMANCE, GPIO, TIMERS, STATES, WEB
# (Sections below are unchanged)
# -----------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TTS_WORKER_COUNT = 2
TTS_SAMPLE_RATE = 24000
INITIAL_QUESTION_COUNT = 3
BUTTON_PIN = 17
QUESTION_TIME = 60
ANSWER_WINDOW = 15
HINT_COUNT = 3
LONG_PRESS_THRESHOLD = 1
DOUBLE_PRESS_WINDOW = 0.35
STATE_WAITING_TOPIC = "WAITING_TOPIC"
STATE_WAITING_TOPIC_INPUT = "WAITING_TOPIC_INPUT"
STATE_WAITING_DIFFICULTY = "WAITING_DIFFICULTY"
STATE_WAITING_DIFFICULTY_INPUT = "WAITING_DIFFICULTY_INPUT"
STATE_READY_TO_START = "READY_TO_START"
STATE_QUESTION_ACTIVE = "QUESTION_ACTIVE"
STATE_ANSWERING = "ANSWERING"
STATE_WAITING_FOR_ANSWER = "WAITING_FOR_ANSWER"
STATE_HINT_ACTIVE = "HINT_ACTIVE"
STATE_ROUND_OVER = "ROUND_OVER"
STATE_GAME_END = "GAME_END"
STATE_GAME_OVER_WAITING_RESTART = "GAME_OVER_WAITING_RESTART"
STATE_PAUSED = "PAUSED"
WEB_PORT = 8080
