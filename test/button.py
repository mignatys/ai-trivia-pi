from gpiozero import Button
import time

button = Button(23)  # hardcode your HAT button GPIO

while True:
    button.wait_for_press()
    start = time.time()
    button.wait_for_release()
    duration = time.time() - start
    print("Short" if duration < 1 else "Long")

