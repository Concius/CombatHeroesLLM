import argparse
import json
import os
import re
from src.tot.models import get_model
from src.tot.tasks.fencing_game import FencingTask

def parse_action(model_output: str, available_actions: list) -> str:
    """
    Parses the raw model output to find the chosen action.
    This parser is robust: it looks for the last line that
    contains one of the valid actions.
    """
    best_action = available_actions[0] # Default action
    
    # Try to find the "FINAL RECOMMENDATION" line
    lines = model_output.strip().split('\n')
    for line in reversed(lines):
        for action in available_actions:
            if re.search(r'\b' + re.escape(action) + r'\b', line, re.IGNORECASE):
                return action # Return the first valid action found from the bottom

    # If no line matches, fall back to finding the first action anywhere
    for action in available_actions:
        if re.search(r'\b' + re.escape(action) + r'\b', model_output, re.IGNORECASE):
            return action
            
    return best_action # Return default if still nothing is found

def run_game():
    """
    Main function to run the 2-player fencing game benchmark using
    the "Parallel Universe ToT" prompting method.
    """
    # --- 1. Setup Game and Models ---
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_p1', type=str, default='gpt-4', help='Model for Player 1')
    parser.add_argument('--model_p2', type=str, default='gpt-4', help='Model for Player 2')
    parser.add_argument('--temperature', type=float, default=0.7, help='Model temperature')
    parser.add_argument('--log_file', type=str, default='fencing_game_log.json', help='Name of the log file')
    args = parser.parse_args()

    # Create model namespaces (as expected by get_model)
    args_p1 = argparse.Namespace(backend=args.model_p1, temperature=args.temperature)
    args_p2 = argparse.Namespace(backend=args.model_p2, temperature=args.temperature)

    task = FencingTask()
    game_log = []
    game_status = 'Continue'
    turn_number = 1

    print(f"--- GAME START ---")
    print(f"Player 1 ({args.model_p1}) vs. Player 2 ({args.model_p2})")
    print(f"Initial State: {task.state}\n")
    
    # --- 2. Run the Game Loop ---
    while game_status == 'Continue':
        print(f"--- Turn {turn_number} ---")
        
        # --- Player 1's Turn (Parallel Universe ToT) ---
        p1_actions = task.get_available_actions(player_id=1)
        # This wrap method gets the prompt from fencing_game.py
        p1_prompt = task.propose_prompt_wrap(player_id=1) 
        
        print(f"P1 ({args.model_p1}) is thinking...")
        p1_model_output = get_model(args_p1)(p1_prompt)
        p1_action = parse_action(p1_model_output, p1_actions)
        
        # --- Player 2's Turn (Parallel Universe ToT) ---
        p2_actions = task.get_available_actions(player_id=2)
        p2_prompt = task.propose_prompt_wrap(player_id=2)
        
        print(f"P2 ({args.model_p2}) is thinking...")
        p2_model_output = get_model(args_p2)(p2_prompt)
        p2_action = parse_action(p2_model_output, p2_actions)

        # --- Resolution ---
        game_status = task.resolve_turn(p1_action, p2_action)
        
        # --- Logging ---
        print(f"P1 chose: {p1_action}")
        print(f"P2 chose: {p2_action}")
        print(f"Result: {game_status}")
        print(f"New State: {task.state}\n")

        turn_data = {
            'turn': turn_number,
            'p1_model': args.model_p1,
            'p1_prompt': p1_prompt,
            'p1_raw_output': p1_model_output, # This logs the full "ToT"
            'p1_action': p1_action,
            'p2_model': args.model_p2,
            'p2_prompt': p2_prompt,
            'p2_raw_output': p2_model_output, # This logs the full "ToT"
            'p2_action': p2_action,
            'game_status': game_status,
            'state_after_turn': task.state.copy()
        }
        game_log.append(turn_data)
        
        turn_number += 1
        
        if turn_number > 20: # Safety stop
            print("Game reached 20 turns, ending in a draw.")
            game_status = 'Draw (Turn Limit)'

    # --- 3. Save Results ---
    print(f"--- GAME OVER: {game_status} ---")
    
    # Save log to results/ folder
    results_dir = 'results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    log_path = os.path.join(results_dir, args.log_file)
    with open(log_path, 'w') as f:
        json.dump(game_log, f, indent=4)
        
    print(f"Game log saved to {log_path}")
    print("This log file is your 'Resultados gerados' for your paper.")

if __name__ == '__main__':
    run_game()