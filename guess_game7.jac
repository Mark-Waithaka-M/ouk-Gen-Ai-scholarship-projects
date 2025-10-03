"""A Number Guessing Game - structural Jac file
"""


import random;
import from byllm.llm { Model }


# configure your model (example placeholder)
glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);


# LLM hint function signature (implemented by host environment)
def give_hint(guess: int, correct_number: int, context: str="") -> str by llm();


a walker GuessGame {
    has player_id: int;
    has level: int = 1;
    has range_min: int = 1;
    has range_max: int = 20;
    has attempts_allowed: int = 3; # base attempts per level
    has attempts_used: int = 0;
    has bonus_attempts: int = 0; # extra attempts granted on correct guesses
    has correct_number: int;
    has stage_trials: int = 0; # total trials in this stage
    has total_points: int = 0;
    has last_feedback: str = "";


    can start with `root entry;
    can process_guess with turn entry;
    can tie_breaker with turn entry;
    can level_up with turn entry;
    can end_stage with turn entry;
}


node turn {
    has correct_number: int = random.randint(1, 20);
}


# CLI convenience: spawn a few sample players when running locally
with entry:__main__ {
    root spawn GuessGame(1);
}