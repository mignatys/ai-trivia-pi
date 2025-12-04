import os
import threading
from logger import log
from config import REQUIRED_AUDIO_ASSETS

class Timer(threading.Thread):
    def __init__(self, interval, callback, recurring=False):
        super().__init__()
        self.interval = interval
        self.callback = callback
        self.recurring = recurring
        self.stopped = threading.Event()
        self.daemon = True

    def run(self):
        while not self.stopped.wait(self.interval):
            self.callback()
            if not self.recurring:
                self.stop()

    def stop(self):
        self.stopped.set()

    def is_running(self):
        return not self.stopped.is_set()

def check_audio_assets():
    """
    Checks for the existence of all required audio files.
    """
    log.info("Checking for required audio assets...")
    missing_files = []
    for asset_path in REQUIRED_AUDIO_ASSETS:
        if not os.path.exists(asset_path):
            missing_files.append(asset_path)
    
    if missing_files:
        log.error("The following required audio assets are missing:")
        for f in missing_files:
            log.error(f"  - {f}")
        return False
    
    log.info("All required audio assets are present.")
    return True
