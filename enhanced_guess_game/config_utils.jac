"""Configuration and Utility Functions for Enhanced Guess Game"""

import json;
import os;
from datetime import datetime, timedelta;

# ============================================================================
# GAME CONFIGURATION
# ============================================================================

glob GAME_CONFIG = {
    "difficulty_levels": [
        {
            "level": 1,
            "name": "Beginner",
            "min_range": 1,
            "max_range": 20,
            "base_trials": 3,
            "tiebreaker_difficulty": "easy"
        },
        {
            "level": 2,
            "name": "Intermediate",
            "min_range": 1,
            "max_range": 50,
            "base_trials": 5,
            "tiebreaker_difficulty": "medium"
        },
        {
            "level": 3,
            "name": "Advanced",
            "min_range": 1,
            "max_range": 100,
            "base_trials": 7,
            "tiebreaker_difficulty": "hard"
        },
        {
            "level": 4,
            "name": "Expert",
            "min_range": 1,
            "max_range": 200,
            "base_trials": 10,
            "tiebreaker_difficulty": "expert"
        }
    ],

    "scoring": {
        "base_correct_score": 100,
        "trial_penalty": 10,
        "min_score_per_correct": 10,
        "streak_bonus_threshold": 3,
        "streak_bonus_points": 50,
        "ai_help_penalty": 20,
        "tiebreaker_bonus": 30
    },

    "milestones": [
        {
            "name": "First Victory",
            "threshold": 1,
            "type": "games_won",
            "reward": 25,
            "icon": "🎯"
        },
        {
            "name": "5 Correct Guesses",
            "threshold": 5,
            "type": "correct_guesses",
            "reward": 50,
            "icon": "⭐"
        },
        {
            "name": "3 Wins in a Row",
            "threshold": 3,
            "type": "win_streak",
            "reward": 100,
            "icon": "🔥"
        },
        {
            "name": "Level 2 Achieved",
            "threshold": 2,
            "type": "level",
            "reward": 75,
            "icon": "📈"
        },
        {
            "name": "Level 3 Achieved",
            "threshold": 3,
            "type": "level",
            "reward": 150,
            "icon": "🏆"
        },
        {
            "name": "Level 4 Achieved",
            "threshold": 4,
            "type": "level",
            "reward": 300,
            "icon": "👑"
        },
        {
            "name": "Perfect Score",
            "threshold": 1000,
            "type": "total_score",
            "reward": 500,
            "icon": "💎"
        },
        {
            "name": "Tiebreaker Master",
            "threshold": 5,
            "type": "tiebreakers_won",
            "reward": 200,
            "icon": "🧠"
        }
    ],

    "ai_settings": {
        "hint_temperature": 0.9,
        "tiebreaker_temperature": 0.7,
        "explanation_temperature": 0.5,
        "prediction_temperature": 0.6,
        "summary_temperature": 0.8
    }
};

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

"""Get difficulty configuration for a specific level"""
def get_difficulty_config(level: int) -> dict {
    for config in GAME_CONFIG["difficulty_levels"] {
        if config["level"] == level {
            return config;
        }
    }
    return GAME_CONFIG["difficulty_levels"][0];  # Default to level 1
}

"""Calculate score for a correct guess based on trials used"""
def calculate_score(trials_used: int) -> int {
    base = GAME_CONFIG["scoring"]["base_correct_score"];
    penalty = GAME_CONFIG["scoring"]["trial_penalty"];
    minimum = GAME_CONFIG["scoring"]["min_score_per_correct"];

    score = base - (trials_used * penalty);
    return max(score, minimum);
}

"""Check if player should level up"""
def should_level_up(accuracy: float, avg_trials: float, current_level: int) -> bool {
    if current_level >= 4 {
        return False;  # Max level reached
    }

    # Level up criteria: 75%+ accuracy and efficient trial usage
    difficulty = get_difficulty_config(current_level);
    max_trials = difficulty["base_trials"];

    return accuracy >= 0.75 and avg_trials <= (max_trials * 0.7);
}

"""Format time duration for display"""
def format_duration(seconds: int) -> str {
    if seconds < 60 {
        return f"{seconds} seconds";
    } elif seconds < 3600 {
        minutes = seconds // 60;
        return f"{minutes} minutes";
    } else {
        hours = seconds // 3600;
        minutes = (seconds % 3600) // 60;
        return f"{hours}h {minutes}m";
    }
}

"""Generate player rank based on total score"""
def get_player_rank(total_score: int) -> dict {
    ranks = [
        {"name": "Novice Guesser", "min_score": 0, "icon": "🌱", "color": "gray"},
        {"name": "Number Apprentice", "min_score": 100, "icon": "📚", "color": "blue"},
        {"name": "Guessing Enthusiast", "min_score": 300, "icon": "🎯", "color": "green"},
        {"name": "Strategic Thinker", "min_score": 600, "icon": "🧠", "color": "purple"},
        {"name": "Math Wizard", "min_score": 1000, "icon": "🔮", "color": "orange"},
        {"name": "Number Ninja", "min_score": 1500, "icon": "🥷", "color": "red"},
        {"name": "Guessing Guru", "min_score": 2500, "icon": "🧘", "color": "gold"},
        {"name": "Grand Master", "min_score": 4000, "icon": "👑", "color": "platinum"},
        {"name": "Legend", "min_score": 6000, "icon": "⚡", "color": "rainbow"}
    ];

    current_rank = ranks[0];
    for rank in ranks {
        if total_score >= rank["min_score"] {
            current_rank = rank;
        }
    }

    return current_rank;
}

"""Calculate statistics from game history"""
def calculate_stats(game_history: list) -> dict {
    if not game_history {
        return {
            "total_guesses": 0,
            "correct_guesses": 0,
            "accuracy": 0.0,
            "avg_trials": 0.0,
            "best_streak": 0,
            "current_streak": 0
        };
    }

    total = len(game_history);
    correct = sum(1 for _, result, _ in game_history if result == "correct");

    # Calculate streaks
    current_streak = 0;
    best_streak = 0;
    temp_streak = 0;

    for _, result, _ in game_history {
        if result == "correct" {
            temp_streak += 1;
            best_streak = max(best_streak, temp_streak);
        } else {
            temp_streak = 0;
        }
    }

    # Current streak (from most recent)
    for i in range(len(game_history) - 1, -1, -1) {
        if game_history[i][1] == "correct" {
            current_streak += 1;
        } else {
            break;
        }
    }

    accuracy = (correct / total * 100) if total > 0 else 0.0;

    return {
        "total_guesses": total,
        "correct_guesses": correct,
        "accuracy": accuracy,
        "best_streak": best_streak,
        "current_streak": current_streak
    };
}

"""Export game session to JSON"""
def export_session_json(session_id: str) -> str {
    conn = db_connection;
    cursor = conn.cursor();

    # Get session data
    cursor.execute('''
        SELECT * FROM game_sessions WHERE session_id = ?
    ''', (session_id,));
    session = cursor.fetchone();

    # Get game history
    cursor.execute('''
        SELECT * FROM game_history WHERE session_id = ?
    ''', (session_id,));
    history = cursor.fetchall();

    # Get tiebreaker history
    cursor.execute('''
        SELECT * FROM tiebreaker_history WHERE session_id = ?
    ''', (session_id,));
    tiebreakers = cursor.fetchall();

    # Get chat history
    cursor.execute('''
        SELECT * FROM chat_history WHERE session_id = ?
    ''', (session_id,));
    chats = cursor.fetchall();

    export_data = {
        "session_id": session_id,
        "export_timestamp": datetime.now().isoformat(),
        "session_data": session,
        "game_history": history,
        "tiebreaker_history": tiebreakers,
        "chat_history": chats
    };

    return json.dumps(export_data, indent=2);
}

"""Generate hint categories based on difference"""
def categorize_hint(guess: int, correct: int) -> str {
    diff = abs(guess - correct);
    percentage = (diff / correct * 100) if correct != 0 else 100;

    if diff == 0 {
        return "perfect";
    } elif diff == 1 {
        return "extremely_close";
    } elif diff <= 2 {
        return "very_close";
    } elif diff <= 5 {
        return "close";
    } elif diff <= 10 {
        return "warm";
    } elif percentage <= 25 {
        return "getting_warm";
    } elif percentage <= 50 {
        return "cool";
    } else {
        return "cold";
    }
}

"""Validate guess input"""
def validate_guess(guess: int, min_range: int, max_range: int) -> tuple {
    if guess < min_range {
        return (False, f"Too low! Guess must be between {min_range} and {max_range}.");
    } elif guess > max_range {
        return (False, f"Too high! Guess must be between {min_range} and {max_range}.");
    } else {
        return (True, "Valid guess");
    }
}

"""Generate achievement notification"""
def format_achievement(milestone: dict, earned: bool) -> str {
    status = "✅" if earned else "🔒";
    icon = milestone["icon"];
    name = milestone["name"];
    reward = milestone["reward"];

    return f"{status} {icon} {name} (+{reward} pts)";
}

"""Clean old session data (older than 30 days)"""
def cleanup_old_sessions() -> int {
    cutoff_date = datetime.now() - timedelta(days=30);

    conn = db_connection;
    cursor = conn.cursor();

    cursor.execute('''
        DELETE FROM game_history 
        WHERE timestamp < ?
    ''', (cutoff_date,));

    cursor.execute('''
        DELETE FROM game_sessions 
        WHERE created_at < ?
    ''', (cutoff_date,));

    cursor.execute('''
        DELETE FROM tiebreaker_history 
        WHERE timestamp < ?
    ''', (cutoff_date,));

    cursor.execute('''
        DELETE FROM chat_history 
        WHERE timestamp < ?
    ''', (cutoff_date,));

    rows_deleted = cursor.rowcount;
    conn.commit();

    return rows_deleted;
}

"""Get leaderboard data"""
def get_leaderboard(limit: int = 10) -> list {
    conn = db_connection;
    cursor = conn.cursor();

    cursor.execute('''
        SELECT 
            session_id,
            total_score,
            highest_level,
            games_won,
            games_lost,
            created_at
        FROM game_sessions
        ORDER BY total_score DESC
        LIMIT ?
    ''', (limit,));

    return cursor.fetchall();
}

"""Format leaderboard for display"""
def format_leaderboard(leaderboard: list) -> str {
    if not leaderboard {
        return "No games played yet. Be the first!";
    }

    output = "🏆 TOP PLAYERS 🏆\n\n";

    medals = ["🥇", "🥈", "🥉"];

    for i, (session_id, score, level, won, lost, created) in enumerate(leaderboard) {
        rank = i + 1;
        medal = medals[i] if i < 3 else f"{rank}.";

        player_rank = get_player_rank(score);

        output += f"{medal} {player_rank['icon']} {player_rank['name']}\n";
        output += f"    Score: {score} | Level: {level} | W/L: {won}/{lost}\n";
        output += f"    Session: {session_id[:8]}...\n\n";
    }

    return output;
}

"""Generate daily challenge configuration"""
def generate_daily_challenge() -> dict {
    import hashlib;

    # Use current date as seed for consistent daily challenges
    today = datetime.now().strftime("%Y-%m-%d");
    seed_value = int(hashlib.md5(today.encode()).hexdigest(), 16) % 10000;

    # Generate challenge based on seed
    challenge_type = seed_value % 3;

    challenges = [
        {
            "name": "Speed Demon",
            "description": "Complete 5 correct guesses in under 2 minutes",
            "type": "speed",
            "target": 5,
            "time_limit": 120,
            "reward": 250
        },
        {
            "name": "Efficiency Expert",
            "description": "Win 3 games using only 1-2 trials each",
            "type": "efficiency",
            "target": 3,
            "max_trials": 2,
            "reward": 300
        },
        {
            "name": "Comeback King",
            "description": "Win a tiebreaker after using all trials",
            "type": "tiebreaker",
            "target": 1,
            "reward": 200
        }
    ];

    return challenges[challenge_type];
}

"""Check if milestone is achieved"""
def check_milestone_achievement(milestone: dict, game_state: dict) -> bool {
    milestone_type = milestone["type"];
    threshold = milestone["threshold"];

    if milestone_type == "games_won" {
        return game_state.get("games_won", 0) >= threshold;
    } elif milestone_type == "correct_guesses" {
        return game_state.get("correct_guesses", 0) >= threshold;
    } elif milestone_type == "win_streak" {
        return game_state.get("current_streak", 0) >= threshold;
    } elif milestone_type == "level" {
        return game_state.get("current_level", 1) >= threshold;
    } elif milestone_type == "total_score" {
        return game_state.get("total_score", 0) >= threshold;
    } elif milestone_type == "tiebreakers_won" {
        return game_state.get("tiebreakers_won", 0) >= threshold;
    }

    return False;
}

# ============================================================================
# DEBUGGING AND TESTING UTILITIES
# ============================================================================

"""Print game state for debugging"""
def debug_print_state(game_state: dict) -> None {
    print("\n" + "="*50);
    print("DEBUG: CURRENT GAME STATE");
    print("="*50);
    for key, value in game_state.items() {
        print(f"{key}: {value}");
    }
    print("="*50 + "\n");
}

"""Generate test game data"""
def generate_test_data(num_games: int = 10) -> None {
    import random;
    import uuid;

    conn = db_connection;
    cursor = conn.cursor();

    for i in range(num_games) {
        session_id = str(uuid.uuid4());

        # Random game statistics
        score = random.randint(100, 2000);
        level = random.randint(1, 4);
        won = random.randint(0, 20);
        lost = random.randint(0, 10);

        cursor.execute('''
            INSERT INTO game_sessions 
            (session_id, current_level, total_score, games_won, games_lost, highest_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, level, score, won, lost, level, "completed"));
    }

    conn.commit();
    print(f"Generated {num_games} test game sessions");
}