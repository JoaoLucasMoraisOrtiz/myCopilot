# In state_manager.pyimport picklefrom pathlib import Pathfrom typing import Dict, Any, Optionalclass AgentStateManager:
    """Class responsible for managing the agent's conversation state and working memory."""
    
    def __init__(self, state_file_path: str = "agent_state.pkl"):
        self.state_file = Path(state_file_path)
        self.messages = []
        self.turn_count = 0
        self.user_goal = ""
        self.project_path = ""
        self.world_state = "No state recorded yet. The task is just beginning." # <<< NEW

    def initialize_new_conversation(self, user_goal: str, project_path: str, system_prompt: str, user_start_prompt: str):
        # ... (existing code)
        self.world_state = "No state recorded yet. The task is just beginning." # <<< NEW
        # ...

    def load_previous_state(self, user_goal: str, project_path: str, system_prompt_template: str) -> bool:
        try:
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
            
            self.messages = state.get('messages', [])
            self.turn_count = state.get('turn_count', 0)
            self.world_state = state.get('world_state', "State not found in the previous save.") # <<< NEW
            self.user_goal = user_goal
            # ... (rest of the code)
            return True
        except Exception as e:
            # ...
            return False

    def save_current_state(self):
        """Saves the current conversation state and working memory."""
        try:
            state = {
                'messages': self.messages,
                'turn_count': self.turn_count,
                'user_goal': self.user_goal,
                'project_path': self.project_path,
                'world_state': self.world_state # <<< NEW
            }
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            print(f"⚠️ Error saving state: {e}")

    # <<< NEW METHODS >>>
    def get_world_state(self) -> str:
        """Returns the current working memory."""
        return self.world_state

    def update_world_state(self, new_state: str):
        """Updates the working memory."""
        if new_state and new_state.strip():
            self.world_state = new_state
            print(f"🧠 Working memory updated: {new_state[:150]}...")
