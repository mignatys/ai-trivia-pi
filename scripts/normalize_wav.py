"""
normalize_wav.py
----------------
A script to find all .wav files in the 'sounds' directory and convert them
to the application's expected audio format (24000 Hz, 16-bit, mono).

This ensures that all sound effects and music play correctly without distortion.

Requires 'ffmpeg' to be installed on the system.
(sudo apt-get install ffmpeg)

To run this script:
- Run from the project root: python3 scripts/normalize_wav.py
"""

import os
import subprocess
import sys

# Add project root to path to allow importing from config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from config import SOUNDS_DIR, TTS_SAMPLE_RATE
except ImportError:
    print("Error: Could not import configuration from config.py.")
    sys.exit(1)

def normalize_audio_files():
    """
    Finds and converts all .wav files in the SOUNDS_DIR.
    """
    print(f"--- Starting Audio Normalization for Directory: {SOUNDS_DIR} ---")
    print(f"Target Format: {TTS_SAMPLE_RATE} Hz, 16-bit PCM, Mono")
    
    converted_count = 0
    failed_count = 0

    for root, _, files in os.walk(SOUNDS_DIR):
        for filename in files:
            if filename.lower().endswith('.wav'):
                input_path = os.path.join(root, filename)
                # Use a temporary file for the output to avoid in-place corruption
                temp_output_path = os.path.join(root, f"temp_{filename}")
                
                print(f"Processing '{input_path}'...")

                command = [
                    'ffmpeg',
                    '-i', input_path,
                    '-acodec', 'pcm_s16le',
                    '-ar', str(TTS_SAMPLE_RATE),
                    '-ac', '1',
                    '-y',  # Overwrite output file if it exists
                    temp_output_path
                ]
                
                try:
                    # Execute the command
                    result = subprocess.run(
                        command, 
                        check=True, 
                        capture_output=True, 
                        text=True
                    )
                    
                    # If conversion is successful, replace the original file
                    os.replace(temp_output_path, input_path)
                    print("  -> Success.")
                    converted_count += 1
                    
                except FileNotFoundError:
                    print("\\nError: 'ffmpeg' command not found.")
                    print("Please ensure ffmpeg is installed and accessible in your system's PATH.")
                    sys.exit(1)
                except subprocess.CalledProcessError as e:
                    print(f"  -> Error converting file: {filename}")
                    print(f"     ffmpeg Error: {e.stderr}")
                    failed_count += 1
                    # Clean up the temporary file if it was created
                    if os.path.exists(temp_output_path):
                        os.remove(temp_output_path)

    print("\\n--- Normalization Complete ---")
    print(f"Successfully converted: {converted_count} files")
    print(f"Failed to convert:    {failed_count} files")

if __name__ == "__main__":
    normalize_audio_files()
