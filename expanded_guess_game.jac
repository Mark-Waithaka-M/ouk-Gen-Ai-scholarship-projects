"""A Number Guessing Game with Dynamic Difficulty and Rewards

This file defines the graph structure, node types, and walker declarations.
"""

import random;
import from byllm.llm { Model }

# Use gemini-2.5-flash for hint generation
glob llm = Model(model_name="gemini/gemini-2.5-flash", verbose=False);

"""Provide a fun hint if guess is incorrect"""
def give_hint(guess: int, correct_number: int) -> str by llm();

# --- Graph Structure Nodes ---

# Node to hold global, persistent game statistics
node GameState {
    has total_correct_guesses: int = 0;
    has consecutive_correct_guesses: int = 0;
}

# Nodes representing different difficulty ranges. They will be linked.
node Difficulty {
    has min_range: int;
    has max_range: int;
    has name: str;
}

# Nodes representing reward milestones, which grant bonus trials.
node Reward {
    has name: str;
    has condition: int; # e.g., 3 consecutive wins
    has reward_value: int; # e.g., 1 bonus trial
    has collected: bool = false;
}

# The node for the current round's target number. Attached to the current Difficulty node.
node turn {
    has correct_number: int;
}

# --- Walkers ---

walker GuessGame {
    has guess: int;
    has initial_trials: int = 10;
    has current_trial: int = 1;
    has bonus_trials: int = 0;

    # FIX: Using the fundamental 'node ref' pattern for graph references
    has difficulty_node: node ref;
    has state_node: node ref;

    can start with `root entry;
    can process_guess with turn entry;
}

# Walker to manage and award rewards based on GameState
walker RewardWalker {
    # FIX: Using the fundamental 'node ref' pattern for graph references
    has state_node: node ref;
    # FIX: Using the fundamental 'walker ref' pattern for walker references
    has game_walker: walker ref;
    can check_rewards;
}

# Walker to run multiple rounds sequentially (Tournament Mode)
walker TournamentWalker {
    has num_rounds: int = 3;
    has current_round: int = 1;
    can start_tournament with `root entry;
}

# Helper walker for initial graph setup
walker difficulty_setup {
    has name: str, min_range: int, max_range: int;
    with Difficulty(name=name, min_range=min_range, max_range=max_range) entry;
}


# --- Initial Graph Setup (Main Entry) ---

with entry:__main__ {
    # 1. Setup Difficulty Graph (Linked List: Easy -> Medium -> Hard)
    root spawn difficulty_setup(
        name="Easy", min_range=1, max_range=10)
        spawn difficulty_setup(
            name="Medium", min_range=1, max_range=50)
            spawn difficulty_setup(
                name="Hard", min_range=1, max_range=100);

    # 2. Setup Reward Graph (Connected to the root)
    root ++> Reward(
        name="Triple Threat",
        condition=3,
        reward_value=1);
    root ++> Reward(
        name="Five-Star General",
        condition=5,
        reward_value=2);

    # 3. Setup GameState Node (Central repository for all stats)
    root ++> GameState;

    # 4. Start the Tournament Mode
    root spawn TournamentWalker(num_rounds=3);
}
