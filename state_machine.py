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
            STATE_WAITING_TOPIC_INPUT: self._on_waiting_topic_input,
            STATE_WAITING_DIFFICULTY: self._on_waiting_difficulty,
            STATE_WAITING_DIFFICULTY_INPUT: self._on_waiting_difficulty_input,
            STATE_READY_TO_START: self._on_ready_to_start,
            STATE_QUESTION_ACTIVE: self._on_question_active,
            STATE_ANSWERING: self._on_answering,
            STATE_WAITING_FOR_ANSWER: self._on_waiting_for_answer,
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
        self.teams_answered = [False, False]
        self.scores = [0, 0]
        if hasattr(self, 'game_timer') and self.game_timer:
            self.game_timer.cancel()
        self.game_timer = None
        self.time_remaining_in_round = 0
        self.timer_start_time = 0
        self.final_score_announced = False

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
        audio.stop_all_sounds() # Stop any currently playing audio
        
        if self.current_state == STATE_WAITING_TOPIC:
            audio.play(TTS_TOPIC)
            self.set_state(STATE_WAITING_TOPIC_INPUT)
        elif self.current_state == STATE_WAITING_TOPIC_INPUT:
            self._select_topic()
        elif self.current_state == STATE_WAITING_DIFFICULTY_INPUT:
            self._select_difficulty()
        elif self.current_state == STATE_READY_TO_START:
            audio.play(tts.get_greeting_audio())
            self._start_new_round()
        elif self.current_state in [STATE_QUESTION_ACTIVE, STATE_HINT_ACTIVE, STATE_WAITING_FOR_ANSWER]:
            self._pause_timer()
            self.set_state(STATE_ANSWERING)
        elif self.current_state == STATE_ROUND_OVER:
            self.current_question_index += 1
            audio.stop_bg() # Stop background music before question
            self._start_new_round()
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
        self._process_next_hint()

    def _select_topic(self):
        recognized_topic = stt.recognize_speech(hint_text="Speak the topic...")
        if recognized_topic:
            self.topic = recognized_topic
            self.set_state(STATE_WAITING_DIFFICULTY)
        else: 
            log.warn("No topic was recognized. Please try again.")
            self.set_state(STATE_WAITING_TOPIC_INPUT) # Go back to waiting for topic input

    def _select_difficulty(self):
        recognized_difficulty = stt.recognize_speech(hint_text="Speak the difficulty...")
        if recognized_difficulty:
            self.difficulty = recognized_difficulty.strip().capitalize()
            self._prepare_game("ru", self.difficulty, self.topic)
        else: 
            log.warn("No difficulty was recognized. Please try again.")
            self.set_state(STATE_WAITING_DIFFICULTY_INPUT) # Go back to waiting for difficulty input

    def _prepare_game(self, language, difficulty, topic):
        log.info(f"Starting new game with topic: '{topic}', difficulty: '{difficulty}'")
        
        # Check if questions file exists
        if not llm.get_questions(language, difficulty, topic):
            self.set_state(STATE_WAITING_TOPIC)
            return
        try:
            with open(GAME_QUESTIONS_FILE, 'r') as f: self.game_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.set_state(STATE_WAITING_TOPIC)
            return
        
        # Check if initial audio files exist
        initial_audio_files_exist = all(os.path.exists(f) for f in [
            tts.get_greeting_audio(),
            tts.get_host_intro_audio(self.game_data['rounds'][0]['id']),
            tts.get_question_audio(self.game_data['rounds'][0]['id'])
        ])

        if not initial_audio_files_exist:
            audio.play(TTS_GENERATING_GAME)
            audio.play_bg(GENERATING_MUSIC, volume=0.3)
            tts.generate_initial_audio(self.game_data)
            tts.generate_remaining_audio()
        
        audio.play(TTS_GAME_READY)
        self.set_state(STATE_READY_TO_START)

    def _start_new_round(self):
        if (self.current_question_index >= 10 and self.scores[0] != self.scores[1]) or self.current_question_index >= 12:
            self.set_state(STATE_GAME_END)
            return

        self.current_hint_index = 0
        self.teams_answered = [False, False]
        self.time_remaining_in_round = QUESTION_TIME
        self.set_state(STATE_QUESTION_ACTIVE)

    def _on_question_active(self):
        log.info(f"State: QUESTION_ACTIVE (Question {self.current_question_index + 1})")
        audio.stop_bg() # Stop background music for question
        if self.current_question_index == 10:
            audio.play(TTS_BONUS_QUESTION)

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

    def _on_waiting_for_answer(self):
        log.info("State: WAITING_FOR_ANSWER. Resuming timer without re-playing question.")
        self._start_or_resume_timer()

    def _on_answering(self):
        log.info("State: ANSWERING")
        user_answer = stt.recognize_speech(timeout_sec=ANSWER_WINDOW)
        if not user_answer:
            self.set_state(STATE_WAITING_FOR_ANSWER)
            return

        result = llm.evaluate_answer(
            question=self.game_data["rounds"][self.current_question_index]["question"],
            correct_answer=self.game_data["rounds"][self.current_question_index]["answer"],
            user_answer=user_answer,
            team_names=self.game_data["team_names"]
        )
        
        team_name = result.get("team_name") if result else None
        if not team_name:
            log.warn(f"LLM did not return a valid team name: {result}. Asking user to try again.")
            audio.play(TTS_WRONG_TEAM)
            self.set_state(STATE_WAITING_FOR_ANSWER)
            return

        try:
            answering_team_index = self.game_data["team_names"].index(team_name)
        except ValueError:
            log.warn(f"LLM returned a non-existent team name: {team_name}. Asking user to try again.")
            audio.play(TTS_WRONG_TEAM)
            self.set_state(STATE_WAITING_FOR_ANSWER)
            return

        if self.teams_answered[answering_team_index]:
            audio.play(TTS_WRONG_TEAM_ANSWERING)
            self.set_state(STATE_WAITING_FOR_ANSWER)
            return

        self.teams_answered[answering_team_index] = True
        
        if result.get("answer") == "CORRECT":
            self.scores[answering_team_index] += 1
            self._handle_correct_answer()
        else:
            audio.play(SOUND_WRONG)
            audio.play(TTS_WRONG_ANSWER)
            if all(self.teams_answered):
                self._reveal_answer_and_end_round()
            else:
                self.set_state(STATE_WAITING_FOR_ANSWER)

    def _handle_correct_answer(self):
        score_audio_path, score_thread = self._generate_score_announcement_async()
        audio.play(SOUND_CORRECT)
        audio.play(TTS_CORRECT_ANSWER)
        self._play_fun_fact()
        if score_thread:
            score_thread.join()
        if score_audio_path and os.path.exists(score_audio_path):
            audio.play(score_audio_path)
        self.set_state(STATE_ROUND_OVER)

    def _generate_score_announcement_async(self):
        round_num = self.current_question_index + 1
        template_key = None
        if round_num == 5: template_key = "INTERMEDIATE"
        elif round_num == 9: template_key = "FINALE"
        elif round_num >= 10: template_key = "GAME_OVER"
        
        if not template_key: return None, None

        template = SCORE_ANNOUNCEMENT_TEMPLATES[template_key]
        
        if template_key == "GAME_OVER":
            self.final_score_announced = True
            if self.scores[0] == self.scores[1]: return None, None
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
        path, thread = tts.generate_sentence_async(text, filename)
        return path, thread

    def _on_hint_active(self):
        pass

    def _process_next_hint(self):
        if self.current_hint_index >= HINT_COUNT:
            self._reveal_answer_and_end_round()
            return

        log.info(f"Processing Hint {self.current_hint_index + 1}")
        self.teams_answered = [False, False] # Reset answering priority after a hint
        self.set_state(STATE_HINT_ACTIVE)
        self.time_remaining_in_round = QUESTION_TIME
        
        hint_audio_key = f"TTS_HINT_{self.current_hint_index + 1}"
        audio.play(globals().get(hint_audio_key))

        question_id = self.game_data["rounds"][self.current_question_index]["id"]
        hint_audio = tts.get_hint_audio(question_id, self.current_hint_index + 1)
        audio.play(hint_audio or TTS_HINT_ERROR)
        
        self.current_hint_index += 1
        self._start_or_resume_timer()

    def _reveal_answer_and_end_round(self):
        if self.current_state != STATE_ROUND_OVER:
            audio.play(TTS_NO_ANSWER)
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
        log.debug(f"Current Scores - {self.game_data['team_names'][0]}: {self.scores[0]}, {self.game_data['team_names'][1]}: {self.scores[1]}")

    def _on_game_end(self):
        log.info("State: GAME_END. Final Scores:")
        log.info(f"{self.game_data['team_names'][0]}: {self.scores[0]}")
        log.info(f"{self.game_data['team_names'][1]}: {self.scores[1]}")
        if self.scores[0] == self.scores[1]:
            audio.play(TTS_GAME_DRAW)
        elif not self.final_score_announced:
            score_audio_path, score_thread = self._generate_score_announcement_async()
            if score_thread:
                score_thread.join()
            if score_audio_path:
                audio.play(score_audio_path)

        audio.play(TTS_NEW_GAME)
        self.set_state(STATE_GAME_OVER_WAITING_RESTART)

    def _on_game_over_waiting_restart(self):
        log.info("State: GAME_OVER_WAITING_RESTART. Press button to start a new game.")

    def _on_paused(self):
        log.info("State: PAUSED.")

    def _on_waiting_topic(self):
        if self._game_ready: 
            log.info("State: WAITING_TOPIC (Game Ready). Press button to start.")
        else: 
            log.info("State: WAITING_TOPIC. Press button to hear topic prompt.")

    def _on_waiting_topic_input(self):
        log.info("State: WAITING_TOPIC_INPUT. Press button to speak the topic now.")

    def _on_waiting_difficulty(self):
        log.info("State: WAITING_DIFFICULTY. Prompting for difficulty.")
        audio.play(TTS_DIFICULTY)
        self.set_state(STATE_WAITING_DIFFICULTY_INPUT)

    def _on_waiting_difficulty_input(self):
        log.info("State: WAITING_DIFFICULTY_INPUT. Press button to speak the difficulty now.")
        
    def _on_ready_to_start(self):
        log.info("State: READY_TO_START. Press button to hear team greeting and start the game.")

game = StateMachine()
