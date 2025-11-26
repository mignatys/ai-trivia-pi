#!/usr/bin/env python3
import time
from aiy.board import Board

LONG_PRESS_TIME = 1.5  # seconds
BLINK_COUNT = 5
BLINK_INTERVAL = 0.2  # seconds

def blink_led(led, times, interval):
    """Blink the LED a fixed number of times."""
    for _ in range(times):
        led.state = led.ON
        time.sleep(interval)
        led.state = led.OFF
        time.sleep(interval)

def main():
    with Board() as board:
        led = board.led  # SingleColorLed for external button
        led_on = False
        press_time = [0]  # store press start time

        # Called when button is pressed
        def on_pressed():
            press_time[0] = time.time()

        # Called when button is released
        def on_released():
            nonlocal led_on
            duration = time.time() - press_time[0]
            if duration < LONG_PRESS_TIME:
                # short press → toggle LED
                led_on = not led_on
                led.state = led.ON if led_on else led.OFF
            else:
                # long press → blink 5 times quickly, then off
                blink_led(led, BLINK_COUNT, BLINK_INTERVAL)
                led_on = False

        # Attach callbacks
        board.button.when_pressed = on_pressed
        board.button.when_released = on_released

        # Keep script running
        while True:
            time.sleep(0.1)

if __name__ == "__main__":
    main()

