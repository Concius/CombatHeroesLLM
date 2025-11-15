# This replaces the simple CoT prompt.
propose_prompt = """
You are an expert fencer in a strategic duel.
Your task is to choose your next action by simulating three possible 'parallel universes' of what might happen next.

---
GAME STATE & RULES:
{input}

STRATEGIC RULES (Rock-Paper-Scissors dynamic):
- ATTACK beats FEINT (The Feinter loses 1 HP)
- FEINT beats KICKS (The Kicker gets 'Cannot Kick' for 1 turn)
- KICKS beats DEFEND (The Defender loses 1 HP)
- DEFEND beats ATTACK (The Attacker gets 'Cannot Attack' for 1 turn)
- Identical moves cancel out.

---
INSTRUCTIONS:
Generate 3 distinct 'universes' (trajectories). For each, propose one of your available actions and then predict your opponent's *most likely* counter-move.
Evaluate the outcome of this 2-move exchange.

Universe 1:
- My Action: [ACTION 1]
- Opponent's Likely Response: [OPPONENT_ACTION]
- Outcome: [Describe the resulting HP and debuff state and why it's good or bad for you]

Universe 2:
- My Action: [ACTION 2]
- Opponent's Likely Response: [OPPONENT_ACTION]
- Outcome: [Describe the resulting HP and debuff state and why it's good or bad for you]

Universe 3:
- My Action: [ACTION 3]
- Opponent's Likely Response: [OPPONENT_ACTION]
- Outcome: [Describe the resulting HP and debuff state and why it's good or bad for you]

---
FINAL RECOMMENDATION:
Based on your 3 simulations, which *first action* is the best?
Output your single best action from the "Available Actions" list and nothing else.
"""

# This value prompt is no longer used by our main script,
# but it's good to keep for future experiments (like Idea 4).
value_prompt = """
You are an expert fencing analyst.
Evaluate the following game state from the player's perspective.
Your goal is to win (opponent HP = 0).

CURRENT STATE:
{input}

Consider all factors:
- Your HP vs. Opponent HP. (A lead is good, being behind is bad).
- Your Status. (Being debuffed is bad).

Rate the strategic value of this position.
Provide a score from 1 (terrible, likely to lose) to 10 (excellent, likely to win).
Output only the number.

Example:
8
"""