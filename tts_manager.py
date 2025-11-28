"""
tts_manager.py
--------------
Handles bulk Text-to-Speech (TTS) generation from a game data JSON using 
the Gemini "Achird" voice. It uses a smart rate limiter to stay within API quotas.
"""

import os
import shutil
import wave
import time
import random
import threading
from collections import deque
from logger import log
from config import (
    TTS_OUTPUT_DIR, 
    INITIAL_QUESTION_COUNT, 
    SCORE_ANNOUNCEMENT_TEMPLATES, 
    TTS_WRONG_TEAM,
    GEMINI_API_KEY,
    OVERWRITE_EXISTING_TTS,
    FORCE_SYNC_TTS_GENERATION
)

try:
    from google import genai
    from google.genai import types
    from google.api_core import exceptions
except ImportError:
    log.error("The 'google-generativeai' library is not installed. Please run 'pip install google-generativeai'.")
    exit(1)

class TTSManager:
    """
    Manages batch TTS generation using the Gemini API with a smart rate limiter.
    """
    def __init__(self):
        self.output_dir = TTS_OUTPUT_DIR
        self.game_data = None
        self.model_id = "gemini-2.5-flash-preview-tts"
        self.voice_name = "Achird"
        
        self.requests_per_minute = 9
        self.request_timestamps = deque()
        self.rate_limit_lock = threading.Lock()
        
        if not GEMINI_API_KEY:
            log.error("GEMINI_API_KEY not found. TTS will be disabled.")
            self.is_ready = False
            return

        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.is_ready = True
            log.info(f"TTS Manager initialized with Gemini model '{self.model_id}' and voice '{self.voice_name}'.")
        except Exception as e:
            log.error(f"Failed to configure Gemini client: {e}")
            self.is_ready = False

    def _wait_for_rate_limit(self):
        """
        A thread-safe method that blocks until a new API request is permitted.
        """
        with self.rate_limit_lock:
            current_time = time.time()
            
            while self.request_timestamps and self.request_timestamps[0] < current_time - 60:
                self.request_timestamps.popleft()
            
            if len(self.request_timestamps) >= self.requests_per_minute:
                oldest_request_time = self.request_timestamps[0]
                wait_time = (oldest_request_time + 60) - current_time
                if wait_time > 0:
                    log.debug(f"Rate limit reached. Waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time)
            
            self.request_timestamps.append(time.time())

    def _clear_cache(self):
        """Atomically removes and recreates the TTS output directory."""
        if os.path.exists(self.output_dir):
            log.info(f"Clearing TTS cache directory: {self.output_dir}")
            try:
                shutil.rmtree(self.output_dir)
            except OSError as e:
                log.error(f"Error removing directory {self.output_dir}: {e}")
        os.makedirs(self.output_dir, exist_ok=True)

    def _synthesize_speech(self, text):
        """
        Calls the Gemini TTS API with retry logic for rate limit and network errors.
        """
        if not self.is_ready:
            return None
        
        self._wait_for_rate_limit()
        
        max_retries = 5
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                config = types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    )
                )
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=text,
                    config=config,
                )
                if response and response.candidates and response.candidates[0].content.parts:
                    return response.candidates[0].content.parts[0].inline_data.data
                else:
                    log.error(f"Received an empty or invalid response from Gemini API for text: '{text}'")
                    return None
            except exceptions.ResourceExhausted as e:
                wait_time = (backoff_factor ** attempt) + (random.random() * 0.5)
                log.warn(f"Attempt {attempt + 1} failed with rate limit error. Retrying after {wait_time:.2f}s...")
                time.sleep(wait_time)
            except exceptions.GoogleAPICallError as e:
                wait_time = (backoff_factor ** attempt) + (random.random() * 0.5)
                log.warn(f"Attempt {attempt + 1} failed with network error. Retrying after {wait_time:.2f}s...")
                time.sleep(wait_time)
            except Exception as e:
                log.error(f"An unexpected error occurred during TTS synthesis for '{text}': {e}")
                return None
        
        log.error(f"All {max_retries} retry attempts failed for text: '{text}'")
        return None

    def _generate_speech_file(self, text, output_filepath):
        """
        Generates a .wav file from the given text, skipping if it exists and
        overwrite is disabled.
        """
        if not OVERWRITE_EXISTING_TTS and os.path.exists(output_filepath):
            log.debug(f"Skipping existing TTS file: {os.path.basename(output_filepath)}")
            return

        log.debug(f"Generating TTS for: {os.path.basename(output_filepath)}")
        audio_bytes = self._synthesize_speech(text)
        if audio_bytes:
            with wave.open(output_filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_bytes)

    def _run_generation_jobs(self, jobs):
        """
        Processes a list of TTS jobs sequentially.
        """
        if not jobs: return
        for text, filepath in jobs:
            self._generate_speech_file(text, filepath)

    def generate_sentence_async(self, text, filename):
        """
        Generates a single audio file. This is now a blocking call but
        keeps the same interface for compatibility.
        """
        if not self.is_ready: return None, None
        filepath = os.path.join(self.output_dir, filename)
        log.info(f"Starting generation for '{filename}'...")
        self._generate_speech_file(text, filepath)
        return filepath, None # Return None for the thread object

    def _get_jobs_for_round(self, round_data):
        q_id = round_data["id"]
        jobs = [
            (round_data["host_intro"], os.path.join(self.output_dir, f"{q_id}_host_intro.wav")),
            (round_data["question"], os.path.join(self.output_dir, f"{q_id}_question.wav")),
            (round_data["answer"], os.path.join(self.output_dir, f"{q_id}_answer.wav")),
            (round_data["fun_fact"], os.path.join(self.output_dir, f"{q_id}_fun_fact.wav"))
        ]
        for j, hint in enumerate(round_data["hints"]):
            jobs.append((hint, os.path.join(self.output_dir, f"{q_id}_hint_{j+1}.wav")))
        return jobs

    def _generate_wrong_team_announcement(self, game_data):
        template = SCORE_ANNOUNCEMENT_TEMPLATES["WRONG_TEAM"]
        text = template.format(team_one=game_data['team_names'][0], team_two=game_data['team_names'][1])
        return (text, TTS_WRONG_TEAM)

    def generate_initial_audio(self, game_data):
        if not self.is_ready: return
        self.game_data = game_data
        if OVERWRITE_EXISTING_TTS:
            self._clear_cache()
        
        initial_jobs = [(game_data["teams_greating"], os.path.join(self.output_dir, "teams_greating.wav"))]
        initial_jobs.append(self._generate_wrong_team_announcement(game_data))
        for i, round_data in enumerate(game_data["rounds"]):
            if i < INITIAL_QUESTION_COUNT:
                initial_jobs.extend(self._get_jobs_for_round(round_data))
        log.info(f"Starting initial TTS generation for {len(initial_jobs)} audio files...")
        self._run_generation_jobs(initial_jobs)
        log.info("Initial TTS generation complete.")

    def generate_remaining_audio(self):
        if not self.is_ready or not self.game_data: return
        remaining_jobs = []
        for i, round_data in enumerate(self.game_data["rounds"]):
            if i >= INITIAL_QUESTION_COUNT:
                remaining_jobs.extend(self._get_jobs_for_round(round_data))
        if not remaining_jobs: return
        
        log.info(f"Starting background generation for {len(remaining_jobs)} remaining audio files...")
        if FORCE_SYNC_TTS_GENERATION:
            log.debug("Forcing synchronous generation for testing.")
            self._run_generation_jobs(remaining_jobs)
        else:
            threading.Thread(target=self._run_generation_jobs, args=(remaining_jobs,), daemon=True).start()

    def _get_audio_path(self, filename):
        filepath = os.path.join(self.output_dir, filename)
        return filepath if os.path.exists(filepath) else ""

    def get_greeting_audio(self):
        return self._get_audio_path("teams_greating.wav")

    def get_host_intro_audio(self, question_id):
        return self._get_audio_path(f"{question_id}_host_intro.wav")

    def get_question_audio(self, question_id):
        return self._get_audio_path(f"{question_id}_question.wav")
    
    def get_answer_audio(self, question_id):
        return self._get_audio_path(f"{question_id}_answer.wav")

    def get_hint_audio(self, question_id, hint_number):
        return self._get_audio_path(f"{question_id}_hint_{hint_number}.wav")

    def get_fun_fact_audio(self, question_id):
        return self._get_audio_path(f"{question_id}_fun_fact.wav")

tts = TTSManager()
