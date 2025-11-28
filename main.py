from audio import audio
import time
from logger import log
from button_handler import ButtonHandler, IS_AIY
from state_machine import game # Import the game instance
from config import INTRO_MUSIC, BACKGROUND_MUSIC, TTS_INTRO

def main():
    """
    Initializes the application, plays the intro sequence, and starts the
    game state machine.
    """
    if not IS_AIY:
        log.error("This application requires the AIY board library to run.")
        return

    # Initial intro sequence
    log.info("Playing intro music...")
    audio.play(INTRO_MUSIC, volume=0.9) # Blocking play for the main intro music

    log.info("Playing background music and intro voiceover...")
    audio.play_bg(BACKGROUND_MUSIC, volume=0.3) # Start looping background music
    
    # Play TTS_INTRO asynchronously. The background music will continue playing.
    audio.play_async(TTS_INTRO, volume=0.9)

    # Use the ButtonHandler as a context manager
    with ButtonHandler() as button:
        # --- Connect ButtonHandler to StateMachine ---
        button.register_short_press(game.handle_short_press)
        button.register_long_press(game.handle_long_press)

        # --- Start the game state machine after the intro ---
        log.info("Application started. Initializing game state machine.")
        game.start()
        
        log.info("Game is running. Press the button to advance the state.")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            audio.stop_bg()
            log.info("Exiting application...")

if __name__ == "__main__":
    main()
