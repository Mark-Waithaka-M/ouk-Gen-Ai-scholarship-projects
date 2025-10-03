"""
max_tokens=60,
)
return resp['choices'][0]['message']['content'].strip()




def llm_tie_breaker(level: int):
# ask LLM to produce a simple one-step arithmetic puzzle whose answer equals a given target
# Keep puzzles solvable by elementary arithmetic
target = random.randint(5, 100)
# produce puzzle such that solution equals target, but include integer factors
prompt = (
f"Generate a short, single-step arithmetic puzzle where the final numeric answer is {target}. "
"Output JSON: {\"question\":..., \"solution\":..., \"explain\":...}."
)
resp = openai.ChatCompletion.create(
model="gpt-4o",
messages=[{"role":"user","content":prompt}],
max_tokens=200,
)
content = resp['choices'][0]['message']['content']
# try to parse JSON out of content
try:
j = json.loads(content)
return j
except Exception:
# fallback: craft a deterministic puzzle
width = 5
area = width * (target // width)
q = f"A farmer builds a shed width {target//width}m and length {width}m. What's the perimeter if area is {area}m^2?"
solution = target
explain = f"area / length = width => {area}/{width} = {target//width}. Perimeter = 2*(l+w) = 2*({width}+{target//width}) = {solution}"
return {"question": q, "solution": solution, "explain": explain}


# --- Game engine functions ---


def new_game(player="player"):
s = GameState(player=player)
s.correct_number = random.randint(s.range_min, s.range_max)
store_game_snapshot(s)
return s




def store_game_snapshot(state: GameState):
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute(
'INSERT INTO games(player, level, range_min, range_max, correct_number, attempts_allowed, attempts_used, bonus_attempts, total_points, history) VALUES (?,?,?,?,?,?,?,?,?,?)',
(state.player, state.level, state.range_min, state.range_max, state.correct_number, state.attempts_allowed, state.attempts_used, state.bonus_attempts, state.total_points, json.dumps(state.history))
)
conn.commit()
conn.close()




def save_game_end(state: GameState):
# to append final state into DB
store_game_snapshot(state)




def process_guess(state: GameState, guess: int):
state.attempts_used += 1
total_available = state.attempts_allowed + state.bonus_attempts
feedback = ""
if guess < state.correct_number:
feedback = llm_hint(guess, state.correct_number, state.history)
state.history.append((guess, 'low'))
elif guess > state.correct_number:
feedback = llm_hint(guess, state.correct_number, state.history)
state.history.append((guess, 'high'))
else:
feedback = "Correct!"
state.bonus_attempts += 1
state.total_points += max(1, (total_available - state.attempts_used + 1))
state.history.append((guess, 'correct'))
return feedback


# Suggest next guess using DB history and LLM
def suggest_guess_from_history(state: GameState):
# gather last