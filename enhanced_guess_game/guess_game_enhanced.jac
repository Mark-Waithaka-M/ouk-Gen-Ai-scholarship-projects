"""Enhanced Number Guessing Game with Multi-Level System"""

import random;
import sqlite3;
import from byllm.llm { Model }

# Initialize LLM
glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);

# Database initialization
glob db_connection = sqlite3.connect('guess_game_history.db', check_same_thread=False);

"""Initialize database tables"""
def init_database() -> None {
    cursor = db_connection.cursor();
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
    ''');
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id TEXT PRIMARY KEY,
            current_level INTEGER,
            total_score INTEGER,
            games_won INTEGER,
            games_lost INTEGER,
            highest_level INTEGER,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''');
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tiebreaker_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            level INTEGER,
            question TEXT,
            correct_answer REAL,
            user_answer REAL,
            is_correct BOOLEAN,
            used_ai_help BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''');
    db_connection.commit();
}

"""Provide a fun hint if guess is incorrect"""
def give_hint(guess: int, correct_number: int) -> str by llm();

"""Generate a math tiebreaker question with answer"""
def generate_tiebreaker(target_number: int, difficulty: str) -> dict by llm();

"""Help user understand tiebreaker solution"""
def explain_tiebreaker_solution(question: str, correct_answer: float) -> str by llm();

"""Analyze game history and suggest next guess"""
def predict_next_guess(session_id: str, min_range: int, max_range: int, trials_left: int) -> str by llm();

"""Log guess to database"""
def log_guess(session_id: str, level: int, guess: int, correct_number: int, result: str, hint: str) -> None {
    cursor = db_connection.cursor();
    cursor.execute('''
        INSERT INTO game_history (session_id, level, guess, correct_number, result, hint)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, level, guess, correct_number, result, hint));
    db_connection.commit();
}

"""Get game history for prediction"""
def get_game_history(session_id: str) -> list {
    cursor = db_connection.cursor();
    cursor.execute('''
        SELECT guess, result, hint, timestamp 
        FROM game_history 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''', (session_id,));
    return cursor.fetchall();
}

# Node definitions
node difficulty_level {
    has level_number: int;
    has min_range: int;
    has max_range: int;
    has max_trials: int;
    has level_name: str;
}

node game_state {
    has session_id: str;
    has correct_number: int;
    has trials_used: int = 0;
    has bonus_trials: int = 0;
    has consecutive_correct: int = 0;
    has total_score: int = 0;
    has current_range: tuple = (1, 20);
}

node reward_milestone {
    has milestone_name: str;
    has threshold: int;
    has reward_points: int;
    has collected: bool = False;
}

node tiebreaker {
    has question: str;
    has correct_answer: float;
    has attempts_left: int = 1;
}

node tournament {
    has tournament_id: str;
    has rounds_played: int = 0;
    has rounds_won: int = 0;
}

# Walker definitions
walker GuessGame {
    has guess: int;
    has session_id: str;

    can start with `root entry;
    can process_guess with game_state entry;
    can check_rewards with reward_milestone entry;
}

walker RewardWalker {
    has session_id: str;
    has game_state_node: game_state;

    can check_milestones with reward_milestone entry;
}

walker TiebreakerWalker {
    has user_answer: float;
    has session_id: str;
    has use_ai_help: bool = False;

    can solve_tiebreaker with tiebreaker entry;
}

walker TournamentWalker {
    has session_id: str;

    can manage_tournament with tournament entry;
    can start_round with tournament entry;
}

walker DifficultyWalker {
    has performance_score: float;

    can adjust_difficulty with difficulty_level entry;
}

# Initialize on startup
with entry:__main__ {
    init_database();

    # Create difficulty graph
    root ++> difficulty_level(
        level_number=1,
        min_range=1,
        max_range=20,
        max_trials=3,
        level_name="Beginner"
    );

    medium = root ++> difficulty_level(
        level_number=2,
        min_range=1,
        max_range=50,
        max_trials=5,
        level_name="Intermediate"
    );

    hard = root ++> difficulty_level(
        level_number=3,
        min_range=1,
        max_range=100,
        max_trials=7,
        level_name="Advanced"
    );

    expert = root ++> difficulty_level(
        level_number=4,
        min_range=1,
        max_range=200,
        max_trials=10,
        level_name="Expert"
    );

    # Link difficulty levels
    [root --> (`?difficulty_level)][0] ++> medium;
    medium ++> hard;
    hard ++> expert;

    # Create reward milestones
    root ++> reward_milestone(
        milestone_name="5 Correct Guesses",
        threshold=5,
        reward_points=50
    );

    root ++> reward_milestone(
        milestone_name="3 Wins in a Row",
        threshold=3,
        reward_points=100
    );

    root ++> reward_milestone(
        milestone_name="Level 3 Achieved",
        threshold=3,
        reward_points=200
    );

    print("Enhanced Guess Game Initialized!");
    print("Database tables created successfully.");
}