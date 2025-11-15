import re
import os
from src.tot.tasks.base import Task
from src.tot.prompts.fencing_game import propose_prompt, value_prompt

class FencingTask(Task):
    """
    Task class for a 2-player fencing game with balanced rock-paper-scissors-style rules.
    Manages game state and provides prompt generation.
    
    FIXED VERSION - Corrected debuff logic and complete game rules
    """
    
    def __init__(self):
        super().__init__()
        self.state = {
            'p1_hp': 3,
            'p2_hp': 3,
            'p1_debuff': None,  # e.g., 'Cannot Attack'
            'p2_debuff': None,
            'turn': 0
        }
        self.base_actions = ['ATTACK', 'DEFEND', 'KICKS', 'FEINT']
        self.game_history = []  # Track all moves for analysis

    def get_state_string(self, player_id: int) -> str:
        """Serializes state to a string for the player."""
        my_hp = self.state['p1_hp'] if player_id == 1 else self.state['p2_hp']
        op_hp = self.state['p2_hp'] if player_id == 1 else self.state['p1_hp']
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        
        state_string = f"You are Player {player_id}.\n"
        state_string += f"Turn: {self.state['turn']}\n"
        state_string += f"CURRENT STATE:\n"
        state_string += f"Your HP: {my_hp}\n"
        state_string += f"Opponent HP: {op_hp}\n"
        state_string += f"Your Status: {my_debuff if my_debuff else 'Normal'}\n"
        return state_string

    def get_available_actions(self, player_id: int) -> list:
        """Returns valid actions, considering debuffs."""
        available_actions = list(self.base_actions)
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        
        # Remove actions that are blocked by debuffs
        if my_debuff == 'Cannot Attack':
            if 'ATTACK' in available_actions: 
                available_actions.remove('ATTACK')
        elif my_debuff == 'Cannot Defend':
            if 'DEFEND' in available_actions: 
                available_actions.remove('DEFEND')
        elif my_debuff == 'Cannot Kick':
            if 'KICKS' in available_actions: 
                available_actions.remove('KICKS')
        elif my_debuff == 'Cannot Feint':
            if 'FEINT' in available_actions: 
                available_actions.remove('FEINT')
                
        return available_actions

    def resolve_turn(self, p1_action: str, p2_action: str) -> str:
        """
        Applies the balanced game rules and updates the state.
        
        FIXED: Debuffs now apply BEFORE clearing, and new debuffs are set AFTER resolution.
        
        Complete Rock-Paper-Scissors rules (4 actions = 6 unique matchups):
        1. ATTACK beats FEINT (Feinter loses 1 HP)
        2. FEINT beats KICKS (Kicker gets 'Cannot Kick')
        3. KICKS beats DEFEND (Defender loses 1 HP)
        4. DEFEND beats ATTACK (Attacker gets 'Cannot Attack')
        5. ATTACK beats KICKS (Kicker gets 'Cannot Kick') - NEW
        6. DEFEND beats FEINT (Feinter gets 'Cannot Feint') - NEW
        """
        
        # Store current debuffs (they should already be enforced by get_available_actions)
        # We'll clear them AFTER applying the turn's effects
        
        # Initialize new debuffs
        new_p1_debuff = None
        new_p2_debuff = None
        
        # Apply game rules - Complete set of 6 matchups
        
        # Rule 1: ATTACK beats FEINT
        if p1_action == 'ATTACK' and p2_action == 'FEINT':
            self.state['p2_hp'] -= 1
        elif p2_action == 'ATTACK' and p1_action == 'FEINT':
            self.state['p1_hp'] -= 1
            
        # Rule 2: FEINT beats KICKS
        elif p1_action == 'FEINT' and p2_action == 'KICKS':
            new_p2_debuff = 'Cannot Kick'
        elif p2_action == 'FEINT' and p1_action == 'KICKS':
            new_p1_debuff = 'Cannot Kick'
            
        # Rule 3: KICKS beats DEFEND
        elif p1_action == 'KICKS' and p2_action == 'DEFEND':
            self.state['p2_hp'] -= 1
        elif p2_action == 'KICKS' and p1_action == 'DEFEND':
            self.state['p1_hp'] -= 1
            
        # Rule 4: DEFEND beats ATTACK
        elif p1_action == 'DEFEND' and p2_action == 'ATTACK':
            new_p2_debuff = 'Cannot Attack'
        elif p2_action == 'DEFEND' and p1_action == 'ATTACK':
            new_p1_debuff = 'Cannot Attack'
        
        # Rule 5: ATTACK beats KICKS (NEW - completes the cycle)
        elif p1_action == 'ATTACK' and p2_action == 'KICKS':
            new_p2_debuff = 'Cannot Kick'
        elif p2_action == 'ATTACK' and p1_action == 'KICKS':
            new_p1_debuff = 'Cannot Kick'
        
        # Rule 6: DEFEND beats FEINT (NEW - completes the cycle)
        elif p1_action == 'DEFEND' and p2_action == 'FEINT':
            new_p2_debuff = 'Cannot Feint'
        elif p2_action == 'DEFEND' and p1_action == 'FEINT':
            new_p1_debuff = 'Cannot Feint'
        
        # If identical moves, they cancel out (no action needed)
        
        # NOW update debuffs (clearing old ones and applying new ones)
        self.state['p1_debuff'] = new_p1_debuff
        self.state['p2_debuff'] = new_p2_debuff
        
        # Increment turn counter
        self.state['turn'] += 1
        
        # Log this turn
        self.game_history.append({
            'turn': self.state['turn'],
            'p1_action': p1_action,
            'p2_action': p2_action,
            'p1_hp': self.state['p1_hp'],
            'p2_hp': self.state['p2_hp'],
            'p1_debuff': self.state['p1_debuff'],
            'p2_debuff': self.state['p2_debuff']
        })
        
        # Check for win/loss conditions
        if self.state['p1_hp'] <= 0 and self.state['p2_hp'] <= 0:
            return 'Draw'
        elif self.state['p1_hp'] <= 0:
            return 'P2 Wins'
        elif self.state['p2_hp'] <= 0:
            return 'P1 Wins'
        
        return 'Continue'

    # --- Wrapper Methods (Called by ToT solver or run_fencing.py) ---

    def propose_prompt_wrap(self, player_id: int) -> str:
        """Wraps the propose prompt with the current state."""
        state_string = self.get_state_string(player_id)
        available_actions = self.get_available_actions(player_id)
        
        # Add available actions to the state string for the prompt
        full_input = f"{state_string}\nAvailable Actions: {available_actions}"
        return propose_prompt.format(input=full_input)
    
    def value_prompt_wrap(self, player_id: int) -> str:
        """Wraps the value prompt with the current state."""
        state_string = self.get_state_string(player_id)
        return value_prompt.format(input=state_string)

    @staticmethod
    def value_outputs_unwrap(value_outputs: list) -> float:
        """Converts the LLM's '1-10' score into a float."""
        try:
            value_str = value_outputs[0].strip().split('\n')[-1]
            value = float(value_str)
            return value / 10.0  # Normalize to 0.0-1.0
        except Exception:
            return 0.5  # Default value if parsing fails
        
    # --- Required by Base Task Class ---
    
    def __len__(self) -> int:
        return 1  # Only one "game" instance

    def get_input(self, idx: int):
        """Get initial game state as string"""
        player_id = 1 if idx == 0 else 2
        return self.get_state_string(player_id)

    def test_output(self, idx: int, output: str):
        """Evaluate output (not used in adversarial setting)"""
        return {'r': 0}
    
    def reset(self):
        """Reset game state for a new game"""
        self.state = {
            'p1_hp': 3,
            'p2_hp': 3,
            'p1_debuff': None,
            'p2_debuff': None,
            'turn': 0
        }
        self.game_history = []
