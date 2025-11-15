#!/bin/bash
#
# Setup and Run Fencing Game
# This script handles PYTHONPATH configuration and runs the game
#

# Add current directory to PYTHONPATH so 'src.tot' imports work
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: ANTHROPIC_API_KEY is not set!"
    echo "Please set it with: export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "============================================"
echo "Running Fencing Game"
echo "============================================"
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# Run the game with all arguments passed through
python run_fencing.py "$@"
