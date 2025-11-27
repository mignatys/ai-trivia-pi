"""
llm_evaluator.py
----------------
Handles all interactions with the Gemini LLM, including generating game
questions and evaluating player answers.
"""

import google.generativeai as genai
import json
from logger import log
from config import GEMINI_API_KEY, QUESTION_PROMPT_FILE, ANSWER_PROMPT_FILE, GAME_QUESTIONS_FILE

class LLMEvaluator:
    """
    A wrapper for the Gemini API to handle prompt-based generation and evaluation.
    Uses a powerful model for question generation and a fast model for evaluation.
    """
    def __init__(self):
        if not GEMINI_API_KEY:
            log.error("GEMINI_API_KEY not found in environment variables. LLM evaluator will be disabled.")
            self.is_ready = False
            self.generation_model = None
            self.evaluation_model = None
            return

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # A powerful model for high-quality question generation
            self.generation_model_name = 'models/gemini-pro-latest'
            self.generation_model = genai.GenerativeModel(self.generation_model_name)
            log.info(f"Using '{self.generation_model_name}' for question generation.")

            # A fast model for low-latency answer evaluation
            self.evaluation_model_name = 'models/gemini-flash-latest'
            self.evaluation_model = genai.GenerativeModel(self.evaluation_model_name)
            log.info(f"Using '{self.evaluation_model_name}' for answer evaluation.")
            
            self.is_ready = True

        except Exception as e:
            log.error(f"An error occurred during Gemini initialization: {e}")
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
        Generates a new set of trivia questions using the powerful generation model.
        """
        if not self.is_ready:
            log.error("LLM is not ready. Cannot generate questions.")
            return False

        prompt_template = self._load_prompt(QUESTION_PROMPT_FILE)
        if not prompt_template:
            return False

        prompt = prompt_template.format(topic=topic, difficulty=difficulty, language=language)
        
        log.info("Generating new trivia questions from LLM...")
        try:
            response = self.generation_model.generate_content(prompt)
            log.debug(f"Raw LLM response (get_questions): {response.text}")

            cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            
            game_data = json.loads(cleaned_json)
            with open(GAME_QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=2, ensure_ascii=False)
            
            log.info(f"Successfully generated and saved new questions to {GAME_QUESTIONS_FILE}")
            return True
        except Exception as e:
            log.error(f"Failed to generate or save questions from LLM: {e}")
            return False

    def evaluate_answer(self, question, correct_answer, user_answer, team_names):
        """
        Evaluates a user's answer using the fast evaluation model.
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
            response = self.evaluation_model.generate_content(prompt)
            log.debug(f"Raw LLM response (evaluate_answer): {response.text}")

            cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_json)
            
            if "answer" in result and "team_name" in result:
                log.info(f"LLM evaluation result: {result['answer']} for team {result['team_name']}")
                return result
            else:
                log.error(f"LLM response is missing required keys: {response.text}")
                return None
        except Exception as e:
            log.error(f"Failed to evaluate answer with LLM: {e}")
            return None

# Global instance
llm = LLMEvaluator()
