"""
tts_manager.py
--------------
Handles bulk Text-to-Speech (TTS) generation from a game data JSON using 
the Gemini "Achird" voice via the Vertex AI endpoint. It uses a reactive 
retry mechanism to handle API rate limits.
"""

import os
import shutil
import wave
import time
import random
import threading
from logger import log
from config import (
    TTS_OUTPUT_DIR, 
    INITIAL_QUESTION_COUNT, 
    SCORE_ANNOUNCEMENT_TEMPLATES, 
    TTS_NO_TEAM,
    OVERWRITE_EXISTING_TTS,
    FORCE_SYNC_TTS_GENERATION,
    GCP_PROJECT_ID,
    GCP_LOCATION
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
    Manages batch TTS generation using the Gemini API via Vertex AI.
    """
    def __init__(self):
        self.output_dir = TTS_OUTPUT_DIR
        self.game_data = None
        self.model_id = "gemini-2.5-flash-tts"
        self.voice_name = "Achird"
        
        try:
            self.client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location=GCP_LOCATION)
            self.is_ready = True
            log.info(f"TTS Manager initialized with Vertex AI model '{self.model_id}' and voice '{self.voice_name}'.")
        except Exception as e:
            log.error(f"Failed to configure Vertex AI client. Ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly: {e}")
            self.is_ready = False

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
        Calls the Gemini TTS API. Returns audio bytes on success, None on failure.
        """
        if not self.is_ready:
            return None
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
        except Exception as e:
            log.error(f"An unexpected error occurred during TTS synthesis for '{text}': {e}")
            return None

    def _generate_speech_file(self, text, output_filepath):
        """
        Generates a .wav file from the given text, retrying up to 10 times on any failure.
        """
        if not OVERWRITE_EXISTING_TTS and os.path.exists(output_filepath):
            log.debug(f"Skipping existing TTS file: {os.path.basename(output_filepath)}")
            return

        max_retries = 10
        for attempt in range(max_retries):
            log.debug(f"Generating TTS for: {os.path.basename(output_filepath)} (Attempt {attempt + 1}/{max_retries})")
            try:
                audio_bytes = self._synthesize_speech(text)
                if audio_bytes:
                    with wave.open(output_filepath, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(audio_bytes)
                    log.debug(f"Successfully generated {os.path.basename(output_filepath)}")
                    return # Success, exit the retry loop
                else:
                    raise ValueError("Synthesize speech returned None")
            except Exception as e:
                log.warn(f"Generation failed for {os.path.basename(output_filepath)} on attempt {attempt + 1}. Reason: {e}")
                if attempt < max_retries - 1:
                    wait_time = 6
                    log.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    log.error(f"All {max_retries} retry attempts failed for {os.path.basename(output_filepath)}. Skipping this file.")

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

    def _generate_no_team_announcement(self, game_data):
        template = SCORE_ANNOUNCEMENT_TEMPLATES["NO_TEAM"]
        text = template.format(team_one=game_data['team_names'][0], team_two=game_data['team_names'][1])
        return (text, TTS_NO_TEAM)

    def generate_initial_audio(self, game_data):
        if not self.is_ready: return
        self.game_data = game_data
        if OVERWRITE_EXISTING_TTS:
            self._clear_cache()
        
        initial_jobs = [(game_data["teams_greating"], os.path.join(self.output_dir, "teams_greating.wav"))]
        initial_jobs.append(self._generate_no_team_announcement(game_data))
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

    def regenerate_round_audio(self, question_id):
        """
        Finds a specific round by its ID and regenerates all audio for it.
        """
        if not self.is_ready or not self.game_data: return
        
        for round_data in self.game_data["rounds"]:
            if round_data["id"] == question_id:
                log.warn(f"Regenerating audio for question ID: {question_id}")
                jobs = self._get_jobs_for_round(round_data)
                self._run_generation_jobs(jobs)
                return
        log.error(f"Could not find round with ID {question_id} to regenerate audio.")

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
