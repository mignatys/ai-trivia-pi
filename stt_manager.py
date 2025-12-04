"""
stt_manager.py
--------------
Handles Speech-to-Text (STT) transcription by directly using the
google-cloud-speech library and sounddevice for audio recording.
This approach avoids the deprecated aiy.voice library wrappers.
"""

import sounddevice as sd
import numpy as np
from google.cloud import speech
from logger import log
import threading
import queue
import wave
import time
from audio import audio

# Audio recording parameters
SAMPLERATE = 16000
CHANNELS = 1
DTYPE = 'int16'
WAV_OUTPUT_FILENAME = "last_recording.wav"
SILENCE_THRESHOLD = 500  # RMS threshold for considering audio as silence
BLOCK_SIZE = 8000 # Block size for audio processing

class STTManager:
    """
    Manages audio recording and streaming to the Google Cloud Speech-to-Text API.
    """
    def __init__(self):
        self.client = speech.SpeechClient()
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLERATE,
                language_code="ru-RU",
            ),
            interim_results=True, # Enable interim results for faster feedback
            single_utterance=False, # Allow multiple utterances
        )
        self._buffer = queue.Queue()
        self._stop_event = threading.Event()
        self._stream = None # To hold the sounddevice stream object
        log.info("Speech-to-Text manager initialized (using sounddevice).")

    def _audio_callback(self, indata, frames, time, status):
        """This is called by the sounddevice stream for each audio block."""
        if status:
            log.warn(f"Sounddevice status: {status}")
        self._buffer.put(bytes(indata))

    def _write_to_wav(self, audio_chunks):
        """Saves the collected audio chunks to a .wav file."""
        log.info(f"Saving recording to {WAV_OUTPUT_FILENAME}...")
        try:
            with wave.open(WAV_OUTPUT_FILENAME, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLERATE)
                wf.writeframes(b''.join(audio_chunks))
            log.info("Recording saved successfully.")
        except Exception as e:
            log.error(f"Failed to save .wav file: {e}")

    def recognize_speech(self, hint_text="Speak now...", timeout_sec=15, silence_duration_sec=0.8):
        """
        Listens for speech and returns the transcribed text.
        Stops listening after a period of silence.
        """
        log.info(f"Listening for speech... ({hint_text})")
        self._buffer = queue.Queue()
        self._stop_event.clear()
        
        recorded_chunks = []
        last_sound_time = time.time()
        full_transcript = ""

        def audio_generator():
            nonlocal last_sound_time
            while not self._stop_event.is_set():
                chunk = self._buffer.get()
                if chunk is None:
                    break
                
                recorded_chunks.append(chunk)
                
                rms = np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(np.float32)**2))
                if rms > SILENCE_THRESHOLD:
                    last_sound_time = time.time()
                
                if time.time() - last_sound_time > silence_duration_sec:
                    log.info(f"Silence detected for over {silence_duration_sec} seconds. Stopping recording.")
                    self._stop_event.set()

                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        try:
            audio.mute_all()
            log.info("Recording started...")
            self._stream = sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype=DTYPE,
                                blocksize=BLOCK_SIZE, callback=self._audio_callback)
            with self._stream:
                requests = audio_generator()
                responses = self.client.streaming_recognize(
                    config=self.streaming_config,
                    requests=requests,
                    timeout=timeout_sec
                )

                for response in responses:
                    if not response.results:
                        continue
                    
                    result = response.results[0]
                    if not result.alternatives:
                        continue

                    transcript = result.alternatives[0].transcript
                    if result.is_final:
                        full_transcript += transcript + " "
                        log.debug(f"Intermediate transcript: '{full_transcript}'")
            
            log.info(f"Final speech recognized: '{full_transcript.strip()}'")
            return full_transcript.strip()

        except Exception as e:
            log.error(f"An error occurred during speech recognition: {e}")
            if "Deadline" in str(e):
                log.info("Recognition timed out.")
            return None
        finally:
            audio.unmute_all()
            self._stop_event.set()
            self._buffer.put(None) # Ensure the generator loop terminates
            self._write_to_wav(recorded_chunks)
            log.info("Recording stopped.")

    def shutdown(self):
        """Explicitly stops the sounddevice stream if it's active."""
        if self._stream and self._stream.active:
            self._stream.stop()
            self._stream.close()
            log.info("Sounddevice stream shut down.")

# Global instance
stt = STTManager()
