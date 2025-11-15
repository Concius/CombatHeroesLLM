import re
import os
from tot.tasks.base import Task
from tot.prompts.fencing_game import propose_prompt, value_prompt # Import new prompts

class FencingTask(Task):
    """
    Task class for a 2-player fencing game with balanced rules.
    Manages game state and provides prompt generation.
    """
    
    def __init__(self):
        super().__init__()
        self.state = {
            'p1_hp': 3,
            'p2_hp': 3,
            'p1_debuff': None, # e.g., 'Cannot Attack'
            'p2_debuff': None
        }
        self.base_actions = ['ATTACK', 'DEFEND', 'KICKS', 'FEINT']

    def get_state_string(self, player_id: int) -> str:
        """Serializes state to a string for the player."""
        my_hp = self.state['p1_hp'] if player_id == 1 else self.state['p2_hp']
        op_hp = self.state['p2_hp'] if player_id == 1 else self.state['p1_hp']
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        
        state_string = f"You are Player {player_id}.\n"
        state_string += f"CURRENT STATE:\n"
        state_string += f"Your HP: {my_hp}\n"
        state_string += f"Opponent HP: {op_hp}\n"
        state_string += f"Your Status: {my_debuff if my_debuff else 'Normal'}\n"
        return state_string

    def get_available_actions(self, player_id: int) -> list:
        """Returns valid actions, considering debuffs."""
        available_actions = list(self.base_actions)
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        
        if my_debuff == 'Cannot Attack':
            if 'ATTACK' in available_actions: available_actions.remove('ATTACK')
        if my_debuff == 'Cannot Defend':
            if 'DEFEND' in available_actions: available_actions.remove('DEFEND')
        if my_debuff == 'Cannot Kick':
            if 'KICKS' in available_actions: available_actions.remove('KICKS')
        if my_debuff == 'Cannot Feint':
            if 'FEINT' in available_actions: available_actions.remove('FEINT')
                
        return available_actions

    def resolve_turn(self, p1_action: str, p2_action: str) -> str:
        """Applies the balanced game rules and updates the state."""
        
        # 1. Clear old debuffs
        self.state['p1_debuff'] = None
        self.state['p2_debuff'] = None

        # 2. Apply BALANCED rules
        # (ATTACK beats FEINT)
        if p1_action == 'ATTACK' and p2_action == 'FEINT':
            self.state['p2_hp'] -= 1
        elif p2_action == 'ATTACK' and p1_action == 'FEINT':
            self.state['p1_hp'] -= 1
            
        # (FEINT beats KICKS)
        elif p1_action == 'FEINT' and p2_action == 'KICKS':
            self.state['p2_debuff'] = 'Cannot Kick'
        elif p2_action == 'FEINT' and p1_action == 'KICKS':
            self.state['p1_debuff'] = 'Cannot Kick'
            
        # (KICKS beats DEFEND)
        elif p1_action == 'KICKS' and p2_action == 'DEFEND':
            self.state['p2_hp'] -= 1
        elif p2_action == 'KICKS' and p1_action == 'DEFEND':
            self.state['p1_hp'] -= 1
            
        # (DEFEND beats ATTACK)
        elif p1_action == 'DEFEND' and p2_action == 'ATTACK':
            self.state['p2_debuff'] = 'Cannot Attack'
        elif p2_action == 'DEFEND' and p1_action == 'ATTACK':
            self.state['p1_debuff'] = 'Cannot Attack'
        
        # (Identical moves cancel out - no action needed)

        # 3. Check for win/loss
        if self.state['p1_hp'] <= 0 and self.state['p2_hp'] <= 0:
            return 'Draw'
        elif self.state['p1_hp'] <= 0:
            return 'P2 Wins'
        elif self.state['p2_hp'] <= 0:
            return 'P1 Wins'
        
        return 'Continue'

    # --- Wrapper Methods (Called by ToT solver) ---

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
        # Tries to parse the last line of the output as a number
        try:
            value_str = value_outputs[0].strip().split('\n')[-1]
            value = float(value_str)
            return value / 10.0 # Normalize to 0.0-1.0
        except Exception:
            return 0.5 # Default value if parsing fails
        
    # --- Required by Base Task Class (less important) ---
    
    def __len__(self) -> int:
        return 1 # Only one "game"

    def get_input(self, idx: int):
        # We will call `propose_prompt_wrap` directly
        # from our custom `run_fencing.py`.
        player_id = 1 if idx == 0 else 2
        return self.get_state_string(player_id)

    def test_output(self, idx: int, output: str):
        return {'r': 0} # Not used