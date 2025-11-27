from audio import audio
import time
from logger import log
from button_handler import ButtonHandler, IS_AIY
from state_machine import game # Import the game instance

def main():
    """
    Initializes the application, plays the intro sequence, and starts the
    game state machine.
    """
    # --- Your original audio intro code ---
    # audio.play("sounds/grand_intro.wav", volume=0.9)
    # audio.play_bg("sounds/intro_bg.wav", volume=0.3)
    # audio.play_async(
    #     "sounds/voice_intro.wav",
    #     volume=0.9,
    #     on_finished=lambda: audio.stop_bg_after_delay()
    # )

    if not IS_AIY:
        log.error("This application requires the AIY board library to run.")
        return

    # Use the ButtonHandler as a context manager
    with ButtonHandler() as button:
        # --- Connect ButtonHandler to StateMachine ---
        button.register_short_press(game.handle_short_press)
        button.register_long_press(game.handle_long_press)

        # --- Start the game ---
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
