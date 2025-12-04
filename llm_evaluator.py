"""
llm_evaluator.py
----------------
Handles all interactions with the Gemini LLM via the Vertex AI High-Level SDK.
"""

import json
import os
import traceback
from logger import log
from config import (
    QUESTION_PROMPT_FILE, 
    ANSWER_PROMPT_FILE, 
    GAME_QUESTIONS_FILE, 
    OVERWRITE_EXISTING_QUESTIONS,
    GCP_PROJECT_ID,
    GCP_LOCATION
)

# --- CORRECT IMPORT: Use the High-Level Vertex AI SDK ---
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
except ImportError:
    log.error("The 'google-cloud-aiplatform' library is not installed. Please run 'pip install google-cloud-aiplatform'.")
    exit(1)

class LLMEvaluator:
    """
    A wrapper for the Gemini LLM API via Vertex AI to handle prompt-based 
    generation and evaluation using the High-Level SDK.
    """
    def __init__(self):
        self.is_ready = False
        # Use official model names
        self.generation_model_name = "gemini-2.5-pro"
        self.evaluation_model_name = "gemini-2.5-flash"

        try:
            log.debug(f"Initializing Vertex AI for project '{GCP_PROJECT_ID}' in location '{GCP_LOCATION}'...")
            
            # --- AUTHENTICATION ---
            # vertexai.init() automatically looks for GOOGLE_APPLICATION_CREDENTIALS
            # which you set in your systemd service file.
            vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
            log.debug("Vertex AI initialized successfully.")

            # --- MODEL SETUP ---
            # We instantiate the model objects directly.
            self.gen_model = GenerativeModel(self.generation_model_name)
            self.eval_model = GenerativeModel(self.evaluation_model_name)
            
            log.info(f"Using '{self.generation_model_name}' for question generation.")
            log.info(f"Using '{self.evaluation_model_name}' for answer evaluation.")
            
            self.is_ready = True
            log.info("LLMEvaluator is ready.")

        except Exception as e:
            log.error(f"LLM Initialization Failed: {e}")
            log.error("Ensure GOOGLE_APPLICATION_CREDENTIALS is set and points to your JSON key.")
            log.error(traceback.format_exc())
            self.is_ready = False

    def _load_prompt(self, filepath):
        """Loads a prompt template from a file."""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            log.error(f"Prompt file not found: {filepath}")
            return None

    def get_questions(self, language, difficulty, topic):
        """
        Generates a new set of trivia questions.
        """
        if not self.is_ready:
            log.error("LLM is not ready. Cannot generate questions.")
            return False
            
        if not OVERWRITE_EXISTING_QUESTIONS and os.path.exists(GAME_QUESTIONS_FILE):
            log.info(f"Skipping question generation, file already exists: {GAME_QUESTIONS_FILE}")
            return True

        prompt_template = self._load_prompt(QUESTION_PROMPT_FILE)
        if not prompt_template:
            return False

        prompt = prompt_template.format(topic=topic, difficulty=difficulty, language=language)
        
        log.info("Generating new trivia questions from LLM...")
        try:
            # --- GENERATION CALL ---
            response = self.gen_model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192, # Increased token limit
                    response_mime_type="application/json" # Forces JSON output (Available in newer models)
                )
            )
            
            # Safety check for empty response
            if not response.candidates or not response.candidates[0].content.parts:
                log.error("LLM returned an empty response for question generation.")
                return False

            raw_response_text = response.text
            log.debug(f"Raw LLM response (get_questions): {raw_response_text}")

            # Cleanup JSON markdown if present (e.g. ```json ... ```)
            cleaned_json = raw_response_text.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
            
            game_data = json.loads(cleaned_json)
            with open(GAME_QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=2, ensure_ascii=False)
            
            log.info(f"Successfully generated and saved new questions to {GAME_QUESTIONS_FILE}")
            return True

        except Exception as e:
            log.error(f"Failed to generate or save questions from LLM: {e}")
            log.error(traceback.format_exc())
            return False

    def evaluate_answer(self, question, correct_answer, user_answer, team_names):
        """
        Evaluates a user's answer.
        """
        if not self.is_ready:
            log.error("LLM is not ready. Cannot evaluate answer.")
            return None

        prompt_template = self._load_prompt(ANSWER_PROMPT_FILE)
        if not prompt_template:
            return None

        prompt = prompt_template.format(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            first_team_name=team_names[0],
            second_team_name=team_names[1]
        )

        log.info(f"Evaluating answer: '{user_answer}'")
        try:
            # --- EVALUATION CALL ---
            response = self.eval_model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1024, # Increased token limit
                    response_mime_type="application/json"
                )
            )

            # Safety check for empty response
            if not response.candidates or not response.candidates[0].content.parts:
                log.error("LLM returned an empty response for answer evaluation (likely hit MAX_TOKENS or safety filters).")
                return None

            raw_response_text = response.text
            
            # Cleanup JSON
            cleaned_json = raw_response_text.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()

            result = json.loads(cleaned_json)
            
            if "answer" in result and "team_name" in result:
                log.info(f"LLM evaluation result: {result['answer']} for team {result['team_name']}")
                return result
            else:
                log.error(f"LLM response is missing required keys: {raw_response_text}")
                return None
        except json.JSONDecodeError as e:
            log.error(f"Failed to decode LLM JSON response: {e}")
            log.error(f"Raw response was: {raw_response_text}")
            return None
        except Exception as e:
            log.error(f"Failed to evaluate answer with LLM: {e}")
            log.error(traceback.format_exc())
            return None

# Global instance
llm = LLMEvaluator()
