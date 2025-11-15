#!/bin/bash
#
# Quick Experiment Launcher
# Run common experiment scenarios easily
#

echo "════════════════════════════════════════════════════════════"
echo "🤺 COMBATHEROES LLM - QUICK EXPERIMENTS 🤺"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ] && [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  WARNING: No API keys set!"
    echo "Please set at least one:"
    echo "  export OPENAI_API_KEY='your-key'"
    echo "  export ANTHROPIC_API_KEY='your-key'"
    echo "  export GOOGLE_API_KEY='your-key'"
    echo "  export DEEPSEEK_API_KEY='your-key'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Choose an experiment:"
echo ""
echo "1. Single Game - Gemini vs Claude (Standard)"
echo "2. Single Game - DeepSeek vs Gemini (First Blood)"
echo "3. Single Game - Claude vs Gemini (Action Points)"
echo "4. Batch (10 games) - Gemini vs Claude (All modes)"
echo "5. Tournament - All models, Standard mode (3 games each)"
echo "6. Custom - I'll specify manually"
echo ""
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "Running: Gemini vs Claude (Standard mode)"
        python run_fencing.py \
            --model_p1 gemini-2.0-flash \
            --model_p2 claude-sonnet-4-20250514 \
            --game_mode standard \
            --max_turns 40 \
            --temperature 1.0 \
            --log_file gemini_claude_standard_40t_1.0t.json
        ;;
    
    2)
        echo ""
        echo "Running: DeepSeek vs Gemini (First Blood mode)"
        python run_fencing.py \
            --model_p1 deepseek-chat \
            --model_p2 gemini-2.0-flash \
            --game_mode first_blood \
            --max_turns 40 \
            --temperature 1.0 \
            --log_file deepseek_gemini_firstblood_40t_1.0t.json
        ;;
    
    3)
        echo ""
        echo "Running: Claude vs Gemini (Action Points mode)"
        python run_fencing.py \
            --model_p1 claude-sonnet-4-20250514 \
            --model_p2 gemini-2.0-flash \
            --game_mode action_points \
            --max_turns 40 \
            --temperature 1.0 \
            --log_file claude_gemini_ap_40t_1.0t.json
        ;;
    
    4)
        echo ""
        echo "Running: 10 games each mode (Gemini vs Claude)"
        echo "This will run 40 total games (10 per mode)"
        echo "Using 40 turns and temperature 1.0 to reduce draws"
        echo ""
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        
        for mode in standard no_kick first_blood action_points; do
            echo ""
            echo "═══ Running mode: $mode ═══"
            for i in {1..10}; do
                echo "Game $i of 10..."
                python run_fencing.py \
                    --model_p1 gemini-2.0-flash \
                    --model_p2 claude-sonnet-4-20250514 \
                    --game_mode $mode \
                    --max_turns 40 \
                    --temperature 1.0 \
                    --log_file "batch_${mode}_game${i}_40t_1.0t.json"
            done
        done
        
        echo ""
        echo "✅ Batch complete! Run analyze_results.py to see stats."
        ;;
    
    5)
        echo ""
        echo "Running: Tournament (All models, Standard mode)"
        echo "Matchups: Gemini vs Claude, DeepSeek vs Gemini, Claude vs DeepSeek"
        echo "3 games per matchup = 9 total games"
        echo "Using 40 turns and temperature 1.0 to reduce draws"
        echo ""
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        
        # Gemini vs Claude
        echo ""
        echo "═══ Gemini vs Claude ═══"
        for i in {1..3}; do
            echo "Game $i of 3..."
            python run_fencing.py \
                --model_p1 gemini-2.0-flash \
                --model_p2 claude-sonnet-4-20250514 \
                --game_mode standard \
                --max_turns 40 \
                --temperature 1.0 \
                --log_file "tournament_gemini_claude_${i}_40t_1.0t.json"
        done
        
        # DeepSeek vs Gemini
        echo ""
        echo "═══ DeepSeek vs Gemini ═══"
        for i in {1..3}; do
            echo "Game $i of 3..."
            python run_fencing.py \
                --model_p1 deepseek-chat \
                --model_p2 gemini-2.0-flash \
                --game_mode standard \
                --max_turns 40 \
                --temperature 1.0 \
                --log_file "tournament_deepseek_gemini_${i}_40t_1.0t.json"
        done
        
        # Claude vs DeepSeek
        echo ""
        echo "═══ Claude vs DeepSeek ═══"
        for i in {1..3}; do
            echo "Game $i of 3..."
            python run_fencing.py \
                --model_p1 claude-sonnet-4-20250514 \
                --model_p2 deepseek-chat \
                --game_mode standard \
                --max_turns 40 \
                --temperature 1.0 \
                --log_file "tournament_claude_deepseek_${i}_40t_1.0t.json"
        done
        
        echo ""
        echo "✅ Tournament complete! Run analyze_results.py to see stats."
        ;;
    
    6)
        echo ""
        echo "Custom Mode"
        echo ""
        echo "Available models:"
        echo "  - deepseek-chat"
        echo "  - deepseek-coder"
        echo "  - claude-sonnet-4-20250514"
        echo "  - gemini-2.0-flash"
        echo "  - gemini-2.0-flash-lite"
        echo "  - gemini-2.5-pro"
        echo "  - gemini-2.5-flash"
        echo ""
        read -p "Player 1 model: " p1
        read -p "Player 2 model: " p2
        echo ""
        echo "Game modes: standard, no_kick, first_blood, action_points"
        read -p "Game mode: " mode
        read -p "Max turns [40]: " maxturns
        maxturns=${maxturns:-40}
        read -p "Temperature [1.0]: " temp
        temp=${temp:-1.0}
        read -p "Log filename: " logfile
        
        # Add turn and temp info to filename if not already specified
        if [[ ! "$logfile" == *"40t"* ]] && [[ ! "$logfile" == *"1.0t"* ]]; then
            logfile="${logfile%.json}_${maxturns}t_${temp}t.json"
        fi
        
        echo ""
        echo "Running: $p1 vs $p2 ($mode mode)"
        echo "Max turns: $maxturns, Temperature: $temp"
        echo "Log file: $logfile"
        python run_fencing.py \
            --model_p1 "$p1" \
            --model_p2 "$p2" \
            --game_mode "$mode" \
            --max_turns "$maxturns" \
            --temperature "$temp" \
            --log_file "$logfile"
        ;;
    
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Experiment complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Results saved in: results/"
echo "Run 'python analyze_results.py' to analyze"
echo ""