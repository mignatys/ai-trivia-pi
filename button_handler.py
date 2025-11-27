"""
button_handler.py
-----------------
Handles button and LED interactions for the AIY Voice HAT, detecting
short and long presses using the aiy.board library.
"""

import time
import threading
from logger import log
from config import LONG_PRESS_THRESHOLD

# Attempt to import aiy.board and set up the board.
# If it fails, the handler will not be functional.
try:
    from aiy.board import Board, Led
    IS_AIY = True
    log.info("AIY board library loaded successfully.")
except ImportError:
    log.warn("AIY board library not found. Button handler will be non-functional.")
    IS_AIY = False

class ButtonHandler:
    """
    Manages button press detection (short vs. long) and LED control
    using the aiy.board library. Designed to be used as a context manager.
    """
    def __init__(self):
        if not IS_AIY:
            self._board = None
            self.led = None
            return

        self._board = Board()
        self.led = self._board.led
        self._short_press_callback = None
        self._long_press_callback = None
        self._press_time = 0

        # Assign the internal methods as callbacks to the board button
        self._board.button.when_pressed = self._on_pressed
        self._board.button.when_released = self._on_released
        log.info("Button handler initialized and callbacks attached.")

    def register_short_press(self, callback):
        """Assigns a function to be called on a short press."""
        log.debug("Short press callback registered.")
        self._short_press_callback = callback

    def register_long_press(self, callback):
        """Assigns a function to be called on a long press."""
        log.debug("Long press callback registered.")
        self._long_press_callback = callback

    def _on_pressed(self):
        """Internal callback for when the button is pressed."""
        self._press_time = time.time()

    def _on_released(self):
        """Internal callback for when the button is released."""
        if self._press_time == 0:
            return
            
        duration = time.time() - self._press_time
        self._press_time = 0

        if duration < LONG_PRESS_THRESHOLD:
            log.info("Short press detected.")
            if self._short_press_callback:
                self._short_press_callback()
        else:
            log.info("Long press detected.")
            if self._long_press_callback:
                self._long_press_callback()

    def set_led_state(self, is_on):
        """Sets the LED state to ON or OFF."""
        if not self.led: return
        log.debug(f"Setting LED state to {'ON' if is_on else 'OFF'}")
        self.led.state = Led.ON if is_on else Led.OFF

    def blink_led(self, times, interval=0.2):
        """Blinks the LED a number of times in a non-blocking way."""
        if not self.led: return
        
        def _blink():
            for _ in range(times):
                self.led.state = Led.ON
                time.sleep(interval)
                self.led.state = Led.OFF
                time.sleep(interval)

        threading.Thread(target=_blink, daemon=True).start()

    def __enter__(self):
        """Allows the class to be used in a 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleans up the board resources when exiting the 'with' block."""
        if self._board:
            self._board.close()
            log.info("AIY board resources released.")
