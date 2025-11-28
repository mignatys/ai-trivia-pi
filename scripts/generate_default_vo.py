"""
generate_default_vo.py
----------------------
A script to generate all the default, pre-canned voiceover lines for the game
using the central TTSManager.

This script reads the `DEFAULT_VOICE_LINES` dictionary from the config file
and uses the TTSManager to generate a .wav file for each entry.

To run this script:
- Run from the project root: python3 scripts/generate_default_vo.py
"""

import os
import sys
import argparse

# Add project root to path to allow importing from our modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from config import DEFAULT_VOICE_LINES, TTS_DEFAULT_DIR
    from tts_manager import tts # Import the global tts instance
except ImportError as e:
    print(f"Error: A required library is missing or there's an import error: {e}")
    sys.exit(1)

def main():
    """
    Main function to iterate through the voice lines and generate audio.
    """
    print("--- Starting Default Voiceover Generation with TTS Manager ---")
    
    if not tts.is_ready:
        print("TTS Manager is not ready. Please check your API keys and configuration.")
        return

    if not DEFAULT_VOICE_LINES:
        print("DEFAULT_VOICE_LINES dictionary is empty. Nothing to do.")
        return

    print(f"Ensuring output directory exists: {TTS_DEFAULT_DIR}")
    os.makedirs(TTS_DEFAULT_DIR, exist_ok=True)
    
    success_count = 0
    fail_count = 0

    # Create a list of jobs for the TTS manager
    jobs = []
    for filepath, text in DEFAULT_VOICE_LINES.items():
        jobs.append((text, filepath))

    # Use the TTS manager's internal generation jobs method.
    # The manager will handle its own rate limiting internally.
    tts._run_generation_jobs(jobs)

    # Verify which files were created
    for filepath, text in DEFAULT_VOICE_LINES.items():
        if os.path.exists(filepath):
            print(f"  -> Verified: {os.path.basename(filepath)}")
            success_count += 1
        else:
            print(f"  -> FAILED: {os.path.basename(filepath)}")
            fail_count += 1
    
    print("\\n--- Generation Complete ---")
    print(f"Successfully generated/verified: {success_count} files")
    print(f"Failed to generate:   {fail_count} files")

if __name__ == "__main__":
    main()
