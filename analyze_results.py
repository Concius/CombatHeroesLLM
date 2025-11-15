#!/usr/bin/env python3
"""
Analyze Fencing Game Results
Generates statistics from multiple game logs for your paper
"""

import json
import os
from glob import glob
from collections import defaultdict

def analyze_games(results_dir='results'):
    """Analyze all game logs and print statistics"""
    
    game_files = sorted(glob(os.path.join(results_dir, '*.json')))
    
    if not game_files:
        print(f"No game files found in {results_dir}/")
        print("Run some games first with run_fencing.py!")
        return
    
    # Initialize counters
    total_games = len(game_files)
    p1_wins = 0
    p2_wins = 0
    draws = 0
    total_turns = 0
    total_tokens = 0
    total_cost = 0.0
    
    # Track actions used
    p1_actions = defaultdict(int)
    p2_actions = defaultdict(int)
    
    # Track game lengths
    game_lengths = []
    
    # Process each game
    for file in game_files:
        with open(file, 'r') as f:
            try:
                data = json.load(f)
                
                # Winner stats
                winner = data['game_info']['winner']
                if winner == 'P1':
                    p1_wins += 1
                elif winner == 'P2':
                    p2_wins += 1
                else:
                    draws += 1
                
                # Turn stats
                turns = data['game_info']['total_turns']
                total_turns += turns
                game_lengths.append(turns)
                
                # Token stats
                total_tokens += data['token_usage']['completion_tokens'] + data['token_usage']['prompt_tokens']
                total_cost += data['token_usage']['cost']
                
                # Action stats (from game history)
                if 'game_history' in data:
                    for turn in data['game_history']:
                        p1_actions[turn['p1_action']] += 1
                        p2_actions[turn['p2_action']] += 1
                        
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue
    
    # Calculate statistics
    avg_turns = total_turns / total_games if total_games > 0 else 0
    avg_tokens = total_tokens / total_games if total_games > 0 else 0
    avg_cost = total_cost / total_games if total_games > 0 else 0
    
    min_turns = min(game_lengths) if game_lengths else 0
    max_turns = max(game_lengths) if game_lengths else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"FENCING GAME BENCHMARK RESULTS")
    print(f"{'='*60}\n")
    
    print(f"📊 GAME OUTCOMES:")
    print(f"  Total Games Played: {total_games}")
    print(f"  Player 1 Wins: {p1_wins} ({p1_wins/total_games*100:.1f}%)")
    print(f"  Player 2 Wins: {p2_wins} ({p2_wins/total_games*100:.1f}%)")
    print(f"  Draws: {draws} ({draws/total_games*100:.1f}%)")
    
    print(f"\n⏱️  GAME LENGTH:")
    print(f"  Average Turns: {avg_turns:.1f}")
    print(f"  Shortest Game: {min_turns} turns")
    print(f"  Longest Game: {max_turns} turns")
    
    print(f"\n💰 TOKEN USAGE & COST:")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Average Tokens/Game: {avg_tokens:.0f}")
    print(f"  Total Cost: ${total_cost:.4f}")
    print(f"  Average Cost/Game: ${avg_cost:.4f}")
    
    print(f"\n🎮 ACTION DISTRIBUTION:")
    print(f"  Player 1:")
    total_p1_actions = sum(p1_actions.values())
    for action, count in sorted(p1_actions.items(), key=lambda x: x[1], reverse=True):
        print(f"    {action}: {count} ({count/total_p1_actions*100:.1f}%)")
    
    print(f"  Player 2:")
    total_p2_actions = sum(p2_actions.values())
    for action, count in sorted(p2_actions.items(), key=lambda x: x[1], reverse=True):
        print(f"    {action}: {count} ({count/total_p2_actions*100:.1f}%)")
    
    print(f"\n{'='*60}")
    print(f"✅ Analysis complete! Use these stats in your paper.")
    print(f"{'='*60}\n")
    
    # Save summary to file
    summary = {
        'total_games': total_games,
        'outcomes': {
            'p1_wins': p1_wins,
            'p2_wins': p2_wins,
            'draws': draws,
            'p1_win_rate': p1_wins/total_games if total_games > 0 else 0,
            'p2_win_rate': p2_wins/total_games if total_games > 0 else 0
        },
        'game_length': {
            'average': avg_turns,
            'min': min_turns,
            'max': max_turns
        },
        'resources': {
            'total_tokens': total_tokens,
            'avg_tokens_per_game': avg_tokens,
            'total_cost_usd': total_cost,
            'avg_cost_per_game': avg_cost
        },
        'actions': {
            'player1': dict(p1_actions),
            'player2': dict(p2_actions)
        }
    }
    
    summary_file = os.path.join(results_dir, 'SUMMARY.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=4)
    
    print(f"📄 Detailed summary saved to: {summary_file}")
    print("   You can include this in your assignment submission!\n")

if __name__ == '__main__':
    import sys
    
    # Allow custom results directory
    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'results'
    
    if not os.path.exists(results_dir):
        print(f"Results directory '{results_dir}' not found!")
        print("Run some games first with run_fencing.py")
        sys.exit(1)
    
    analyze_games(results_dir)
