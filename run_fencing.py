import argparse
import json
import os
import re
from src.tot.models import get_model, gpt_usage
from src.tot.tasks.fencing_game import FencingTask

def parse_action(model_output: str, available_actions: list) -> str:
    """
    Parses the raw model output to find the chosen action.
    This parser is robust: it looks for the last line that
    contains one of the valid actions.
    
    IMPROVED: Better error handling and logging
    """
    best_action = available_actions[0]  # Default fallback
    
    # Try to find action in the output
    lines = model_output.strip().split('\n')
    
    # Search from bottom to top (final recommendation is usually last)
    for line in reversed(lines):
        line_upper = line.upper()
        for action in available_actions:
            if action in line_upper:
                return action
    
    # If nothing found in reverse, try forward search
    for action in available_actions:
        if action in model_output.upper():
            return action
    
    # Last resort: return first available action
    print(f"Warning: Could not parse action from output. Using default: {best_action}")
    print(f"Output was: {model_output[:200]}...")
    return best_action

def run_game(args):
    """
    Main function to run the 2-player fencing game benchmark using
    the "Parallel Universe ToT" prompting method.
    
    FIXED VERSION: Proper model loading and error handling
    """
    # --- 1. Setup Game and Models ---
    print(f"\n{'='*60}")
    print(f"FENCING GAME BENCHMARK")
    print(f"{'='*60}")
    print(f"Player 1 Model: {args.model_p1}")
    print(f"Player 2 Model: {args.model_p2}")
    print(f"Temperature: {args.temperature}")
    print(f"Max Turns: {args.max_turns}")
    print(f"{'='*60}\n")
    
    # Create model callables using get_model factory
    args_p1 = argparse.Namespace(backend=args.model_p1, temperature=args.temperature)
    args_p2 = argparse.Namespace(backend=args.model_p2, temperature=args.temperature)
    
    model_p1 = get_model(args_p1)
    model_p2 = get_model(args_p2)
    
    task = FencingTask()
    game_log = []
    game_status = 'Continue'
    turn_number = 1
    
    print(f"Initial State: {task.state}\n")
    
    # --- 2. Run the Game Loop ---
    try:
        while game_status == 'Continue':
            print(f"{'─'*60}")
            print(f"Turn {turn_number}")
            print(f"{'─'*60}")
            
            # --- Player 1's Turn ---
            p1_actions = task.get_available_actions(player_id=1)
            p1_prompt = task.propose_prompt_wrap(player_id=1)
            
            print(f"P1 ({args.model_p1}) thinking...")
            print(f"  Available actions: {p1_actions}")
            
            try:
                p1_model_output = model_p1(p1_prompt, n=1, stop=None)[0]
                p1_action = parse_action(p1_model_output, p1_actions)
            except Exception as e:
                print(f"Error getting P1 response: {e}")
                p1_action = p1_actions[0]
                p1_model_output = f"ERROR: {str(e)}"
            
            # --- Player 2's Turn ---
            p2_actions = task.get_available_actions(player_id=2)
            p2_prompt = task.propose_prompt_wrap(player_id=2)
            
            print(f"P2 ({args.model_p2}) thinking...")
            print(f"  Available actions: {p2_actions}")
            
            try:
                p2_model_output = model_p2(p2_prompt, n=1, stop=None)[0]
                p2_action = parse_action(p2_model_output, p2_actions)
            except Exception as e:
                print(f"Error getting P2 response: {e}")
                p2_action = p2_actions[0]
                p2_model_output = f"ERROR: {str(e)}"
            
            # --- Resolution ---
            game_status = task.resolve_turn(p1_action, p2_action)
            
            # --- Display Results ---
            print(f"\n  P1 chose: {p1_action}")
            print(f"  P2 chose: {p2_action}")
            print(f"  Result: {game_status}")
            print(f"  New State:")
            print(f"    P1: {task.state['p1_hp']} HP, Status: {task.state['p1_debuff'] or 'Normal'}")
            print(f"    P2: {task.state['p2_hp']} HP, Status: {task.state['p2_debuff'] or 'Normal'}")
            print()
            
            # --- Logging ---
            turn_data = {
                'turn': turn_number,
                'p1_model': args.model_p1,
                'p1_prompt': p1_prompt,
                'p1_raw_output': p1_model_output,
                'p1_action': p1_action,
                'p1_available_actions': p1_actions,
                'p2_model': args.model_p2,
                'p2_prompt': p2_prompt,
                'p2_raw_output': p2_model_output,
                'p2_action': p2_action,
                'p2_available_actions': p2_actions,
                'game_status': game_status,
                'state_after_turn': task.state.copy()
            }
            game_log.append(turn_data)
            
            turn_number += 1
            
            # Safety stop
            if turn_number > args.max_turns:
                print(f"\nGame reached {args.max_turns} turns, ending in a draw.")
                game_status = 'Draw (Turn Limit)'
                break
    
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user!")
        game_status = 'Interrupted'
    except Exception as e:
        print(f"\n\nFatal error during game: {e}")
        import traceback
        traceback.print_exc()
        game_status = f'Error: {str(e)}'
    
    # --- 3. Save Results ---
    print(f"\n{'='*60}")
    print(f"GAME OVER: {game_status}")
    print(f"{'='*60}")
    print(f"Total turns: {turn_number - 1}")
    
    # Get token usage
    usage = gpt_usage(args.model_p1)
    print(f"\nToken Usage:")
    print(f"  Prompt tokens: {usage['prompt_tokens']}")
    print(f"  Completion tokens: {usage['completion_tokens']}")
    print(f"  Estimated cost: ${usage['cost']:.4f}")
    
    # Save detailed log
    results_dir = 'results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    log_path = os.path.join(results_dir, args.log_file)
    
    game_summary = {
        'game_info': {
            'p1_model': args.model_p1,
            'p2_model': args.model_p2,
            'temperature': args.temperature,
            'max_turns': args.max_turns,
            'result': game_status,
            'total_turns': turn_number - 1,
            'winner': game_status.split()[0] if 'Wins' in game_status else 'Draw'
        },
        'token_usage': usage,
        'game_history': task.game_history,
        'turn_by_turn_log': game_log
    }
    
    with open(log_path, 'w') as f:
        json.dump(game_summary, f, indent=4)
    
    print(f"\nDetailed log saved to: {log_path}")
    print("This file contains all prompts, responses, and game states.")
    print("\nYou can use this as 'Resultados gerados' for your assignment! 📊")
    
    return game_summary

def main():
    parser = argparse.ArgumentParser(description='Run LLM Fencing Game Benchmark')
    
    # Model arguments
    parser.add_argument('--model_p1', type=str, default='gpt-4', 
                        help='Model for Player 1 (e.g., gpt-4, claude-sonnet-4-20250514)')
    parser.add_argument('--model_p2', type=str, default='gpt-4',
                        help='Model for Player 2 (e.g., gpt-4, claude-sonnet-4-20250514)')
    parser.add_argument('--temperature', type=float, default=0.7,
                        help='Model temperature (0.0-1.0)')
    
    # Game arguments
    parser.add_argument('--max_turns', type=int, default=20,
                        help='Maximum number of turns before draw')
    parser.add_argument('--log_file', type=str, default='fencing_game_log.json',
                        help='Name of the output log file')
    
    args = parser.parse_args()
    
    # Validate API keys
    if args.model_p1.startswith('claude') or args.model_p2.startswith('claude'):
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("ERROR: ANTHROPIC_API_KEY not set!")
            print("Please set it: export ANTHROPIC_API_KEY='your-key-here'")
            return
    
    if args.model_p1.startswith('gpt') or args.model_p2.startswith('gpt'):
        if not os.getenv('OPENAI_API_KEY'):
            print("ERROR: OPENAI_API_KEY not set!")
            print("Please set it: export OPENAI_API_KEY='your-key-here'")
            return
    
    # Run the game
    run_game(args)

if __name__ == '__main__':
    main()




