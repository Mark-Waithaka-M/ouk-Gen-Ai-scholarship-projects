import random
import sqlite3
import time
import gradio as gr
import json
import requests
from typing import Dict, Any, List

# --- Global/API Configuration ---
API_KEY = ""
# Using standard model for structured/text generation
GEMINI_TEXT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"

# --- Database Management ---

def setup_database(db_name="guessing_game_results.db"):
    """
    Connects to the SQLite database and ensures the results table exists and has the necessary columns.
    Returns the connection object.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            timestamp DATETIME,
            correct_guesses INTEGER,
            total_attempts_used INTEGER,
            final_score INTEGER,
            win_status TEXT,
            difficulty_reached TEXT 
        )
    ''')
    conn.commit()
    return conn

# --- Game Persistence Base Class ---

class GamePersistence:
    """Handles saving results. Connection is established only at the point of saving."""
    def __init__(self, user_id):
        self.user_id = user_id

    def save_result(self, correct_guesses, total_attempts_used, final_score, win_status, difficulty_reached):
        """Saves the final game result by establishing a temporary connection."""
        try:
            db_conn = setup_database()
            cursor = db_conn.cursor()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

            cursor.execute('''
                INSERT INTO game_results (user_id, timestamp, correct_guesses, total_attempts_used, final_score, win_status, difficulty_reached)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.user_id, timestamp, correct_guesses, total_attempts_used, final_score, win_status, difficulty_reached))
            db_conn.commit()

            return f"\n--- Tournament Result Saved to Database ---\nResults for User {self.user_id} saved successfully at {timestamp}."
        except Exception as e:
            # Important: Log error but return a clean failure message
            print(f"Database Save Error: {e}")
            return f"\n--- WARNING: FAILED TO SAVE RESULT ---\nDatabase Error: Failed to connect or save result."
        finally:
            if 'db_conn' in locals() and db_conn:
                db_conn.close()

# --- Game Logic Class ---

class GuessingGame(GamePersistence):
    """Core logic for the enhanced number guessing game with dynamic difficulty and tournament mode."""

    DIFFICULTY_LEVELS = {
        "EASY": {"range": 20, "max_attempts": 5, "threshold": 2},
        "MEDIUM": {"range": 50, "max_attempts": 7, "threshold": 3},
        "HARD": {"range": 100, "max_attempts": 9, "threshold": 4},
        "EXPERT": {"range": 200, "max_attempts": 10, "threshold": 999}
    }

    def __init__(self, total_rounds=3):
        user_id = "anon_" + str(int(time.time()))
        super().__init__(user_id)

        self.game_running = True
        self.is_challenging = False
        self.challenge_target = None
        self.challenge_options = {}
        self.challenge_solution_key = None
        self.challenge_question = None

        self.total_rounds = total_rounds
        self.current_round = 1

        self.difficulty_level = "EASY"
        config = self.DIFFICULTY_LEVELS[self.difficulty_level]

        self.initial_attempts = config["max_attempts"]
        self.number_range = config["range"]
        self.remaining_attempts = self.initial_attempts
        self.correct_guesses_in_round = 0

        self.correct_streak = 0
        self.total_attempts_used = 0
        self.score = 0
        self.guess_history = [] # Stores {'guess': number, 'result': 'low'|'high'}

        self.correct_number = None
        self.generate_new_target()

    def generate_new_target(self):
        """Sets a new random target number based on the current range."""
        self.correct_number = random.randint(1, self.number_range)
        self.guess_history = [] # Clear history for new number

    def calculate_reward(self):
        """Dynamic Reward Network: Reward based on streak and difficulty level."""
        base_reward = 100
        difficulty_multiplier = self._get_difficulty_multiplier()
        streak_bonus = self.correct_streak * 0.20
        reward = int(base_reward * difficulty_multiplier * (1 + streak_bonus))
        self.score += reward
        return reward

    def _get_difficulty_multiplier(self):
        """Helper to get reward multiplier based on current difficulty."""
        if self.difficulty_level == "MEDIUM": return 1.5
        if self.difficulty_level == "HARD": return 2.5
        if self.difficulty_level == "EXPERT": return 4.0
        return 1.0

    def get_current_difficulty_config(self, level=None):
        """Returns the config for the current or specified difficulty level."""
        return self.DIFFICULTY_LEVELS.get(level or self.difficulty_level)

    def update_difficulty(self, check_threshold=True):
        """Checks if the player meets the threshold to advance to the next difficulty level."""
        level_keys = list(self.DIFFICULTY_LEVELS.keys())
        current_index = level_keys.index(self.difficulty_level)

        if current_index < len(level_keys) - 1:
            next_level_key = level_keys[current_index + 1]
            current_config = self.get_current_difficulty_config()

            if not check_threshold or self.correct_guesses_in_round >= current_config["threshold"]:
                self.difficulty_level = next_level_key
                next_config = self.get_current_difficulty_config(next_level_key)

                self.remaining_attempts = next_config["max_attempts"]
                self.number_range = next_config["range"]
                self.correct_guesses_in_round = 0

                return (
                    f"\n🎉 **DIFFICULTY UPGRADE!** Moving to **{self.difficulty_level}** (Range: 1-{self.number_range}). "
                    f"Attempts reset to {self.remaining_attempts}."
                )
        return ""

    def process_guess(self, guess):
        """Processes a single guess and updates game state."""
        # Returns: message, is_correct, is_game_over, is_challenging_return, challenge_target
        if not self.game_running or self.is_challenging:
            return (
                "Game Over or Challenge in Progress! Click 'Start New Game' or finish the Challenge.",
                False, False, False, None
            )

        self.total_attempts_used += 1

        if guess == self.correct_number:
            self.correct_guesses_in_round += 1
            self.correct_streak += 1
            self.remaining_attempts += 1

            reward_amount = self.calculate_reward()
            difficulty_message = self.update_difficulty()

            message = (
                f"🥳 **Correct!** Number was {self.correct_number}.\n"
                f"Streak: **{self.correct_streak}** (Reward: +{reward_amount} points | Total Score: **{self.score}**).\n"
                f"BONUS! Attempts +1. Current attempts left: **{self.remaining_attempts}**."
            )
            message += difficulty_message
            self.generate_new_target()
            message += f"\n--- New Target in range 1-{self.number_range} ---"
            return (message, True, False, False, None)

        else:
            self.remaining_attempts -= 1
            self.correct_streak = 0

            result_type = "high" if guess > self.correct_number else "low"
            self.guess_history.append({'guess': guess, 'result': result_type})

            message = "Too high!" if guess > self.correct_number else "Too low!"
            message += f"\nYour streak is broken. Attempts left: **{self.remaining_attempts}**."

            # TIE-BREAKER LOGIC: Challenge only on 0 attempts left
            if self.remaining_attempts <= 0:
                return self.round_failed()

            # If attempts > 0, proceed with the usual hint
            message += f"\nGuess again! Current range: 1-{self.number_range}."
            return (message, False, False, False, None)

    def round_failed(self):
        """Handles round failure, sets challenge mode, and saves the target."""
        self.is_challenging = True
        self.challenge_target = self.correct_number

        challenge_message = (
            f"⚠️ **ROUND FAILED!** You ran out of attempts. The number was hidden. "
            f"Before you can advance, you must pass the Game Master's **COMPUTATIONAL CHALLENGE**!"
        )
        return (
            challenge_message,
            False,
            False,
            True,
            self.challenge_target
        )

    def game_over(self):
        """Handles the end of the entire tournament and saves results."""
        self.game_running = False
        self.is_challenging = False # Ensure challenge is off

        win_status = "LOST"
        if self.difficulty_level in ["HARD", "EXPERT"] or self.score >= 500:
            win_status = "WON"

        db_message = super().save_result(
            self.correct_guesses_in_round,
            self.total_attempts_used,
            self.score,
            win_status,
            self.difficulty_level
        )

        final_message = (
            f"\n=============================================\n"
            f"🏆 **TOURNAMENT OVER** ({self.current_round}/{self.total_rounds} Rounds Completed) 🏆\n"
            f"Final Status: **{win_status}**.\n"
            f"Highest Difficulty Reached: **{self.difficulty_level}**.\n"
            f"Your Final Score: **{self.score} points**.\n"
            f"Total Guesses Made: {self.total_attempts_used}.\n"
            f"=============================================\n"
            f"{db_message}"
        )
        return (final_message, False, True, False, None)

# --- Serialization and Deserialization (No Change) ---

def serialize_game(game):
    """Serializes the game object to a JSON string for Gradio state management."""
    state = {
        'initial_attempts': game.initial_attempts, 'number_range': game.number_range,
        'remaining_attempts': game.remaining_attempts, 'correct_guesses_in_round': game.correct_guesses_in_round,
        'total_attempts_used': game.total_attempts_used, 'score': game.score,
        'game_running': game.game_running, 'correct_number': game.correct_number,
        'user_id': game.user_id, 'difficulty_level': game.difficulty_level,
        'correct_streak': game.correct_streak, 'total_rounds': game.total_rounds,
        'current_round': game.current_round, 'is_challenging': game.is_challenging,
        'challenge_target': game.challenge_target,
        'challenge_solution_key': game.challenge_solution_key,
        'challenge_question': game.challenge_question,
        'guess_history': game.guess_history
    }
    return json.dumps(state)

def deserialize_game(state_str):
    """Deserializes a JSON string back into a functional GuessingGame object."""
    state = json.loads(state_str)
    game = GuessingGame(total_rounds=state.get('total_rounds', 3))

    game.initial_attempts = state.get('initial_attempts', 5)
    game.number_range = state.get('number_range', 20)
    game.remaining_attempts = state.get('remaining_attempts', 5)
    game.correct_guesses_in_round = state.get('correct_guesses_in_round', 0)
    game.total_attempts_used = state.get('total_attempts_used', 0)
    game.score = state.get('score', 0)
    game.game_running = state.get('game_running', True)
    game.correct_number = state.get('correct_number', None)
    game.user_id = state.get('user_id', "anon_default")
    game.difficulty_level = state.get('difficulty_level', 'EASY')
    game.correct_streak = state.get('correct_streak', 0)
    game.current_round = state.get('current_round', 1)
    game.is_challenging = state.get('is_challenging', False)
    game.challenge_target = state.get('challenge_target', None)
    # challenge_options is regenerated dynamically, no need to store full options map
    game.challenge_solution_key = state.get('challenge_solution_key', None)
    game.challenge_question = state.get('challenge_question', None)
    game.guess_history = state.get('guess_history', [])

    return game

# --- Gemini API Functions (No Change) ---

def call_gemini_api(payload: Dict[str, Any]) -> str:
    """Helper function to make synchronous POST request to Gemini API with exponential backoff."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_TEXT_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=15
            )
            response.raise_for_status()

            result = response.json()

            # Extract text (standard and structured format)
            text_part = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0]
            text = text_part.get('text')

            if not text:
                 raise ValueError("Gemini response was empty or malformed.")

            return text.strip()

        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return json.dumps({"error": f"API request failed: {e}"})
        except Exception as e:
            return json.dumps({"error": f"General error: {e}"})

# --- Challenge Functions ---

def generate_challenge_and_options(target_number):
    """Generates a structured math challenge from Gemini."""

    # Simple deterministic way to generate distractors around the target
    option_b_val = target_number + random.randint(1, 3)
    option_c_val = target_number - random.randint(1, 3)
    while option_c_val <= 0 or option_c_val == option_b_val:
        option_c_val = target_number - random.randint(1, 3)

    options_list = [str(target_number), str(option_b_val), str(option_c_val)]
    random.shuffle(options_list)

    options_map = {
        "A": options_list[0],
        "B": options_list[1],
        "C": options_list[2]
    }

    correct_key = next(k for k, v in options_map.items() if v == str(target_number))


    prompt = (
        f"Create a single, simple math word problem for a high school student where the final, numerical answer "
        f"is exactly **{target_number}**. The problem should involve one or two basic geometric/arithmetic concepts. "
        f"Provide the problem and three multiple-choice options, which must be exactly: "
        f"A: {options_map['A']}, B: {options_map['B']}, C: {options_map['C']}. "
        f"The options should be presented as strings in the JSON."
    )

    schema = {
        "type": "OBJECT",
        "properties": {
            "question": {"type": "STRING", "description": "The math word problem."},
            "option_A": {"type": "STRING", "description": "The value of option A."},
            "option_B": {"type": "STRING", "description": "The value of option B."},
            "option_C": {"type": "STRING", "description": "The value of option C."},
            "correct_answer": {"type": "INTEGER", "description": "The numerical value of the correct answer."}
        },
        "required": ["question", "option_A", "option_B", "option_C", "correct_answer"]
    }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        },
        "systemInstruction": {"parts": [{"text": "You are a puzzle master, generating a challenging math problem in perfect JSON format."}]}
    }

    response_json_str = call_gemini_api(payload)

    try:
        data = json.loads(response_json_str)

        if "error" in data:
            raise ValueError(f"API failure detected: {data['error']}")

        if "question" in data:

            final_data = {
                "question": data["question"],
                "options": {
                    "A": data.get("option_A", options_map['A']),
                    "B": data.get("option_B", options_map['B']),
                    "C": data.get("option_C", options_map['C'])
                },
                "correct_key": correct_key
            }
            return final_data
        else:
            raise ValueError("Malformed or incorrect challenge data returned by Gemini.")

    except Exception as e:
        # Fallback challenge if Gemini fails or API request fails
        print(f"Gemini Challenge Generation Failed: {e}")
        return {
            "question": f"FALLBACK CHALLENGE (API OFFLINE - Solve for X): If X is the number you missed, what is X? (The number is {target_number})",
            "options": {
                "A": str(target_number),
                "B": str(target_number + 1),
                "C": str(target_number - 1 if target_number > 1 else 1)
            },
            "correct_key": "A"
        }

def start_challenge(game_state_str, challenge_target_int):
    """Initiates the challenge and prepares the UI."""
    game = deserialize_game(game_state_str)

    if challenge_target_int is None or not game.is_challenging:
        # This prevents UI freezing if triggered incorrectly
        return [
            game_state_str,
            gr.update(value="Challenge start error: Target not set or challenge state inactive.", visible=True),
            gr.update(interactive=False, choices=["A", "B", "C"], value=None),
            gr.update(interactive=False), # guess_input
            gr.update(interactive=False), # guess_btn
            gr.update(interactive=False), # challenge_submit_btn
            gr.update(visible=True), # challenge_area
            gr.update(interactive=False) # solver_btn
        ]

    target = int(challenge_target_int)
    challenge_data = generate_challenge_and_options(target)

    question = challenge_data["question"]
    options = challenge_data["options"]
    correct_key = challenge_data["correct_key"]

    keys = list(options.keys())
    random.shuffle(keys)

    # Store minimal data needed for submission
    game.challenge_solution_key = correct_key
    game.challenge_question = question

    choice_list = [f"**{k}**: {options[k]}" for k in keys]

    challenge_ui_markdown = f"""
    ### 🧠 Computational Challenge Active!
    **Solve this to proceed (The correct answer is the number you missed!):**
    
    ---
    
    {question}
    
    ---
    
    Choices:
    {choice_list[0]}
    {choice_list[1]}
    {choice_list[2]}
    """

    # Return game state and UI updates
    return [
        serialize_game(game),
        gr.update(value=challenge_ui_markdown, visible=True),
        gr.update(interactive=True, choices=keys, value=None), # challenge_radio
        gr.update(interactive=False, placeholder="Challenge in progress..."), # guess_input
        gr.update(interactive=False), # guess_btn
        gr.update(interactive=True), # challenge_submit_btn
        gr.update(visible=True), # challenge_area
        gr.update(interactive=True) # solver_btn
    ]

def submit_challenge(game_state_str, selected_option):
    """Validates the user's answer to the challenge."""
    # Returns 12 outputs: [game_state, feedback_output, current_score, attempts_left, range_status, round_status,
    # guess_input, challenge_area, guess_area, guess_btn, hint_btn, challenge_target_state]

    game = deserialize_game(game_state_str)

    if selected_option is None:
        return [
            game_state_str, gr.update(value="🛑 Please select an option (A, B, or C) before submitting."), gr.update(),
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        ]

    solution_value = game.challenge_target

    if selected_option == game.challenge_solution_key:
        # --- CHALLENGE SUCCESS PATH (Continue Game) ---
        game.is_challenging = False
        game.current_round += 1

        # Determine next difficulty/config
        level_keys = list(game.DIFFICULTY_LEVELS.keys())
        current_index = level_keys.index(game.difficulty_level)

        # Advance difficulty if possible
        if current_index < len(level_keys) - 1:
            next_level_key = level_keys[current_index + 1]
            game.difficulty_level = next_level_key
            next_config = game.get_current_difficulty_config(next_level_key)
        else:
            # Stay at max difficulty or current level
            next_config = game.get_current_difficulty_config()

        # Reset game variables for the new round
        game.remaining_attempts = next_config["max_attempts"]
        game.number_range = next_config["range"]
        game.correct_guesses_in_round = 0
        game.correct_streak = 0
        game.generate_new_target() # Generates the new number for the new round

        message = (
            f"✅ **CHALLENGE PASSED!** The number was **{solution_value}**.\n"
            f"Starting **ROUND {game.current_round}** of {game.total_rounds}."
        )
        message += f"\nDifficulty set to **{game.difficulty_level}** (Range: 1-{game.number_range}). Attempts reset to {game.remaining_attempts}."

        if game.current_round > game.total_rounds:
            final_message, _, _, _, _ = game.game_over()
            message = final_message

            # Disable all game elements (Game Over)
            return [
                serialize_game(game), gr.update(value=message), gr.update(value=game.score), gr.update(value=game.remaining_attempts),
                gr.update(value=f"1-{game.number_range}"), gr.update(value=f"Tournament Complete"),
                gr.update(interactive=False, placeholder="Game Over"),
                gr.update(visible=False), gr.update(visible=True),
                gr.update(interactive=False), gr.update(interactive=False), None
            ]

        # SUCCESS and continue game: CRITICAL STEP TO RE-ENABLE GUESSING
        return [
            serialize_game(game), gr.update(value=message), gr.update(value=game.score), gr.update(value=game.remaining_attempts),
            gr.update(value=f"1-{game.number_range}"), gr.update(value=f"Round {game.current_round}/{game.total_rounds}"),
            gr.update(interactive=True, placeholder=f"Type a whole number (1-{game.number_range})..."), # Re-enable
            gr.update(visible=False), gr.update(visible=True), # HIDE CHALLENGE, SHOW GUESS
            gr.update(interactive=True), gr.update(interactive=True), None # Re-enable Guess and Hint buttons
        ]
    else:
        # --- CHALLENGE FAILURE PATH (Game Over) ---
        message = (
            f"❌ **CHALLENGE FAILED!** You selected '{selected_option}'. "
            f"The correct answer (and the number you needed to guess) was **{solution_value}**. "
            f"The tournament is over."
        )
        final_message, _, is_game_over, _, _ = game.game_over()
        message += final_message

        # Disable all game elements
        return [
            serialize_game(game), gr.update(value=message), gr.update(value=game.score), gr.update(value=game.remaining_attempts),
            gr.update(value=f"1-{game.number_range}"), gr.update(value=f"Game Over"),
            gr.update(interactive=False, placeholder="Game Over"),
            gr.update(visible=False), gr.update(visible=True),
            gr.update(interactive=False), gr.update(interactive=False), None
        ]

def solve_challenge_with_gemini(game_state_str):
    """Provides a step-by-step solution breakdown for the current challenge for a point cost."""
    COST = 20
    game = deserialize_game(game_state_str)

    if game.score < COST:
        return [game_state_str, gr.update(value=game.score), "🛑 Insufficient score! You need 20 points to purchase the solution breakdown."]

    game.score -= COST

    question = game.challenge_question
    if not question:
        return [game_state_str, gr.update(value=game.score), gr.update(value="Error: No challenge question is currently active.")]

    prompt = f"The user needs help solving this math problem for a tie-breaker: '{question}'. Provide a brief, step-by-step mathematical solution that clearly shows the logic and the final answer. The final numerical answer must be clearly stated at the end."

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": "You are a patient, expert math tutor. Provide a clean, easy-to-read solution to the user's math problem. Use LaTeX for math notation."}]}
    }

    solution_text = call_gemini_api(payload)

    try:
        error_check = json.loads(solution_text)
        if 'error' in error_check:
            solution = f"Solution Error: Gemini API is offline. (-{COST} points lost)"
        else:
            solution = solution_text
    except json.JSONDecodeError:
        solution = solution_text

    message = f"🧠 **Challenge Solution Breakdown!** (-{COST} points)\n\n{solution}"

    return [
        serialize_game(game),
        gr.update(value=game.score),
        gr.update(value=message)
    ]

# --- Strategic Hint Function (Replaces Clue) ---

def get_strategic_hint(game_state_str):
    """Analyzes guess history and provides a strategic next guess from Gemini."""
    game = deserialize_game(game_state_str)
    COST = 50

    if game.is_challenging:
        return [game_state_str, gr.update(value=game.score), "Cannot request a strategic hint during a challenge."]

    if game.score < COST:
        return [game_state_str, gr.update(value=game.score), "🛑 Insufficient score! You need 50 points to purchase a strategic hint."]

    if len(game.guess_history) < 2:
        return [game_state_str, gr.update(value=game.score), "🤔 Not enough data! Make at least two guesses before asking for a strategic analysis."]

    game.score -= COST

    # 2. Prepare context for strategic hint
    history = game.guess_history
    current_low = 1
    current_high = game.number_range

    for entry in history:
        guess = entry['guess']
        result = entry['result']
        if result == 'low' and guess > current_low:
            current_low = guess
        elif result == 'high' and guess < current_high:
            current_high = guess

    history_summary = ", ".join([f"Guess {h['guess']} ({h['result']})" for h in history])

    # Highly specific prompt for optimal guess
    prompt = (
        f"The user is guessing a whole number between {current_low} and {current_high} (original range: 1-{game.number_range}). "
        f"The full guess history is: {history_summary}. "
        f"Based on the principle of binary search and probability simplification, provide a single, concrete number (an integer) that the user should try next. "
        f"Then, explain your choice in one sentence, following this format: 'The most appropriate next choice is [NUMBER] which centrally simplifies the probability because [REASON].' Do NOT include the brackets in the output. Your entire response must be a single strategic sentence."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": "You are a master strategist, providing precise, data-driven advice to minimize guesses."}]}
    }

    hint_text = call_gemini_api(payload)

    try:
        error_check = json.loads(hint_text)
        if 'error' in error_check:
            hint = f"Hint Error: Gemini API is offline. (-{COST} points lost)"
        else:
            hint = hint_text
    except json.JSONDecodeError:
        hint = hint_text

    message = f"🎯 **Strategic Hint Purchased!** (-{COST} points)\n\n{hint}\n\nAttempts left: **{game.remaining_attempts}**."

    return [
        serialize_game(game),
        gr.update(value=game.score),
        gr.update(value=message)
    ]

# --- Gemini Hint/Chat Function (General Chat) ---

def get_gemini_hint(game_state_str, chat_history: List[Dict[str, str]], user_question):
    """Generates a contextual hint or response from Gemini based on the user's question."""
    if not user_question:
        return chat_history, "", game_state_str

    game = deserialize_game(game_state_str)

    # Determine if the question is game-related
    is_game_strategy_question = any(keyword in user_question.lower() for keyword in ["guess", "number", "close", "range", "hint", "best"])

    if is_game_strategy_question:
        # Persona: Strategic Guide (more helpful, less cryptic)
        current_low = 1
        current_high = game.number_range
        for entry in game.guess_history:
            if entry['result'] == 'low' and entry['guess'] > current_low: current_low = entry['guess']
            elif entry['result'] == 'high' and entry['guess'] < current_high: current_high = entry['guess']

        game_context = (
            f"The user is currently in a game where the target is between {current_low} and {current_high}. "
            f"Attempts left: {game.remaining_attempts}. "
            f"The player's specific question is: '{user_question}'"
        )
        system_prompt = (
            "You are the **Strategic Game Guide**. You must provide a single, highly relevant, and encouraging tip that directs the player's thinking without giving away the exact answer. "
            "Suggest a general strategy or narrow the range. Keep the answer to 1-2 sentences."
        )
    else:
        # Persona: Game Master Oracle (for generic/off-topic questions)
        game_context = f"The player's non-game related question is: '{user_question}'"
        system_prompt = (
            "You are the **enigmatic Game Master Oracle**. Your responses must be cryptic, encouraging, "
            "and avoid directly revealing the target number. If the user asks a non-game related question, answer it in character as a mysterious guide. Keep your answer brief (1-2 sentences)."
        )

    # Format chat history for context (Gradio type='messages' is Dict[str, str])
    history_parts = [{"role": entry['role'], "parts": [{"text": entry['content']}]} for entry in chat_history]

    payload = {
        "contents": history_parts + [{"role": "user", "parts": [{"text": game_context}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    gemini_response = call_gemini_api(payload)

    try:
        error_check = json.loads(gemini_response)
        if 'error' in error_check:
            hint = f"AI Oracle is resting. API Error: {error_check['error']}"
        else:
            hint = gemini_response
    except json.JSONDecodeError:
        hint = gemini_response

    # Update chat history (using type='messages' format)
    chat_history.append({"role": "user", "content": user_question})
    chat_history.append({"role": "assistant", "content": hint})

    return chat_history, "", game_state_str

# --- Gradio Handler Functions ---

def toggle_calculator_visibility(is_visible):
    """Toggles the visibility of the calculator group."""
    new_visibility = not is_visible
    # Only two outputs are needed: the new state and the button text
    return new_visibility, gr.update(value="Hide Calculator" if new_visibility else "Show Calculator")

def initialize_game():
    """Initializes a new game instance."""
    db_conn = setup_database()
    db_conn.close()

    new_game = GuessingGame(total_rounds=3)

    initial_message = (
        f"**TOURNAMENT STARTED!** (Round {new_game.current_round} of {new_game.total_rounds})\n"
        f"Difficulty: **{new_game.difficulty_level}** (Range: 1-{new_game.number_range}).\n"
        f"You have **{new_game.remaining_attempts}** attempts to progress."
    )
    # Return 13 values to match outputs list
    return [
        serialize_game(new_game),
        initial_message,
        new_game.score,
        new_game.remaining_attempts,
        f"1-{new_game.number_range}",
        f"Round {new_game.current_round}/{new_game.total_rounds}",
        gr.update(interactive=True, placeholder=f"Type a whole number (1-{new_game.number_range})..."),
        [], # chat_history (Empty list)
        gr.update(visible=False), # challenge_area (Hide challenge)
        gr.update(visible=True), # guess_area (Show guess)
        gr.update(interactive=True), # guess_btn
        gr.update(interactive=True), # hint_btn
        None, # challenge_target_state (Clear target)
        False # calculator_visible_state (Initial state: Hidden)
    ]

def handle_guess(game_state_str, guess_input):
    """Gradio handler for user guesses."""
    # Returns 12 outputs: [game_state, feedback_output, current_score, attempts_left, range_status, round_status,
    # guess_input, challenge_area, guess_area, guess_btn, hint_btn, challenge_target_state]

    game = deserialize_game(game_state_str)

    try:
        guess = int(guess_input)
        if not 1 <= guess <= game.number_range:
             message = f"🛑 Input out of range: Please enter a whole number between 1 and {game.number_range}."
             # IMPORTANT: If input is invalid, ensure controls remain active to prevent freezing
             return [
                 serialize_game(game), message, game.score, game.remaining_attempts,
                 f"1-{game.number_range}", f"Round {game.current_round}/{game.total_rounds}",
                 gr.update(interactive=True, placeholder=f"Type a whole number (1-{game.number_range})..."),
                 gr.update(visible=game.is_challenging), gr.update(visible=not game.is_challenging),
                 gr.update(interactive=True), gr.update(interactive=True), game.challenge_target
             ]
    except ValueError:
        message = "🛑 Invalid input: Please enter a whole number."
        # IMPORTANT: If input is invalid, ensure controls remain active to prevent freezing
        return [
            serialize_game(game), message, game.score, game.remaining_attempts,
            f"1-{game.number_range}", f"Round {game.current_round}/{game.total_rounds}",
            gr.update(interactive=True, placeholder=f"Type a whole number (1-{game.number_range})..."),
            gr.update(visible=game.is_challenging), gr.update(visible=not game.is_challenging),
            gr.update(interactive=True), gr.update(interactive=True), game.challenge_target
        ]

    # Returns: message, is_correct, is_game_over, is_challenging_return, challenge_target
    result = game.process_guess(guess)
    message, is_correct, is_game_over, is_challenging_return, challenge_target = result


    # State flags based on the result
    guess_input_interactive = not is_game_over and not is_challenging_return
    guess_btn_interactive = not is_game_over and not is_challenging_return
    hint_interactive = not is_challenging_return and not is_game_over
    challenge_area_visible_flag = is_challenging_return
    guess_area_visible_flag = not is_challenging_return


    # Return 12 values to match outputs list
    return [
        serialize_game(game),
        message,
        game.score,
        game.remaining_attempts,
        f"1-{game.number_range}",
        f"Round {game.current_round}/{game.total_rounds}",
        gr.update(interactive=guess_input_interactive, placeholder=f"Type a whole number (1-{game.number_range})..."),
        gr.update(visible=challenge_area_visible_flag), # challenge_area
        gr.update(visible=guess_area_visible_flag),    # guess_area
        gr.update(interactive=guess_btn_interactive), # guess_btn
        gr.update(interactive=hint_interactive), # hint_btn
        challenge_target # Pass the value, not the State object.
    ]


# --- Gradio Interface Layout ---

custom_css = """
body { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }
.gradio-container { max-width: 1200px; margin: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); background-color: #161b22; }
h1 { color: #58a6ff; text-align: center; padding-top: 10px; }
.status-box, .stat-item { background-color: #21262d; border-radius: 8px; padding: 10px; margin: 5px; font-size: 1.1em; border: 1px solid #30363d; }
.stat-item strong { color: #79c0ff; }
.feedback-box { background-color: #0c1a2c; border: 2px solid #58a6ff; border-radius: 8px; padding: 15px; min-height: 150px; overflow-y: auto; }
.gradio-btn-primary { background-color: #238636; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
.gradio-input-text { border: 1px solid #30363d !important; background-color: #0d1117 !important; color: #c9d1d9 !important; }

/* CALCULATOR CSS (simplified positioning) */
.calculator-group {
    padding: 10px;
}
.calculator-pad {
    background-color: #333;
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    width: 250px;
    margin: 10px auto; 
}
.calc-display {
    background-color: #444;
    color: white;
    padding: 10px;
    text-align: right;
    font-size: 1.5em;
    border-radius: 5px;
    margin-bottom: 10px;
    min-height: 40px; 
}
.calc-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 5px;
}
.calc-button {
    background-color: #555;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 15px 0;
    font-size: 1.1em;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.calc-button:hover {
    background-color: #666;
}
.calc-op {
    background-color: #ff9500;
}
.calc-op:hover {
    background-color: #e08500;
}
.calc-clear {
    background-color: #aaa;
    color: #333;
}
.calc-clear:hover {
    background-color: #999;
}
"""

# Simple Calculator JavaScript (for client-side function)
# FIX: Using class selectors for robustness inside Gradio's structure
calculator_js = """
let currentInput = '0';
let previousInput = null;
let operation = null;
let pendingReset = false;

function updateDisplay() {
    const display = document.querySelector('#calc-display'); 
    if (display) {
        // Limit display length to avoid overflow
        display.textContent = currentInput.substring(0, 15); 
    }
}

function handleNumber(number) {
    if (pendingReset) {
        currentInput = '0';
        pendingReset = false;
    }
    
    if (currentInput === '0' && number !== '.') {
        currentInput = number;
    } else if (number === '.' && currentInput.includes('.')) {
        return;
    } else if (currentInput.length < 15) { // Prevent excessive input
        currentInput += number;
    }
}

function handleOperator(nextOperator) {
    if (previousInput === null) {
        previousInput = parseFloat(currentInput);
    } else if (operation) {
        const result = performCalculation();
        currentInput = String(result);
        previousInput = result;
    }
    operation = nextOperator;
    pendingReset = true; 
}

function performCalculation() {
    const current = parseFloat(currentInput);
    const previous = previousInput;
    
    if (isNaN(current) || isNaN(previous)) return current;
    
    if (operation === '+') return previous + current;
    if (operation === '-') return previous - current;
    if (operation === '*') return previous * current;
    if (operation === '/') {
        if (current === 0) return NaN; // Division by zero
        return previous / current;
    }
    
    return current;
}

function handleEquals() {
    if (operation) {
        let result = performCalculation();
        if (isNaN(result) || !isFinite(result)) {
            currentInput = 'Error';
        } else {
            // Round to a few decimal places to avoid floating point issues
            currentInput = String(Math.round(result * 10000000) / 10000000); 
        }
        previousInput = null;
        operation = null;
        pendingReset = true;
    }
}

function setupCalculator() {
    // FIX: Using querySelectorAll with a class to find buttons reliably
    const buttons = document.querySelectorAll('.calc-button'); 
    buttons.forEach(button => {
        // Defensive: clear old listeners before adding new ones
        button.onclick = null; 
        
        button.addEventListener('click', () => {
            const value = button.textContent;
            
            if (button.classList.contains('calc-num') || value === '.') {
                handleNumber(value);
            } else if (value === 'C') {
                currentInput = '0';
                previousInput = null;
                operation = null;
                pendingReset = false;
            } else if (value === '±') {
                const num = parseFloat(currentInput);
                if (!isNaN(num)) currentInput = String(-num);
            } else if (value === '%') {
                const num = parseFloat(currentInput);
                if (!isNaN(num)) currentInput = String(num / 100);
            } else if (value === '=') {
                handleEquals();
            } else if (button.classList.contains('calc-op')) {
                handleOperator(value);
            }
            updateDisplay();
        });
    });
    updateDisplay();
}

// Ensure setup runs after Gradio has injected the HTML
setTimeout(setupCalculator, 500); 
"""

with gr.Blocks(css=custom_css, title="Enhanced Guessing Game Tournament") as demo:
    gr.HTML("<h1 style='color: #58a6ff;'>🏆 The Enhanced Guessing Game Tournament 🏆</h1>")

    game_state = gr.State(value=serialize_game(GuessingGame(total_rounds=3)))
    challenge_target_state = gr.State(value=None)
    calculator_visible_state = gr.State(value=False) # State for calculator visibility

    # ------------------ Main Layout ------------------

    with gr.Row():
        with gr.Column(scale=2):
            with gr.Group(elem_classes="status-box"):
                gr.Markdown(
                    """
                    ### 📜 Tournament Rules
                    1. The goal is to survive all rounds and reach the highest difficulty.
                    2. Correct guesses earn points, increase your streak, and give a **BONUS ATTEMPT**!
                    3. Run out of attempts? You face a **COMPUTATIONAL CHALLENGE** to continue (the tie-breaker).
                    4. Spend **50 points** for a **Strategic Hint** (AI analysis of your best next guess).
                    """
                )

        with gr.Column(scale=1):
            with gr.Group(elem_classes="status-box"):
                gr.Markdown("### 📊 Game Status")
                current_score = gr.Number(label="Current Score", value=0, interactive=False, elem_classes="stat-item")
                attempts_left = gr.Number(label="Attempts Left", value=5, interactive=False, elem_classes="stat-item")

                with gr.Row():
                    range_status = gr.Textbox(label="Current Range", value="1-20", interactive=False, elem_classes="stat-item")
                    round_status = gr.Textbox(label="Tournament Status", value="Round 1/3", interactive=False, elem_classes="stat-item")

            new_game_btn = gr.Button("Start New Tournament (3 Rounds)", variant="primary", elem_classes="gradio-btn-primary")

    # ------------------ Calculator UI (Fixed - relies on toggle_calculator_visibility) ------------------

    with gr.Group(visible=False, elem_classes="calculator-group") as calculator_group:
        gr.HTML(
            f"""
            <div class="calculator-pad">
                <div id="calc-display" class="calc-display">0</div>
                <div class="calc-grid">
                    <button class="calc-button calc-clear">C</button>
                    <button class="calc-button calc-op">±</button>
                    <button class="calc-button calc-op">%</button>
                    <button class="calc-button calc-op">/</button>
                    <button class="calc-button calc-num">7</button>
                    <button class="calc-button calc-num">8</button>
                    <button class="calc-button calc-num">9</button>
                    <button class="calc-button calc-op">*</button>
                    <button class="calc-button calc-num">4</button>
                    <button class="calc-button calc-num">5</button>
                    <button class="calc-button calc-num">6</button>
                    <button class="calc-button calc-op">-</button>
                    <button class="calc-button calc-num">1</button>
                    <button class="calc-button calc-num">2</button>
                    <button class="calc-button calc-num">3</button>
                    <button class="calc-button calc-op">+</button>
                    <button class="calc-button calc-num" style="grid-column: span 2">0</button>
                    <button class="calc-button calc-num">.</button>
                    <button class="calc-button calc-op">=</button>
                </div>
            </div>
            <script>{calculator_js}</script>
            """
        )

    # ------------------ Game / Challenge Interface ------------------

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Game Feedback Console")
            feedback_output = gr.Markdown(
                label="Game Messages",
                value="Click 'Start New Tournament' to begin your challenge!",
                elem_classes="feedback-box",
                container=True
            )

            # Area for standard guessing (Visible by default)
            with gr.Group(visible=True) as guess_area:
                with gr.Row():
                    guess_input = gr.Textbox(
                        label="Enter your guess",
                        placeholder="Type a whole number (1-20)...",
                        interactive=False,
                        elem_classes="gradio-input-text"
                    )
                    guess_btn = gr.Button("Submit Guess", variant="secondary", interactive=False)
                # Strategic Hint Button
                hint_btn = gr.Button("🎯 Get Strategic Hint (50 Pts)", interactive=False)

            # Area for challenge (Hidden by default)
            with gr.Group(visible=False) as challenge_area:
                challenge_markdown = gr.Markdown("Challenge loading...")
                challenge_radio = gr.Radio(label="Select Your Answer", interactive=False, choices=["A", "B", "C"])
                challenge_submit_btn = gr.Button("Submit Challenge Answer", variant="primary", interactive=False)
                # Solver Button
                solver_btn = gr.Button("🧠 Ask AI for Solution Breakdown (20 Pts)", interactive=False)

        # AI Chat/Hint Interface
        with gr.Column(scale=1):
            gr.Markdown("### 🤖 Game Master AI Chat")
            chat_history = gr.Chatbot(label="Game Master", height=300, type='messages')
            chat_input = gr.Textbox(
                label="Ask for a hint or chat!",
                placeholder="e.g., 'Am I close?' or 'Tell me a joke.'",
                elem_classes="gradio-input-text"
            )
            chat_submit_btn = gr.Button("Get Chat Response", variant="tertiary")

            # Calculator Button (Controls visibility of the calculator_group)
            calc_toggle_btn = gr.Button("Show Calculator", variant="secondary", size="sm")

    # --- Component Interactions ---

    # 1. Toggle Calculator
    calc_toggle_btn.click(
        fn=toggle_calculator_visibility,
        inputs=[calculator_visible_state],
        outputs=[calculator_visible_state, calc_toggle_btn],
        queue=False
    ).then(
        None,
        inputs=[calculator_visible_state],
        outputs=[calculator_group],
        # Direct Gradio visibility update
        queue=False,
        js="""(is_visible) => {
            const group = document.querySelector('.calculator-group');
            if (group) {
                group.style.display = is_visible ? 'block' : 'none';
            }
        }"""
    )


    # 2. Start New Game
    new_game_btn.click(
        fn=initialize_game,
        inputs=[],
        outputs=[
            game_state, feedback_output, current_score, attempts_left, range_status,
            round_status, guess_input, chat_history, challenge_area, guess_area,
            guess_btn, hint_btn, challenge_target_state, calculator_visible_state
        ]
    )

    # 3. Handle Guess
    guess_btn.click(
        fn=handle_guess,
        inputs=[game_state, guess_input],
        outputs=[
            game_state, feedback_output, current_score, attempts_left, range_status,
            round_status, guess_input, challenge_area, guess_area, guess_btn, hint_btn, challenge_target_state
        ]
    )
    guess_input.submit(
        fn=handle_guess,
        inputs=[game_state, guess_input],
        outputs=[
            game_state, feedback_output, current_score, attempts_left, range_status,
            round_status, guess_input, challenge_area, guess_area, guess_btn, hint_btn, challenge_target_state
        ]
    )

    # 4. Handle Challenge Trigger
    challenge_target_state.change(
        fn=start_challenge,
        inputs=[game_state, challenge_target_state],
        outputs=[
            game_state, challenge_markdown, challenge_radio, guess_input, guess_btn, challenge_submit_btn, challenge_area, solver_btn
        ],
        queue=False
    )

    # 5. Handle Challenge Submission
    challenge_submit_btn.click(
        fn=submit_challenge,
        inputs=[game_state, challenge_radio],
        outputs=[
            game_state, feedback_output, current_score, attempts_left, range_status, round_status,
            guess_input, challenge_area, guess_area, guess_btn, hint_btn, challenge_target_state
        ]
    )

    # 6. Handle Challenge Solver
    solver_btn.click(
        fn=solve_challenge_with_gemini,
        inputs=[game_state],
        outputs=[game_state, current_score, feedback_output]
    )

    # 7. Handle Chat/Hint (Improved Logic)
    chat_submit_btn.click(
        fn=get_gemini_hint,
        inputs=[game_state, chat_history, chat_input],
        outputs=[chat_history, chat_input, game_state],
        show_progress="full"
    )
    chat_input.submit(
        fn=get_gemini_hint,
        inputs=[game_state, chat_history, chat_input],
        outputs=[chat_history, chat_input, game_state],
        show_progress="full"
    )

    # 8. Handle Strategic Hint
    hint_btn.click(
        fn=get_strategic_hint,
        inputs=[game_state],
        outputs=[game_state, current_score, feedback_output]
    )

if __name__ == "__main__":
    demo.launch(share=True)
