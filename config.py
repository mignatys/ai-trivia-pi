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
OVERWRITE_EXISTING_QUESTIONS = True
OVERWRITE_EXISTING_TTS = True
# Force synchronous TTS generation for testing
FORCE_SYNC_TTS_GENERATION = False
# Set to False to disable automatic app start for development
AUTO_START_APP = True
# Set to True to automatically start the next question without a button press
DISABLE_NEXT_QUESTION_BUTTON = True

# -----------------------------------------
# LOGGING
# -----------------------------------------
# Set to "DEBUG", "INFO", "WARN", "ERROR" to control log verbosity
LOG_LEVEL = "DEBUG"

# -----------------------------------------
# GCP CONFIGURATION
# -----------------------------------------
GCP_PROJECT_ID = "gen-lang-client-0573652137"
GCP_LOCATION = "global"

# -----------------------------------------
# PATHS (relative to project root)
# -----------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SOUNDS_DIR = os.path.join(PROJECT_ROOT, "sounds")
QUESTIONS_DIR = os.path.join(PROJECT_ROOT, "questions")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts") # Fixed: Changed PROMPT_ROOT to PROJECT_ROOT

# Game data and prompts
GAME_QUESTIONS_FILE = os.path.join(QUESTIONS_DIR, "game_questions.json")
QUESTION_PROMPT_FILE = os.path.join(PROMPTS_DIR, "question")
ANSWER_PROMPT_FILE = os.path.join(PROMPTS_DIR, "answer")

# Pre-generated sound effects
SOUND_CORRECT = os.path.join(SOUNDS_DIR, "correct.wav")
SOUND_WRONG = os.path.join(SOUNDS_DIR, "wrong.wav")
SOUND_BUTTON_PRESS = os.path.join(SOUNDS_DIR, "button_press.wav")
SOUND_TIME_WARNING = os.path.join(SOUNDS_DIR, "time_warning.wav")
SOUND_SUSPENSE_TIMER = os.path.join(SOUNDS_DIR, "suspense_timer.wav")
SOUND_WINNER_ANNOUNCEMENT = os.path.join(SOUNDS_DIR, "winner_announcement.wav")

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
TTS_NO_TEAM = os.path.join(TTS_OUTPUT_DIR, "no_team.wav")
TTS_TOPIC = os.path.join(TTS_DEFAULT_DIR, "topic.wav")
TTS_DIFICULTY = os.path.join(TTS_DEFAULT_DIR, "difficulty.wav")
TTS_FIRST_QUESTION = os.path.join(TTS_DEFAULT_DIR, "first_question.wav")
TTS_NEXT_QUESTION = os.path.join(TTS_DEFAULT_DIR, "next_question.wav")
TTS_REMEMBER_NAMES = os.path.join(TTS_DEFAULT_DIR, "remember_names.wav")

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
    "NO_TEAM": "Такой команды у нас нет. Назовите свою команду, а потом дайте ответ на вопрос. Сегодня играют {team_one} и {team_two}."
}

# -----------------------------------------
# DEFAULT VOICE LINES (for generation script)
# -----------------------------------------

DEFAULT_VOICE_LINES = {
    TTS_TOPIC: "Нажмите красную кнопку и назовите тему квиза",
    TTS_DIFICULTY: "Нажмите кнопку и выберите уровень сложности от одного до пяти, например три.",
    TTS_QUESTION_ERROR: "Хм, кажется я профукал следующий вопрос, придется пропустить",
    TTS_HINT_ERROR: "Забыл подсказку, ладно, пропустим",
    TTS_HOST_INTRO_ERROR: "Хотел остроумно пошутить перед вопросом, но забыл что хотел сказать, переходим к вопросу",
    TTS_CORRECT_ANSWER: "Это правельный ответ!",
    TTS_WRONG_ANSWER: "Ответ неверный",
    TTS_INCOMPLETE_ANSWER: "Ответ неполный, уточните ваш ответ и попробуйте еще раз",
    TTS_NO_ANSWER: "К сожалению ни одна из команд не смогла дать нам верный ответ, а теперь внимание верный ответ",
    TTS_HINT_1: "Первая подсказка",
    TTS_HINT_2: "Вторая подсказка",
    TTS_HINT_3: "Третья подсказка",
    TTS_WRONG_TEAM_ANSWERING: "Не так быстро, вы уже дали не верный ответ, сейчас отвечает команда соперников",
    TTS_BONUS_QUESTION: "По результатам десяти вопросов у нас ничья. Сейчас разыграем финальный бонусный вопрос,",
    TTS_GAME_DRAW: "Это была отчаянная борьба, и по результатам игры, победила дружба!",
    TTS_NEW_GAME: "Чтобы начать новую игру, нажмите кнопку.",
    TTS_GENERATING_GAME: "Превосходно! Тема выбрана. Сейчас я погуглю вам вопросы, погуляю с собакой, и мы сразу начнем. А пока — сделайте пару отжиманий извилинами! Они нам будут нужны в тонусе.",
    TTS_GAME_READY: "Ну что, команды, я придумал вам интересные вопросы! Если вы готовы — жмите кнопку, и мы начинаем!",
    TTS_FIRST_QUESTION: "А теперь внимание команды, первый вопрос!",
    TTS_NEXT_QUESTION: "Нажмите кнопку чтобы услышать следующий вопрос!",
    TTS_REMEMBER_NAMES: "Друзья, определитесь кто играет за какую команду. Если нужно, запишите названия, и нажмите кнопку, чтобы продолжить!",
    TTS_INTRO: "Привет! Меня зовут Михаил, и я рад приветствовать вас на нашем квизе! Сегодня нас ждут интересные вопросы, шутки и, конечно же, море веселья. А сейчас кратко о правилах. В игре 10 раундов, на ответ дается 1 минута. За 5 секунд до конца будет звуковой сигнал. Игроки должны успеть нажать на красную кнопку до окончания минуты, чтобы дать ответ на вопрос. Теперь важно: после нажатия кнопки нужно сказать название команды и ответ. Если ответ неверный, таймер продолжается, и право ответа переходит команде соперника. Если правильного ответа нет, будет три подсказки. После окончания раунда снова нажмите красную кнопку, чтобы услышать следующий вопрос. Долгое нажатие позволяет ввести голосовую команду, например, 'помощь'. Ну вот и всё, пристегните ваши ремни и нажмите кнопку, чтобы начать игру!"
}

# -----------------------------------------
# AUDIO ASSETS
# -----------------------------------------

REQUIRED_AUDIO_ASSETS = [
    SOUND_CORRECT, SOUND_WRONG, SOUND_BUTTON_PRESS, SOUND_WINNER_ANNOUNCEMENT,
    SOUND_TIME_WARNING, SOUND_SUSPENSE_TIMER, INTRO_MUSIC, BACKGROUND_MUSIC, GENERATING_MUSIC,
    TTS_QUESTION_ERROR, TTS_HINT_ERROR, TTS_HOST_INTRO_ERROR, TTS_CORRECT_ANSWER,
    TTS_WRONG_ANSWER, TTS_INCOMPLETE_ANSWER, TTS_NO_ANSWER, TTS_HINT_1, TTS_HINT_2,
    TTS_HINT_3, TTS_WRONG_TEAM_ANSWERING, TTS_BONUS_QUESTION, TTS_GAME_DRAW,
    TTS_NEW_GAME, TTS_INTRO, TTS_GENERATING_GAME, TTS_GAME_READY,
    TTS_TOPIC, TTS_DIFICULTY, TTS_FIRST_QUESTION, TTS_NEXT_QUESTION, TTS_REMEMBER_NAMES
]

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
STATE_WAITING_DIFFICULTY = "WAITING_DIFFICULTY"
STATE_READY_TO_START = "READY_TO_START"
STATE_WAITING_FOR_FIRST_QUESTION = "WAITING_FOR_FIRST_QUESTION"
STATE_QUESTION_ACTIVE = "QUESTION_ACTIVE"
STATE_ANSWERING = "ANSWERING"
STATE_WAITING_FOR_ANSWER = "WAITING_FOR_ANSWER"
STATE_HINT_ACTIVE = "HINT_ACTIVE"
STATE_ROUND_OVER = "ROUND_OVER"
STATE_GAME_END = "GAME_END"
STATE_GAME_OVER_WAITING_RESTART = "GAME_OVER_WAITING_RESTART"
STATE_PAUSED = "PAUSED"
WEB_PORT = 8080
