#!/bin/bash
#
# Run Multiple Fencing Games for Benchmarking
# Usage: ./run_experiments.sh [num_games] [model1] [model2]
#
# Examples:
#   ./run_experiments.sh 10 claude-sonnet-4-20250514 claude-sonnet-4-20250514
#   ./run_experiments.sh 5 gpt-4 gpt-4
#   ./run_experiments.sh 10 claude-sonnet-4-20250514 gpt-4

# Default values
NUM_GAMES=${1:-10}
MODEL_P1=${2:-"claude-sonnet-4-20250514"}
MODEL_P2=${3:-"claude-sonnet-4-20250514"}
TEMPERATURE=0.7

echo "========================================"
echo "FENCING GAME BATCH EXPERIMENTS"
echo "========================================"
echo "Number of games: $NUM_GAMES"
echo "Player 1 model: $MODEL_P1"
echo "Player 2 model: $MODEL_P2"
echo "Temperature: $TEMPERATURE"
echo "========================================"
echo ""

# Create results directory if it doesn't exist
mkdir -p results

# Run the games
for i in $(seq 1 $NUM_GAMES); do
    GAME_NUM=$(printf "%03d" $i)
    echo "─────────────────────────────────────────"
    echo "Running game $i of $NUM_GAMES..."
    echo "─────────────────────────────────────────"
    
    python run_fencing.py \
        --model_p1 "$MODEL_P1" \
        --model_p2 "$MODEL_P2" \
        --temperature $TEMPERATURE \
        --log_file "game_${GAME_NUM}.json"
    
    if [ $? -eq 0 ]; then
        echo "✓ Game $i complete!"
    else
        echo "✗ Game $i failed!"
    fi
    
    echo ""
done

echo "========================================"
echo "BATCH COMPLETE!"
echo "========================================"
echo "Ran $NUM_GAMES games"
echo "Results saved in results/ directory"
echo ""
echo "Run analysis with:"
echo "  python analyze_results.py"
echo ""
echo "========================================"
