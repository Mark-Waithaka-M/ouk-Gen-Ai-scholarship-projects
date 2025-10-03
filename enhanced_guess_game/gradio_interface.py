"""Gradio Dashboard for Enhanced Guessing Game - Clean Version"""

import gradio as gr
import sqlite3
import uuid
import random
import math
import re
from datetime import datetime

# ============================================================================
# GLOBAL STATE
# ============================================================================
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

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================
def get_db_connection():
    return sqlite3.connect('guess_game_history.db', check_same_thread=False)

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS game_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, level INTEGER, guess INTEGER,
        correct_number INTEGER, result TEXT, hint TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, role TEXT, message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jokes_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, joke_text TEXT, is_funny BOOLEAN,
        is_repeated BOOLEAN, gemini_response TEXT, accepted_as_guess BOOLEAN,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_database()

# ============================================================================
# GAME LOGIC FUNCTIONS
# ============================================================================
def start_new_game():
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
        f"🎮 New Game Started!\n\n"
        f"Session: {current_session_id[:8]}...\n"
        f"Level: {game_state['level']}\n"
        f"Range: {game_state['current_range'][0]}-{game_state['current_range'][1]}\n"
        f"Trials: {game_state['max_trials']}\n\n"
        f"Good luck! 🍀",
        None, []
    )

def generate_hint(guess, correct):
    diff = abs(guess - correct)
    if diff <= 2: return "🔥 Burning hot! So close!"
    elif diff <= 5: return "☀️ Getting warm!"
    elif diff <= 10: return "❄️ A bit chilly."
    else: return "🧊 Ice cold!"

def trigger_tiebreaker():
    global game_state
    game_state["tiebreaker_active"] = True
    target = game_state["correct_number"]

    problem_type = random.choice(["perimeter", "area", "equation"])

    if problem_type == "perimeter":
        length = random.randint(3, 8)
        width = max(1, target // 2 - length)
        game_state["tiebreaker_answer"] = 2 * (length + width)
        game_state["tiebreaker_question"] = (
            f"A rectangular shed has length {length}m and width {width}m. What is the perimeter in meters?")
    elif problem_type == "area":
        length = random.randint(2, 5)
        game_state["tiebreaker_answer"] = target
        game_state["tiebreaker_question"] = (
            f"A rectangle has area {target * length}m² and length {length}m. What is the width in meters?")
    else:
        a, b = random.randint(2, 5), random.randint(1, 10)
        game_state["tiebreaker_answer"] = target
        game_state["tiebreaker_question"] = f"Solve for x: {a}x + {b} = {a * target + b}"

    return (
        f"\n\n⚡ TIEBREAKER TIME! ⚡\n"
        f"Solve this problem:\n\n"
        f"📝 {game_state['tiebreaker_question']}\n\n"
        f"Use calculator or click 'Get AI Help'!")

def submit_guess(guess_input):
    global game_state, current_session_id

    if not game_state["game_active"]:
        return "⚠️ Start a new game first!", None
    if game_state["tiebreaker_active"]:
        return "⚡ Complete tiebreaker first!", None

    try:
        guess = int(guess_input)
    except:
        return "❌ Enter a valid number!", None

    min_r, max_r = game_state["current_range"]
    if guess < min_r or guess > max_r:
        return f"❌ Guess between {min_r} and {max_r}!", None

    game_state["trials_used"] += 1
    max_trials = game_state["max_trials"] + game_state["bonus_trials"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if guess < game_state["correct_number"]:
        hint = generate_hint(guess, game_state["correct_number"])
        feedback = (
            f"📊 Trial {game_state['trials_used']}/{max_trials}\n\n"
            f"Guess: {guess}\n⬇️ Too Low!\n\n{hint}\n\n"
            f"💡 Number is higher than {guess}")
        cursor.execute(
            'INSERT INTO game_history (session_id, level, guess, correct_number, result, hint) VALUES (?,?,?,?,?,?)',
            (current_session_id, game_state['level'], guess, game_state['correct_number'], "too_low", hint))
        if game_state["trials_used"] >= max_trials:
            feedback += f"\n\n❌ Out of trials!" + trigger_tiebreaker()

    elif guess > game_state["correct_number"]:
        hint = generate_hint(guess, game_state["correct_number"])
        feedback = (
            f"📊 Trial {game_state['trials_used']}/{max_trials}\n\n"
            f"Guess: {guess}\n⬆️ Too High!\n\n{hint}\n\n"
            f"💡 Number is lower than {guess}")
        cursor.execute(
            'INSERT INTO game_history (session_id, level, guess, correct_number, result, hint) VALUES (?,?,?,?,?,?)',
            (current_session_id, game_state['level'], guess, game_state['correct_number'], "too_high", hint))
        if game_state["trials_used"] >= max_trials:
            feedback += f"\n\n❌ Out of trials!" + trigger_tiebreaker()
    else:
        game_state["bonus_trials"] += 1
        game_state["consecutive_correct"] += 1
        score_gained = max(100 - (game_state['trials_used'] * 10), 10)
        game_state["total_score"] += score_gained

        feedback = (
            f"🎉 CORRECT! 🎉\n\n"
            f"Trial {game_state['trials_used']}\n"
            f"✨ +1 bonus trial!\n"
            f"💰 +{score_gained} points\n"
            f"📈 Total: {game_state['total_score']}\n"
            f"🔥 Streak: {game_state['consecutive_correct']}")

        if game_state["consecutive_correct"] == 3:
            feedback += "\n\n🎊 3 IN A ROW! +50 points!"
            game_state["total_score"] += 50

        cursor.execute(
            'INSERT INTO game_history (session_id, level, guess, correct_number, result, hint) VALUES (?,?,?,?,?,?)',
            (current_session_id, game_state['level'], guess, game_state['correct_number'], "correct", "Success!"))

        game_state["correct_number"] = random.randint(min_r, max_r)
        game_state["trials_used"] = 0
        feedback += f"\n\n🎮 New round! Guess {min_r}-{max_r}"

    conn.commit()
    conn.close()
    return feedback, None

def submit_tiebreaker(answer_input, use_ai_help):
    global game_state

    if not game_state["tiebreaker_active"]:
        return "⚠️ No active tiebreaker!", None

    try:
        user_answer = float(answer_input)
    except:
        return "❌ Enter a valid number!", None

    correct = game_state["tiebreaker_answer"]
    is_correct = abs(user_answer - correct) < 0.01

    feedback = f"Question: {game_state['tiebreaker_question']}\n\n"
    feedback += f"Your answer: {user_answer}\nCorrect: {correct}\n\n"

    if use_ai_help:
        feedback += "⚠️ AI help used: -20 points\n"
        game_state["total_score"] = max(0, game_state["total_score"] - 20)

    if is_correct:
        feedback += (
            "✅ CORRECT! Tiebreaker won!\n\n"
            "Trials refilled!\n"
            f"New trials: {game_state['max_trials'] + game_state['bonus_trials'] + 1}")
        game_state["tiebreaker_active"] = False
        game_state["trials_used"] = 0
        game_state["bonus_trials"] += 1
        game_state["game_active"] = True
    else:
        feedback += (
            f"❌ INCORRECT!\n\n"
            f"📊 GAME OVER\n"
            f"Score: {game_state['total_score']}\n"
            f"Streak: {game_state['consecutive_correct']}\n\n"
            f"Thanks for playing!")
        game_state["game_active"] = False
        game_state["tiebreaker_active"] = False

    return feedback, None

def get_game_stats():
    global game_state, current_session_id
    if not current_session_id:
        return "No active game."
    return (
        f"📊 GAME STATS\n\n"
        f"Level: {game_state['level']}\n"
        f"Score: {game_state['total_score']} 💰\n"
        f"Streak: {game_state['consecutive_correct']} 🔥\n"
        f"Bonus Trials: {game_state['bonus_trials']}\n"
        f"Trials Left: {game_state['max_trials'] + game_state['bonus_trials'] - game_state['trials_used']}")

# ============================================================================
# JOKE HANDLING
# ============================================================================
def handle_joke(joke_text):
    global game_state, current_session_id

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT joke_text FROM jokes_history WHERE session_id = ?', (current_session_id,))
    previous = cursor.fetchall()

    # Check for repeats
    for (prev,) in previous:
        prev_words = set(prev.lower().split())
        curr_words = set(joke_text.lower().split())
        similarity = len(prev_words & curr_words) / max(len(prev_words | curr_words), 1)
        if similarity > 0.7:
            response = "😅 I've heard that one! Try a different joke."
            cursor.execute(
                'INSERT INTO jokes_history (session_id, joke_text, is_funny, is_repeated, gemini_response, accepted_as_guess) VALUES (?,?,?,?,?,?)',
                (current_session_id, joke_text, False, True, response, False))
            conn.commit()
            conn.close()
            return response

    # Evaluate joke
    joke_lower = joke_text.lower()
    has_setup = any(w in joke_lower for w in ["why", "what", "how", "knock", "?"])
    has_length = len(joke_text.split()) > 5
    has_punctuation = "?" in joke_text or "!" in joke_text
    is_funny = sum([has_setup, has_length, has_punctuation]) >= 2

    if is_funny:
        game_state["trials_used"] += 1
        score = max(100 - (game_state['trials_used'] * 10), 10)
        game_state["total_score"] += score
        game_state["bonus_trials"] += 1
        game_state["consecutive_correct"] += 1

        response = (
            f"😂🎉 HILARIOUS!\n\n"
            f"✅ Counts as CORRECT!\n"
            f"💰 +{score} points (Total: {game_state['total_score']})\n"
            f"✨ +1 trial\n"
            f"🔥 Streak: {game_state['consecutive_correct']}")

        cursor.execute(
            'INSERT INTO game_history (session_id, level, guess, correct_number, result, hint) VALUES (?,?,?,?,?,?)',
            (current_session_id, game_state['level'], -1, game_state['correct_number'], "joke_success", joke_text[:100]))

        min_r, max_r = game_state['current_range']
        game_state['correct_number'] = random.randint(min_r, max_r)
        game_state['trials_used'] = 0
    else:
        game_state["trials_used"] += 1
        max_trials = game_state['max_trials'] + game_state['bonus_trials']
        response = f"😐 Not quite funny enough!\n\n❌ Counts as incorrect\n⚠️ Trial {game_state['trials_used']}/{max_trials}"

        if game_state['trials_used'] >= max_trials:
            response += "\n\n" + trigger_tiebreaker()

        cursor.execute(
            'INSERT INTO game_history (session_id, level, guess, correct_number, result, hint) VALUES (?,?,?,?,?,?)',
            (current_session_id, game_state['level'], -1, game_state['correct_number'], "joke_fail", joke_text[:100]))

    cursor.execute(
        'INSERT INTO jokes_history (session_id, joke_text, is_funny, is_repeated, gemini_response, accepted_as_guess) VALUES (?,?,?,?,?,?)',
        (current_session_id, joke_text, is_funny, False, response, True))
    conn.commit()
    conn.close()
    return response

# ============================================================================
# AI CHAT FUNCTION
# ============================================================================
def chat_with_gemini(user_message, chat_history):
    global game_state, current_session_id

    if chat_history is None:
        chat_history = []

    if not current_session_id:
        return chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": "⚠️ Start a game first!"}]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT guess, result, hint FROM game_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10',
        (current_session_id,))
    history = cursor.fetchall()

    msg_lower = user_message.lower()
    min_r, max_r = game_state['current_range']
    trials_left = game_state['max_trials'] + game_state['bonus_trials'] - game_state['trials_used']

    # DETECT JOKE
    if any(k in msg_lower for k in ["joke:", "here's a joke", "knock knock"]) or \
       (("why" in msg_lower or "what" in msg_lower) and "?" in user_message and len(user_message.split()) > 8):
        response = handle_joke(user_message)

    # DETECT TIEBREAKER HELP REQUEST
    elif game_state.get("tiebreaker_active") and any(k in msg_lower for k in
        ["help", "solve", "explain", "tiebreaker", "math", "problem", "how to"]):

        question = game_state.get("tiebreaker_question", "")
        answer = game_state.get("tiebreaker_answer", 0)

        response = f"🤖 **Tiebreaker Solution**\n\n**Question:** {question}\n\n**Step-by-Step:**\n\n"

        if "perimeter" in question.lower():
            nums = re.findall(r'\d+', question)
            if len(nums) >= 2:
                l, w = int(nums[0]), int(nums[1])
                response += (
                    f"Given: length={l}m, width={w}m\n"
                    f"Formula: Perimeter = 2(l + w)\n\n"
                    f"1️⃣ Add: {l} + {w} = {l+w}\n"
                    f"2️⃣ Multiply: 2 × {l+w} = {2*(l+w)}\n\n"
                    f"**Answer: {2*(l+w)}m**\n\n"
                    f"💡 Calculator: ({l} + {w}) × 2")
        elif "area" in question.lower() and "width" in question.lower():
            nums = re.findall(r'\d+', question)
            if len(nums) >= 2:
                area, length = int(nums[0]), int(nums[1])
                width = area / length
                response += (
                    f"Given: Area={area}m², length={length}m\n"
                    f"Formula: width = Area ÷ length\n\n"
                    f"1️⃣ Substitute: width = {area} ÷ {length}\n"
                    f"2️⃣ Calculate: width = {width}\n\n"
                    f"**Answer: {width}m**\n\n"
                    f"💡 Calculator: {area} ÷ {length}")
        elif "solve" in question.lower() or "x" in question.lower():
            match = re.search(r'(\d+)x\s*\+\s*(\d+)\s*=\s*(\d+)', question)
            if match:
                a, b, result = map(int, match.groups())
                x = (result - b) / a
                response += (
                    f"Equation: {a}x + {b} = {result}\n\n"
                    f"1️⃣ Subtract {b}: {a}x = {result-b}\n"
                    f"2️⃣ Divide by {a}: x = {x}\n\n"
                    f"**Answer: {x}**\n\n"
                    f"💡 Calculator:\n  {result} - {b} = {result-b}\n  {result-b} ÷ {a} = {x}")

        response += f"\n\n⚠️ Check 'Use AI Help' and submit for -20 pts penalty."

    # DETECT PREDICTION REQUEST
    elif any(k in msg_lower for k in
        ["predict", "next", "suggest", "what number", "which number", "help me guess", "recommend"]):

        if history:
            too_low = [g for g, r, _ in history if r == "too_low"]
            too_high = [g for g, r, _ in history if r == "too_high"]

            lower = max(too_low) if too_low else min_r
            upper = min(too_high) if too_high else max_r
            remaining = upper - lower - 1
            suggested = (lower + upper) // 2

            prob = min((1 / max(remaining / (2 ** trials_left), 1)) * 100, 99) if trials_left > 0 else 0

            response = (
                f"🎯 **Strategic Prediction**\n\n"
                f"📊 **Game Analysis:**\n"
                f"• Score: {game_state['total_score']}\n"
                f"• Trials left: {trials_left}/{game_state['max_trials'] + game_state['bonus_trials']}\n"
                f"• Streak: {game_state['consecutive_correct']}\n"
                f"• Level: {game_state['level']}\n\n"
                f"📈 **Your Guess History:**\n")

            if too_low:
                response += f"• Too low: {', '.join(map(str, too_low[:5]))}\n"
            if too_high:
                response += f"• Too high: {', '.join(map(str, too_high[:5]))}\n"

            response += (
                f"\n🔍 **Statistical Analysis:**\n"
                f"• Original range: {min_r}-{max_r}\n"
                f"• **Narrowed to: {lower}-{upper}**\n"
                f"• Remaining: **{remaining} numbers**\n"
                f"• Success prob: **~{prob:.1f}%**\n\n"
                f"🧮 **Binary Search Logic:**\n"
                f"Midpoint: ({lower} + {upper}) ÷ 2 = **{suggested}**\n\n"
                f"💡 **RECOMMENDATION: {suggested}**\n\n"
                f"**Why {suggested}?**\n"
                f"1️⃣ Splits range evenly\n"
                f"2️⃣ Eliminates ~50% of possibilities\n"
                f"3️⃣ Optimal strategy with {trials_left} trial(s)\n"
                f"4️⃣ Maximizes information gain\n\n")

            if trials_left <= 2:
                response += f"⚠️ **CRITICAL:** Only {trials_left} left! Use {suggested}\n"
        else:
            mid = (min_r + max_r) // 2
            response = (
                f"🎯 **Fresh Start Strategy**\n\n"
                f"📊 **Setup:**\n"
                f"• Range: {min_r}-{max_r}\n"
                f"• Trials: {trials_left}\n"
                f"• No guesses yet\n\n"
                f"💡 **Start with {mid}**\n\n"
                f"**Why?**\n"
                f"• Perfect midpoint\n"
                f"• Eliminates 50% immediately\n"
                f"• Binary search = optimal\n"
                f"• Best first move!")

    # GENERAL HELP/STRATEGY
    elif any(k in msg_lower for k in ["how", "strategy", "rules", "help", "tip", "advice"]):
        response = (
            f"🎮 **Game Guide**\n\n"
            f"📊 **Status:**\n"
            f"• Range: {min_r}-{max_r}\n"
            f"• Trials: {trials_left}\n"
            f"• Score: {game_state['total_score']}\n\n"
            f"**How to Play:**\n"
            f"1. Guess numbers\n"
            f"2. Get feedback\n"
            f"3. Correct = +1 trial\n"
            f"4. Build score!\n\n"
            f"**😄 Joke Option:**\n"
            f"• Tell me a joke\n"
            f"• Funny = correct ✅\n"
            f"• Not funny = incorrect ❌\n\n"
            f"**💡 Pro Tips:**\n"
            f"• Use binary search\n"
            f"• Track high/low\n"
            f"• Save jokes for tough spots\n"
            f"• Build streaks!")

    # DEFAULT RESPONSE
    else:
        response = (
            f"🤖 **AI Assistant**\n\n"
            f"📊 **Current Status:**\n"
            f"• Range: {min_r}-{max_r}\n"
            f"• Trials: {trials_left}\n"
            f"• Score: {game_state['total_score']}\n\n"
            f"**I can help with:**\n\n"
            f"🎯 **Predictions**\n"
            f"   Say: 'predict the next number'\n\n"
            f"😄 **Jokes**\n"
            f"   Say: 'Here's a joke: ...'\n\n"
            f"⚡ **Tiebreakers**\n"
            f"   Say: 'help with tiebreaker'\n\n"
            f"📚 **Strategy**\n"
            f"   Ask: 'how to play'\n\n"
            f"What would you like?")

    cursor.execute('INSERT INTO chat_history (session_id, role, message) VALUES (?,?,?)',
                   (current_session_id, "user", user_message))
    cursor.execute('INSERT INTO chat_history (session_id, role, message) VALUES (?,?,?)',
                   (current_session_id, "assistant", response))
    conn.commit()
    conn.close()

    return chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}]

def request_ai_help(chat_history):
    global game_state
    if not game_state.get("tiebreaker_active"):
        return chat_history + [
            {"role": "user", "content": "Help with tiebreaker"},
            {"role": "assistant", "content": "⚠️ No tiebreaker active!"}]
    return chat_with_gemini("help me solve the tiebreaker", chat_history)

def calculator_compute(num1, op, num2):
    try:
        n1, n2 = float(num1 or 0), float(num2 or 0)
        if op == "+": return str(n1 + n2)
        elif op == "-": return str(n1 - n2)
        elif op == "×": return str(n1 * n2)
        elif op == "÷": return str(n1 / n2) if n2 != 0 else "Error"
        elif op == "^": return str(n1 ** n2)
        elif op == "√": return str(math.sqrt(n1))
        return "Invalid"
    except:
        return "Error"

# ============================================================================
# GRADIO INTERFACE
# ============================================================================
with gr.Blocks(theme=gr.themes.Soft(), title="Enhanced Guessing Game") as demo:
    gr.Markdown("# 🎮 Enhanced Number Guessing Game\n### Powered by AI")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("""
## 📋 How to Play

1. **Start Game** - Click button
2. **Make Guess** OR **Tell Joke**
3. **Get Feedback**
4. **Earn Bonuses** - +1 trial per correct
5. **Solve Tiebreakers**

### 😄 Joke Feature
Chat: "Here's a joke: ..."
- Funny = Correct ✅
- Not funny = Incorrect ❌
- No repeats!

### 🤖 AI Help
Ask for predictions, jokes, or tiebreaker help!
            """)

        with gr.Column(scale=3):
            game_status = gr.Textbox(
                label="🎮 Game Status",
                value="Click 'Start New Game'!",
                lines=10,
                interactive=False)

            with gr.Row():
                start_btn = gr.Button("🎮 Start New Game", variant="primary", size="lg")
                stats_btn = gr.Button("📊 Stats", size="lg")

            gr.Markdown("### Your Guess")
            with gr.Row():
                guess_input = gr.Number(label="Number", precision=0)
                submit_btn = gr.Button("🎯 Submit", variant="primary")

            gr.Markdown("### ⚡ Tiebreaker")
            with gr.Row():
                tie_answer = gr.Number(label="Answer", precision=2)
                use_ai = gr.Checkbox(label="Use AI Help (-20pts)")
            with gr.Row():
                submit_tie_btn = gr.Button("✓ Submit Answer", variant="primary")
                ai_help_btn = gr.Button("🤖 Get AI Help", variant="secondary")

    with gr.Accordion("🧮 Calculator", open=False):
        with gr.Row():
            calc_n1 = gr.Number(label="Num 1", precision=2)
            calc_op = gr.Dropdown(["+", "-", "×", "÷", "^", "√"], label="Op", value="+")
            calc_n2 = gr.Number(label="Num 2", precision=2)
        calc_result = gr.Textbox(label="Result", interactive=False)
        calc_btn = gr.Button("Calculate")

    gr.Markdown("## 💬 Chat with AI")
    chatbot = gr.Chatbot(label="AI Assistant", height=300, type="messages")
    with gr.Row():
        chat_input = gr.Textbox(
            label="Message",
            placeholder="Ask for predictions, tell jokes, or get help...",
            scale=4)
        chat_btn = gr.Button("Send", variant="primary", scale=1)

    # Events
    start_btn.click(start_new_game, outputs=[game_status, calc_result, chatbot])
    submit_btn.click(submit_guess, inputs=[guess_input], outputs=[game_status, guess_input])
    submit_tie_btn.click(submit_tiebreaker, inputs=[tie_answer, use_ai], outputs=[game_status, tie_answer]).then(
        lambda: False, outputs=use_ai)
    ai_help_btn.click(request_ai_help, inputs=[chatbot], outputs=[chatbot]).then(
        lambda: True, outputs=use_ai)
    stats_btn.click(get_game_stats, outputs=game_status)
    chat_btn.click(chat_with_gemini, inputs=[chat_input, chatbot], outputs=chatbot).then(
        lambda: "", outputs=chat_input)
    chat_input.submit(chat_with_gemini, inputs=[chat_input, chatbot], outputs=chatbot).then(
        lambda: "", outputs=chat_input)
    calc_btn.click(calculator_compute, inputs=[calc_n1, calc_op, calc_n2], outputs=calc_result)

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)