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

# Audio recording parameters
SAMPLERATE = 16000
CHANNELS = 1
DTYPE = 'int16'
WAV_OUTPUT_FILENAME = "last_recording.wav"

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
            interim_results=False,
            single_utterance=True,
        )
        self._buffer = queue.Queue()
        self._stop_event = threading.Event()
        log.info("Speech-to-Text manager initialized (using sounddevice).")

    def _audio_callback(self, indata, frames, time, status):
        """This is called by the sounddevice stream for each audio block."""
        if status:
            # This warning is common on Raspberry Pi and means the CPU is not
            # keeping up with the audio stream. It's generally safe to ignore
            # unless recognition quality is severely impacted.
            log.warn(f"Sounddevice status: {status}")
        self._buffer.put(bytes(indata))

    def _write_to_wav(self, audio_chunks):
        """Saves the collected audio chunks to a .wav file."""
        log.info(f"Saving recording to {WAV_OUTPUT_FILENAME}...")
        try:
            with wave.open(WAV_OUTPUT_FILENAME, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                # FIX: Hardcode the sample width to 2 bytes for 'int16'
                # This is more robust than using a helper function.
                wf.setsampwidth(2)
                wf.setframerate(SAMPLERATE)
                wf.writeframes(b''.join(audio_chunks))
            log.info("Recording saved successfully.")
        except Exception as e:
            log.error(f"Failed to save .wav file: {e}")

    def recognize_speech(self, hint_text="Speak now...", timeout_sec=15):
        """
        Listens for a single utterance and returns the transcribed text.
        """
        log.info(f"Listening for speech... ({hint_text})")
        self._buffer = queue.Queue()
        self._stop_event.clear()
        
        recorded_chunks = []

        def audio_generator():
            while not self._stop_event.is_set():
                chunk = self._buffer.get()
                if chunk is None:
                    break
                recorded_chunks.append(chunk)
                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        try:
            log.info("Recording started...")
            with sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype=DTYPE,
                                callback=self._audio_callback):
                
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

                    if result.is_final:
                        text = result.alternatives[0].transcript
                        log.info(f"Speech recognized: '{text}'")
                        return text
            
            log.info("No speech detected within the timeout.")
            return None

        except Exception as e:
            log.error(f"An error occurred during speech recognition: {e}")
            if "Deadline" in str(e):
                log.info("Recognition timed out.")
            return None
        finally:
            # This ensures recording is always stopped and the file is saved.
            self._stop_event.set()
            self._write_to_wav(recorded_chunks)
            log.info("Recording stopped.")

# Global instance
stt = STTManager()
