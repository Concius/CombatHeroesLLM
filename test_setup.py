#!/usr/bin/env python3
"""
Quick test to verify your CombatHeroesLLM setup is working
Run this BEFORE trying to run the full game
"""

import sys
import os

print("="*60)
print("COMBATHEROES LLM - SETUP TEST")
print("="*60)
print()

# Test 1: PYTHONPATH
print("Test 1: Checking PYTHONPATH...")
pythonpath = os.environ.get('PYTHONPATH', '')
current_dir = os.getcwd()

if current_dir in pythonpath or pythonpath == '':
    print(f"  ✓ PYTHONPATH includes current directory")
else:
    print(f"  ⚠️  Warning: Current directory not in PYTHONPATH")
    print(f"     Run: export PYTHONPATH=\"${{PYTHONPATH}}:$(pwd)\"")
print()

# Test 2: Import src.tot.models
print("Test 2: Importing src.tot.models...")
try:
    from src.tot.models import get_model, gpt_usage
    print("  ✓ Successfully imported get_model and gpt_usage")
except ImportError as e:
    print(f"  ✗ Failed to import: {e}")
    print("  Fix: Make sure you replaced src/tot/models.py with models_FIXED_v2.py")
    sys.exit(1)
print()

# Test 3: Import src.tot.tasks.fencing_game
print("Test 3: Importing src.tot.tasks.fencing_game...")
try:
    from src.tot.tasks.fencing_game import FencingTask
    print("  ✓ Successfully imported FencingTask")
except ImportError as e:
    print(f"  ✗ Failed to import: {e}")
    print("  Fix: Make sure you replaced src/tot/tasks/fencing_game.py with fencing_game_FIXED_v2.py")
    sys.exit(1)
print()

# Test 4: Check API keys
print("Test 4: Checking API keys...")
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
openai_key = os.environ.get('OPENAI_API_KEY', '')

if anthropic_key:
    print(f"  ✓ ANTHROPIC_API_KEY is set (length: {len(anthropic_key)})")
else:
    print(f"  ⚠️  ANTHROPIC_API_KEY not set (you'll need this for Claude models)")
    
if openai_key:
    print(f"  ✓ OPENAI_API_KEY is set (length: {len(openai_key)})")
else:
    print(f"  ⚠️  OPENAI_API_KEY not set (you'll need this for GPT models)")
print()

# Test 5: Check Anthropic SDK
print("Test 5: Checking Anthropic SDK...")
try:
    from anthropic import Anthropic
    print("  ✓ Anthropic SDK installed")
except ImportError:
    print("  ✗ Anthropic SDK not installed")
    print("  Fix: pip install anthropic")
    sys.exit(1)
print()

# Test 6: Create a FencingTask instance
print("Test 6: Creating FencingTask instance...")
try:
    task = FencingTask()
    print("  ✓ FencingTask created successfully")
    print(f"     Initial state: {task.state}")
except Exception as e:
    print(f"  ✗ Failed to create FencingTask: {e}")
    sys.exit(1)
print()

# Test 7: Test get_model factory
print("Test 7: Testing get_model factory...")
try:
    import argparse
    args = argparse.Namespace(backend='claude-sonnet-4-20250514', temperature=0.7)
    model = get_model(args)
    print("  ✓ get_model factory works")
except Exception as e:
    print(f"  ✗ Failed to create model: {e}")
    sys.exit(1)
print()

print("="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print()
print("You're ready to run the game!")
print()
print("Next steps:")
print("  1. Set your API key: export ANTHROPIC_API_KEY='your-key'")
print("  2. Run a game: ./run_game.sh --model_p1 claude-sonnet-4-20250514 --model_p2 claude-sonnet-4-20250514")
print()
