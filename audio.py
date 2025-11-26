import os
import threading
import pygame
import time

os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['SDL_ALSA_DEVICE'] = 'plughw:2,0'

class AudioManager:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        self.bg_lock = threading.Lock()

    # Blocking playback for voice/effects
    def play(self, filepath, volume=1.0):
        sound = pygame.mixer.Sound(filepath)
        sound.set_volume(volume)
        channel = pygame.mixer.find_channel()
        if channel is None:
            channel = pygame.mixer.Channel(0)
        channel.play(sound)
        while channel.get_busy():
            pygame.time.delay(50)

    # Async playback for voice/effects
    def play_async(self, filepath, volume=1.0, on_finished=None):
        def _play():
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

        threading.Thread(target=_play, daemon=True).start()

    # Background music using pygame.mixer.music (dedicated, loopable)
    def play_bg(self, filepath, volume=0.5):
        with self.bg_lock:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)  # infinite loop

    # Stop background music
    def stop_bg(self):
        with self.bg_lock:
            pygame.mixer.music.stop()

    def stop_bg_after_delay(self, delay=2):
        time.sleep(delay)
        audio.stop_bg()

# Global instance
audio = AudioManager()

