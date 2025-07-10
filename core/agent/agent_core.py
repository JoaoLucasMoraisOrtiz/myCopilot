"""
Agent Core - Refatorado e Modularizado

Orquestrador principal do agente com arquitetura limpa e modular.
"""

import json
from pathlib import Path
from analyzers.java_analyzer import build_symbol_table as build_java_symbol_table
from analyzers.react_analyzer import build_symbol_table as build_react_symbol_table

# Módulos refatorados
from core.agent.response_parser import AgentResponseParser
from core.agent.tool_executor import AgentToolExecutor
from core.agent.llm_interface import AgentLLMInterface
from core.agent.state_manager import AgentStateManager

# Prompts
from core.agent.agent_prompts import (
    SYSTEM_PROMPT_TEMPLATE, 
    USER_START_PROMPT, 
    TOOL_OBSERVATION_PROMPT,
    SYSTEM_PROMPT_NEW_MODE_TEMPLATE,
    USER_START_PROMPT_NEW_MODE
)


def detect_project_type(project_path):
    """
    Detecta o tipo de projeto baseado nos arquivos e estrutura
    Retorna: 'java', 'react', 'mixed' ou 'unknown'
    """
    project_path = Path(project_path)
    
    # Contadores para diferentes tipos de arquivo
    java_files = list(project_path.rglob('*.java'))
    react_files = list(project_path.rglob('*.tsx')) + list(project_path.rglob('*.jsx'))
    js_ts_files = list(project_path.rglob('*.ts')) + list(project_path.rglob('*.js'))
    
    # Arquivos específicos de cada framework
    has_package_json = (project_path / 'package.json').exists()
    has_pom_xml = (project_path / 'pom.xml').exists()
    has_build_gradle = (project_path / 'build.gradle').exists() or (project_path / 'build.gradle.kts').exists()
    has_next_config = any(project_path.glob('next.config.*'))
    has_app_folder = (project_path / 'app').exists() and any((project_path / 'app').rglob('*.tsx'))
    has_pages_folder = (project_path / 'pages').exists() and any((project_path / 'pages').rglob('*.tsx'))
    
    # Scoring baseado em indicadores
    java_score = len(java_files) * 2
    if has_pom_xml:
        java_score += 10
    if has_build_gradle:
        java_score += 10
    
    react_score = len(react_files) * 3 + len(js_ts_files)
    if has_package_json:
        react_score += 5
    if has_next_config:
        react_score += 15
    if has_app_folder or has_pages_folder:
        react_score += 10
    
    print(f"🔍 Detecção de projeto - Java: {java_score}, React: {react_score}")
    print(f"   Arquivos Java: {len(java_files)}, React/TS: {len(react_files)}, JS/TS: {len(js_ts_files)}")
    
    # Decisão baseada nos scores
    if java_score > react_score and java_score > 5:
        return 'java'
    elif react_score > java_score and react_score > 5:
        return 'react'
    elif java_score > 0 and react_score > 0:
        return 'mixed'
    else:
        return 'unknown'


def build_symbol_table(project_path):
    """
    Detecta o tipo de projeto e usa o analisador apropriado
    """
    project_type = detect_project_type(project_path)
    
    if project_type == 'java':
        print("📊 Usando analisador Java")
        return build_java_symbol_table(project_path)
    elif project_type == 'react':
        print("📊 Usando analisador React/Next.js")
        return build_react_symbol_table(project_path)
    elif project_type == 'mixed':
        print("📊 Projeto misto detectado - usando analisador React como principal")
        return build_react_symbol_table(project_path)
    else:
        print("⚠️ Tipo de projeto não reconhecido - usando analisador Java como fallback")
        return build_java_symbol_table(project_path)


class AgentToolbox:
    """Caixa de ferramentas do agente - mantida para compatibilidade."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.symbol_table = build_symbol_table(project_path)
        # Estado para controlar o que foi abstraído
        self.abstracted_content = {}
        self.next_abstraction_id = 1

    def _create_abstraction_id(self):
        """Cria um ID único para conteúdo abstraído"""
        abstraction_id = f"abs_{self.next_abstraction_id}"
        self.next_abstraction_id += 1
        return abstraction_id

    def continue_reading(self, abstraction_id, page=1):
        """Permite ao LLM recuperar conteúdo que foi abstraído"""
        from .callInfoFromDict import paginator
        if abstraction_id in paginator.abstractions:
            return paginator.get_page(abstraction_id, page)
        
        if abstraction_id not in self.abstracted_content:
            return f"❌ ID de abstração '{abstraction_id}' não encontrado. IDs disponíveis: {list(self.abstracted_content.keys())} | Paginações: {list(paginator.abstractions.keys())}"
        
        content = self.abstracted_content[abstraction_id]
        del self.abstracted_content[abstraction_id]
        
        return f"📖 Conteúdo completo para {abstraction_id}:\n\n{content}"

    def list_classes(self):
        """Lista todas as classes/arquivos do projeto."""
        return '\n- '.join(self.symbol_table.keys())

    def get_class_metadata(self, class_name):
        """Obtém metadata de uma classe específica."""
        entry = self.symbol_table.get(class_name)
        if not entry:
            return f"Classe/Arquivo '{class_name}' não encontrado."
        
        # Limita o número de relacionamentos para evitar overflow
        relationships = entry.get('relationships', [])
        if len(relationships) > 20:
            relationships = relationships[:20]
            relationships.append({"type": "INFO", "target": f"... e mais {len(entry['relationships']) - 20} relacionamentos"})
        
        # Detecta se é projeto Java ou React baseado na estrutura dos dados
        is_java_project = 'type' in entry and 'extends' in entry
        
        if is_java_project:
            # Estrutura para projetos Java
            methods = entry.get('methods', [])
            if len(methods) > 15:
                methods = methods[:15]
                methods.append(f"... e mais {len(entry['methods']) - 15} métodos")
            
            metadata = {
                'file_path': entry['file_path'],
                'type': entry['type'],
                'extends': entry.get('extends'),
                'implements': entry.get('implements', []),
                'fields': entry.get('fields', []),
                'constructors': entry.get('constructors', []),
                'methods': methods,
                'relationships': relationships
            }
        else:
            # Estrutura para projetos React/Next.js
            components = entry.get('components', [])
            if len(components) > 10:
                components = components[:10]
                components.append(f"... e mais {len(entry['components']) - 10} componentes")
            
            hooks = entry.get('hooks', [])
            if len(hooks) > 15:
                hooks = hooks[:15]
                hooks.append(f"... e mais {len(entry['hooks']) - 15} hooks")
            
            imports = entry.get('imports', {})
            if len(imports) > 10:
                import_items = list(imports.items())[:10]
                limited_imports = dict(import_items)
                if len(imports) > 10:
                    limited_imports['_more'] = f"... e mais {len(imports) - 10} imports"
                imports = limited_imports
            
            metadata = {
                'file_path': entry['file_path'],
                'relative_path': entry.get('relative_path', ''),
                'file_type': entry.get('file_type', ''),
                'components': components,
                'hooks': hooks,
                'exports': entry.get('exports', []),
                'props_interfaces': entry.get('props_interfaces', []),
                'api_calls': entry.get('api_calls', []),
                'routes': entry.get('routes', []),
                'nextjs_features': entry.get('nextjs_features', []),
                'imports': imports,
                'relationships': relationships
            }
        
        result = json.dumps(metadata, indent=2, ensure_ascii=False)
        
        # Limita o tamanho total da resposta
        if len(result) > 6000:
            result = result[:6000] + "\n\n[... metadata truncado para evitar overflow ...]"
        
        return result

    def get_code(self, class_name, method_name=None, abstracted=True):
        """Obtém código com opção de abstração inteligente"""
        from .callInfoFromDict import process_llm_request, paginator
        
        request_data = {
            "class": class_name,
            "method": method_name,
            "abstract": abstracted
        }
        request_json = json.dumps(request_data)
        result = process_llm_request(request_json, self.symbol_table)
        
        if not abstracted and len(result) > 8000:
            content_id = f"{class_name}_{method_name if method_name else 'full'}"
            result = paginator.abstract_content(result, content_id)
        
        return result

    def read_file(self, filepath, abstracted=True):
        """Lê arquivo com opção de abstração"""
        from .callInfoFromDict import process_llm_request, paginator
        
        request_data = {
            "pathFile": filepath,
            "abstract": abstracted
        }
        request_json = json.dumps(request_data)
        result = process_llm_request(request_json, self.symbol_table)
        
        if not abstracted and len(result) > 8000:
            content_id = f"file_{filepath.split('/')[-1]}"
            result = paginator.abstract_content(result, content_id)
        
        return result


class Agent:
    """
    Agente principal refatorado com arquitetura modular.
    
    Responsabilidades separadas em:
    - AgentStateManager: Gerenciamento de estado
    - AgentLLMInterface: Comunicação com LLM
    - AgentResponseParser: Parsing de respostas
    - AgentToolExecutor: Execução de comandos
    """
    
    def __init__(self, user_goal, project_path, max_turns=10, continue_mode=False):
        self.user_goal = user_goal
        self.project_path = project_path
        self.max_turns = max_turns
        self.continue_mode = continue_mode
        
        # Componentes modulares
        self.toolbox = AgentToolbox(project_path)
        self.state_manager = AgentStateManager()
        self.llm_interface = AgentLLMInterface()
        self.response_parser = AgentResponseParser()
        self.tool_executor = AgentToolExecutor(self.toolbox, project_path)
        
        # Inicialização baseada no modo
        if continue_mode:
            self._load_previous_state()
        else:
            self._initialize_new_conversation()
    
    def _load_previous_state(self):
        """Carrega estado anterior se disponível."""
        success = self.state_manager.load_previous_state(
            self.user_goal, 
            self.project_path, 
            SYSTEM_PROMPT_TEMPLATE
        )
        
        if not success:
            print("🆕 Iniciando nova conversa...")
            self._initialize_new_conversation()
    
    def _initialize_new_conversation(self, mode="edit"):
        """Inicializa uma nova conversa."""
        if mode == "new":
            system_prompt = SYSTEM_PROMPT_NEW_MODE_TEMPLATE
            user_start_prompt = USER_START_PROMPT_NEW_MODE
        else:
            system_prompt = SYSTEM_PROMPT_TEMPLATE
            user_start_prompt = USER_START_PROMPT
        
        self.state_manager.initialize_new_conversation(
            self.user_goal, 
            self.project_path, 
            system_prompt, 
            user_start_prompt
        )
    
    def run(self, mode="edit"):
        """
        Executa o loop principal do agente.
        
        Args:
            mode: 'edit' para análise de projeto existente, 'new' para criação
        """
        print("INFO: Agente iniciado. Objetivo:", self.user_goal)
        print(f"[MODO: {mode.upper()}]")
        print("="*50)
        
        # Reinicializa com o prompt correto se não está em modo continue
        if not self.continue_mode:
            self._initialize_new_conversation(mode)
        
        if mode == "edit":
            return self._run_edit_mode()
        elif mode == "new":
            return self._run_new_mode()
        else:
            print(f"❌ Modo '{mode}' não reconhecido. Use 'edit' ou 'new'.")
            return None
    
    def _run_edit_mode(self):
        """Executa o modo de edição/análise de projeto existente."""
        return self._run_main_loop("edit")
    
    def _run_new_mode(self):
        """Executa o modo de criação de projeto do zero."""
        # Cria diretório de output se não existir
        output_dir = Path(self.project_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"🆕 Criando projeto do zero em: {output_dir}")
        
        return self._run_main_loop("new")
    
    def _run_main_loop(self, mode: str):
        """Loop principal unificado para ambos os modos."""
        
        # Determina turno inicial
        if self.continue_mode:
            start_turn = self.state_manager.get_turn_count()
            print(f"🔄 Continuando do turno {start_turn + 1}")
        else:
            start_turn = 0
            print(f"🆕 Iniciando nova análise ({mode} mode)")
        
        for turn in range(start_turn, self.max_turns):
            self.state_manager.increment_turn()
            current_turn = self.state_manager.get_turn_count()
            print(f"\n--- TURNO {current_turn} ---")
            
            # Processa resposta do LLM
            llm_response = self._get_llm_response(turn, start_turn)
            self.state_manager.add_message("assistant", llm_response)
            self.state_manager.save_current_state()
            
            # Analisa e executa ação
            action_json = self.response_parser.parse_action_from_response(llm_response)
            
            # Verifica se é resposta final
            if action_json.get("command") == "final_answer":
                return self._handle_final_answer(action_json)
            
            # Executa ferramenta e adiciona observação
            execution_result = self.tool_executor.execute_tool(action_json)
            tool_observation = TOOL_OBSERVATION_PROMPT.format(execution_result=execution_result)
            self.state_manager.add_message("user", tool_observation)
            self.state_manager.save_current_state()
        
        print(f"INFO: Agente atingiu o número máximo de turnos ({mode} mode).")
        return None
    
    def _get_llm_response(self, turn: int, start_turn: int) -> str:
        """Obtém resposta do LLM considerando modo continue."""
        
        messages = self.state_manager.get_messages()
        
        # Se for modo continue e primeiro turno, processa última mensagem do assistente
        if self.continue_mode and turn == start_turn and messages:
            last_message = messages[-1]
            if last_message["role"] == "assistant":
                print("🔄 Processando última resposta do assistente...")
                self.state_manager.get_messages().pop()  # Remove para reprocessar
                return last_message["content"]
        
        # Chama LLM normalmente
        current_turn = self.state_manager.get_turn_count()
        return self.llm_interface.call_llm(messages, current_turn)
    
    def _handle_final_answer(self, action_json):
        """Processa resposta final do agente."""
        print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
        answer = action_json["args"][0] if action_json.get("args") else "[resposta vazia]"
        print(answer)
        
        # Limpa arquivo de estado
        self.state_manager.cleanup_state_file()
        
        return answer


# Classe mantida para compatibilidade com código existente
class AgentCore(Agent):
    """Classe de compatibilidade - use Agent diretamente."""
    pass
