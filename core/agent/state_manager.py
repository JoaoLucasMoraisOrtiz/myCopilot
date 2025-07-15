import json # Add this import
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

class AgentStateManager:
    """Class responsible for managing the agent's conversation state and working memory."""
    
    # MODIFIED: The world_state is now a dictionary
    def __init__(self, state_file_path: str = "agent_state.pkl"):
        self.state_file = Path(state_file_path)
        self.messages = []
        self.turn_count = 0
        self.user_goal = ""
        self.project_path = ""
        self.world_state = {} # It's a dictionary now
        self._initialize_world_state()

    # NEW: A dedicated initializer for the world_state structure
    def _initialize_world_state(self, goal: str = ""):
        """Initializes or resets the world state to its default structure."""
        self.world_state = {
            "mode": "PLANNING", # Always starts in PLANNING mode
            "user_goal": goal,
            "plan": [], # A list of tasks, e.g., ["[ ] Step 1", "[ ] Step 2"]
            "knowledge_summary": "Awaiting user goal to begin planning."
        }

    # MODIFIED: Ensure initialization uses the new structure
    def initialize_new_conversation(self, user_goal: str, project_path: str, system_prompt: str, user_start_prompt: str):
        # ... (your existing code for messages, etc.)
        self._initialize_world_state(goal=user_goal)
        # ...

    # MODIFIED: Handle JSON serialization when saving
    def save_current_state(self):
        """Saves the current state, serializing world_state to JSON."""
        try:
            state = {
                'messages': self.messages,
                'turn_count': self.turn_count,
                'user_goal': self.user_goal,
                'project_path': self.project_path,
                'world_state_json': json.dumps(self.world_state, indent=2) # Save as JSON string
            }
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            print(f"⚠️ Error saving state: {e}")

    # MODIFIED: Handle JSON deserialization when loading
    def load_previous_state(self, user_goal: str, project_path: str, system_prompt_template: str) -> bool:
        # ...
        try:
            # ...
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
            self.messages = state.get('messages', [])
            self.turn_count = state.get('turn_count', 0)
            world_state_json = state.get('world_state_json') # Load the JSON string
            if world_state_json:
                self.world_state = json.loads(world_state_json)
            else:
                self._initialize_world_state(goal=user_goal) # Fallback
            # ...
            return True
        except Exception as e:
            return False

    # MODIFIED: `update_world_state` can now update specific keys
    def update_world_state(self, updates: dict):
        """Updates the world_state dictionary with new values."""
        self.world_state.update(updates)
        print(f"🧠 World state updated. New mode: {self.world_state.get('mode')}")
