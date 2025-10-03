# 🎮 Enhanced Number Guessing Game

An advanced, AI-powered number guessing game built with Jac programming language, featuring graph-based state management, dynamic difficulty levels, tiebreaker challenges, and an interactive Gradio dashboard powered by Gemini AI.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [File Structure](#file-structure)
- [How to Play](#how-to-play)
- [Game Mechanics](#game-mechanics)
- [Technical Details](#technical-details)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)

## ✨ Features

### Core Game Mechanics
- **Persistent Progress**: Game doesn't end on correct guess - earn bonus trials and keep playing!
- **Bonus Trial System**: Each correct guess awards +1 trial for future rounds
- **Progressive Difficulty**: 4 difficulty levels with expanding ranges (1-20, 1-50, 1-100, 1-200)
- **Tiebreaker Challenges**: Math problems to continue when trials are depleted
- **Reward System**: Points-based scoring with milestones and achievements

### AI-Powered Features
- **Smart Hints**: Gemini AI generates creative, contextual hints
- **Strategic Advisor**: AI analyzes game history and suggests optimal guesses using binary search
- **Dynamic Tiebreakers**: AI generates custom math problems with answers matching the target number
- **Solution Explanations**: Step-by-step math problem explanations (with point deduction)

### Interactive Dashboard
- **Gradio Interface**: Beautiful, intuitive web interface
- **Real-time Chat**: Conversation with Gemini AI for predictions and help
- **Built-in Calculator**: For solving tiebreaker problems (collapsible to save space)
- **Game History**: Complete tracking of all guesses, results, and scores
- **Statistics Panel**: Live performance metrics and analytics

### Advanced Jac Features
- **Graph-Based State**: Difficulty levels represented as connected nodes
- **Walker Agents**: Specialized walkers for game logic, rewards, and tournaments
- **Reward Network**: Milestone nodes with automatic achievement detection
- **Tournament Mode**: Multi-round competition tracking

## 🏗️ Architecture

### Jac Programming Paradigm

This game leverages Jac's unique features:

1. **Graph Traversal for Difficulty**: Difficulty levels are nodes in a graph. Players traverse upward on good performance.

2. **Walker-Based Logic**: Different walkers handle specific concerns:
   - `GuessGame`: Main game loop
   - `RewardWalker`: Checks and awards milestones
   - `TiebreakerWalker`: Handles math challenges
   - `TournamentWalker`: Manages multi-round games
   - `DifficultyWalker`: Adjusts challenge level

3. **Node-Based State**: Game state, difficulty levels, rewards, and tiebreakers are all nodes in the game graph.

4. **LLM Integration**: Seamless AI function calls using `by llm()` syntax.

## 📦 Installation

### Prerequisites

```bash
# Install Jac
pip install jaclang

# Install required Python packages
pip install gradio sqlite3 byllm

# For Gemini API
pip install google-generativeai
```

### Setup

1. **Clone or download the game files:**
```bash
mkdir enhanced_guess_game
cd enhanced_guess_game
```

2. **Set up your API key:**
```bash
# Create a .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

3. **Initialize the database:**
The database will be created automatically on first run.

## 📁 File Structure

```
enhanced_guess_game/
├── guess_game_enhanced.jac          # Main game logic & node definitions
├── guess_game_enhanced.impl.jac     # Walker implementations
├── llm_prompts.jac                  # AI prompt definitions
├── gradio_interface.py              # Web dashboard
├── guess_game_history.db            # SQLite database (auto-created)
└── README.md                        # This file
```

## 🎮 How to Play

### Quick Start

1. **Launch the Gradio Dashboard:**
```bash
python gradio_interface.py
```

2. **Or run via Jac CLI:**
```bash
jac run guess_game_enhanced.jac
```

### Gameplay Flow

1. **Start New Game**: Click "Start New Game" button
2. **Make Your Guess**: Enter a number in the valid range
3. **Receive Feedback**: See if you're too high, too low, or correct
4. **Earn Bonuses**: Correct guesses grant bonus trials
5. **Face Tiebreakers**: Solve math problems when trials run out
6. **Use AI Help**: Ask Gemini for strategic advice
7. **Progress Levels**: Successfully complete rounds to increase difficulty

## 🎯 Game Mechanics

### Scoring System

| Action | Points |
|--------|--------|
| Correct guess (1st trial) | 100 points |
| Correct guess (2nd trial) | 90 points |
| Correct guess (3rd trial) | 80 points |
| 3 correct in a row | +50 bonus |
| Complete tiebreaker | Refill trials |
| Use AI help (tiebreaker) | -20 points |
| Milestone achievements | 50-200 points |

### Trial System

- **Base Trials**: Start with 3 trials per round
- **Bonus Trials**: +1 for each correct guess (cumulative)
- **Tiebreaker**: Solve a math problem to refill trials
- **Example**: Guess correctly 5 times → You'll have 8 trials (3 base + 5 bonus)

### Difficulty Levels

| Level | Name | Range | Base Trials |
|-------|------|-------|-------------|
| 1 | Beginner | 1-20 | 3 |
| 2 | Intermediate | 1-50 | 5 |
| 3 | Advanced | 1-100 | 7 |
| 4 | Expert | 1-200 | 10 |

**Progression**: Level up when you achieve 75%+ accuracy with good trial efficiency.

### Tiebreaker Challenges

When you run out of trials, you face a math problem where the answer equals the correct number:

**Example Tiebreakers:**
- **Geometry**: "A rectangle has length 5m and area 20m². What is the perimeter?"
- **Algebra**: "Solve for x: 3x + 5 = 26"
- **Word Problems**: "A farmer's shed dimensions result in..."

**Options:**
- Solve independently using the calculator
- Request AI help (costs 20 points)
- Fail → Game ends with summary

## 🔧 Technical Details

### Database Schema

#### `game_history` Table
```sql
CREATE TABLE game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    level INTEGER,
    guess INTEGER,
    correct_number INTEGER,
    result TEXT,           -- 'too_low', 'too_high', 'correct'
    hint TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `game_sessions` Table
```sql
CREATE TABLE game_sessions (
    session_id TEXT PRIMARY KEY,
    current_level INTEGER,
    total_score INTEGER,
    games_won INTEGER,
    games_lost INTEGER,
    highest_level INTEGER,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `tiebreaker_history` Table
```sql
CREATE TABLE tiebreaker_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    level INTEGER,
    question TEXT,
    correct_answer REAL,
    user_answer REAL,
    is_correct BOOLEAN,
    used_ai_help BOOLEAN,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `chat_history` Table
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,             -- 'user' or 'assistant'
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Graph Structure

```
root
├── difficulty_level (Beginner: 1-20)
│   └── difficulty_level (Intermediate: 1-50)
│       └── difficulty_level (Advanced: 1-100)
│           └── difficulty_level (Expert: 1-200)
├── game_state
│   └── tiebreaker (when triggered)
└── reward_milestone (multiple)
```

### Walker Flow Diagram

```
GuessGame Walker
    ├── start() → Initialize/Get game_state
    └── process_guess()
        ├── Too Low/High → Log & give hint
        │   └── Trials exhausted? → trigger_tiebreaker()
        └── Correct → Award bonus, spawn RewardWalker, new round

RewardWalker
    └── check_milestones() → Award points for achievements

TiebreakerWalker
    └── solve_tiebreaker()
        ├── Correct → Refill trials, continue game
        └── Incorrect → End game, show summary

DifficultyWalker
    └── adjust_difficulty() → Traverse to next difficulty node
```

## 🤖 AI Functions

### LLM-Powered Features

All AI functions use the Gemini API via `by llm()` syntax:

1. **`give_hint(guess, correct_number)`**
   - Generates creative, contextual hints
   - Temperature: 0.9 (creative)

2. **`generate_tiebreaker(target_number, difficulty)`**
   - Creates math problems with target answer
   - Returns JSON with question, answer, solution
   - Temperature: 0.7 (balanced)

3. **`explain_tiebreaker_solution(question, answer)`**
   - Provides step-by-step explanations
   - Temperature: 0.5 (precise)

4. **`predict_next_guess(session_id, range, trials_left)`**
   - Analyzes history for optimal strategy
   - Uses binary search principles
   - Temperature: 0.6 (analytical)

5. **`generate_game_summary(stats)`**
   - Creates personalized performance report
   - Temperature: 0.8 (engaging)

## 📊 API Reference

### Gradio Dashboard Functions

#### `start_new_game() -> tuple`
Initializes a new game session.

**Returns:**
- Game status message
- Cleared calculator
- Cleared chat

#### `submit_guess(guess: int) -> tuple`
Processes a player's guess.

**Parameters:**
- `guess`: The number guessed by player

**Returns:**
- Feedback message
- Cleared input field

#### `submit_tiebreaker(answer: float, use_ai: bool) -> tuple`
Validates tiebreaker answer.

**Parameters:**
- `answer`: Player's solution
- `use_ai`: Whether AI help was used

**Returns:**
- Result message
- Cleared answer field

#### `chat_with_gemini(message: str, history: list) -> list`
Interacts with AI assistant.

**Parameters:**
- `message`: User's question
- `history`: Chat history

**Returns:**
- Updated chat history

#### `calculator_compute(num1: float, op: str, num2: float) -> str`
Performs calculation.

**Parameters:**
- `num1`: First number
- `op`: Operation (+, -, ×, ÷, ^, √)
- `num2`: Second number

**Returns:**
- Calculation result

#### `get_game_stats() -> str`
Retrieves current session statistics.

**Returns:**
- Formatted statistics string

## 🎨 Gradio Interface Components

### Main Sections

1. **How to Play Panel** (Left column)
   - Game rules
   - Scoring explanation
   - Win conditions

2. **Game Area** (Right column)
   - Game status display
   - Control buttons (Start, Stats)
   - Guess input
   - Tiebreaker input

3. **Calculator** (Collapsible)
   - Basic operations
   - Power and square root
   - Toggle visibility

4. **AI Chat** (Bottom)
   - Chat with Gemini
   - Ask for predictions
   - Get strategy advice

5. **History** (Accordion)
   - View past guesses
   - See results and hints
   - Refresh button

## 🚀 Advanced Usage

### Tournament Mode

Run multiple rounds and track overall performance:

```python
# In Jac
tournament = root ++> tournament(
    tournament_id="weekend_challenge",
    rounds_played=0,
    rounds_won=0
);

walker = TournamentWalker(session_id="weekend_challenge");
root spawn walker;
```

### Custom Difficulty

Create custom difficulty nodes:

```python
custom = root ++> difficulty_level(
    level_number=5,
    min_range=1,
    max_range=500,
    max_trials=15,
    level_name="Nightmare"
);
```

### Reward Milestones

Add custom achievements:

```python
root ++> reward_milestone(
    milestone_name="Perfect Score",
    threshold=10,
    reward_points=500
);
```

## 🐛 Troubleshooting

### Common Issues

**Database locked error:**
```bash
# Delete and recreate database
rm guess_game_history.db
python gradio_interface.py
```

**Gemini API errors:**
```bash
# Check API key
echo $GEMINI_API_KEY

# Or check .env file
cat .env
```

**Import errors:**
```bash
# Reinstall dependencies
pip install --upgrade jaclang byllm gradio
```

## 📈 Performance Tips

### For Players

1. **Use Binary Search**: Always guess the middle of the remaining range
2. **Track Patterns**: Note which numbers appear frequently
3. **Save AI Help**: Use it only for difficult tiebreakers
4. **Build Streaks**: 3 correct in a row gives bonus points
5. **Calculator Shortcuts**: Use for quick tiebreaker calculations

### For Developers

1. **Database Indexing**: Add indexes for frequent queries
```sql
CREATE INDEX idx_session_id ON game_history(session_id);
CREATE INDEX idx_timestamp ON game_history(timestamp);
```

2. **Connection Pooling**: Implement for multiple concurrent users
3. **Cache LLM Responses**: Store similar hints to reduce API calls
4. **Batch Database Writes**: Commit multiple operations together

## 🎓 Learning Objectives

This project demonstrates:

- **Jac Language Features**: Graphs, walkers, nodes, LLM integration
- **State Management**: Using graph structures instead of traditional variables
- **AI Integration**: Seamless LLM function calls
- **Full-Stack Development**: Backend (Jac) + Frontend (Gradio)
- **Database Design**: SQLite schema for game persistence
- **Game Design**: Reward systems, difficulty curves, player engagement

## 🤝 Contributing

Ideas for expansion:

1. **Multiplayer Mode**: Compete against other players
2. **Leaderboards**: Global high scores
3. **Custom Themes**: Visual customization
4. **Sound Effects**: Audio feedback
5. **Mobile App**: Native mobile version
6. **Social Features**: Share achievements
7. **More Tiebreaker Types**: Logic puzzles, riddles
8. **Achievement Badges**: Visual rewards
9. **Daily Challenges**: Special themed games
10. **Replay System**: Watch past games

## 📝 License

This project is open source and available for educational purposes.

## 🙏 Acknowledgments

- **Jac Language**: For the innovative graph-based programming paradigm
- **Google Gemini**: For powering the AI features
- **Gradio**: For the excellent UI framework
- **SQLite**: For reliable database management

## 📧 Support

For questions, issues, or suggestions:
- Check the troubleshooting section
- Review the code comments
- Experiment with the examples
- Modify and extend the game

---

**Happy Guessing! 🎮🎯**

*May your guesses be strategic and your tiebreakers solvable!*