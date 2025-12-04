import os
import threading
import pygame
import time
from config import TTS_SAMPLE_RATE
from logger import log

os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['SDL_ALSA_DEVICE'] = 'plughw:2,0'

class AudioManager:
    def __init__(self):
        pygame.mixer.init(frequency=TTS_SAMPLE_RATE, size=-16, channels=1, buffer=4096)
        self.bg_lock = threading.Lock()
        self.is_muted = False

    def mute_all(self):
        if self.is_muted: return
        log.debug("Muting all audio.")
        pygame.mixer.music.pause()
        pygame.mixer.pause()
        self.is_muted = True

    def unmute_all(self):
        if not self.is_muted: return
        log.debug("Unmuting all audio.")
        pygame.mixer.music.unpause()
        pygame.mixer.unpause()
        self.is_muted = False

    def stop_all_sounds(self):
        """Stops all currently playing sounds on all channels."""
        pygame.mixer.stop()

    def play(self, filepath, volume=1.0):
        """Blocking playback for voice/effects."""
        if not filepath or not os.path.exists(filepath):
            log.warn(f"Audio file not found, skipping playback: {filepath}")
            return
        try:
            sound = pygame.mixer.Sound(filepath)
            sound.set_volume(volume)
            channel = pygame.mixer.find_channel()
            if channel is None:
                channel = pygame.mixer.Channel(0)
            channel.play(sound)
            while channel.get_busy():
                pygame.time.delay(50)
        except pygame.error as e:
            log.error(f"Error playing audio file {filepath}: {e}")

    def play_async(self, filepath, volume=1.0, on_finished=None):
        """Async playback for voice/effects."""
        if not filepath or not os.path.exists(filepath):
            log.warn(f"Audio file not found, skipping async playback: {filepath}")
            if on_finished:
                on_finished()
            return
            
        def _play():
            try:
                sound = pygame.mixer.Sound(filepath)
                sound.set_volume(volume)
                channel = pygame.mixer.find_channel()
                if channel is None:
                    channel = pygame.mixer.Channel(0)
                channel.play(sound)
                while channel.get_busy():
                    pygame.time.delay(50)
                if on_finished:
                    on_finished()
            except pygame.error as e:
                log.error(f"Error in async audio playback for {filepath}: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def play_bg(self, filepath, volume=0.5):
        """Background music using pygame.mixer.music (dedicated, loopable)."""
        if not filepath or not os.path.exists(filepath):
            log.warn(f"Background audio file not found, skipping playback: {filepath}")
            return
        with self.bg_lock:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops=-1)
            except pygame.error as e:
                log.error(f"Error playing background audio {filepath}: {e}")

    def stop_bg(self):
        """Stop background music."""
        with self.bg_lock:
            pygame.mixer.music.stop()

    def stop_bg_after_delay(self, delay=2):
        time.sleep(delay)
        audio.stop_bg()

    def shutdown(self):
        """Quits the pygame mixer to release audio resources."""
        pygame.mixer.quit()
        log.info("Pygame mixer shut down.")

# Global instance
audio = AudioManager()
