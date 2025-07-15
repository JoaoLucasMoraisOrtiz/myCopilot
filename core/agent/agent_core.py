
"""
Agent Core - Refatorado com arquitetura ACI

Orquestrador principal do agente que usa o ACIOrchestrator para interagir com o ambiente.
"""
from pathlib import Path

# Importa os novos componentes da arquitetura
from devtools.shell_executor import ShellExecutor
from devtools.aci import ACIOrchestrator

# Módulos de agente existentes que serão mantidos
from core.agent.response_parser import AgentResponseParser
from core.agent.llm_interface import AgentLLMInterface
from core.agent.state_manager import AgentStateManager

# Prompts
from core.agent.agent_prompts import (
    SYSTEM_PROMPT_TEMPLATE, 
    USER_START_PROMPT, 
    TOOL_OBSERVATION_PROMPT,
    SYSTEM_PROMPT_NEW_MODE_TEMPLATE,
    USER_START_PROMPT_NEW_MODE,
    SYSTEM_PROMPT_CONTINUATION_TEMPLATE,
    SYSTEM_PROMPT_NEW_MODE_CONTINUATION_TEMPLATE
)

class Agent:
    """
    Agente principal refatorado com arquitetura ACI.
    """
    
    def __init__(self, user_goal, project_path, max_turns=10, continue_mode=False, llm_type="vscode", api_key=None):
        self.user_goal = user_goal
        self.project_path = project_path
        self.max_turns = max_turns
        self.continue_mode = continue_mode
        self.llm_type = llm_type
        self.api_key = api_key
        
        # --- ARQUITETURA ACI ---
        # Inicializa o executor de shell com o diretório de trabalho do projeto
        self.shell_executor = ShellExecutor(working_directory=self.project_path)
        # O orquestrador ACI usa o executor de shell para rodar os comandos
        self.aci_orchestrator = ACIOrchestrator(self.shell_executor)
        
        # Componentes modulares
        self.state_manager = AgentStateManager()
        self.llm_interface = AgentLLMInterface(llm_type=llm_type, api_key=api_key)
        self.response_parser = AgentResponseParser()
        # O tool_executor agora é o nosso orquestrador ACI
        self.tool_executor = self.aci_orchestrator
        
        # Inicialização baseada no modo
        if continue_mode:
            self._load_previous_state()
        else:
            # Sempre inicializa com modo correto
            self._initialize_new_conversation(mode="new" if llm_type in ["codestral", "gemini", "gemini_api"] else "edit")
    
    def _load_previous_state(self):
        """Carrega estado anterior se disponível."""
        success = self.state_manager.load_previous_state(
            self.user_goal, self.project_path, SYSTEM_PROMPT_TEMPLATE
        )
        if not success:
            print("🆕 Iniciando nova conversa...")
            self._initialize_new_conversation(mode="edit")
    
    def _initialize_new_conversation(self, mode="edit"):
        """Inicializa uma nova conversa."""
        if mode == "new":
            system_prompt = SYSTEM_PROMPT_NEW_MODE_TEMPLATE
            user_start_prompt = USER_START_PROMPT_NEW_MODE
        else:
            system_prompt = SYSTEM_PROMPT_TEMPLATE
            user_start_prompt = USER_START_PROMPT
        # Chamada correta com todos os argumentos
        self.state_manager.initialize_new_conversation(
            self.user_goal,
            self.project_path,
            system_prompt,
            user_start_prompt
        )
    
    def run(self, mode="edit"):
        """Executa o loop principal do agente."""
        print("INFO: Agente iniciado. Objetivo:", self.user_goal)
        print(f"[MODO: {mode.upper()}]")
        print("="*50)
        # Sempre inicializa corretamente
        if not self.continue_mode:
            self._initialize_new_conversation(mode)
        return self._run_main_loop(mode)
    
    def _run_main_loop(self, mode: str):
        """Main loop with 'World State' management."""
        start_turn = self.state_manager.get_turn_count() if self.continue_mode else 0
        
        for turn in range(start_turn, self.max_turns):
            self.state_manager.increment_turn()
            current_turn = self.state_manager.get_turn_count()
            print(f"\n--- TURN {current_turn} ---")

            # 1. Get message history and current state
            messages = self.state_manager.get_messages()
            current_world_state = self.state_manager.get_world_state()

            # 2. Prepare the system prompt for this turn
            if current_turn > 1:
                system_prompt_content = SYSTEM_PROMPT_CONTINUATION_TEMPLATE.format(
                    user_goal=self.user_goal,
                    world_state=current_world_state
                )
                messages[0] = {"role": "system", "content": system_prompt_content}
            
            # 3. Call the LLM
            llm_response = self.llm_interface.call_llm(messages, current_turn)
            self.state_manager.add_message("assistant", llm_response)

            # 4. Parse the response to get STATE and ACTION
            new_world_state, action_json = self.response_parser.parse(llm_response)

            # 5. Update the agent's state
            if new_world_state:
                self.state_manager.update_world_state(new_world_state)
            
            self.state_manager.save_current_state()

            # 6. Execute the action
            if action_json and action_json.get("command") == "submit":
                return self._handle_final_answer(action_json)
            
            command = action_json.get("command") if action_json else None
            args = action_json.get("args", []) if action_json else []

            if command:
                execution_result = self.tool_executor.dispatch_command(command, args)
            else:
                execution_result = "Error: No valid action was generated."
            
            tool_observation = TOOL_OBSERVATION_PROMPT.format(execution_result=str(execution_result))
            self.state_manager.add_message("user", tool_observation)
            self.state_manager.save_current_state()
        
        print(f"INFO: Agent reached max turns ({mode} mode).")
        return None

    def _handle_final_answer(self, action_json):
        """Processa a resposta final do agente."""
        print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
        answer = action_json.get("args", ["Tarefa concluída."])[0]
        print(answer)
        
        print("\n" + "="*20 + " VERIFICAÇÃO FINAL " + "="*20)
        print("O agente finalizou a tarefa. Recomenda-se rodar os testes manualmente se necessário.")
        
        self.state_manager.cleanup_state_file()
        return answer

# Classe de compatibilidade, se outros módulos ainda a utilizam
class AgentCore(Agent):
    """Classe de compatibilidade - use Agent diretamente."""
    pass
