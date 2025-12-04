import time
import signal
import sys
from logger import log
from audio import audio
from stt_manager import stt
from llm_evaluator import llm
from button_handler import ButtonHandler, IS_AIY
from state_machine import game
from config import INTRO_MUSIC, BACKGROUND_MUSIC, TTS_INTRO, AUTO_START_APP
from utils import check_audio_assets
from web import app as web_app
from web import network_manager as net

shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    log.info(f"Signal {sig} received. Initiating graceful shutdown.")
    shutdown_requested = True

def main():
    global shutdown_requested
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not AUTO_START_APP:
        log.info("AUTO_START_APP is set to False. Exiting.")
        return

    # --- Network and Web UI Setup ---
    web_app.start_in_thread()
    if not net.is_connected():
        log.info("No WiFi connection. Starting setup hotspot.")
        net.start_hotspot()
        while not shutdown_requested:
            time.sleep(1)
        log.info("Shutdown requested while in hotspot mode.")
        sys.exit(0)

    # --- Pre-flight checks ---
    if not IS_AIY:
        log.error("This application requires the AIY board library to run.")
        sys.exit(1)
        
    if not check_audio_assets():
        log.error("Cannot start the game due to missing audio assets.")
        sys.exit(1)

    # --- Main Game Loop ---
    with ButtonHandler() as button:
        game.button_handler = button # Pass the button handler to the state machine
        button.register_short_press(game.handle_short_press)
        button.register_long_press(game.handle_long_press)

        # --- Intro Sequence ---
        log.info("Playing intro music...")
        audio.play(INTRO_MUSIC, volume=0.9)
        log.info("Playing background music and intro voiceover...")
        audio.play_bg(BACKGROUND_MUSIC, volume=0.3)
        
        def start_game_logic():
            log.info("Application started. Initializing game state machine.")
            game.start()
            if not llm.is_ready:
                log.error("LLM failed to initialize. Exiting application.")
                global shutdown_requested
                shutdown_requested = True
            else:
                web_app.set_game_ready_status(True)
                log.info("Game is running. Press the button to advance the state.")

        audio.play_async(TTS_INTRO, volume=0.9, on_finished=start_game_logic)

        try:
            while not shutdown_requested:
                time.sleep(0.1)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt received. Initiating graceful shutdown.")
            shutdown_requested = True
        finally:
            log.info("Performing final shutdown procedures.")
            audio.stop_bg()
            audio.shutdown()
            stt.shutdown()
            log.info("Application exited gracefully.")
            sys.exit(0)

if __name__ == "__main__":
    main()
