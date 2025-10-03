# 🚀 Quick Start Guide - Enhanced Guessing Game

Get up and running in 5 minutes!

## ⚡ Super Quick Setup

### Step 1: Install Dependencies
```bash
pip install jaclang gradio sqlite3 google-generativeai
```

### Step 2: Set Up Gemini API Key
```bash
# Get your free API key from: https://makersuite.google.com/app/apikey
export GEMINI_API_KEY="your_api_key_here"
```

### Step 3: Run the Game
```bash
# Launch Gradio Dashboard
python gradio_interface.py

# OR run via Jac CLI
jac run guess_game_enhanced.jac
```

### Step 4: Open Your Browser
```
Navigate to: http://localhost:7860
```

---

## 🎮 First Game Tutorial

### 1. Start Your First Game
- Click **"🎮 Start New Game"** button
- You'll see: "Guess a number between 1 and 20"
- You have 3 trials to start

### 2. Make Your First Guess
- Enter a number (try 10 - the middle!)
- Click **"🎯 Submit Guess"**
- Get feedback: Too High, Too Low, or Correct!

### 3. Win Your First Round
- **Correct guess?** You get:
  - Points (90-100 depending on trials used)
  - +1 bonus trial for next round
  - A new number to guess!
- **Wrong guess?** You get:
  - A creative hint from Gemini AI
  - Remaining trials count
  - Keep guessing!

### 4. Handle Your First Tiebreaker
If you use all trials without guessing correctly:
- You'll get a math problem
- The answer equals the correct number!
- Use the calculator (expand it from accordion)
- Or ask Gemini for help (costs 20 points)
- **Solve it correctly** = Trials refilled, game continues!
- **Fail it** = Game ends, see your summary

### 5. Use the AI Assistant
Click on the chat box at the bottom:
- Type: **"predict the next number"**
- Gemini analyzes your guess history
- Suggests optimal strategy using binary search
- Explains why that guess is best!

---

## 🎯 Pro Tips for Beginners

### The Binary Search Strategy
1. **First guess**: Always start at the middle (10 for range 1-20)
2. **Too high?** Next guess: middle of lower half
3. **Too low?** Next guess: middle of upper half
4. **Example**:
   - Guess 10 → Too high
   - Guess 5 → Too low
   - Guess 7 or 8 → You're narrowing it down!

### Maximizing Your Score
- ✅ Guess correctly on 1st trial = 100 points
- ✅ Guess correctly on 2nd trial = 90 points
- ✅ Guess correctly on 3rd trial = 80 points
- 🔥 3 correct in a row = +50 bonus!
- 💎 Each correct guess = +1 trial forever

### When to Use AI Help
- **For predictions**: FREE! Ask anytime for strategy
- **For tiebreakers**: -20 points, but might save your game
- **Tip**: Try solving tiebreaker yourself first using calculator

---

## 📊 Understanding the Interface

### Main Panels

```
┌─────────────────────────────────────────────────┐
│  📋 HOW TO PLAY    │  🎮 GAME STATUS            │
│  (Instructions)    │  (Current game info)        │
│                    │                             │
│                    │  [Start] [Stats] buttons    │
│                    │                             │
│                    │  Your Guess: [____]         │
│                    │  [Submit Guess]             │
│                    │                             │
│                    │  Tiebreaker: [____]         │
│                    │  [Submit Answer]            │
└─────────────────────────────────────────────────┘
│  🧮 CALCULATOR (Expandable)                     │
│  [Num1] [Operation] [Num2] = [Result]          │
└─────────────────────────────────────────────────┘
│  💬 CHAT WITH GEMINI AI                         │
│  [Chat messages display here]                   │
│  [Type your message...] [Send]                  │
└─────────────────────────────────────────────────┘
│  📜 GAME HISTORY (Expandable)                   │
│  [Previous guesses and results]                 │
└─────────────────────────────────────────────────┘
```

---

## 🎓 Learning the Mechanics

### Bonus Trial System Explained
```
Start: 3 trials
Correct guess #1: 3 + 1 = 4 trials now
Correct guess #2: 4 + 1 = 5 trials now
Correct guess #3: 5 + 1 = 6 trials now + 50 bonus points!

This is cumulative - you keep building up trials!
```

### Tiebreaker Math Examples

**Easy Tiebreaker (Correct answer: 18)**
```
Question: "A rectangle has length 5m and area 20m².
           What is the perimeter?"

Solution:
1. Area = length × width
2. 20 = 5 × width
3. width = 4m
4. Perimeter = 2(length + width) = 2(5 + 4) = 18m ✓

Use calculator: 20 ÷ 5 = 4, then 2 × (5 + 4) = 18
```

**Medium Tiebreaker (Correct answer: 7)**
```
Question: "Solve for x: 3x + 5 = 26"

Solution:
1. Subtract 5: 3x = 21
2. Divide by 3: x = 7 ✓

Use calculator: 26 - 5 = 21, then 21 ÷ 3 = 7
```

### Level Progression

| Current Level | Performance Needed | Next Level |
|---------------|-------------------|------------|
| 1 (1-20) | 75%+ accuracy, avg ≤2 trials | 2 (1-50) |
| 2 (1-50) | 75%+ accuracy, avg ≤3 trials | 3 (1-100) |
| 3 (1-100) | 75%+ accuracy, avg ≤5 trials | 4 (1-200) |
| 4 (1-200) | You've mastered it! | 👑 |

---

## 🔥 Common Scenarios

### Scenario 1: Hot Streak! 🎉
```
You: Guess 10 → Correct! (100 pts, +1 trial)
You: Guess 15 → Correct! (100 pts, +1 trial)
You: Guess 8  → Correct! (100 pts, +1 trial, +50 streak bonus!)

Result: 350 points, 6 trials for next round!
```

### Scenario 2: Tiebreaker Comeback 💪
```
Round 1: Wrong, Wrong, Wrong → Out of trials!
Tiebreaker: "Solve for x: 2x + 3 = 15"
You: Calculate... 15 - 3 = 12, 12 ÷ 2 = 6 ✓
Result: Trials refilled! Game continues!
```

### Scenario 3: Using AI Strategically 🤖
```
Your guesses so far:
- 10 → Too high
- 5 → Too low
- 8 → Too high

Ask Gemini: "predict next number"
Gemini: "The number is between 5 and 8. Try 6 or 7.
         With binary search, try 6 first!"
You: Guess 6 → Correct! 🎯
```

---

## 🛠️ Calculator Quick Reference

### Basic Operations
- **Addition**: 5 + 3 = 8
- **Subtraction**: 10 - 4 = 6
- **Multiplication**: 6 × 3 = 18
- **Division**: 20 ÷ 5 = 4

### Advanced Operations
- **Power**: 2 ^ 3 = 8 (2 cubed)
- **Square Root**: √16 = 4 (only uses first number)

### Tiebreaker Usage
```
Problem: "Rectangle area = 35m², length = 7m. Find perimeter."

Step 1: Find width
  - Calculator: 35 ÷ 7 = 5

Step 2: Calculate perimeter
  - Calculator: 7 + 5 = 12
  - Calculator: 12 × 2 = 24

Answer: 24m
```

---

## 📈 Tracking Your Progress

### View Stats Anytime
Click **"📊 View Stats"** to see:
- Current score
- Accuracy percentage
- Win streak
- Bonus trials accumulated
- Level progress

### Check History
Expand **"📜 View Game History"** to review:
- All your guesses
- Results (too high/low/correct)
- Hints received
- Timestamps

### Achievements to Unlock
- 🎯 First Victory (25 pts)
- ⭐ 5 Correct Guesses (50 pts)
- 🔥 3 Wins in a Row (100 pts)
- 📈 Level 2 Achieved (75 pts)
- 🏆 Level 3 Achieved (150 pts)
- 👑 Level 4 Achieved (300 pts)
- 💎 Perfect Score - 1000+ (500 pts)
- 🧠 Tiebreaker Master (200 pts)

---

## 🎮 Game Modes

### Standard Mode (Default)
- Play casually at your own pace
- Build up trials and score
- Progress through levels

### Speed Challenge (Coming Soon)
- Complete X correct guesses in time limit
- Bonus points for speed
- Extra pressure!

### Tournament Mode (CLI Only)
```bash
jac run guess_game_enhanced.jac --tournament
```
- Multiple rounds
- Track overall performance
- Compete for best score

---

## 🐛 Troubleshooting

### "Please start a game first"
**Fix**: Click the green **"🎮 Start New Game"** button

### Calculator not appearing
**Fix**: Click on **"🧮 Calculator"** accordion to expand it

### Gemini not responding
**Fix**: Check your API key is set correctly
```bash
echo $GEMINI_API_KEY
# Should show your key, not empty
```

### Game froze / Not responding
**Fix**: Refresh the page and start a new game

### Want to reset everything
**Fix**: Delete the database and restart
```bash
rm guess_game_history.db
python gradio_interface.py
```

---

## 🎯 Your First Session Goals

### Beginner Goals (First 10 minutes)
- ✅ Start your first game
- ✅ Make 5 guesses
- ✅ Get 1 correct guess
- ✅ Earn your first bonus trial
- ✅ Ask Gemini for help once

### Intermediate Goals (First 30 minutes)
- ✅ Score 300+ points
- ✅ Win 3 games in a row
- ✅ Complete a tiebreaker
- ✅ Unlock 3 achievements
- ✅ Reach Level 2

### Advanced Goals (First Hour)
- ✅ Score 1000+ points
- ✅ Reach Level 3
- ✅ Maintain 80%+ accuracy
- ✅ Win 5 tiebreakers
- ✅ Earn the "Guessing Guru" rank

---

## 💡 Strategy Cheat Sheet

### Best Opening Moves by Level
```
Level 1 (1-20):   Start with 10
Level 2 (1-50):   Start with 25
Level 3 (1-100):  Start with 50
Level 4 (1-200):  Start with 100
```

### Optimal Guess Sequence (Example: Range 1-20)
```
Guess 1: 10
  - Too high? → Guess 5
  - Too low?  → Guess 15

Guess 2: 5 (if too high)
  - Too high? → Guess 3
  - Too low?  → Guess 7

Guess 3: Narrow it down to 2-3 possibilities
```

### When You're Down to Last Trial
- **Ask Gemini for prediction** (it's free!)
- Use binary search logic
- Make your best educated guess
- If wrong, prepare for tiebreaker

### Tiebreaker Strategy
1. Read problem carefully
2. Identify what's being asked
3. Use calculator for each step
4. Double-check your answer
5. Only use AI help if really stuck

---

## 🎊 Ready to Play!

You now know everything to start playing and winning!

### Quick Recap
1. **Start game** → You have 3 trials
2. **Guess strategically** → Use binary search
3. **Win round** → Get +1 trial and points
4. **Repeat** → Build trials and score
5. **Level up** → Harder ranges, more trials
6. **Use AI** → For strategy (free) or help (-20 pts)
7. **Have fun!** → It's a game, enjoy! 🎮

---

## 🚀 Launch Command

```bash
python gradio_interface.py
```

**Then open:** http://localhost:7860

---

**Good luck, and may your guesses be ever accurate! 🎯✨**

---

## 📚 Next Steps

Once you're comfortable:
- Read the full README.md for advanced features
- Explore the Jac code to understand graph mechanics
- Try tournament mode
- Modify difficulty settings in config_utils.jac
- Challenge friends to beat your high score!

**Have questions?** Check the README troubleshooting section or experiment with the code!