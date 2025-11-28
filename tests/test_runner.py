"""
test_runner.py
--------------
A data-driven test runner for the StateMachine.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from state_machine import StateMachine
from config import *

SCENARIOS_FILE = os.path.join(os.path.dirname(__file__), 'test_scenarios.json')

STATE_MAP = {
    "STATE_WAITING_TOPIC": STATE_WAITING_TOPIC,
    "STATE_WAITING_TOPIC_INPUT": STATE_WAITING_TOPIC_INPUT,
    "STATE_WAITING_DIFFICULTY": STATE_WAITING_DIFFICULTY,
    "STATE_WAITING_DIFFICULTY_INPUT": STATE_WAITING_DIFFICULTY_INPUT,
    "STATE_QUESTION_ACTIVE": STATE_QUESTION_ACTIVE,
    "STATE_ANSWERING": STATE_ANSWERING,
    "STATE_WAITING_FOR_ANSWER": STATE_WAITING_FOR_ANSWER,
    "STATE_HINT_ACTIVE": STATE_HINT_ACTIVE,
    "STATE_ROUND_OVER": STATE_ROUND_OVER,
    "STATE_GAME_END": STATE_GAME_END,
    "STATE_GAME_OVER_WAITING_RESTART": STATE_GAME_OVER_WAITING_RESTART,
    "STATE_PAUSED": STATE_PAUSED,
}

class DataDrivenStateMachineTests(unittest.TestCase):

    def load_scenarios(self):
        with open(SCENARIOS_FILE, 'r') as f:
            return json.load(f)

    @patch('state_machine.os.path.exists')
    @patch('state_machine.tts', autospec=True)
    @patch('state_machine.llm', autospec=True)
    @patch('state_machine.stt', autospec=True)
    @patch('state_machine.audio', autospec=True)
    @patch('state_machine.Timer', autospec=True)
    def test_all_scenarios(self, MockTimer, MockAudio, MockStt, MockLlm, MockTts, MockPathExists):
        """
        This single test method iterates through all scenarios, using subtests
        to ensure mocks are reset and failures are reported independently.
        """
        scenarios = self.load_scenarios()

        for scenario in scenarios:
            with self.subTest(scenario['name']):
                # --- Setup for this specific sub-test ---
                sm = StateMachine()
                
                audio_play_calls = []
                path_to_key = {v: k for k, v in globals().items() if isinstance(v, str) and ('.wav' in v or '.mp3' in v)}
                
                def audio_side_effect(filepath, **kwargs):
                    key = path_to_key.get(filepath, f"DYNAMIC_AUDIO:{os.path.basename(filepath)}")
                    audio_play_calls.append(key)

                MockAudio.play.side_effect = audio_side_effect
                MockAudio.play_bg.side_effect = lambda path, **kwargs: audio_play_calls.append(path_to_key.get(path, path))
                MockAudio.stop_bg.side_effect = lambda: audio_play_calls.append("STOP_BG_MUSIC")

                MockTts.get_host_intro_audio.side_effect = lambda q_id: f"/mock/intro_{q_id}.wav"
                MockTts.get_question_audio.side_effect = lambda q_id: f"/mock/question_{q_id}.wav"
                MockTts.get_hint_audio.side_effect = lambda q_id, h_num: f"/mock/hint_{q_id}_{h_num}.wav"
                MockTts.get_answer_audio.side_effect = lambda q_id: f"/mock/answer_{q_id}.wav"
                MockTts.get_fun_fact_audio.side_effect = lambda q_id: f"/mock/fun_fact_{q_id}.wav"
                MockTts.get_greeting_audio.side_effect = lambda: "/mock/teams_greating.wav"
                MockTts.generate_sentence_async.side_effect = lambda text, filename: (os.path.join(TTS_OUTPUT_DIR, filename), MagicMock())

                stt_returns = [a.get('stt_return') for a in scenario['actions'] if 'stt_return' in a]
                llm_returns = [a.get('llm_eval') for a in scenario['actions'] if 'llm_eval' in a]
                MockStt.recognize_speech.side_effect = stt_returns
                MockLlm.evaluate_answer.side_effect = llm_returns
                
                if 'setup' in scenario:
                    for key, value in scenario['setup'].items():
                        setattr(sm, key, value)

                initial_state_name = scenario.get('initial_state')
                initial_state_value = STATE_MAP.get(initial_state_name)
                sm.set_state(initial_state_value)

                for action in scenario['actions']:
                    action_type = action.get('type')
                    if action_type == 'short_press':
                        sm.handle_short_press()
                    elif action_type == 'timer_expired':
                        if MockTimer.call_args:
                            timer_callback = MockTimer.call_args[0][1]
                            timer_callback()
                        else: self.fail("Test scenario requested 'timer_expired' but no timer was started.")
                    elif action_type == 'wait_for_async_tts':
                        MockPathExists.return_value = True
                        sm._handle_correct_answer()

                print(f"\\n--- Scenario: {scenario['name']} ---")
                
                expected_state_name = scenario['expected_final_state']
                expected_state_value = STATE_MAP.get(expected_state_name)
                print(f"Expected Final State: {expected_state_name} -> Actual: {sm.current_state}")
                self.assertEqual(sm.current_state, expected_state_value)
                
                expected_audio_keys = scenario.get('expected_audio_played', [])
                
                print(f"Expected Audio Played: {expected_audio_keys}")
                print(f"Actual Audio Played:   {audio_play_calls}")
                
                actual_set = set(audio_play_calls)
                expected_set = set(expected_audio_keys)
                self.assertTrue(expected_set.issubset(actual_set), f"Missing expected audio. Expected {expected_set}, but got {actual_set}")

                print("✅ Scenario Passed")

if __name__ == '__main__':
    unittest.main()
