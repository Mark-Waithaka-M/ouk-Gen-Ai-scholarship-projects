impl GuessGame.start {
    # 1. Initialize walker references
    self.state_node = [root --> GameState];
    self.difficulty_node = [root --> Difficulty.name == "Easy"];

    if not self.difficulty_node {
        print("Error: Difficulty nodes not initialized in graph.");
        disengage;
    }

    # 2. Find or create the turn node attached to the current difficulty
    next_turn = [self.difficulty_node --> (`?turn)] | self.difficulty_node ++> turn;

    # 3. Set the correct number based on the current difficulty range
    range_min = self.difficulty_node.min_range;
    range_max = self.difficulty_node.max_range;
    next_turn.correct_number = random.randint(range_min, range_max);

    # 4. Provide current round info
    trials_remaining = self.initial_trials - self.current_trial + 1 + self.bonus_trials;
    print(f"--- Starting Round ({self.difficulty_node.name} Mode) ---");
    print(f"Guess a number between {range_min} and {range_max}.");
    print(f"You have {trials_remaining} guesses remaining (Base: {self.initial_trials}, Bonus: {self.bonus_trials}).");

    visit next_turn;
}

impl GuessGame.process_guess {

    current_trials_allowed = self.initial_trials + self.bonus_trials;

    # Check for loss condition BEFORE processing the current guess
    if self.current_trial > current_trials_allowed {
        print("\n--- GAME OVER (LOSS) ---");
        print(f"You used all {current_trials_allowed} trials. The correct number was {here.correct_number}. You lost this round.");
        self.state_node.consecutive_correct_guesses = 0;
        disengage;
    }

    if self.guess == here.correct_number {
        # --- Correct Guess (WIN) ---
        print("\n*** CONGRATULATIONS! You guessed correctly! ***");

        # 1. Update Game State and grant base bonus for winning
        self.state_node.total_correct_guesses += 1;
        self.state_node.consecutive_correct_guesses += 1;
        self.bonus_trials += 1;

        print(f"Trial history: {self.current_trial} used.");
        print("BONUS: Your guessing chances have been increased by 1 for the next game!");

        # 2. Check for Rewards (Reward Network traversal)
        here spawn RewardWalker(state_node=self.state_node, game_walker=self);

        # 3. Dynamic Difficulty Adjustment (Graph Traversal FORWARD)
        next_difficulty = [self.difficulty_node --> Difficulty];

        if next_difficulty {
            self.difficulty_node = next_difficulty;
            print(f"Difficulty increased! Moving to {self.difficulty_node.name} (1-{self.difficulty_node.max_range}).");
        } else {
            print("You are at the maximum difficulty (Hard).");
        }

        # 4. Continuous Play: Prepare for the next round
        here.correct_number = random.randint(
            self.difficulty_node.min_range,
            self.difficulty_node.max_range
        );
        self.current_trial = 1; # Reset trial count for the new round

        # Revisit the turn node to continue the game loop (waiting for the next external guess)
        visit here;

    } else {
        # --- Incorrect Guess (LOSS OF TRIAL) ---

        # 1. Provide Hint using LLM
        hint = give_hint(self.guess, here.correct_number);
        print(f"Wrong guess (Trial {self.current_trial}/{current_trials_allowed}): {hint}");

        # 2. Update trial count and reset streak
        self.current_trial += 1;
        self.state_node.consecutive_correct_guesses = 0;

        # 3. Dynamic Difficulty (Penalty: traverse BACKWARD if possible)
        prev_difficulty = [self.difficulty_node <-- Difficulty];

        if prev_difficulty and self.difficulty_node.name != "Easy" {
             self.difficulty_node = prev_difficulty;
             print(f"Difficulty lowered! Moving back to {self.difficulty_node.name}.");
        }

        # If this guess depleted the trials, handle game over
        if self.current_trial > current_trials_allowed {
            print("\n--- GAME OVER (LOSS) ---");
            print(f"You ran out of trials! The correct number was {here.correct_number}.");
            disengage;
        } else {
            # Continue waiting for the next guess
            visit here;
        }
    }
}

impl RewardWalker.check_rewards {
    # Traverse all uncollected reward nodes attached to the root
    for reward_node in [root --> Reward(collected=false)] {
        if self.state_node.consecutive_correct_guesses >= reward_node.condition {

            # Milestone hit! Apply reward and mark as collected
            self.game_walker.bonus_trials += reward_node.reward_value;
            reward_node.collected = true;

            print(f"\n<<< REWARD UNLOCKED: {reward_node.name} >>>");
            print(f"You earned {reward_node.reward_value} additional bonus trial(s)! Total bonus trials: {self.game_walker.bonus_trials}.");

            disengage; # Stop the reward walker after applying the reward
        }
    }
}

impl TournamentWalker.start_tournament {
    print(f"\n==============================================");
    print(f"*** Starting {self.num_rounds}-Round Guessing Tournament ***");
    print(f"==============================================");

    while self.current_round <= self.num_rounds {
        print(f"\n--- TOURNAMENT ROUND {self.current_round} ---");

        # Spawn a new GuessGame walker. The user will provide the guess externally
        # to drive the game's process_guess ability.
        root spawn GuessGame(guess=0);

        self.current_round += 1;
    }

    print("\n----------------------------------------------");
    print("Tournament Walkers Spawned.");
    print("To play, repeatedly call the 'GuessGame.process_guess' ability with your guess.");
    print("Example: jac run guess_game6.jac -w GuessGame(guess=5)");
    print("----------------------------------------------");
    disengage;
}
