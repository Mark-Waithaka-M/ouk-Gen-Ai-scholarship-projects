"""Gradio Dashboard for Enhanced Guessing Game"""

import gradio as gr
import sqlite3
import uuid
from datetime import datetime
import math
import random

# Global variables
current_session_id = None
game_state = {
    "correct_number": None,
    "trials_used": 0,
    "bonus_trials": 0,
    "total_score": 0,
    "consecutive_correct": 0,
    "current_range": (1, 20),
    "max_trials": 3,
    "level": 1,
    "game_active": False,
    "tiebreaker_active": False,
    "tiebreaker_answer": None,
    "tiebreaker_question": None
}

# Database connection
def get_db_connection():
    return sqlite3.connect('guess_game_history.db', check_same_thread=False)

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            level INTEGER,
            guess INTEGER,
            correct_number INTEGER,
            result TEXT,
            hint TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jokes_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            joke_text TEXT,
            is_funny BOOLEAN,
            is_repeated BOOLEAN,
            gemini_response TEXT,
            accepted_as_guess BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

def start_new_game():
    """Start a new game session"""
    global current_session_id, game_state

    current_session_id = str(uuid.uuid4())
    game_state = {
        "correct_number": random.randint(1, 20),
        "trials_used": 0,
        "bonus_trials": 0,
        "total_score": 0,
        "consecutive_correct": 0,
        "current_range": (1, 20),
        "max_trials": 3,
        "level": 1,
        "game_active": True,
        "tiebreaker_active": False,
        "tiebreaker_answer": None,
        "tiebreaker_question": None
    }

    return (
        f"🎮 New Game Started!\n\nSession ID: {current_session_id[:8]}...\n"
        f"Level: {game_state['level']}\n"
        f"Range: {game_state['current_range'][0]} - {game_state['current_range'][1]}\n"
        f"Trials: {game_state['max_trials'] + game_state['bonus_trials']}\n\n"
        f"Good luck! 🍀",
        None,  # Clear calculator
        []   # Clear chat
    )

def generate_hint(guess, correct):
    """Generate a creative hint"""
    diff = abs(guess - correct)
    if diff <= 2:
        return "🔥 You're burning hot! So close!"
    elif diff <= 5:
        return "☀️ Getting warm! You're on the right track."
    elif diff <= 10:
        return "❄️ A bit chilly. Try adjusting your guess."
    else:
        return "🧊 Ice cold! You're quite far off."

def trigger_tiebreaker():
    """Generate and trigger a tiebreaker question"""
    global game_state

    game_state["tiebreaker_active"] = True
    target = game_state["correct_number"]

    # Generate a math problem that results in the target number
    problem_types = ["perimeter", "area_to_width", "simple_equation"]
    problem_type = random.choice(problem_types)

    if problem_type == "perimeter":
        length = random.randint(3, 10)
        width = max(1, target // 2 - length)
        game_state["tiebreaker_answer"] = 2 * (length + width)
        game_state["tiebreaker_question"] = (
            f"A farmer is building a rectangular shed with length {length}m and width {width}m. "
            f"What is the perimeter in meters?"
        )
    elif problem_type == "area_to_width":
        length = random.randint(2, 5)
        area = target * length
        game_state["tiebreaker_answer"] = target
        game_state["tiebreaker_question"] = (
            f"A rectangle has an area of {area} m² and a length of {length}m. "
            f"What is the width in meters?"
        )
    else:
        a = random.randint(2, 5)
        b = random.randint(1, 10)
        result = a * target + b
        game_state["tiebreaker_answer"] = target
        game_state["tiebreaker_question"] = (
            f"Solve for x: {a}x + {b} = {result}"
        )

    return (
        f"\n\n⚡ TIEBREAKER TIME! ⚡\n"
        f"Solve this problem to continue:\n\n"
        f"📝 {game_state['tiebreaker_question']}\n\n"
        f"Use the calculator below or ask Gemini for help!"
    )

def submit_guess(guess_input):
    """Process a guess submission"""
    global game_state

    if not game_state["game_active"]:
        return "⚠️ Please start a new game first!", None

    if game_state["tiebreaker_active"]:
        return "⚡ Complete the tiebreaker first!", None

    try:
        guess = int(guess_input)
    except (ValueError, TypeError):
        return "❌ Please enter a valid number!", None

    min_range, max_range = game_state["current_range"]

    if guess < min_range or guess > max_range:
        return f"❌ Please guess between {min_range} and {max_range}!", None

    game_state["trials_used"] += 1
    max_trials = game_state["max_trials"] + game_state["bonus_trials"]

    # Log to database
    conn = get_db_connection()
    cursor = conn.cursor()

    feedback = ""

    if guess < game_state["correct_number"]:
        hint = generate_hint(guess, game_state["correct_number"])
        result = "too_low"
        feedback = (
            f"📊 Trial {game_state['trials_used']}/{max_trials}\n\n"
            f"Your guess: {guess}\n"
            f"Result: ⬇️ Too Low!\n\n"
            f"{hint}\n\n"
            f"💡 Tip: The number is higher than {guess}"
        )

        cursor.execute('''
            INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, game_state['level'], guess,
              game_state['correct_number'], result, hint))

        if game_state["trials_used"] >= max_trials:
            feedback += f"\n\n❌ GAME OVER!\nYou've used all {max_trials} trials."
            feedback += trigger_tiebreaker()

    elif guess > game_state["correct_number"]:
        hint = generate_hint(guess, game_state["correct_number"])
        result = "too_high"
        feedback = (
            f"📊 Trial {game_state['trials_used']}/{max_trials}\n\n"
            f"Your guess: {guess}\n"
            f"Result: ⬆️ Too High!\n\n"
            f"{hint}\n\n"
            f"💡 Tip: The number is lower than {guess}"
        )

        cursor.execute('''
            INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, game_state['level'], guess,
              game_state['correct_number'], result, hint))

        if game_state["trials_used"] >= max_trials:
            feedback += f"\n\n❌ GAME OVER!\nYou've used all {max_trials} trials."
            feedback += trigger_tiebreaker()

    else:  # Correct guess!
        result = "correct"
        game_state["bonus_trials"] += 1
        game_state["consecutive_correct"] += 1

        score_gained = max(100 - (game_state['trials_used'] * 10), 10)
        game_state["total_score"] += score_gained

        feedback = (
            f"🎉 CONGRATULATIONS! 🎉\n\n"
            f"You guessed correctly on trial {game_state['trials_used']}!\n\n"
            f"✨ Bonus: +1 trial!\n"
            f"You now have {game_state['max_trials'] + game_state['bonus_trials']} trials.\n\n"
            f"💰 Score: +{score_gained} points\n"
            f"📈 Total Score: {game_state['total_score']}\n"
            f"🔥 Streak: {game_state['consecutive_correct']} correct in a row"
        )

        if game_state["consecutive_correct"] == 3:
            feedback += "\n\n🎊 3 IN A ROW BONUS! +50 points!"
            game_state["total_score"] += 50

        cursor.execute('''
            INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, game_state['level'], guess,
              game_state['correct_number'], result, "Success!"))

        # Start new round
        game_state["correct_number"] = random.randint(min_range, max_range)
        game_state["trials_used"] = 0

        feedback += (
            f"\n\n🎮 NEW ROUND STARTED!\n"
            f"Guess a number between {min_range} and {max_range}"
        )

    conn.commit()
    conn.close()

    return feedback, None

def submit_tiebreaker(answer_input, use_ai_help):
    """Process tiebreaker answer"""
    global game_state

    if not game_state["tiebreaker_active"]:
        return "⚠️ No active tiebreaker!", None

    try:
        user_answer = float(answer_input)
    except (ValueError, TypeError):
        return "❌ Please enter a valid number!", None

    correct_answer = game_state["tiebreaker_answer"]
    tolerance = 0.01
    is_correct = abs(user_answer - correct_answer) < tolerance

    feedback = f"Question: {game_state['tiebreaker_question']}\n\n"
    feedback += f"Your answer: {user_answer}\n"
    feedback += f"Correct answer: {correct_answer}\n\n"

    if use_ai_help:
        feedback += "⚠️ AI help used: -20 points\n"
        game_state["total_score"] = max(0, game_state["total_score"] - 20)

    if is_correct:
        feedback += (
            "✅ CORRECT! You've won the tiebreaker!\n\n"
            "Your trials have been refilled!\n"
            f"New trials: {game_state['max_trials'] + game_state['bonus_trials'] + 1}"
        )
        game_state["tiebreaker_active"] = False
        game_state["trials_used"] = 0
        game_state["bonus_trials"] += 1
        game_state["game_active"] = True

    else:
        feedback += (
            f"❌ INCORRECT!\n\n"
            f"📊 FINAL GAME SUMMARY:\n"
            f"Total Score: {game_state['total_score']}\n"
            f"Consecutive Correct: {game_state['consecutive_correct']}\n"
            f"Level Reached: {game_state['level']}\n\n"
            f"Thanks for playing!"
        )
        game_state["game_active"] = False
        game_state["tiebreaker_active"] = False

    return feedback, None

def handle_joke_submission(joke_text, context):
    """Handle joke submissions as alternative to guessing"""
    global game_state, current_session_id

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if joke has been told before
    cursor.execute('''
        SELECT joke_text FROM jokes_history WHERE session_id = ?
    ''', (current_session_id,))
    previous_jokes = cursor.fetchall()

    is_repeated = False
    for (prev_joke,) in previous_jokes:
        prev_words = set(prev_joke.lower().split())
        curr_words = set(joke_text.lower().split())
        if len(prev_words & curr_words) / max(len(prev_words), len(curr_words)) > 0.7:
            is_repeated = True
            break

    if is_repeated:
        response = (
            f"😅 **Oops! I've Heard That One Before!**\n\n"
            f"Nice try, but I remember this joke! Try a different one."
        )
        cursor.execute('''
            INSERT INTO jokes_history 
            (session_id, joke_text, is_funny, is_repeated, gemini_response, accepted_as_guess)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, joke_text, False, True, response, False))
        conn.commit()
        conn.close()
        return response

    # Evaluate joke quality
    joke_lower = joke_text.lower()
    has_punchline = any(word in joke_lower for word in ["because", "why", "what", "how", "knock knock", "?"])
    has_length = len(joke_text.split()) > 5
    has_structure = "?" in joke_text or "!" in joke_text

    is_funny = sum([has_punchline, has_length, has_structure]) >= 2

    if is_funny:
        game_state["trials_used"] += 1
        score_gained = max(100 - (game_state['trials_used'] * 10), 10)
        game_state["total_score"] += score_gained
        game_state["bonus_trials"] += 1
        game_state["consecutive_correct"] += 1

        response = (
            f"😂🎉 **HAHAHA! That's Hilarious!**\n\n"
            f"✅ **Counts as a CORRECT guess!**\n"
            f"💰 **+{score_gained} points** (Total: {game_state['total_score']})\n"
            f"✨ **+1 bonus trial**\n"
            f"🔥 **Streak: {game_state['consecutive_correct']}**"
        )

        cursor.execute('''
            INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, game_state['level'], -1,
              game_state['correct_number'], "joke_success", joke_text[:100]))

        min_range, max_range = game_state['current_range']
        game_state['correct_number'] = random.randint(min_range, max_range)
        game_state['trials_used'] = 0

    else:
        game_state["trials_used"] += 1
        max_trials = game_state['max_trials'] + game_state['bonus_trials']

        response = f"😐 **Hmm... Not Quite There**\n\n❌ Counts as incorrect guess\n"
        response += f"⚠️ Trial {game_state['trials_used']}/{max_trials} used"

        if game_state['trials_used'] >= max_trials:
            response += "\n\n" + trigger_tiebreaker()

        cursor.execute('''
            INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_session_id, game_state['level'], -1,
              game_state['correct_number'], "joke_fail", joke_text[:100]))

    cursor.execute('''
        INSERT INTO jokes_history 
        (session_id, joke_text, is_funny, is_repeated, gemini_response, accepted_as_guess)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_session_id, joke_text, is_funny, False, response, True))

    conn.commit()
    conn.close()
    return response

def chat_with_gemini(user_message, chat_history):
    """Chat with Gemini for game predictions and help"""
    global game_state, current_session_id

    if chat_history is None:
        chat_history = []

    if not current_session_id:
        return chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": "⚠️ Please start a game first!"}
        ]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT guess, result, hint FROM game_history 
        WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10
    ''', (current_session_id,))
    history = cursor.fetchall()

    message_lower = user_message.lower()

    # Check if it's a joke
    if any(keyword in message_lower for keyword in ["joke", "here's a joke", "wanna hear", "funny"]):
        response = handle_joke_submission(user_message, "")

    # Check if asking for prediction
    elif any(keyword in message_lower for keyword in ["predict", "next", "suggest", "what number", "help me guess"]):
        if history:
            too_low = [g for g, r, _ in history if r == "too_low"]
            too_high = [g for g, r, _ in history if r == "too_high"]

            lower_bound = max(too_low) if too_low else game_state['current_range'][0]
            upper_bound = min(too_high) if too_high else game_state['current_range'][1]
            suggested_guess = (lower_bound + upper_bound) // 2

            response = (
                f"🎯 **Strategic Prediction**\n\n"
                f"📊 Range narrowed to: **{lower_bound} - {upper_bound}**\n"
                f"💡 **Recommended guess: {suggested_guess}**\n\n"
                f"**Why?** Binary search divides possibilities by half!"
            )
        else:
            mid_point = (game_state['current_range'][0] + game_state['current_range'][1]) // 2
            response = f"🎯 **Start with {mid_point}** - the perfect middle!"

    # General help
    else:
        response = (
            f"🤖 **AI Assistant**\n\n"
            f"Ask me to:\n"
            f"🎯 'predict the next number'\n"
            f"😄 Tell a joke (counts as guess!)\n"
            f"⚡ Help with tiebreaker"
        )

    cursor.execute('INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)',
                   (current_session_id, "user", user_message))
    cursor.execute('INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)',
                   (current_session_id, "assistant", response))
    conn.commit()
    conn.close()

    return chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]

def calculator_compute(num1, operation, num2):
    """Simple calculator"""
    try:
        n1 = float(num1) if num1 else 0
        n2 = float(num2) if num2 else 0

        if operation == "+":
            result = n1 + n2
        elif operation == "-":
            result = n1 - n2
        elif operation == "×":
            result = n1 * n2
        elif operation == "÷":
            result = n1 / n2 if n2 != 0 else "Error"
        elif operation == "^":
            result = n1 ** n2
        elif operation == "√":
            result = math.sqrt(n1)
        else:
            result = "Invalid"

        return f"{result}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_game_stats():
    """Get current game statistics"""
    if not current_session_id:
        return "No active game."

    return (
        f"📊 **GAME STATISTICS**\n\n"
        f"Level: {game_state['level']}\n"
        f"Total Score: {game_state['total_score']} 💰\n"
        f"Current Streak: {game_state['consecutive_correct']} 🔥\n"
        f"Bonus Trials: {game_state['bonus_trials']}\n"
        f"Trials Remaining: {game_state['max_trials'] + game_state['bonus_trials'] - game_state['trials_used']}"
    )

# Create Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(), title="Enhanced Guessing Game") as demo:
    gr.Markdown("# 🎮 Enhanced Number Guessing Game\n### Powered by Gemini AI")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("""
                ## 📋 How to Play
                
                1. **Start a New Game**
                2. **Make Your Guess** or **Tell a Joke**
                3. **Get Feedback**
                4. **Earn Bonuses** - +1 trial per correct guess
                5. **Solve Tiebreakers** if needed
                
                ### 😄 Joke Feature
                Tell Gemini a funny joke in the chat!
                - **Funny joke** = Correct guess ✅
                - **Not funny** = Incorrect guess ❌
                - No repeating jokes!
            """)

        with gr.Column(scale=3):
            game_status = gr.Textbox(
                label="🎮 Game Status",
                value="Click 'Start New Game' to begin!",
                lines=8,
                interactive=False
            )

            with gr.Row():
                start_btn = gr.Button("🎮 Start New Game", variant="primary", size="lg")
                stats_btn = gr.Button("📊 View Stats", size="lg")

            gr.Markdown("### Enter Your Guess")
            with gr.Row():
                guess_input = gr.Number(label="Your Guess", precision=0)
                submit_guess_btn = gr.Button("🎯 Submit Guess", variant="primary")

            gr.Markdown("### ⚡ Tiebreaker Zone")
            with gr.Row():
                tiebreaker_answer = gr.Number(label="Your Answer", precision=2)
                use_ai = gr.Checkbox(label="Use AI Help (-20 pts)")
            submit_tiebreaker_btn = gr.Button("✓ Submit Tiebreaker Answer")

    with gr.Accordion("🧮 Calculator (for Tiebreakers)", open=False):
        with gr.Row():
            calc_num1 = gr.Number(label="Number 1", precision=2)
            calc_operation = gr.Dropdown(
                choices=["+", "-", "×", "÷", "^", "√"],
                label="Operation",
                value="+"
            )
            calc_num2 = gr.Number(label="Number 2", precision=2)
        calc_result = gr.Textbox(label="Result", interactive=False)
        calc_btn = gr.Button("Calculate")

    gr.Markdown("## 💬 Chat with Gemini AI")
    chatbot = gr.Chatbot(label="Gemini Assistant", height=300, type="messages")
    with gr.Row():
        chat_input = gr.Textbox(
            label="Ask Gemini",
            placeholder="Ask for predictions, tell a joke, or get help...",
            scale=4
        )
        chat_btn = gr.Button("Send", variant="primary", scale=1)

    # Event Handlers
    start_btn.click(start_new_game, outputs=[game_status, calc_result, chatbot])
    submit_guess_btn.click(submit_guess, inputs=[guess_input], outputs=[game_status, guess_input])
    submit_tiebreaker_btn.click(
        submit_tiebreaker,
        inputs=[tiebreaker_answer, use_ai],
        outputs=[game_status, tiebreaker_answer]
    ).then(lambda: False, outputs=use_ai)

    stats_btn.click(get_game_stats, outputs=game_status)
    chat_btn.click(chat_with_gemini, inputs=[chat_input, chatbot], outputs=chatbot).then(
        lambda: "", outputs=chat_input
    )
    chat_input.submit(chat_with_gemini, inputs=[chat_input, chatbot], outputs=chatbot).then(
        lambda: "", outputs=chat_input
    )
    calc_btn.click(calculator_compute, inputs=[calc_num1, calc_operation, calc_num2], outputs=calc_result)

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)