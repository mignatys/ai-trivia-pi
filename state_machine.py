"""
state_machine.py
----------------
The core game engine that manages the game's state, flow, and logic.
It transitions between states based on user input (button presses) and
internal timers.
"""

import json
import os
import time
from logger import log
from config import *
from audio import audio
from tts_manager import tts
from llm_evaluator import llm
from stt_manager import stt

class StateMachine:
    """
    Manages the trivia game's state and orchestrates the overall game flow.
    """
    def __init__(self):
        self.current_state = None
        self.game_data = None
        self.current_question_index = 0
        self.incomplete_answer_count = 0
        self.topic = ""
        self.difficulty = ""
        self._game_ready = False

        self.state_handlers = {
            STATE_WAITING_TOPIC: self._on_waiting_topic,
            STATE_WAITING_DIFFICULTY: self._on_waiting_difficulty,
            STATE_QUESTION_ACTIVE: self._on_question_active,
            STATE_ANSWER_PENDING: self._on_answer_pending,
            STATE_HINT_ACTIVE: self._on_hint_active,
            STATE_GAME_END: self._on_game_end,
            STATE_PAUSED: self._on_paused,
        }
        log.info("State machine initialized.")

    def set_state(self, new_state):
        if new_state not in self.state_handlers:
            log.error(f"Attempted to transition to an unknown state: {new_state}")
            return

        log.info(f"Transitioning from {self.current_state} to {new_state}")
        self.current_state = new_state
        
        handler = self.state_handlers[new_state]
        handler()

    def start(self):
        self.set_state(STATE_WAITING_TOPIC)

    def handle_short_press(self):
        log.debug(f"Short press received in state: {self.current_state}")
        
        if self.current_state == STATE_WAITING_TOPIC:
            if self._game_ready:
                self.set_state(STATE_QUESTION_ACTIVE)
            else:
                # Listen for the topic
                recognized_topic = stt.recognize_speech(hint_text="Speak the topic...")
                if recognized_topic:
                    self.topic = recognized_topic
                    log.info(f"Topic selected: {self.topic}")
                    self.set_state(STATE_WAITING_DIFFICULTY)
                else:
                    log.warn("No topic was recognized. Please try again.")
                    # TODO: Play a "please try again" sound
        
        elif self.current_state == STATE_WAITING_DIFFICULTY:
            # Listen for the difficulty
            recognized_difficulty = stt.recognize_speech(hint_text="Speak the difficulty (Easy, Medium, or Hard)...")
            if recognized_difficulty:
                # Normalize the recognized text
                self.difficulty = recognized_difficulty.strip().capitalize()
                log.info(f"Difficulty selected: {self.difficulty}")
                # Use the recognized values to prepare the game
                self._prepare_game("ru", self.difficulty, self.topic)
            else:
                log.warn("No difficulty was recognized. Please try again.")
                # TODO: Play a "please try again" sound

        elif self.current_state == STATE_QUESTION_ACTIVE:
            self.set_state(STATE_ANSWER_PENDING)

        elif self.current_state == STATE_ANSWER_PENDING:
            self._handle_answer_attempt()

    def handle_long_press(self):
        log.debug(f"Long press received in state: {self.current_state}")

    def _prepare_game(self, language, difficulty, topic):
        log.info(f"Starting new game with topic: '{topic}', difficulty: '{difficulty}'")

        # For testing, we can still use the local file if it exists
        if os.path.exists(GAME_QUESTIONS_FILE):
            log.info(f"Found existing game file. Using local data and ignoring selected topic/difficulty.")
        else:
            log.info(f"No local game file found. Generating new questions from LLM...")
            if not llm.get_questions(language, difficulty, topic):
                log.error("Failed to generate questions. Aborting game setup.")
                self.set_state(STATE_WAITING_TOPIC)
                return
        
        try:
            with open(GAME_QUESTIONS_FILE, 'r') as f:
                self.game_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log.error(f"Failed to load game data: {e}")
            self.set_state(STATE_WAITING_TOPIC)
            return

        audio.play_bg(BACKGROUND_MUSIC, volume=0.3)
        audio.play(TTS_GENERATING_GAME)
        
        tts.generate_initial_audio(self.game_data)

        audio.stop_bg()
        audio.play(TTS_GAME_READY)
        
        tts.generate_remaining_audio()

        self._game_ready = True
        log.info("Game is ready. Press the button to start the first question.")
        self.set_state(STATE_WAITING_TOPIC)

    def _on_waiting_topic(self):
        if self._game_ready:
            log.info("State: WAITING_TOPIC (Game Ready). Press button to start.")
        else:
            log.info("State: WAITING_TOPIC. Press button to speak the topic.")

    def _on_waiting_difficulty(self):
        log.info("State: WAITING_DIFFICULTY. Press button to speak the difficulty.")

    def _on_question_active(self):
        self.incomplete_answer_count = 0
        log.info(f"State: QUESTION_ACTIVE (Question {self.current_question_index + 1})")
        
        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        
        audio.play(tts.get_host_intro_audio(question_id) or TTS_HOST_INTRO_ERROR)
        audio.play(tts.get_question_audio(question_id) or TTS_QUESTION_ERROR)
        
        log.info("Press button to simulate timer ending and enter answer phase.")

    def _on_answer_pending(self):
        log.info("State: ANSWER_PENDING. Waiting for a team to buzz in.")
        log.info("Press button to speak your answer.")

    def _handle_answer_attempt(self):
        """Captures a spoken answer and evaluates it."""
        current_round = self.game_data["rounds"][self.current_question_index]
        question = current_round["question"]
        correct_answer = current_round["answer"]
        team_names = self.game_data["team_names"]

        user_answer = stt.recognize_speech(timeout_sec=ANSWER_WINDOW)

        if user_answer is None:
            log.info("No answer was provided.")
            audio.play(TTS_WRONG_ANSWER)
            self._next_question()
            return

        result = llm.evaluate_answer(question, correct_answer, user_answer, team_names)

        if not result:
            log.error("Answer evaluation failed.")
            self._next_question()
            return

        if result["answer"] == "CORRECT":
            log.info("Answer is CORRECT!")
            audio.play(TTS_CORRECT_ANSWER)
            self._next_question()
        elif result["answer"] == "INCORRECT":
            log.info("Answer is INCORRECT.")
            audio.play(TTS_WRONG_ANSWER)
            self._next_question()
        elif result["answer"] == "INCOMPLETE":
            self.incomplete_answer_count += 1
            if self.incomplete_answer_count >= 2:
                log.info("Answer is INCOMPLETE for the second time. Counting as incorrect.")
                audio.play(TTS_WRONG_ANSWER)
                self._next_question()
            else:
                log.info("Answer is INCOMPLETE. Asking team to clarify.")
                audio.play(TTS_INCOMPLETE_ANSWER)
                self.set_state(STATE_ANSWER_PENDING)

    def _next_question(self):
        """Advances the game to the next question or ends it."""
        self.current_question_index += 1
        if self.current_question_index < len(self.game_data["rounds"]):
            self.set_state(STATE_QUESTION_ACTIVE)
        else:
            self.set_state(STATE_GAME_END)

    def _on_hint_active(self):
        log.info("State: HINT_ACTIVE.")

    def _on_game_end(self):
        log.info("State: GAME_END. The game is over.")

    def _on_paused(self):
        log.info("State: PAUSED.")

game = StateMachine()
