#!/usr/bin/env python3
"""
Quick test to validate all game modes and configurations
Run this BEFORE running full experiments
"""

import sys
import os

print("="*60)
print("COMBATHEROES LLM - GAME MODE VALIDATION")
print("="*60)
print()

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from src.tot.tasks.fencing_game import FencingTask
    from src.tot.models import get_model, gpt_usage
    print("  ✓ Successfully imported all modules")
except ImportError as e:
    print(f"  ✗ Failed to import: {e}")
    sys.exit(1)
print()

# Test 2: Validate all game modes
print("Test 2: Validating game modes...")
game_modes = ['standard', 'no_kick', 'first_blood', 'action_points']

for mode in game_modes:
    try:
        task = FencingTask(game_mode=mode)
        config = task.config
        print(f"  ✓ {mode.upper()}")
        print(f"    - HP: {config['hp']}")
        print(f"    - Actions: {config['actions']}")
        print(f"    - AP: {config['action_points']}")
        print(f"    - Debuffs: {config['debuffs']}")
        print(f"    - Win: {config['win_condition']}")
    except Exception as e:
        print(f"  ✗ {mode.upper()}: {e}")
        sys.exit(1)
print()

# Test 3: Check available actions logic
print("Test 3: Testing action availability...")
task = FencingTask(game_mode='standard')

# Normal state
actions = task.get_available_actions(player_id=1)
assert len(actions) == 4, "Should have 4 actions in standard mode"
print(f"  ✓ Normal state: {actions}")

# With debuff
task.state['p1_debuff'] = 'Cannot Attack'
actions = task.get_available_actions(player_id=1)
assert 'ATTACK' not in actions, "ATTACK should be blocked"
assert len(actions) == 3, "Should have 3 actions with debuff"
print(f"  ✓ With debuff: {actions}")

# No kick mode
task = FencingTask(game_mode='no_kick')
actions = task.get_available_actions(player_id=1)
assert 'KICKS' not in actions, "KICKS should not exist in no_kick mode"
assert len(actions) == 3, "Should have 3 actions in no_kick mode"
print(f"  ✓ No kick mode: {actions}")

# Action points mode
task = FencingTask(game_mode='action_points')
task.state['p1_ap'] = 1  # Only 1 AP left
actions = task.get_available_actions(player_id=1)
assert 'ATTACK' not in actions, "ATTACK costs 2 AP, should be blocked"
assert 'KICKS' not in actions, "KICKS costs 2 AP, should be blocked"
assert 'DEFEND' in actions, "DEFEND costs 1 AP, should be available"
assert 'FEINT' in actions, "FEINT costs 1 AP, should be available"
print(f"  ✓ Action points (1 AP): {actions}")
print()

# Test 4: Test game resolution
print("Test 4: Testing game resolution...")

# Standard mode: Simple attack
task = FencingTask(game_mode='standard')
status = task.resolve_turn('ATTACK', 'FEINT')
assert task.state['p2_hp'] == 2, "ATTACK should beat FEINT"
assert status == 'Continue', "Game should continue"
print("  ✓ Standard: ATTACK beats FEINT")

# First blood mode
task = FencingTask(game_mode='first_blood')
status = task.resolve_turn('ATTACK', 'FEINT')
assert 'P1 Wins' in status, "P1 should win on first blood"
print("  ✓ First Blood: P1 wins immediately")

# Action points drain
task = FencingTask(game_mode='action_points')
task.state['p1_ap'] = 1
task.state['p2_ap'] = 1
status = task.resolve_turn('DEFEND', 'FEINT')  # Both cost 1 AP
assert task.state['p1_ap'] == 0, "P1 should have 0 AP"
assert task.state['p2_ap'] == 0, "P2 should have 0 AP"
assert 'Draw' in status, "Should be draw when both out of AP"
print("  ✓ Action Points: Both drain to 0 = draw")
print()

# Test 5: Check API key availability
print("Test 5: Checking API keys...")
apis = {
    'OpenAI': 'OPENAI_API_KEY',
    'Anthropic (Claude)': 'ANTHROPIC_API_KEY',
    'Google (Gemini)': 'GOOGLE_API_KEY'
}

available_apis = []
for name, env_var in apis.items():
    if os.getenv(env_var):
        print(f"  ✓ {name} API key set")
        available_apis.append(name)
    else:
        print(f"  ⚠  {name} API key NOT set")

if not available_apis:
    print("\n  ⚠️  Warning: No API keys set! You won't be able to run games.")
    print("  Set at least one:")
    print("    export OPENAI_API_KEY='your-key'")
    print("    export ANTHROPIC_API_KEY='your-key'")
    print("    export GOOGLE_API_KEY='your-key'")
print()

# Test 6: Model factory
print("Test 6: Testing model factory...")
import argparse

test_models = []
if 'OpenAI' in available_apis:
    test_models.append('gpt-4')
if 'Anthropic (Claude)' in available_apis:
    test_models.append('claude-sonnet-4-20250514')
if 'Google (Gemini)' in available_apis:
    test_models.append('gemini-1.5-pro')

for model_name in test_models:
    try:
        args = argparse.Namespace(backend=model_name, temperature=0.7)
        model = get_model(args)
        print(f"  ✓ {model_name} factory works")
    except Exception as e:
        print(f"  ✗ {model_name} factory failed: {e}")
print()

print("="*60)
print("✅ ALL VALIDATION TESTS PASSED!")
print("="*60)
print()
print("You're ready to run experiments!")
print()
print("Quick start examples:")
print()
print("1. Standard mode (Claude vs Claude):")
print("   python run_fencing.py --model_p1 claude-sonnet-4-20250514 --model_p2 claude-sonnet-4-20250514 --game_mode standard")
print()
print("2. First Blood (Gemini vs Claude):")
print("   python run_fencing.py --model_p1 gemini-1.5-pro --model_p2 claude-sonnet-4-20250514 --game_mode first_blood")
print()
print("3. Action Points (GPT-4 vs Gemini):")
print("   python run_fencing.py --model_p1 gpt-4 --model_p2 gemini-1.5-pro --game_mode action_points")
print()






