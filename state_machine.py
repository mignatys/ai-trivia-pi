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
from utils import Timer

class StateMachine:
    """
    Manages the trivia game's state and orchestrates the overall game flow.
    """
    def __init__(self):
        self.reset_game()

        self.state_handlers = {
            STATE_WAITING_TOPIC: self._on_waiting_topic,
            STATE_WAITING_DIFFICULTY: self._on_waiting_difficulty,
            STATE_QUESTION_ACTIVE: self._on_question_active,
            STATE_ANSWERING: self._on_answering,
            STATE_HINT_ACTIVE: self._on_hint_active,
            STATE_ROUND_OVER: self._on_round_over,
            STATE_GAME_END: self._on_game_end,
            STATE_GAME_OVER_WAITING_RESTART: self._on_game_over_waiting_restart,
            STATE_PAUSED: self._on_paused,
        }
        log.info("State machine initialized.")

    def reset_game(self):
        """Resets all game variables to their initial state for a new game."""
        log.info("Resetting game state for a new game.")
        self.current_state = None
        self._game_ready = False
        self.game_data = None
        self.topic = ""
        self.difficulty = ""
        self.current_question_index = 0
        self.current_hint_index = 0
        self.team_priority = 0
        self.teams_answered = [False, False]
        self.wrong_team_attempts = 0
        self.scores = [0, 0]
        if hasattr(self, 'game_timer') and self.game_timer:
            self.game_timer.cancel()
        self.game_timer = None
        self.time_remaining_in_round = 0
        self.timer_start_time = 0

    def set_state(self, new_state):
        if self.current_state == new_state: return
        if self.game_timer and new_state != STATE_PAUSED:
            self.game_timer.cancel()
            self.game_timer = None
        log.info(f"Transitioning from {self.current_state} to {new_state}")
        self.current_state = new_state
        handler = self.state_handlers.get(new_state)
        if handler: handler()
        else: log.error(f"No handler found for state: {new_state}")

    def start(self):
        self.set_state(STATE_WAITING_TOPIC)

    def handle_short_press(self):
        log.debug(f"Short press received in state: {self.current_state}")
        if self.current_state == STATE_WAITING_TOPIC:
            if self._game_ready: self._start_new_round()
            else: self._select_topic()
        elif self.current_state == STATE_WAITING_DIFFICULTY: self._select_difficulty()
        elif self.current_state in [STATE_QUESTION_ACTIVE, STATE_HINT_ACTIVE]:
            self._pause_timer()
            self.set_state(STATE_ANSWERING)
        elif self.current_state == STATE_ROUND_OVER: self._start_new_round()
        elif self.current_state == STATE_GAME_OVER_WAITING_RESTART:
            self.reset_game()
            self.set_state(STATE_WAITING_TOPIC)

    def handle_long_press(self):
        log.debug(f"Long press received in state: {self.current_state}")

    def _start_or_resume_timer(self):
        if self.time_remaining_in_round <= 0:
            self._on_timer_expired()
            return
        self.timer_start_time = time.time()
        self.game_timer = Timer(self.time_remaining_in_round, self._on_timer_expired)
        self.game_timer.start()

    def _pause_timer(self):
        if self.game_timer and self.game_timer.is_running():
            self.game_timer.cancel()
            elapsed_time = time.time() - self.timer_start_time
            self.time_remaining_in_round -= elapsed_time
            log.debug(f"Timer paused. Time remaining: {self.time_remaining_in_round:.2f}s")

    def _on_timer_expired(self):
        log.info("Timer expired.")
        self.set_state(STATE_HINT_ACTIVE)

    def _select_topic(self):
        recognized_topic = stt.recognize_speech(hint_text="Speak the topic...")
        if recognized_topic:
            self.topic = recognized_topic
            self.set_state(STATE_WAITING_DIFFICULTY)
        else: log.warn("No topic was recognized. Please try again.")

    def _select_difficulty(self):
        recognized_difficulty = stt.recognize_speech(hint_text="Speak the difficulty...")
        if recognized_difficulty:
            self.difficulty = recognized_difficulty.strip().capitalize()
            self._prepare_game("ru", self.difficulty, self.topic)
        else: log.warn("No difficulty was recognized. Please try again.")

    def _prepare_game(self, language, difficulty, topic):
        log.info(f"Starting new game with topic: '{topic}', difficulty: '{difficulty}'")
        if os.path.exists(GAME_QUESTIONS_FILE):
            log.info(f"Found existing game file. Using local data.")
        else:
            if not llm.get_questions(language, difficulty, topic):
                self.set_state(STATE_WAITING_TOPIC)
                return
        try:
            with open(GAME_QUESTIONS_FILE, 'r') as f: self.game_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.set_state(STATE_WAITING_TOPIC)
            return
        audio.play_bg(BACKGROUND_MUSIC, volume=0.3)
        audio.play(DEFAULT_VOICE_LINES[TTS_GENERATING_GAME])
        tts.generate_initial_audio(self.game_data)
        audio.stop_bg()
        audio.play(DEFAULT_VOICE_LINES[TTS_GAME_READY])
        tts.generate_remaining_audio()
        self._game_ready = True
        self.set_state(STATE_WAITING_TOPIC)

    def _start_new_round(self):
        # Check for endgame conditions
        if self.current_question_index == 10 and self.scores[0] != self.scores[1]:
            self.set_state(STATE_GAME_END)
            return
        if self.current_question_index >= 12:
            self.set_state(STATE_GAME_END)
            return

        self.current_hint_index = 0
        self.teams_answered = [False, False]
        self.wrong_team_attempts = 0
        self.team_priority = self.current_question_index % 2
        self.time_remaining_in_round = QUESTION_TIME
        self.set_state(STATE_QUESTION_ACTIVE)

    def _on_question_active(self):
        log.info(f"State: QUESTION_ACTIVE (Question {self.current_question_index + 1})")
        if self.current_question_index == 10: # Bonus question
            audio.play(DEFAULT_VOICE_LINES[TTS_BONUS_QUESTION])

        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        host_intro = tts.get_host_intro_audio(question_id)
        question_audio = tts.get_question_audio(question_id)

        if not host_intro or not question_audio:
            log.warn("Missing audio for question, skipping.")
            self.current_question_index += 1
            self._start_new_round()
            return

        audio.play(host_intro)
        audio.play(question_audio)
        self._start_or_resume_timer()

    def _on_answering(self):
        log.info("State: ANSWERING")
        user_answer = stt.recognize_speech(timeout_sec=ANSWER_WINDOW)
        if not user_answer:
            self._start_or_resume_timer()
            self.set_state(STATE_QUESTION_ACTIVE)
            return

        result = llm.evaluate_answer(
            question=self.game_data["rounds"][self.current_question_index]["question"],
            correct_answer=self.game_data["rounds"][self.current_question_index]["answer"],
            user_answer=user_answer,
            team_names=self.game_data["team_names"]
        )
        if not result:
            self._start_or_resume_timer()
            self.set_state(STATE_QUESTION_ACTIVE)
            return

        try:
            answering_team_index = self.game_data["team_names"].index(result["team_name"])
        except ValueError:
            self._start_or_resume_timer()
            self.set_state(STATE_QUESTION_ACTIVE)
            return

        if answering_team_index != self.team_priority:
            self.wrong_team_attempts += 1
            if self.wrong_team_attempts >= 2:
                audio.play(DEFAULT_VOICE_LINES[TTS_NO_ANSWER])
                self._reveal_answer_and_end_round()
            else:
                audio.play(DEFAULT_VOICE_LINES[TTS_WRONG_TEAM_ANSWERING])
                self._start_or_resume_timer()
                self.set_state(STATE_QUESTION_ACTIVE)
            return

        self.teams_answered[answering_team_index] = True
        
        if result["answer"] == "CORRECT":
            self.scores[answering_team_index] += 1
            self._handle_correct_answer()
        else: # INCORRECT or INCOMPLETE
            audio.play(SOUND_WRONG)
            audio.play(DEFAULT_VOICE_LINES[TTS_WRONG_ANSWER])
            self.team_priority = 1 - self.team_priority
            if all(self.teams_answered):
                self._reveal_answer_and_end_round()
            else:
                self._start_or_resume_timer()
                self.set_state(STATE_QUESTION_ACTIVE)

    def _handle_correct_answer(self):
        """Handles the sequence after a correct answer is given."""
        # Start generating score announcement in the background
        score_audio_path = self._generate_score_announcement_async()
        
        audio.play(SOUND_CORRECT)
        audio.play(DEFAULT_VOICE_LINES[TTS_CORRECT_ANSWER])
        
        self._play_fun_fact()
        
        # Wait for and play the score announcement if it's ready
        if score_audio_path:
            while not os.path.exists(score_audio_path):
                time.sleep(0.1)
            audio.play(score_audio_path)
            
        self.set_state(STATE_ROUND_OVER)

    def _generate_score_announcement_async(self):
        """Generates the appropriate score announcement based on the round."""
        round_num = self.current_question_index + 1
        template_key = None
        if round_num == 5: template_key = TTS_INTERMEDIATE_SCORE
        elif round_num == 9: template_key = TTS_FINALE_SCORE
        elif round_num == 10: template_key = TTS_GAME_SCORE
        
        if not template_key: return None

        template = DEFAULT_VOICE_LINES[template_key]
        
        # Determine winner/loser for the final score
        if round_num == 10:
            winner_index = 0 if self.scores[0] > self.scores[1] else 1
            loser_index = 1 - winner_index
            text = template.format(
                winner=self.game_data['team_names'][winner_index],
                winner_score=self.scores[winner_index],
                loser=self.game_data['team_names'][loser_index],
                loser_score=self.scores[loser_index]
            )
        else:
            text = template.format(
                team_one=self.game_data['team_names'][0],
                score_one=self.scores[0],
                team_two=self.game_data['team_names'][1],
                score_two=self.scores[1]
            )
        
        filename = f"score_announcement_round_{round_num}.wav"
        return tts.generate_sentence_async(text, filename)

    def _on_hint_active(self):
        if self.current_hint_index >= HINT_COUNT:
            self._reveal_answer_and_end_round()
            return
        log.info(f"State: HINT_ACTIVE (Hint {self.current_hint_index + 1})")
        self.time_remaining_in_round = QUESTION_TIME
        hint_key = f"TTS_HINT_{self.current_hint_index + 1}"
        audio.play(DEFAULT_VOICE_LINES.get(hint_key))
        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        hint_audio = tts.get_hint_audio(question_id, self.current_hint_index + 1)
        audio.play(hint_audio or DEFAULT_VOICE_LINES[TTS_HINT_ERROR])
        self.current_hint_index += 1
        self._start_or_resume_timer()

    def _reveal_answer_and_end_round(self):
        audio.play(DEFAULT_VOICE_LINES[TTS_NO_ANSWER])
        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        answer_audio = tts.get_answer_audio(question_id)
        audio.play(answer_audio)
        self._play_fun_fact()
        self.set_state(STATE_ROUND_OVER)

    def _play_fun_fact(self):
        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        fun_fact_audio = tts.get_fun_fact_audio(question_id)
        if fun_fact_audio: audio.play(fun_fact_audio)

    def _on_round_over(self):
        log.info("State: ROUND_OVER. Press button for next question.")
        self.current_question_index += 1

    def _on_game_end(self):
        log.info("State: GAME_END. Final Scores:")
        log.info(f"{self.game_data['team_names'][0]}: {self.scores[0]}")
        log.info(f"{self.game_data['team_names'][1]}: {self.scores[1]}")
        if self.scores[0] == self.scores[1]:
            audio.play(DEFAULT_VOICE_LINES[TTS_GAME_DRAW])
        else:
            # The final score announcement was already played after round 10
            pass
        audio.play(DEFAULT_VOICE_LINES[TTS_NEW_GAME])
        self.set_state(STATE_GAME_OVER_WAITING_RESTART)

    def _on_game_over_waiting_restart(self):
        log.info("State: GAME_OVER_WAITING_RESTART. Press button to start a new game.")

    def _on_paused(self):
        log.info("State: PAUSED.")

    def _on_waiting_topic(self):
        if self._game_ready: log.info("State: WAITING_TOPIC (Game Ready). Press button to start.")
        else: log.info("State: WAITING_TOPIC. Press button to speak the topic.")

    def _on_waiting_difficulty(self):
        log.info("State: WAITING_DIFFICULTY. Press button to speak the difficulty.")

game = StateMachine()
