Python to Jac Project: Enhanced Number Guessing Game (Challenge Edition)
Overview
This project serves as a comprehensive study in converting a feature-rich, object-oriented Python application into a Jac (Jaseci's programming language) application. The goal is to highlight how procedural and class-based complexity in Python can be more elegantly and intuitively represented using Jac's graph-based programming model (nodes, edges, and walkers).

The current artifact is the Python implementation, featuring a highly interactive Gradio UI, complex game logic, dynamic challenges, and data persistence using SQLite.

Project Goals
Python Implementation: Create a robust and scalable number guessing game using Python best practices (completed).

Feature Expansion: Incorporate dynamic challenge mechanics and AI integration to create a challenging and interactive experience (completed).

Jac Translation: Translate the final Python architecture into a Jac program, specifically focusing on replacing object state management and conditional logic with Graph Nodes and Walkers.

Comparative Analysis: Document the differences in structure, scalability, and readability between the two approaches.

Prerequisites
To run the game, you need:

Python 3.8+

Gradio: For the interactive web interface.

Requests: For API communication with Gemini.

An API Key: A valid Gemini API key is required and must be provided in the API_KEY variable within the Python file for the AI chat and solver features to function.

How to Run
Install Dependencies:

pip install -r requirements.txt

Insert API Key: Open the Python file and replace the placeholder value for API_KEY with your actual key.

Execute the Script:

python expanded_guessing_game3.py

The application will launch in your browser via Gradio.

Current Features (Python Implementation)
The core logic of the game, managed by the GameState class, now implements a challenging progression system:

1. Dynamic Progression and Challenge System
Dynamic Difficulty: The game difficulty increases by 1 after every correct guess, tracked as Difficulty 1, 2, 3....

Expanding Range: The number guessing range expands dynamically with the difficulty level. The range is set from 1 to 10×Difficulty (e.g., D1: 1-10, D2: 1-20, D3: 1-30, etc.).

Challenge Trigger: The player has 5 attempts per round. Running out of attempts immediately halts the guessing round and triggers a Challenge sequence.

2. Mandatory Challenge System
If the player fails to guess the number, they must pass two consecutive challenges to resume the guessing game:

Sequence Challenge: The first failure triggers a challenge requiring the user to identify the next number in a mathematical sequence.

Tie-Breaker Challenge: If the player fails the Sequence Challenge, they proceed to a final, general knowledge Tie-Breaker question.

Game Conclusion: The overall game is won or lost based on the outcome of the Tie-Breaker Challenge, and the final result is immediately saved.

3. Gemini API Integration (Game Master AI)
The game incorporates robust AI interaction features powered by the Gemini 2.5 Flash API:

Contextual Chat: A dedicated Chatbot allows players to ask the Game Master AI for conversational hints regarding the guessing range or general questions.

Challenge Solver: A unique feature where the player can press a button to ask the AI to provide the correct answer and a generated explanation for the current Sequence or Tie-Breaker question.

Robust Parsing: Custom logic is implemented to ensure the AI's structured responses are correctly parsed to extract the official answer and explanation without crashing the Gradio UI.

4. Persistence and UI
Database: Game results (final score, attempts, Win/Loss status, and Difficulty Reached) are saved to a local SQLite database (guessing_game_results.db).

User Interface: A custom-styled Gradio UI provides an interactive interface featuring:

Real-time stats tracking (Score, Attempts, Range).

Dedicated interface switching between the Guessing Area and the Challenge Area.

A Calculator Toggle to show/hide a simple utility component.