from audio import audio
import time

def main():
    # Play intro voiceover (blocking)
    audio.play("sounds/grand_intro.wav", volume=0.9)

    # Start background music
    audio.play_bg("sounds/intro_bg.wav", volume=0.3)

    # Play voice intro async and stop BG when done
    audio.play_async(
        "sounds/voice_intro.wav",
        volume=0.9,
        on_finished=lambda: audio.stop_bg_after_delay()
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        audio.stop_bg()
        print("Exiting...")

if __name__ == "__main__":
    main()

