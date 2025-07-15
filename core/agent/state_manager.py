import json
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

class AgentStateManager:
    """Classe responsável por gerenciar o estado da conversa e a memória de trabalho do agente."""
    
    def __init__(self, state_file_path: str = "agent_state.pkl"):
        self.state_file = Path(state_file_path)
        self.messages = []
        self.turn_count = 0
        self.user_goal = ""
        self.project_path = ""
        self.world_state = "Nenhum estado registrado ainda. A tarefa está apenas começando."
    
    def initialize_new_conversation(self, user_goal: str, project_path: str, system_prompt: str, user_start_prompt: str):
        """Inicializa uma nova conversa do zero."""
        try:
            formatted_prompt = system_prompt.format(
                user_goal=user_goal,
                command="",
                project_path=project_path
            )
        except KeyError:
            try:
                formatted_prompt = system_prompt.format(user_goal=user_goal)
            except KeyError:
                formatted_prompt = system_prompt
        self.messages = [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": user_start_prompt}
        ]
        self.turn_count = 0
        self.user_goal = user_goal
        self.project_path = project_path
        self.world_state = "Nenhum estado registrado ainda. A tarefa está apenas começando."
        print("🆕 Nova conversa inicializada")
    
    def load_previous_state(self, user_goal: str, project_path: str, system_prompt_template: str) -> bool:
        if not self.state_file.exists():
            print("📂 Nenhum estado anterior encontrado")
            return False
        try:
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
            self.messages = state.get('messages', [])
            self.turn_count = state.get('turn_count', 0)
            self.world_state = state.get('world_state', "Estado não encontrado no save anterior.")
            self.user_goal = user_goal
            self.project_path = project_path
            if self.messages and self.messages[0]["role"] == "system":
                self.messages[0]["content"] = system_prompt_template.format(user_goal=user_goal)
            print(f"📁 Estado carregado: {len(self.messages)} mensagens, turno {self.turn_count}")
            if len(self.messages) >= 2:
                print("\n--- ÚLTIMAS MENSAGENS ---")
                for msg in self.messages[-2:]:
                    role_emoji = "🤖" if msg["role"] == "assistant" else "👤"
                    content_preview = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                    print(f"{role_emoji} {msg['role'].upper()}: {content_preview}")
                print("--- FIM DO CONTEXTO ---\n")
            return True
        except Exception as e:
            print(f"⚠️ Erro ao carregar estado anterior: {e}")
            return False
    
    def save_current_state(self):
        try:
            state = {
                'messages': self.messages,
                'turn_count': self.turn_count,
                'user_goal': self.user_goal,
                'project_path': self.project_path,
                'world_state': self.world_state
            }
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def increment_turn(self):
        self.turn_count += 1
    
    def cleanup_state_file(self):
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                print("🗑️ Arquivo de estado removido")
        except Exception as e:
            print(f"⚠️ Erro ao remover arquivo de estado: {e}")
    
    def get_messages(self) -> list:
        return self.messages
    
    def get_turn_count(self) -> int:
        return self.turn_count
    
    def get_world_state(self) -> str:
        return self.world_state
    
    def update_world_state(self, new_state: str):
        if new_state and new_state.strip():
            self.world_state = new_state
            print(f"🧠 Memória de trabalho atualizada: {new_state[:150]}...")
