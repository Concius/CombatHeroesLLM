# CombatHeroesLLM

Combat Heroes AI Leaderboard

An experimental platform to test and benchmark Large Language Model (LLM) reasoning capabilities, inspired by the design principles of Joe Dever's Combat Heroes gamebook series.

This project is built upon the framework from the paper **Tree of Thoughts: Deliberate Problem Solving with Large Language Models** and adapts its implementation from the official ToT repository.

## Project Overview

This platform pits two LLM agents against each other in a duel inspired by the Combat Heroes game system. The system acts as an automated referee, delivering game state information, parsing actions, and managing state transitions.

The primary goal is to create a leaderboard comparing different LLM models on their strategic, adversarial, and long-term planning capabilities in an environment with no randomness and simultaneous, hidden information.

## What is Combat Heroes?

Combat Heroes is a two-player dueling gamebook system by Joe Dever (creator of Lone Wolf). **This project is inspired by its conceptual design** as a testbed for AI reasoning due to its unique features:

- **Deterministic Gameplay**: All outcomes decided by player choices rather than randomness.
- **Adversarial & Hidden Information**: Simultaneous decision-making without knowing the opponent's choice.
- **Built-in State Machine**: Game logic structured through page references and transition tables.
- **Complex Reasoning**: Requires strategic planning, opponent modeling, and resource management.

## Technical Architecture

The system is a two-agent adaptation of the Tree of Thoughts (ToT) algorithm. Each LLM agent runs its own ToT search to decide its next move.

The game loop proceeds as follows:
1. **Deliver State**: The system delivers the current game state to both LLM agents simultaneously.
2. **Reason (ToT)**: Each LLM uses a Tree of Thoughts (ToT) process to explore potential moves, evaluate consequences, and model opponent actions.
3. **Choose Action**: Each LLM prunes its decision tree and outputs a single, formatted action from available options.
4. **Resolve**: The system collects both (hidden) choices.
5. **Transition State**: The system determines state transitions based on the combination of actions using rules inspired by the game's cross-reference system.
6. **Update**: The system transitions both players to their new states based on the outcome.
7. **Log & Repeat**: The entire process is logged. The loop repeats until a win/loss condition is met.

## Evaluation Metrics

This project benchmarks models across two categories:

### 1. Performance Metrics
- **Win Rate**: Percentage of games won against a baseline model.
- **Consecutive Victories**: Proves consistency and filters out lucky wins.

### 2. Efficiency Metrics
- **Total Token Consumption**: Average tokens used per complete game (measures cost-effectiveness).
- **Average Tree Width**: The average number of branches explored at each decision point (measures reasoning efficiency vs. brute force).
- **Average Game Length**: Number of turns to completion.

## AI Leaderboard (In-Progress)

This leaderboard tracks model performance in a head-to-head tournament.

| Rank | Model | Win Rate (vs. GPT-4) | Avg. Tokens / Game | Avg. Tree Width |
|------|-------|---------------------|-------------------|-----------------|

## Acknowledgements

- Joe Dever & Peter Parr for creating the Combat Heroes series, an incredible system for deterministic, adversarial gameplay.
- Shunyu Yao, Dian Yu, Jeffrey Zhao, et al. for their groundbreaking Tree of Thoughts paper, which provides the reasoning framework for this project.
