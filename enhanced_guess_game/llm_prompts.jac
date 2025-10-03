"""LLM Prompt Implementations for Enhanced Guess Game"""

# Hint Generation Prompt
can give_hint(guess: int, correct_number: int) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.9
) {
    '''
    You are a creative hint generator for a number guessing game.
    
    Given:
    - User's guess: {guess}
    - Correct number: {correct_number}
    
    Generate a fun, creative hint that helps the user without revealing the exact number.
    Use metaphors, analogies, or playful language. Be encouraging!
    
    Examples:
    - "You're in the right neighborhood, but need to climb a few floors higher! 🏢"
    - "Like Goldilocks, you're getting warmer... but not quite porridge-perfect yet! 🥣"
    - "Think of it as a thermometer reading - you're still in the chilly zone! ❄️"
    
    Keep it brief (1-2 sentences) and fun!
    '''
}

# Tiebreaker Question Generation
can generate_tiebreaker(target_number: int, difficulty: str) -> dict by llm(
    incl_context=True,
    reason=True,
    temperature=0.7,
    return_json=True
) {
    '''
    Generate a creative math problem where the answer equals the target number.
    
    Target answer: {target_number}
    Difficulty level: {difficulty}
    
    Create a real-world scenario problem (geometry, algebra, or word problem) that naturally
    results in the target number as the answer.
    
    Return a JSON object with:
    {
        "question": "The complete problem statement",
        "answer": the_numeric_answer (float),
        "solution_steps": "Brief explanation of how to solve it",
        "problem_type": "geometry/algebra/arithmetic/word_problem"
    }
    
    Examples:
    
    For target_number = 18:
    {
        "question": "A rectangular garden has a length of 5 meters. If the area is 20 square meters, what is the perimeter in meters?",
        "answer": 18.0,
        "solution_steps": "Width = 20/5 = 4m. Perimeter = 2(5+4) = 18m",
        "problem_type": "geometry"
    }
    
    For target_number = 7:
    {
        "question": "Solve for x: 3x + 5 = 26",
        "answer": 7.0,
        "solution_steps": "3x = 26 - 5 = 21, x = 21/3 = 7",
        "problem_type": "algebra"
    }
    
    Make it appropriate for the difficulty level:
    - "easy": Simple arithmetic, basic geometry
    - "medium": Multi-step problems, rectangles/triangles
    - "hard": Complex word problems, equations with multiple operations
    '''
}

# Tiebreaker Solution Explanation
can explain_tiebreaker_solution(question: str, correct_answer: float) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.5
) {
    '''
    Explain how to solve this tiebreaker math problem step-by-step.
    
    Problem: {question}
    Correct Answer: {correct_answer}
    
    Provide a clear, educational explanation that:
    1. Identifies what type of problem it is
    2. Lists the given information
    3. Shows the formula or method to use
    4. Works through the calculation step-by-step
    5. Verifies the answer
    
    Use clear formatting with bullet points or numbered steps.
    Be encouraging and educational, like a friendly tutor!
    
    Keep it concise (4-6 steps maximum).
    '''
}

# Prediction and Strategy Assistant
can predict_next_guess(session_id: str, min_range: int, max_range: int, trials_left: int) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.6
) {
    '''
    You are a strategic game advisor helping a player make optimal guesses.
    
    Current game state:
    - Possible range: {min_range} to {max_range}
    - Trials remaining: {trials_left}
    
    The game history will be provided in context showing previous guesses and results.
    
    Analyze the history and provide:
    1. What the guess history tells us about the correct number
    2. The optimal next guess using binary search strategy
    3. Why this guess is strategic
    4. The probability of success
    
    Use game theory and binary search principles. Be encouraging but analytical!
    
    Format your response like:
    🎯 Strategic Analysis:
    [Your analysis]
    
    💡 Recommended Next Guess: [number]
    
    📊 Why this works:
    [Explanation]
    
    🎲 Your odds: [probability explanation]
    '''
}

# Game Summary Generator
can generate_game_summary(
    total_score: int,
    games_won: int,
    games_lost: int,
    highest_level: int,
    accuracy: float,
    total_guesses: int
) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.8
) {
    '''
    Generate an engaging game summary report for the player.
    
    Statistics:
    - Total Score: {total_score}
    - Games Won: {games_won}
    - Games Lost: {games_lost}
    - Highest Level: {highest_level}
    - Accuracy: {accuracy}%
    - Total Guesses: {total_guesses}
    
    Create a fun, personalized summary that:
    1. Celebrates their achievements with emojis
    2. Highlights impressive stats
    3. Provides constructive feedback on areas to improve
    4. Gives them a fun title/rank based on performance
    5. Encourages them to play again
    
    Be creative with titles like "Number Ninja", "Guessing Guru", "Math Wizard", etc.
    
    Use formatting, emojis, and make it engaging!
    '''
}

# Dynamic Difficulty Advisor
can suggest_difficulty_adjustment(
    correct_rate: float,
    avg_trials_used: float,
    consecutive_wins: int,
    current_level: int
) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.5
) {
    '''
    Analyze player performance and suggest difficulty adjustments.
    
    Performance metrics:
    - Success rate: {correct_rate}%
    - Average trials per game: {avg_trials_used}
    - Win streak: {consecutive_wins}
    - Current level: {current_level}
    
    Determine if the player should:
    - LEVEL UP: Move to harder difficulty (if performing very well)
    - STAY: Current difficulty is appropriate
    - LEVEL DOWN: Move to easier difficulty (if struggling)
    
    Provide:
    1. Your recommendation (LEVEL UP/STAY/LEVEL DOWN)
    2. Reasoning based on the metrics
    3. Encouragement and tips
    
    Response format:
    **Recommendation:** [LEVEL UP/STAY/LEVEL DOWN]
    
    **Analysis:**
    [Your reasoning]
    
    **Tips:**
    [Helpful advice]
    '''
}

# Reward Flavor Text Generator
can generate_reward_message(
    milestone_name: str,
    points_earned: int,
    achievement_context: str
) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.9
) {
    '''
    Generate an exciting reward announcement message!
    
    Milestone achieved: {milestone_name}
    Points earned: {points_earned}
    Context: {achievement_context}
    
    Create a celebratory message that:
    - Uses exciting language and emojis
    - Makes the player feel accomplished
    - Is brief but impactful (2-3 sentences)
    
    Examples:
    "🎊 LEGENDARY! You've cracked the code 5 times in a row! Your pattern recognition is off the charts! +50 bonus points!"
    
    "⚡ UNSTOPPABLE! Three perfect predictions - you're reading this game like a book! +100 points to your mastery!"
    
    Be creative and enthusiastic!
    '''
}

# Tutorial/Help Content Generator
can generate_tutorial_section(topic: str) -> str by llm(
    incl_context=True,
    reason=True,
    temperature=0.6
) {
    '''
    Generate helpful tutorial content for a specific game topic.
    
    Topic: {topic}
    
    Available topics:
    - "binary_search_strategy"
    - "tiebreaker_math_tips"
    - "scoring_system"
    - "difficulty_levels"
    - "bonus_trials"
    - "using_ai_assistant"
    
    Provide clear, concise explanations with:
    1. What it is
    2. How it works
    3. Pro tips for using it effectively
    4. Common mistakes to avoid
    
    Use examples and be beginner-friendly!
    Format with headers, bullets, and emojis for readability.
    '''
}

# Hint Quality Evaluator (for testing)
can evaluate_hint_quality(hint: str, guess: int, correct: int) -> dict by llm(
    incl_context=True,
    reason=True,
    temperature=0.3,
    return_json=True
) {
    '''
    Evaluate the quality of a generated hint.
    
    Hint: {hint}
    User guess: {guess}
    Correct answer: {correct}
    
    Rate the hint on:
    1. Helpfulness (1-5): Does it guide without giving away the answer?
    2. Creativity (1-5): Is it engaging and fun?
    3. Clarity (1-5): Is it easy to understand?
    4. Appropriate difficulty (1-5): Not too easy or hard?
    
    Return JSON:
    {
        "helpfulness": score,
        "creativity": score,
        "clarity": score,
        "difficulty": score,
        "overall": average_score,
        "feedback": "Brief comment on the hint quality"
    }
    '''
}