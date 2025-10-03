import random
import sqlite3
import time
import gradio as gr
import json

# --- Global/API Configuration (Required for Gradio/LLM) ---
API_KEY = "" # Your API Key will be injected here
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"

# --- Database Management ---

def setup_database(db_name="guessing_game_results.db"):
    """
    Connects to the SQLite database and ensures the results table exists.
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

# --- Game Persistence Base Class (REFACTORED) ---

class GamePersistence:
    """Handles saving results. Connection is established only at the point of saving."""
    def __init__(self, user_id):
        # We no longer store the connection in the state to avoid blocking on deserialization
        self.user_id = user_id

    def save_result(self, correct_guesses, total_attempts_used, final_score, win_status, difficulty_reached):
        """Saves the final game result by establishing a temporary connection."""
        try:
            # Establish connection only when saving the final result (blocking operation)
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
            return f"\n--- WARNING: FAILED TO SAVE RESULT ---\nDatabase Error: {e}"
        finally:
            # Close the connection immediately after saving
            if 'db_conn' in locals() and db_conn:
                db_conn.close()


# --- Game Logic Class (REFACTORED __init__) ---

class GuessingGame(GamePersistence):
    """Core logic for the enhanced number guessing game with dynamic difficulty and tournament mode."""

    DIFFICULTY_LEVELS = {
        "EASY": {"range": 20, "max_attempts": 5, "threshold": 2},
        "MEDIUM": {"range": 50, "max_attempts": 7, "threshold": 3},
        "HARD": {"range": 100, "max_attempts": 9, "threshold": 4},
        "EXPERT": {"range": 200, "max_attempts": 10, "threshold": 999}
    }

    def __init__(self, total_rounds=3):
        # Initialize Persistence WITHOUT calling setup_database here!
        user_id = "anon_" + str(int(time.time()))
        super().__init__(user_id)

        # Tournament State
        self.total_rounds = total_rounds
        self.current_round = 1

        # Difficulty State
        self.difficulty_level = "EASY"
        config = self.DIFFICULTY_LEVELS[self.difficulty_level]

        # Core Game State
        self.initial_attempts = config["max_attempts"]
        self.number_range = config["range"]
        self.remaining_attempts = self.initial_attempts
        self.correct_guesses_in_round = 0

        # Reward Network / History State
        self.correct_streak = 0
        self.performance_history = []
        self.total_attempts_used = 0
        self.bonus_attempts_earned = 0
        self.score = 0

        self.game_running = True
        self.correct_number = None
        self.generate_new_target()

    def generate_new_target(self):
        """Sets a new random target number based on the current range."""
        self.correct_number = random.randint(1, self.number_range)

    def calculate_reward(self):
        """Dynamic Reward Network: Reward based on streak and difficulty level."""

        base_reward = 100
        difficulty_multiplier = self._get_difficulty_multiplier()

        # Streak bonus: 20% increase for each consecutive correct guess
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

    def update_difficulty(self):
        """Checks if the player meets the threshold to advance to the next difficulty level."""
        current_config = self.DIFFICULTY_LEVELS[self.difficulty_level]

        level_keys = list(self.DIFFICULTY_LEVELS.keys())
        current_index = level_keys.index(self.difficulty_level)

        if current_index < len(level_keys) - 1:
            next_level_key = level_keys[current_index + 1]

            # Check threshold
            if self.correct_guesses_in_round >= current_config["threshold"]:
                self.difficulty_level = next_level_key
                next_config = self.DIFFICULTY_LEVELS[next_level_key]

                # Reset round metrics and update game parameters
                self.remaining_attempts = next_config["max_attempts"]
                self.number_range = next_config["range"]
                self.correct_guesses_in_round = 0

                return (
                    f"\n🎉 **DIFFICULTY UPGRADE!** Moving to **{self.difficulty_level}** (Range: 1-{self.number_range}). "
                    f"Attempts reset to {self.remaining_attempts}."
                )
        return "" # No difficulty change

    def process_guess(self, guess):
        """Processes a single guess and updates game state."""
        if not self.game_running:
            return ("Tournament Over! Click 'Start New Game' to play again.", False, True)

        self.total_attempts_used += 1

        if guess == self.correct_number:
            # Correct Guess Logic
            self.correct_guesses_in_round += 1
            self.correct_streak += 1
            self.performance_history.append('win')
            self.remaining_attempts += 1 # Bonus attempt
            self.bonus_attempts_earned += 1

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
            return (message, True, False)

        else:
            # Incorrect Guess Logic
            self.remaining_attempts -= 1
            self.correct_streak = 0 # Reset streak on loss
            self.performance_history.append('loss')

            message = "Too high!" if guess > self.correct_number else "Too low!"
            message += f"\nYour streak is broken. Attempts left: **{self.remaining_attempts}**."

            if self.remaining_attempts <= 0:
                return self.round_over()

            return (message, False, False)

    def round_over(self):
        """Handles the transition between tournament rounds."""

        self.performance_history.append('round_end')

        if self.current_round < self.total_rounds:
            # Move to next round
            self.current_round += 1
            # Reset attempts to max for current difficulty level
            current_config = self.DIFFICULTY_LEVELS[self.difficulty_level]
            self.remaining_attempts = current_config["max_attempts"]
            self.correct_guesses_in_round = 0
            self.correct_streak = 0
            self.generate_new_target()

            round_message = (
                f"\n--- ROUND {self.current_round - 1} FAILED (Target was {self.correct_number}) ---\n"
                f"Starting **ROUND {self.current_round}** of {self.total_rounds}.\n"
                f"Difficulty: **{self.difficulty_level}** (Range: 1-{self.number_range}). Attempts reset to {self.remaining_attempts}."
            )
            return (round_message, False, False)
        else:
            # Tournament Over
            return self.game_over()

    def game_over(self):
        """Handles the end of the entire tournament and saves results."""
        self.game_running = False

        # Determine win status (e.g., reached HARD difficulty or score threshold)
        win_status = "LOST"
        if self.difficulty_level in ["HARD", "EXPERT"] or self.score >= 500:
            win_status = "WON"

        # The save_result function now handles its own connection/disconnection
        db_message = super().save_result(
            self.correct_guesses_in_round,
            self.total_attempts_used,
            self.score,
            win_status,
            self.difficulty_level
        )

        final_message = (
            f"\n=============================================\n"
            f"🏆 **TOURNAMENT OVER** ({self.total_rounds} Rounds Completed) 🏆\n"
            f"Final Status: **{win_status}**.\n"
            f"Highest Difficulty Reached: **{self.difficulty_level}**.\n"
            f"Your Final Score: **{self.score} points**.\n"
            f"Total Guesses Made: {self.total_attempts_used}.\n"
            f"=============================================\n"
            f"{db_message}"
        )
        return (final_message, False, True) # message, is_correct, is_game_over

# --- Gradio Utility Functions (FIXED ASYNCHRONOUS BLOCKING) ---

async def get_gemini_hint(game_state_str, chat_history, user_query):
    """Generates a contextual, engaging hint using the Gemini API."""

    if not user_query:
        return [chat_history, gr.update(value=''), game_state_str]

    chat_history.append({"role": "user", "content": user_query})

    game_data = json.loads(game_state_str)

    system_prompt = (
        "You are an energetic, slightly mysterious AI Game Master. Your responses should be encouraging, "
        "witty, and provide vague, thematic hints. DO NOT reveal the correct number. "
        "The user is in Round {current_round} of {total_rounds} at {difficulty} difficulty, "
        "guessing a number between 1 and {range}. They have {attempts} attempts left. "
        "Their current score is {score} and their current streak is {streak}. "
        "Keep your response concise, friendly, and fun (under 50 words)."
    ).format(
        current_round=game_data.get('current_round', 1),
        total_rounds=game_data.get('total_rounds', 3),
        difficulty=game_data.get('difficulty_level', 'EASY'),
        range=game_data.get('number_range', 20),
        attempts=game_data.get('remaining_attempts', 5),
        score=game_data.get('score', 0),
        streak=game_data.get('correct_streak', 0)
    )

    prompt = f"The user asked: '{user_query}'"

    # API Request Setup
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    # Removed synchronous time.sleep loop which was blocking the entire application
    try:
        # Use the environment's fetch capability
        response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if not response.ok:
            # Handle non-200 responses
            error_details = await response.text()
            raise Exception(f"API call failed with status: {response.status}. Details: {error_details}")

        result = await response.json()

        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "Hmm, the connection is static. Try guessing a number!")

        chat_history.append({"role": "assistant", "content": text})

        return [chat_history, gr.update(value=''), game_state_str]

    except Exception as e:
        # Handle exceptions gracefully
        print(f"Gemini API Error: {e}")
        bot_message = f"Apologies, the Game Master is currently offline due to a connection issue. Error: {e}"
        chat_history.append({"role": "assistant", "content": bot_message})
        return [chat_history, gr.update(value=''), game_state_str]


def serialize_game(game):
    """Serializes the game object to a JSON string for Gradio state management."""
    # We only serialize the necessary state variables
    state = {
        'initial_attempts': game.initial_attempts,
        'number_range': game.number_range,
        'remaining_attempts': game.remaining_attempts,
        'correct_guesses_in_round': game.correct_guesses_in_round,
        'total_attempts_used': game.total_attempts_used,
        'bonus_attempts_earned': game.bonus_attempts_earned,
        'score': game.score,
        'game_running': game.game_running,
        'correct_number': game.correct_number,
        'user_id': game.user_id,
        'difficulty_level': game.difficulty_level,
        'correct_streak': game.correct_streak,
        'performance_history': game.performance_history,
        'total_rounds': game.total_rounds,
        'current_round': game.current_round
    }
    return json.dumps(state)

def deserialize_game(state_str):
    """
    Deserializes a JSON string back into a functional GuessingGame object.
    Crucially, this uses the original GuessingGame constructor that NO LONGER
    calls a blocking database setup.
    """
    state = json.loads(state_str)

    # Create a dummy game instance
    # Note: We must pass total_rounds=state.get(...) because GuessingGame.__init__ requires it.
    game = GuessingGame(total_rounds=state.get('total_rounds', 3))

    # Overwrite state with saved values
    game.initial_attempts = state.get('initial_attempts', 5)
    game.number_range = state.get('number_range', 20)
    game.remaining_attempts = state.get('remaining_attempts', 5)
    game.correct_guesses_in_round = state.get('correct_guesses_in_round', 0)
    game.total_attempts_used = state.get('total_attempts_used', 0)
    game.bonus_attempts_earned = state.get('bonus_attempts_earned', 0)
    game.score = state.get('score', 0)
    game.game_running = state.get('game_running', True)
    game.correct_number = state.get('correct_number', None)
    game.user_id = state.get('user_id', "anon_default")

    game.difficulty_level = state.get('difficulty_level', 'EASY')
    game.correct_streak = state.get('correct_streak', 0)
    game.performance_history = state.get('performance_history', [])
    game.current_round = state.get('current_round', 1)

    return game

def initialize_game():
    """Initializes a new game instance and returns its serialized state."""
    # Ensure the DB table exists before starting the game
    # This is fine as it's only called once when the user clicks 'Start New Tournament'
    db_conn = setup_database()
    db_conn.close()

    new_game = GuessingGame(total_rounds=3) # Default 3 rounds

    initial_message = (
        f"**TOURNAMENT STARTED!** (Round {new_game.current_round} of {new_game.total_rounds})\n"
        f"Difficulty: **{new_game.difficulty_level}** (Range: 1-{new_game.number_range}).\n"
        f"You have **{new_game.remaining_attempts}** attempts to progress."
    )
    empty_chat = []
    return [
        serialize_game(new_game),
        initial_message,
        new_game.score,
        new_game.remaining_attempts,
        f"1-{new_game.number_range}",
        f"Round {new_game.current_round}/{new_game.total_rounds}",
        gr.update(interactive=True),
        empty_chat
    ]

def handle_guess(game_state_str, guess_input):
    """Gradio handler for user guesses."""
    game = deserialize_game(game_state_str)

    # Input validation
    try:
        guess = int(guess_input)
    except ValueError:
        message = "🛑 Invalid input: Please enter a whole number."
        return [game_state_str, message, game.score, game.remaining_attempts, f"1-{game.number_range}", f"Round {game.current_round}/{game.total_rounds}", gr.update(interactive=True)]

    if not game.game_running:
        message = "Tournament Over! Click 'Start New Game' to play again."
        return [game_state_str, message, game.score, game.remaining_attempts, f"1-{game.number_range}", f"Round {game.current_round}/{game.total_rounds}", gr.update(interactive=False)]

    if not (1 <= guess <= game.number_range):
        message = f"🛑 Input is out of range! Please enter a number between 1 and {game.number_range}."
        return [serialize_game(game), message, game.score, game.remaining_attempts, f"1-{game.number_range}", f"Round {game.current_round}/{game.total_rounds}", gr.update(interactive=True)]

    # Process the guess
    message, is_correct, is_game_over = game.process_guess(guess)

    # Determine interactivity based on game state
    input_interactive = not is_game_over

    # Update Gradio components
    return [
        serialize_game(game),
        message,
        game.score,
        game.remaining_attempts,
        f"1-{game.number_range}",
        f"Round {game.current_round}/{game.total_rounds}",
        gr.update(interactive=input_interactive)
    ]

# --- Gradio Interface Layout ---

custom_css = """
body {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117; 
    color: #c9d1d9; 
}
.gradio-container {
    max-width: 1200px;
    margin: auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    background-color: #161b22; 
}
h1 {
    color: #58a6ff; 
    text-align: center;
    padding-top: 10px;
}
.status-box, .stat-item {
    background-color: #21262d; 
    border-radius: 8px;
    padding: 10px;
    margin: 5px;
    font-size: 1.1em;
    border: 1px solid #30363d;
}
.stat-item strong {
    color: #79c0ff;
}
.feedback-box {
    background-color: #0c1a2c; 
    border: 2px solid #58a6ff;
    border-radius: 8px;
    padding: 15px;
    min-height: 150px;
    overflow-y: auto;
}
.gradio-btn-primary {
    background-color: #238636; 
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}
.gradio-input-text {
    border: 1px solid #30363d !important;
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
}
"""

with gr.Blocks(css=custom_css, title="Enhanced Guessing Game Tournament") as demo:
    gr.HTML("<h1 style='color: #58a6ff;'>🏆 The Enhanced Guessing Game Tournament 🏆</h1>")

    game_state = gr.State(value=serialize_game(GuessingGame(total_rounds=3)))

    with gr.Row():
        with gr.Column(scale=2):
            with gr.Group(elem_classes="status-box"):
                gr.Markdown(
                    """
                    ### 📜 Tournament Rules
                    1. The goal is to survive all rounds and reach the highest difficulty.
                    2. Correct guesses earn points, increase your streak, and give a **BONUS ATTEMPT**!
                    3. Reach a **correct guess threshold** to advance to the next **Difficulty Level** (EASY, MEDIUM, HARD, EXPERT).
                    4. Fail to progress before running out of attempts, and the round ends. Complete all rounds to finish the tournament!
                    5. Results are saved to a local SQLite database.
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

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Game Feedback Console")
            feedback_output = gr.Markdown(
                label="Game Messages",
                value="Click 'Start New Tournament' to begin your challenge!",
                elem_classes="feedback-box",
                container=True
            )

            with gr.Row():
                guess_input = gr.Textbox(
                    label="Enter your guess",
                    placeholder="Type a whole number (1-20)...",
                    interactive=False,
                    elem_classes="gradio-input-text"
                )
                guess_btn = gr.Button("Submit Guess", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### 🤖 Game Master AI Chat")
            chat_history = gr.Chatbot(label="Game Master", height=300, type='messages')
            chat_input = gr.Textbox(
                label="Ask for a hint or chat!",
                placeholder="e.g., 'Am I close?' or 'Tell me a joke.'",
                elem_classes="gradio-input-text"
            )
            chat_submit_btn = gr.Button("Get Hint", variant="tertiary")

    # --- Component Interactions ---

    new_game_btn.click(
        fn=initialize_game,
        inputs=[],
        outputs=[game_state, feedback_output, current_score, attempts_left, range_status, round_status, guess_input, chat_history]
    )

    guess_btn.click(
        fn=handle_guess,
        inputs=[game_state, guess_input],
        outputs=[game_state, feedback_output, current_score, attempts_left, range_status, round_status, guess_input]
    )
    guess_input.submit(
        fn=handle_guess,
        inputs=[game_state, guess_input],
        outputs=[game_state, feedback_output, current_score, attempts_left, range_status, round_status, guess_input]
    )

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

# --- Server Startup ---

if __name__ == "__main__":
    demo.launch(share=True)