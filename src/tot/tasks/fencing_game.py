import re
import os
from src.tot.tasks.base import Task
from src.tot.prompts.fencing_game import propose_prompt, value_prompt

class FencingTask(Task):
    """
    Task class for a 2-player fencing game with multiple game modes.
    Supports: standard, no_kick, first_blood, action_points
    
    UPDATED VERSION - Multiple game modes with configurable rules
    """
    
    # Game mode configurations
    GAME_MODES = {
        'standard': {
            'hp': 3,
            'action_points': None,  # Infinite actions
            'actions': ['ATTACK', 'DEFEND', 'KICKS', 'FEINT'],
            'action_costs': None,
            'win_condition': 'hp_zero',
            'debuffs': True,
            'description': 'Classic mode: 3 HP, 4 actions, debuffs enabled'
        },
        'no_kick': {
            'hp': 3,
            'action_points': None,
            'actions': ['ATTACK', 'DEFEND', 'FEINT'],
            'action_costs': None,
            'win_condition': 'hp_zero',
            'debuffs': True,
            'description': '3-way RPS: 3 HP, 3 actions (no KICKS), debuffs enabled'
        },
        'first_blood': {
            'hp': 3,
            'action_points': None,
            'actions': ['ATTACK', 'DEFEND', 'KICKS', 'FEINT'],
            'action_costs': None,
            'win_condition': 'first_damage',
            'debuffs': True,
            'description': 'First to deal HP damage wins'
        },
        'action_points': {
            'hp': 3,
            'action_points': 5,
            'actions': ['ATTACK', 'DEFEND', 'KICKS', 'FEINT'],
            'action_costs': {'ATTACK': 2, 'DEFEND': 1, 'KICKS': 2, 'FEINT': 1},
            'win_condition': 'ap_zero_or_hp_zero',
            'debuffs': False,  # No debuffs in AP mode
            'description': 'Resource management: 5 AP, actions cost AP, no debuffs'
        }
    }
    
    def __init__(self, game_mode='standard'):
        super().__init__()
        
        # Validate game mode
        if game_mode not in self.GAME_MODES:
            raise ValueError(f"Unknown game mode: {game_mode}. "
                           f"Valid modes: {list(self.GAME_MODES.keys())}")
        
        self.game_mode = game_mode
        self.config = self.GAME_MODES[game_mode]
        
        # Initialize state based on game mode
        self.state = {
            'p1_hp': self.config['hp'],
            'p2_hp': self.config['hp'],
            'p1_ap': self.config['action_points'],
            'p2_ap': self.config['action_points'],
            'p1_debuff': None,
            'p2_debuff': None,
            'turn': 0,
            'first_damage_dealt': False  # For first_blood mode
        }
        
        self.base_actions = self.config['actions']
        self.game_history = []

    def get_state_string(self, player_id: int) -> str:
        """Serializes state to a string for the player."""
        my_hp = self.state['p1_hp'] if player_id == 1 else self.state['p2_hp']
        op_hp = self.state['p2_hp'] if player_id == 1 else self.state['p1_hp']
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        
        state_string = f"You are Player {player_id}.\n"
        state_string += f"Game Mode: {self.game_mode.upper()} - {self.config['description']}\n"
        state_string += f"Turn: {self.state['turn']}\n"
        state_string += f"CURRENT STATE:\n"
        state_string += f"Your HP: {my_hp}\n"
        state_string += f"Opponent HP: {op_hp}\n"
        
        # Add AP info if using action points mode
        if self.config['action_points'] is not None:
            my_ap = self.state['p1_ap'] if player_id == 1 else self.state['p2_ap']
            op_ap = self.state['p2_ap'] if player_id == 1 else self.state['p1_ap']
            state_string += f"Your Action Points: {my_ap}\n"
            state_string += f"Opponent Action Points: {op_ap}\n"
            state_string += f"Action Costs: {self.config['action_costs']}\n"
        
        state_string += f"Your Status: {my_debuff if my_debuff else 'Normal'}\n"
        
        return state_string

    def get_available_actions(self, player_id: int) -> list:
        """Returns valid actions, considering debuffs and action points."""
        available_actions = list(self.base_actions)
        my_debuff = self.state['p1_debuff'] if player_id == 1 else self.state['p2_debuff']
        my_ap = self.state['p1_ap'] if player_id == 1 else self.state['p2_ap']
        
        # Remove actions blocked by debuffs (if debuffs enabled)
        if self.config['debuffs'] and my_debuff:
            if my_debuff == 'Cannot Attack' and 'ATTACK' in available_actions:
                available_actions.remove('ATTACK')
            elif my_debuff == 'Cannot Defend' and 'DEFEND' in available_actions:
                available_actions.remove('DEFEND')
            elif my_debuff == 'Cannot Kick' and 'KICKS' in available_actions:
                available_actions.remove('KICKS')
            elif my_debuff == 'Cannot Feint' and 'FEINT' in available_actions:
                available_actions.remove('FEINT')
        
        # Remove actions that cost more AP than available (if using AP mode)
        if self.config['action_points'] is not None and self.config['action_costs']:
            available_actions = [
                action for action in available_actions
                if self.config['action_costs'][action] <= my_ap
            ]
        
        # Ensure at least one action is available
        if not available_actions:
            # In AP mode, if no actions available, player loses
            return []
        
        return available_actions

    def resolve_turn(self, p1_action: str, p2_action: str) -> str:
        """
        Applies game rules based on the current game mode.
        Returns game status: 'Continue', 'P1 Wins', 'P2 Wins', 'Draw'
        """
        
        # Deduct action points if using AP mode
        if self.config['action_points'] is not None and self.config['action_costs']:
            self.state['p1_ap'] -= self.config['action_costs'][p1_action]
            self.state['p2_ap'] -= self.config['action_costs'][p2_action]
        
        # Initialize new debuffs
        new_p1_debuff = None
        new_p2_debuff = None
        
        # Track if damage was dealt this turn (for first_blood mode)
        damage_dealt_this_turn = False
        
        # Apply game rules based on mode
        if self.game_mode == 'no_kick':
            # 3-way RPS: ATTACK beats FEINT, DEFEND beats ATTACK, FEINT beats DEFEND
            
            # ATTACK beats FEINT (damage)
            if p1_action == 'ATTACK' and p2_action == 'FEINT':
                self.state['p2_hp'] -= 1
                damage_dealt_this_turn = True
            elif p2_action == 'ATTACK' and p1_action == 'FEINT':
                self.state['p1_hp'] -= 1
                damage_dealt_this_turn = True
            
            # DEFEND beats ATTACK (debuff if enabled)
            elif p1_action == 'DEFEND' and p2_action == 'ATTACK':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Attack'
            elif p2_action == 'DEFEND' and p1_action == 'ATTACK':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Attack'
            
            # FEINT beats DEFEND (debuff if enabled)
            elif p1_action == 'FEINT' and p2_action == 'DEFEND':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Defend'
            elif p2_action == 'FEINT' and p1_action == 'DEFEND':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Defend'
        
        else:
            # Standard, first_blood, and action_points modes use full 6-rule system
            
            # Rule 1: ATTACK beats FEINT (damage)
            if p1_action == 'ATTACK' and p2_action == 'FEINT':
                self.state['p2_hp'] -= 1
                damage_dealt_this_turn = True
            elif p2_action == 'ATTACK' and p1_action == 'FEINT':
                self.state['p1_hp'] -= 1
                damage_dealt_this_turn = True
            
            # Rule 2: FEINT beats KICKS (debuff)
            elif p1_action == 'FEINT' and p2_action == 'KICKS':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Kick'
            elif p2_action == 'FEINT' and p1_action == 'KICKS':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Kick'
            
            # Rule 3: KICKS beats DEFEND (damage)
            elif p1_action == 'KICKS' and p2_action == 'DEFEND':
                self.state['p2_hp'] -= 1
                damage_dealt_this_turn = True
            elif p2_action == 'KICKS' and p1_action == 'DEFEND':
                self.state['p1_hp'] -= 1
                damage_dealt_this_turn = True
            
            # Rule 4: DEFEND beats ATTACK (debuff)
            elif p1_action == 'DEFEND' and p2_action == 'ATTACK':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Attack'
            elif p2_action == 'DEFEND' and p1_action == 'ATTACK':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Attack'
            
            # Rule 5: ATTACK beats KICKS (debuff)
            elif p1_action == 'ATTACK' and p2_action == 'KICKS':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Kick'
            elif p2_action == 'ATTACK' and p1_action == 'KICKS':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Kick'
            
            # Rule 6: DEFEND beats FEINT (debuff)
            elif p1_action == 'DEFEND' and p2_action == 'FEINT':
                if self.config['debuffs']:
                    new_p2_debuff = 'Cannot Feint'
            elif p2_action == 'DEFEND' and p1_action == 'FEINT':
                if self.config['debuffs']:
                    new_p1_debuff = 'Cannot Feint'
        
        # Update debuffs (clear old, apply new)
        if self.config['debuffs']:
            self.state['p1_debuff'] = new_p1_debuff
            self.state['p2_debuff'] = new_p2_debuff
        
        # Mark if first damage was dealt (for first_blood mode)
        if damage_dealt_this_turn:
            self.state['first_damage_dealt'] = True
        
        # Increment turn counter
        self.state['turn'] += 1
        
        # Log this turn
        self.game_history.append({
            'turn': self.state['turn'],
            'p1_action': p1_action,
            'p2_action': p2_action,
            'p1_hp': self.state['p1_hp'],
            'p2_hp': self.state['p2_hp'],
            'p1_ap': self.state['p1_ap'],
            'p2_ap': self.state['p2_ap'],
            'p1_debuff': self.state['p1_debuff'],
            'p2_debuff': self.state['p2_debuff']
        })
        
        # Check win conditions based on game mode
        return self._check_win_condition()
    
    def _check_win_condition(self) -> str:
        """Check win condition based on game mode."""
        
        # First Blood: Win on first damage dealt
        if self.config['win_condition'] == 'first_damage' and self.state['first_damage_dealt']:
            if self.state['p1_hp'] < 3:  # P2 damaged P1
                return 'P2 Wins (First Blood)'
            elif self.state['p2_hp'] < 3:  # P1 damaged P2
                return 'P1 Wins (First Blood)'
        
        # Action Points mode: Lose if AP reaches 0
        if self.config['win_condition'] == 'ap_zero_or_hp_zero':
            if self.state['p1_ap'] <= 0 and self.state['p2_ap'] <= 0:
                return 'Draw (Both Out of AP)'
            elif self.state['p1_ap'] <= 0:
                return 'P2 Wins (P1 Out of AP)'
            elif self.state['p2_ap'] <= 0:
                return 'P1 Wins (P2 Out of AP)'
        
        # Standard HP check (applies to all modes)
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
            'p1_hp': self.config['hp'],
            'p2_hp': self.config['hp'],
            'p1_ap': self.config['action_points'],
            'p2_ap': self.config['action_points'],
            'p1_debuff': None,
            'p2_debuff': None,
            'turn': 0,
            'first_damage_dealt': False
        }
        self.game_history = []