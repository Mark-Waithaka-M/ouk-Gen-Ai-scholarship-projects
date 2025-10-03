import random
import sqlite3
import time

# --- Database Management ---

def setup_database(db_name="guessing_game_results.db"):
    """Connects to the SQLite database and ensures the results table exists."""
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
            win_status TEXT
        )
    ''')
    conn.commit()
    return conn

# --- Game Logic ---

class Game:
    """Base class for the game."""
    def __init__(self, attempts):
        self.initial_attempts = attempts
        self.db_conn = setup_database()
        # In a real app, userId would be retrieved from an auth service, here we use a simple placeholder
        self.user_id = "anonymous_" + str(int(time.time()))

    def play(self):
        raise NotImplementedError('Subclasses must implement this method.')

    def save_result(self, correct_guesses, total_attempts_used, final_score, win_status):
        """Saves the final game result to the SQLite database."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO game_results (user_id, timestamp, correct_guesses, total_attempts_used, final_score, win_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.user_id, time.time(), correct_guesses, total_attempts_used, final_score, win_status))
        self.db_conn.commit()
        print("\n--- Game Result Saved to Database ---")
        print(f"Results for User {self.user_id} saved successfully.")

class GuessTheNumberGame(Game):
    def __init__(self, attempts=10, number_range=10):
        super().__init__(attempts)
        self.number_range = number_range
        self.remaining_attempts = attempts
        self.correct_guesses = 0
        self.total_attempts_used = 0
        self.bonus_attempts_earned = 0
        self.score = 0
        self.game_running = True
        self.generate_new_target()
        print(f"Welcome to the Enhanced Guessing Game! Range: 1 to {self.number_range}")
        print(f"You start with {self.initial_attempts} attempts.")

    def generate_new_target(self):
        """Sets a new random target number."""
        self.correct_number = random.randint(1, self.number_range)

    def calculate_reward(self):
        """Implements a reward system based on the number of correct guesses."""
        base_reward = 100
        multiplier = 1 + (self.correct_guesses * 0.25) # 25% bonus for each previous correct guess
        reward = int(base_reward * multiplier)
        self.score += reward
        return reward

    def process_guess(self, guess):
        """Checks the user's guess and updates the game state accordingly."""
        self.total_attempts_used += 1

        if guess > self.correct_number:
            print("Too high!")
        elif guess < self.correct_number:
            print("Too low!")
        else:
            # Correct Guess Logic (Non-exiting, bonus attempts, reward)
            self.correct_guesses += 1
            self.remaining_attempts += 1
            self.bonus_attempts_earned += 1
            reward_amount = self.calculate_reward()

            print(f"\n🥳 Congratulations! You guessed correctly! The number was {self.correct_number}.")
            print(f"You earned {reward_amount} points. Your total score is now {self.score}.")
            print(f"BONUS! Your guessing chances have been increased by 1.")
            self.generate_new_target()
            print(f"A new number has been chosen between 1 and {self.number_range}.")
            return

        # Decrement attempts only if the guess was wrong
        self.remaining_attempts -= 1

    def play(self):
        """The main game loop."""
        while self.game_running and self.remaining_attempts > 0:
            print(f"\n--- Round {self.correct_guesses + 1} | Score: {self.score} ---")
            print(f"Attempts left: {self.remaining_attempts} (Total Bonus Attempts: {self.bonus_attempts_earned})")

            guess_input = input(f"Guess a number between 1 and {self.number_range}: ")

            if guess_input.isdigit():
                guess = int(guess_input)
                if 1 <= guess <= self.number_range:
                    self.process_guess(guess)
                else:
                    print(f"Input is out of range! Please enter a number between 1 and {self.number_range}.")
            else:
                print("That's not a valid integer! Try again.")

        # Game Over Condition (Remaining attempts depleted)
        self.game_over()

    def game_over(self):
        """Handles the end of the game."""
        self.game_running = False

        if self.remaining_attempts <= 0:
            print("\n=============================================")
            print("🛑 GAME OVER. All your guessing chances are depleted.")
            print(f"The last number you were trying to guess was {self.correct_number}.")
            print(f"You managed to guess correctly {self.correct_guesses} times.")
            print(f"Your Final Score: {self.score} points.")
            print(f"Total Attempts Used: {self.total_attempts_used}.")
            print("=============================================")

            win_status = "LOST"
            if self.correct_guesses >= 3: # Example criteria for a 'Win' status
                 win_status = "WON"

            self.save_result(
                self.correct_guesses,
                self.total_attempts_used,
                self.score,
                win_status
            )

        self.db_conn.close()


if __name__ == '__main__':
    try:
        game = GuessTheNumberGame(attempts=5, number_range=20) # Start with 5 attempts, number range 1-20
        game.play()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
