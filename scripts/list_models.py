"""
list_models.py
--------------
A simple test script to connect to the Gemini API and list all available models.
This helps verify that the API key is working and shows which models can be used.

To run this script:
1. Make sure you have your GEMINI_API_KEY set in a .env file in the project root.
2. Run from the project root: python3 -m scripts.list_models
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file in the parent directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please create a .env file in the project root and add your key.")
        return

    try:
        genai.configure(api_key=api_key)

        print("Successfully connected to the Gemini API.")
        print("Available Models:")
        print("-" * 30)

        for m in genai.list_models():
            print(f"Model Name: {m.name}")
            print(f"  - Supported Methods: {m.supported_generation_methods}")
            print("-" * 30)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
