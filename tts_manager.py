"""
tts_manager.py
--------------
Handles bulk Text-to-Speech (TTS) generation from a game data JSON.
It uses multiple threads to generate audio files in the background and
provides an API to retrieve the paths to the generated files.
"""

import os
import shutil
import subprocess
import threading
import queue
import time
from logger import log
from config import DEFAULT_TTS_MODEL, TTS_OUTPUT_DIR, TTS_WORKER_COUNT, INITIAL_QUESTION_COUNT

class TTSManager:
    """
    Manages batch TTS generation in two phases: initial (blocking) and
    remaining (background), plus on-the-fly sentence generation.
    """
    def __init__(self):
        self.model_path = DEFAULT_TTS_MODEL
        self.output_dir = TTS_OUTPUT_DIR
        self.num_workers = TTS_WORKER_COUNT
        self.game_data = None
        
        if not os.path.exists(self.model_path):
            log.error(f"TTS model not found at: {self.model_path}. TTS will be disabled.")
            self.is_ready = False
        else:
            self.is_ready = True
            log.info(f"TTS Manager initialized with {self.num_workers} workers.")

    def _clear_cache(self):
        """Atomically removes and recreates the TTS output directory."""
        if os.path.exists(self.output_dir):
            log.info(f"Clearing TTS cache directory: {self.output_dir}")
            try:
                shutil.rmtree(self.output_dir)
            except OSError as e:
                log.error(f"Error removing directory {self.output_dir}: {e}")
                return
        
        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            log.error(f"Error creating directory {self.output_dir}: {e}")

    def _tts_worker(self, job_queue):
        """The worker thread function that processes a given queue of TTS jobs."""
        while True:
            try:
                text, output_filepath = job_queue.get(block=False)
                self._generate_speech(text, output_filepath)
                job_queue.task_done()
            except queue.Empty:
                break

    def _generate_speech(self, text, output_filepath):
        """Calls the Piper TTS engine to generate a .wav file."""
        if os.path.exists(output_filepath):
            return

        log.debug(f"Generating TTS for: {os.path.basename(output_filepath)}")
        command = f'echo "{text}" | piper --model {self.model_path} --output_file {output_filepath}'
        
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to generate TTS for '{text}'. Error: {e.stderr}")

    def _run_generation_jobs(self, jobs):
        """
        Creates a queue for the given jobs and processes them with worker threads.
        This is a blocking call that waits for all jobs in the list to complete.
        """
        if not jobs:
            return

        job_queue = queue.Queue()
        for job in jobs:
            job_queue.put(job)

        threads = []
        for _ in range(self.num_workers):
            thread = threading.Thread(target=self._tts_worker, args=(job_queue,), daemon=True)
            threads.append(thread)
            thread.start()
        
        job_queue.join()

    def generate_sentence_async(self, text, filename):
        """
        Generates a single audio file in a background thread (non-blocking).
        """
        if not self.is_ready: return
        
        filepath = os.path.join(self.output_dir, filename)
        log.info(f"Starting async generation for '{filename}'...")
        # The job is a simple tuple of (text, filepath)
        job = (text, filepath)
        # We create a mini-queue for just this one job
        job_queue = queue.Queue()
        job_queue.put(job)
        
        # Start a single, dedicated thread for this one-off job
        threading.Thread(target=self._tts_worker, args=(job_queue,), daemon=True).start()
        return filepath

    def _get_jobs_for_round(self, round_data):
        """Returns a list of TTS jobs for a single round."""
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

    def generate_initial_audio(self, game_data):
        """
        Phase 1: Generates high-priority audio (blocking).
        """
        if not self.is_ready: return
        self.game_data = game_data
        self._clear_cache()

        initial_jobs = []
        initial_jobs.append((game_data["teams_greating"], os.path.join(self.output_dir, "teams_greating.wav")))

        for i, round_data in enumerate(game_data["rounds"]):
            if i < INITIAL_QUESTION_COUNT:
                initial_jobs.extend(self._get_jobs_for_round(round_data))
        
        log.info(f"Starting initial TTS generation for {len(initial_jobs)} audio files...")
        self._run_generation_jobs(initial_jobs)
        log.info("Initial TTS generation complete.")

    def generate_remaining_audio(self):
        """
        Phase 2: Generates the rest of the audio in the background (non-blocking).
        """
        if not self.is_ready or not self.game_data: return

        remaining_jobs = []
        for i, round_data in enumerate(self.game_data["rounds"]):
            if i >= INITIAL_QUESTION_COUNT:
                remaining_jobs.extend(self._get_jobs_for_round(round_data))

        if not remaining_jobs:
            return

        log.info(f"Starting background generation for {len(remaining_jobs)} remaining audio files...")
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
