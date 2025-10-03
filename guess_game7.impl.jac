# Implementation of GuessGame walkers


if self.guess < here.correct_number {
self.last_feedback = give_hint(self.guess, here.correct_number, "low");
print(self.last_feedback);
# if still attempts left, keep same turn; otherwise go to end_stage
if self.attempts_used < total_available {
here ++> turn(here.correct_number);
} else {
visit [root];
}
} elif self.guess > here.correct_number {
self.last_feedback = give_hint(self.guess, here.correct_number, "high");
print(self.last_feedback);
if self.attempts_used < total_available {
here ++> turn(here.correct_number);
} else {
visit [root];
}
} else {
# correct guess
print("Congratulations! You guessed correctly.");
# reward: +1 bonus attempt for future, and points
self.bonus_attempts = self.bonus_attempts + 1;
self.total_points = self.total_points + max(1, (total_available - self.attempts_used + 1) );
# if the guess was on the 10th trial and it was allowed, record special message
print("Bonus granted: +1 attempt for future levels.");
# after a correct guess allow player to proceed (stay in the game)
here ++> turn(here.correct_number);
}
}


impl GuessGame.end_stage {
# Called when attempts exhausted or when host decides to end a stage
total_available = self.attempts_allowed + self.bonus_attempts;
if self.attempts_used >= total_available and self.guess != here.correct_number {
# stage lost, offer tie-breaker
print("Stage lost. Entering tie-breaker opportunity.");
visit [root];
} else {
# stage cleared, level up
visit [root];
}
}


impl GuessGame.tie_breaker {
# placeholder: invoke LLM to produce a simple arithmetic puzzle
# host environment should call the llm with a prompt and present the puzzle to the player
print("Generating tie-breaker question via LLM...");
disengage;
}


impl GuessGame.level_up {
# increase difficulty: expand range and refill attempts
self.level = self.level + 1;
# Example progression: level 1 -> 1-20, level 2 -> 1-50, level 3 -> 1-100
if self.level == 2 {
self.range_max = 50;
} elif self.level == 3 {
self.range_max = 100;
} else {
self.range_max = self.range_max + int(self.range_max * 0.5);
}
# refill attempts (base plus existing bonus)
self.attempts_used = 0;
self.attempts_allowed = self.attempts_allowed + 1; # slightly harder but add one base attempt
here ++> turn(random.randint(self.range_min, self.range_max));
}