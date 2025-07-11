import json
import re
import pickle
from pathlib import Path
from analyzers.java_analyzer import build_symbol_table as build_java_symbol_table
from analyzers.react_analyzer import build_symbol_table as build_react_symbol_table
from core.llm.llm_client import LLMClient
from core.code_corrector import get_corrector_for_language
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
        # Para projetos mistos, prioriza React/Next.js
        return build_react_symbol_table(project_path)
    else:
        print("⚠️ Tipo de projeto não reconhecido - usando analisador Java como fallback")
        return build_java_symbol_table(project_path)

class AgentToolbox:
    def __init__(self, project_path):
        self.project_path = project_path
        self.symbol_table = build_symbol_table(project_path)
        # Estado para controlar o que foi abstraído
        self.abstracted_content = {}  # chave: identificador único, valor: conteúdo completo
        self.next_abstraction_id = 1

    def _create_abstraction_id(self):
        """Cria um ID único para conteúdo abstraído"""
        abstraction_id = f"abs_{self.next_abstraction_id}"
        self.next_abstraction_id += 1
        return abstraction_id

    def _abstract_code_block(self, content, max_lines=5):
        """Abstrai um bloco de código mostrando apenas as primeiras linhas e criando um marcador de continuação"""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        # Cria um ID de abstração e armazena o conteúdo completo
        abstraction_id = self._create_abstraction_id()
        self.abstracted_content[abstraction_id] = content
        
        # Retorna apenas as primeiras linhas + marcador
        visible_lines = lines[:max_lines]
        hidden_count = len(lines) - max_lines
        visible_lines.append(f"    // ... [ABSTRAÍDO: {hidden_count} linhas restantes - use continue_reading('{abstraction_id}') para ver o resto]")
        
        return '\n'.join(visible_lines)

    def _abstract_method_body(self, method_content):
        """Abstrai o corpo de um método, mantendo apenas a assinatura e primeiras linhas"""
        lines = method_content.split('\n')
        
        # Encontra onde termina a assinatura do método (geralmente na linha com '{')
        signature_end = 0
        for i, line in enumerate(lines):
            if '{' in line:
                signature_end = i
                break
        
        if signature_end == 0:
            return method_content  # Não conseguiu identificar a estrutura
        
        # Mantém a assinatura + algumas linhas do corpo
        signature_lines = lines[:signature_end + 1]
        body_lines = []
        brace_count = 0
        content_lines = 0
        
        for i in range(signature_end + 1, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            
            # Adiciona apenas as primeiras 3 linhas de conteúdo
            if content_lines < 3 and line.strip() and not line.strip().startswith('//'):
                body_lines.append(line)
                content_lines += 1
            elif brace_count == 0:  # Fim do método
                break
        
        if len(lines) > signature_end + len(body_lines) + 5:  # Se há conteúdo suficiente para abstrair
            abstraction_id = self._create_abstraction_id()
            self.abstracted_content[abstraction_id] = method_content
            
            abstracted_method = signature_lines + body_lines
            remaining_lines = len(lines) - len(abstracted_method) - 1
            abstracted_method.append(f"        // ... [MÉTODO ABSTRAÍDO: ~{remaining_lines} linhas restantes - use continue_reading('{abstraction_id}') para ver o método completo]")
            abstracted_method.append("    }")
            
            return '\n'.join(abstracted_method)
        
        return method_content

    def continue_reading(self, abstraction_id, page=1):
        """
        Permite ao LLM recuperar conteúdo que foi abstraído
        Suporta tanto o sistema antigo quanto o novo sistema de paginação
        """
        # Primeiro tenta o novo sistema de paginação
        from .callInfoFromDict import paginator
        if abstraction_id in paginator.abstractions:
            return paginator.get_page(abstraction_id, page)
        
        # Fallback para o sistema antigo
        if abstraction_id not in self.abstracted_content:
            return f"❌ ID de abstração '{abstraction_id}' não encontrado. IDs disponíveis: {list(self.abstracted_content.keys())} | Paginações: {list(paginator.abstractions.keys())}"
        
        content = self.abstracted_content[abstraction_id]
        # Remove o ID após uso para limpar memória
        del self.abstracted_content[abstraction_id]
        
        return f"📖 Conteúdo completo para {abstraction_id}:\n\n{content}"

    def list_classes(self):
        return '\n- '.join(self.symbol_table.keys())

    def get_class_metadata(self, class_name):
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
        """
        Obtém código com opção de abstração inteligente
        abstracted=True: mostra versão resumida com marcadores para continue_reading
        abstracted=False: mostra código completo (pode causar overflow)
        """
        from .callInfoFromDict import process_llm_request, paginator
        
        # Usa o novo sistema integrado
        request_data = {
            "class": class_name,
            "method": method_name,
            "abstract": abstracted
        }
        request_json = json.dumps(request_data)
        result = process_llm_request(request_json, self.symbol_table)
        
        # Se não abstraído e muito grande, força abstração
        if not abstracted and len(result) > 8000:
            content_id = f"{class_name}_{method_name if method_name else 'full'}"
            result = paginator.abstract_content(result, content_id)
        
        return result

    def read_file(self, filepath, abstracted=True):
        """
        Lê arquivo com opção de abstração
        abstracted=True: versão resumida com marcadores
        abstracted=False: conteúdo completo
        """
        from .callInfoFromDict import process_llm_request, paginator
        
        # Usa o novo sistema integrado
        request_data = {
            "pathFile": filepath,
            "abstract": abstracted
        }
        request_json = json.dumps(request_data)
        result = process_llm_request(request_json, self.symbol_table)
        
        # Se não abstraído e muito grande, força abstração
        if not abstracted and len(result) > 8000:
            content_id = f"file_{filepath.split('/')[-1]}"
            result = paginator.abstract_content(result, content_id)
        
        return result


class Agent:
    def __init__(self, user_goal, project_path, max_turns=10, continue_mode=False):
        self.toolbox = AgentToolbox(project_path)
        self.user_goal = user_goal
        self.max_turns = max_turns
        self.project_path = project_path
        self.continue_mode = continue_mode
        self.state_file = Path("agent_state.pkl")
        self.mode = "edit"  # Modo padrão, será definido no run()
        
        if continue_mode:
            self.load_previous_state()
        else:
            self.initialize_new_conversation()

    def initialize_new_conversation(self, mode="edit"):
        """Inicializa uma nova conversa do zero com prompts específicos do modo"""
        if mode == "new":
            system_prompt = SYSTEM_PROMPT_NEW_MODE_TEMPLATE.format(user_goal=self.user_goal)
            user_start_prompt = USER_START_PROMPT_NEW_MODE
        else:
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_goal=self.user_goal)
            user_start_prompt = USER_START_PROMPT
        
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_start_prompt}
        ]
        self.turn_count = 0
        
    def load_previous_state(self):
        """Carrega estado da conversa anterior"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                
                self.messages = state.get('messages', [])
                self.turn_count = state.get('turn_count', 0)
                
                # Atualiza o system prompt com o objetivo atual
                if self.messages and self.messages[0]["role"] == "system":
                    self.messages[0]["content"] = SYSTEM_PROMPT_TEMPLATE.format(user_goal=self.user_goal)
                
                print(f"📁 Estado carregado: {len(self.messages)} mensagens, turno {self.turn_count}")
                
                # Mostra as últimas 2 mensagens para contexto
                if len(self.messages) >= 2:
                    print("\n--- ÚLTIMAS MENSAGENS ---")
                    for i, msg in enumerate(self.messages[-2:]):
                        role_emoji = "🤖" if msg["role"] == "assistant" else "👤"
                        content_preview = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                        print(f"{role_emoji} {msg['role'].upper()}: {content_preview}")
                    print("--- FIM DO CONTEXTO ---\n")
                    
            except Exception as e:
                print(f"⚠️ Erro ao carregar estado anterior: {e}")
                print("🆕 Iniciando nova conversa...")
                self.initialize_new_conversation()
        else:
            print("📂 Nenhum estado anterior encontrado. Iniciando nova conversa...")
            self.initialize_new_conversation()
    
    def save_current_state(self):
        """Salva o estado atual da conversa"""
        try:
            state = {
                'messages': self.messages,
                'turn_count': self.turn_count,
                'user_goal': self.user_goal,
                'project_path': self.project_path
            }
            
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")

    def call_llm(self, current_turn=0):
        # Limita o tamanho total do contexto para evitar overflow
        # Apenas as últimas 4 mensagens são enviadas para evitar duplicação de contexto
        last_messages = self.messages[-4:]
        prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in last_messages])
        
        # Adiciona pressão temporal baseada no número de turnos
        pressure_message = self._get_pressure_message(current_turn)
        if pressure_message:
            print(f"🎯 APLICANDO PRESSÃO TEMPORAL (Turno {current_turn}): {pressure_message[:80]}...")
            prompt += f"\n\nUSER: {pressure_message}"
        
        # Gestão inteligente de contexto para respostas grandes
        original_length = len(prompt)
        
        # Limite mais flexível para permitir respostas grandes
        # if original_length > 25000:  # 25k chars max (aumentado de 20k)
        #     print(f"⚠️ Prompt muito longo ({original_length} chars), aplicando compressão inteligente...")
            
        #     # Estratégia de compressão progressiva
        #     if original_length > 40000:  # Muito crítico
        #         # Mantém system prompt + últimas 2 mensagens
        #         truncated_messages = [self.messages[0]]
        #         truncated_messages.extend(self.messages[-2:])
        #         print("🔄 Compressão crítica: mantendo apenas 2 últimas mensagens")
        #     elif original_length > 30000:  # Crítico
        #         # Mantém system prompt + últimas 3 mensagens
        #         truncated_messages = [self.messages[0]]
        #         truncated_messages.extend(self.messages[-3:])
        #         print("🔄 Compressão alta: mantendo 3 últimas mensagens")
        #     else:  # Moderado
        #         # Mantém system prompt + últimas 4 mensagens
        #         truncated_messages = [self.messages[0]]
        #         truncated_messages.extend(self.messages[-4:])
        #         print("🔄 Compressão moderada: mantendo 4 últimas mensagens")
            
            # Reconstrói o prompt
        #prompt ='' #'\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in truncated_messages])
        if pressure_message:
            prompt += f"\n\nUSER: {pressure_message}"
            
        print(f"✅ Prompt comprimido: {len(prompt)} chars (redução de {original_length - len(prompt)} chars)")
        
        # Log do tamanho final do prompt
        print(f"📊 Enviando prompt de {len(prompt)} chars para o LLM...")
        
        client = LLMClient()
        client.connect()
        response = client.send_prompt(prompt)
        client.close()
        
        # Log da resposta recebida
        if response:
            print(f"📨 Resposta recebida: {len(response)} chars")
            if len(response) > 20000:
                print("⚠️ Resposta muito grande detectada - processamento otimizado será aplicado")
        
        return response

    def _get_pressure_message(self, current_turn):
        """Gera mensagens de pressão temporal baseadas no número de turnos"""
        if current_turn >= 8:
            return "URGENTE: Você está no turno 8/10. DEVE fornecer final_answer no PRÓXIMO turno ou perderá a oportunidade de responder. Analise se já tem informação suficiente para uma resposta útil."
        elif current_turn >= 6:
            return "ATENÇÃO: Você está no turno 6/10. Comece a considerar seriamente usar final_answer. Você tem informação suficiente para uma resposta parcial útil?"
        elif current_turn >= 5:
            return "REFLEXÃO: Já coletou bastante informação. Avalie se pode fornecer uma resposta útil ou se precisa de apenas mais 1-2 observações específicas."
        elif current_turn >= 4:
            return "FOCO: Você está na metade do caminho. Mantenha o foco no objetivo principal e evite explorações tangenciais."
        else:
            return None  # Sem pressão nos primeiros turnos

    def _extract_json_from_response(self, response_text):
        """Extrai JSON da resposta do LLM com parsing robusto"""
        import re
        import json
        
        # Estratégia 1: JSON em bloco markdown ```json ... ```
        json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_block_match:
            json_str = json_block_match.group(1).strip()
            print(f"🔍 JSON encontrado em bloco: {json_str[:100]}...")
            try:
                data = json.loads(json_str)
                # Remove parênteses do comando se presente
                cmd = data.get('command', '')
                if isinstance(cmd, str) and cmd.endswith('()'):
                    data['command'] = cmd[:-2]
                return data
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON do bloco: {e}")
        
        # Estratégia 2: JSON iniciando com {"command" - melhorada para strings longas
        start = response_text.find('{"command"')
        if start != -1:
            substr = response_text[start:]
            # Detecta JSON balanceado considerando escape de quotes
            stack = []
            in_string = False
            escaped = False
            
            for i, ch in enumerate(substr):
                if escaped:
                    escaped = False
                    continue
                    
                if ch == '\\' and in_string:
                    escaped = True
                    continue
                    
                if ch == '"' and not escaped:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if ch == '{': 
                        stack.append('{')
                    elif ch == '}':
                        if stack: 
                            stack.pop()
                        if not stack:
                            candidate = substr[:i+1]
                            print(f"🔍 JSON encontrado (balanceado): {candidate[:100]}...")
                            try:
                                data = json.loads(candidate)
                                # Remove parênteses do comando se presente
                                cmd = data.get('command', '')
                                if isinstance(cmd, str) and cmd.endswith('()'):
                                    data['command'] = cmd[:-2]
                                print(f"✅ JSON válido extraído: {data.get('command', 'unknown')}")
                                return data
                            except json.JSONDecodeError as e:
                                print(f"❌ Erro ao decodificar JSON balanceado: {e}")
                                # Continua procurando outros JSONs possíveis
                                break
        
        # Estratégia 3: Busca por padrões mais amplos de JSON - melhorada
        # Primeiro tenta encontrar JSONs completos com save_code/create_file
        save_code_pattern = r'\{\s*"command"\s*:\s*"(save_code|create_file)"\s*,\s*"args"\s*:\s*\[\s*"[^"]+"\s*,\s*"([^"\\]|\\.)*"\s*\]\s*\}'
        save_match = re.search(save_code_pattern, response_text, re.DOTALL)
        if save_match:
            json_str = save_match.group(0)
            print(f"🔍 JSON save_code encontrado: {json_str[:100]}...")
            try:
                data = json.loads(json_str)
                cmd = data.get('command', '')
                if isinstance(cmd, str) and cmd.endswith('()'):
                    data['command'] = cmd[:-2]
                print(f"✅ JSON save_code válido extraído: {data.get('command', 'unknown')}")
                return data
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON save_code: {e}")
        
        # Padrões para outros comandos
        json_patterns = [
            # Padrão específico para comandos conhecidos simples
            r'\{\s*"command"\s*:\s*"(list_classes|get_class_metadata|get_code|read_file|continue_reading|final_answer)"\s*(?:,\s*"args"\s*:\s*\[[^\]]*\])?\s*\}',
            # Padrão simples sem args
            r'\{\s*"command"\s*:\s*"[^"]+"\s*\}',
        ]
        
        for pattern in json_patterns:
            for match in re.finditer(pattern, response_text):
                json_str = match.group(0)
                print(f"🔍 JSON encontrado (padrão): {json_str[:100]}...")
                try:
                    data = json.loads(json_str)
                    # Remove parênteses do comando se presente
                    cmd = data.get('command', '')
                    if isinstance(cmd, str) and cmd.endswith('()'):
                        data['command'] = cmd[:-2]
                    # Verifica se é um comando válido
                    if cmd in ["list_classes", "get_class_metadata", "get_code", "read_file", "continue_reading", "save_code", "create_file", "final_answer"]:
                        print(f"✅ JSON padrão válido extraído: {cmd}")
                        return data
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON por padrão: {e}")
                    continue
        
        # Estratégia 3.5: Extração manual para save_code com strings longas
        # Quando regex falha, tenta extrair manualmente
        save_start = response_text.find('{"command": "save_code"')
        if save_start != -1:
            print("🔍 Tentando extração manual de save_code...")
            try:
                # Encontra o início dos args
                args_start = response_text.find('"args":', save_start)
                if args_start != -1:
                    # Encontra o array args
                    bracket_start = response_text.find('[', args_start)
                    if bracket_start != -1:
                        # Extrai filename (primeiro argumento)
                        first_quote = response_text.find('"', bracket_start)
                        second_quote = response_text.find('"', first_quote + 1)
                        filename = response_text[first_quote + 1:second_quote]
                        
                        # Encontra o início do código (segundo argumento)
                        comma_pos = response_text.find(',', second_quote)
                        code_start_quote = response_text.find('"', comma_pos)
                        
                        # Busca pela aspas de fechamento do código
                        # Precisa considerar escapes
                        code_content_start = code_start_quote + 1
                        pos = code_content_start
                        while pos < len(response_text):
                            if response_text[pos] == '"' and response_text[pos-1] != '\\':
                                # Verifica se é realmente o fim (próximo char deve ser ] ou ,)
                                next_meaningful = pos + 1
                                while next_meaningful < len(response_text) and response_text[next_meaningful].isspace():
                                    next_meaningful += 1
                                if next_meaningful < len(response_text) and response_text[next_meaningful] in ']},':
                                    # Encontrou o fim do código
                                    code_content = response_text[code_content_start:pos]
                                    # Decodifica escapes básicos
                                    code_content = code_content.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                                    
                                    result = {
                                        "command": "save_code",
                                        "args": [filename, code_content]
                                    }
                                    print(f"✅ Save_code extraído manualmente: {filename}")
                                    return result
                            pos += 1
                            
            except Exception as e:
                print(f"❌ Erro na extração manual: {e}")
        
        # Estratégia 3.6: Extração manual para create_file
        create_start = response_text.find('{"command": "create_file"')
        if create_start != -1:
            print("🔍 Tentando extração manual de create_file...")
            try:
                # Mesmo processo que save_code
                args_start = response_text.find('"args":', create_start)
                if args_start != -1:
                    bracket_start = response_text.find('[', args_start)
                    if bracket_start != -1:
                        first_quote = response_text.find('"', bracket_start)
                        second_quote = response_text.find('"', first_quote + 1)
                        filename = response_text[first_quote + 1:second_quote]
                        
                        comma_pos = response_text.find(',', second_quote)
                        code_start_quote = response_text.find('"', comma_pos)
                        
                        code_content_start = code_start_quote + 1
                        pos = code_content_start
                        while pos < len(response_text):
                            if response_text[pos] == '"' and response_text[pos-1] != '\\':
                                next_meaningful = pos + 1
                                while next_meaningful < len(response_text) and response_text[next_meaningful].isspace():
                                    next_meaningful += 1
                                if next_meaningful < len(response_text) and response_text[next_meaningful] in ']},':
                                    code_content = response_text[code_content_start:pos]
                                    code_content = code_content.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                                    
                                    result = {
                                        "command": "save_file",
                                        "args": [filename, code_content]
                                    }
                                    print(f"✅ Create_file extraído manualmente: {filename}")
                                    return result
                            pos += 1
                            
            except Exception as e:
                print(f"❌ Erro na extração manual de create_file: {e}")
        
        # Estratégia 4: Busca por comandos diretos sem JSON formal
        command_patterns = [
            (r'list_classes\(\)', "list_classes", []),
            (r'get_class_metadata\("([^"]+)"\)', "get_class_metadata", None),
            (r'get_code\("([^"]+)"\)', "get_code", None),
            (r'read_file\("([^"]+)"\)', "read_file", None),
            (r'continue_reading\("([^"]+)"\)', "continue_reading", None),
            (r'save_code\("([^"]+)",\s*"([^"]+)"\)', "save_code", "dual_args"),
            (r'create_file\("([^"]+)",\s*"([^"]+)"\)', "create_file", "dual_args"),
            (r'final_answer\("([^"]+)"\)', "final_answer", None),
        ]
        
        for pattern, command, default_args in command_patterns:
            match = re.search(pattern, response_text)
            if match:
                if default_args == "dual_args":
                    args = [match.group(1), match.group(2)]
                elif default_args is None:
                    args = [match.group(1)]
                else:
                    args = default_args
                print(f"🔍 Comando direto encontrado: {command} com args: {args}")
                return {"command": command, "args": args}
        
        return None
    
    def _intelligent_fallback(self, response_content):
        """Aplica fallback inteligente baseado no contexto da resposta"""
        import re
        
        content_lower = response_content.lower()
        
        # Estratégia 1: Procura por comandos explícitos mencionados
        explicit_commands = [
            (r'list_classes\b', "list_classes", []),
            (r'get_class_metadata\b', "get_class_metadata", []),
            (r'get_code\b', "get_code", []),
            (r'read_file\b', "read_file", []),
            (r'continue_reading\b', "continue_reading", []),
            (r'final_answer\b', "final_answer", [response_content]),
        ]
        
        for pattern, command, default_args in explicit_commands:
            if re.search(pattern, content_lower):
                print(f"🔍 Fallback: Comando explícito encontrado '{command}'")
                return {"command": command, "args": default_args}
        
        # Estratégia 2: Procura por IDs de abstração
        abs_match = re.search(r'abs_(\d+)', response_content)
        if abs_match:
            abs_id = f"abs_{abs_match.group(1)}"
            print(f"🔍 Fallback: ID de abstração encontrado '{abs_id}'")
            return {"command": "continue_reading", "args": [abs_id]}
        
        # Estratégia 3: Análise de contexto para identificar intenção
        
        # Verifica se é uma análise final
        final_indicators = [
            "em resumo", "concluindo", "conclusão", "final", "sistema é", 
            "arquitetura", "estrutura geral", "compreensão", "entendimento",
            "análise completa", "baseado na", "com base em", "portanto",
            "dessa forma", "assim", "logo", "concluímos"
        ]
        
        final_count = sum(1 for indicator in final_indicators if indicator in content_lower)
        
        # Se tem muitos indicadores finais ou é longo, provavelmente é final_answer
        if final_count >= 2 or (final_count >= 1 and len(response_content.split()) > 50):
            print(f"🔍 Fallback: Análise final detectada ({final_count} indicadores)")
            return {"command": "final_answer", "args": [response_content]}
        
        # Verifica se está solicitando listar classes
        if any(phrase in content_lower for phrase in [
            "listar", "list", "quais classes", "classes existem", "mapear",
            "visão geral", "panorama", "escopo", "todas as classes"
        ]):
            print("🔍 Fallback: Solicitação de listagem detectada")
            return {"command": "list_classes", "args": []}
        
        # Procura por nomes de classes específicas mencionadas
        class_patterns = [
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)',
            r'classe\s+([A-Za-z_][A-Za-z0-9_]*)',
            r'([A-Za-z_][A-Za-z0-9_]*)\s*class',
            r'([A-Za-z_][A-Za-z0-9_]*Service)\b',
            r'([A-Za-z_][A-Zaelz0-9_]*Manager)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Controller)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Repository)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Entity)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Model)\b',
            r'([A-Za-z_][A-Za-z0-9_]*DAO)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Impl)\b'
        ]
        
        for pattern in class_patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                class_name = match.group(1)
                print(f"🔍 Fallback: Classe identificada '{class_name}'")
                
                # Decide comando baseado no contexto
                if any(word in content_lower for word in [
                    'código', 'code', 'implementação', 'método', 'ver', 'mostrar',
                    'examinar', 'analisar', 'investigar'
                ]):
                    return {"command": "get_code", "args": [class_name]}
                elif any(word in content_lower for word in [
                    'metadata', 'informações', 'estrutura', 'relacionamentos', 
                    'herança', 'extends', 'implements', 'dependências'
                ]):
                    return {"command": "get_class_metadata", "args": [class_name]}
                else:
                    # Padrão: pegar metadata primeiro
                    return {"command": "get_class_metadata", "args": [class_name]}
        
        # Procura por arquivos mencionados
        file_patterns = [
            r'arquivo\s+([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'examinar\s+([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'ler\s+([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'file\s+([A-Za-z_][A-Za-z0-9_/]*\.java)'
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                file_name = match.group(1)
                print(f"🔍 Fallback: Arquivo identificado '{file_name}'")
                return {"command": "read_file", "args": [file_name]}
        
        # Estratégia 4: Análise contextual baseada na estrutura da resposta
        
        # Se menciona "Pensamento:" está seguindo o protocolo, mas talvez sem JSON
        if "pensamento:" in content_lower:
            # Procura por menções específicas após "Ação:"
            action_match = re.search(r'ação:\s*(.+)', response_content, re.IGNORECASE | re.DOTALL)
            if action_match:
                action_text = action_match.group(1).strip()
                print(f"🔍 Fallback: Texto da ação encontrado: {action_text[:100]}...")
                
                # Tenta extrair JSON da seção de ação
                action_json = self._extract_json_from_response(action_text)
                if action_json:
                    return action_json
                
                # Se não tem JSON, analisa o texto da ação
                if "list_classes" in action_text.lower():
                    return {"command": "list_classes", "args": []}
                elif "get_class_metadata" in action_text.lower():
                    # Tenta extrair nome da classe
                    class_match = re.search(r'"([^"]+)"', action_text)
                    if class_match:
                        return {"command": "get_class_metadata", "args": [class_match.group(1)]}
                elif "get_code" in action_text.lower():
                    class_match = re.search(r'"([^"]+)"', action_text)
                    if class_match:
                        return {"command": "get_code", "args": [class_match.group(1)]}
        
        # Estratégia 5: Fallback final baseado no comprimento e contexto
        word_count = len(response_content.split())
        
        if word_count > 100:
            # Resposta longa, provavelmente é análise final
            print(f"🔍 Fallback: Resposta longa ({word_count} palavras) - assumindo final_answer")
            return {"command": "final_answer", "args": [response_content]}
        elif word_count > 10:
            # Resposta média, pode ser lista de classes
            print(f"🔍 Fallback: Resposta média ({word_count} palavras) - assumindo list_classes")
            return {"command": "list_classes", "args": []}
        else:
            # Resposta muito curta, comando padrão
            print(f"🔍 Fallback: Resposta curta ({word_count} palavras) - comando padrão")
            return {"command": "list_classes", "args": []}

    def parse_action_from_response(self, response_content):
        """Analisa a resposta do LLM e extrai a ação a ser executada"""
        try:
            # Log da resposta para debug
            char_count = len(response_content)
            preview_size = 300 if char_count > 1000 else 200
            print(f"📋 Resposta do LLM ({char_count} chars):")
            print(f"   Início: {response_content[:preview_size]}...")
            if char_count > preview_size:
                print(f"   Final: ...{response_content[-preview_size:]}")
            
            # Estratégia 1: Extração direta de JSON
            json_result = self._extract_json_from_response(response_content)
            if json_result:
                print(f"✅ JSON extraído com sucesso: {json_result}")
                return json_result
            
            print("⚠️ Nenhum JSON válido encontrado, aplicando análise semântica...")
            
            # Estratégia 2: Análise semântica da resposta
            content_lower = response_content.lower()
            
            # Verifica se é uma resposta final explícita
            final_keywords = [
                "final_answer", "resposta final", "conclusão", "resumo final",
                "em resumo", "concluindo", "portanto", "dessa forma", "assim",
                "baseado na análise", "com base em", "análise completa"
            ]
            
            for keyword in final_keywords:
                if keyword in content_lower:
                    print(f"🎯 Palavra-chave de finalização detectada: '{keyword}'")
                    return {"command": "final_answer", "args": [response_content]}
            
            # Verifica se está seguindo o protocolo estruturado
            if "pensamento:" in content_lower and "ação:" in content_lower:
                print("🔍 Protocolo estruturado detectado, analisando seção de ação...")
                
                # Extrai a seção de ação
                action_match = re.search(r'ação:\s*(.+)', response_content, re.IGNORECASE | re.DOTALL)
                if action_match:
                    action_section = action_match.group(1).strip()
                    print(f"� Seção de ação: {action_section[:200]}...")
                    
                    # Tenta extrair JSON da seção de ação
                    action_json = self._extract_json_from_response(action_section)
                    if action_json:
                        print(f"✅ JSON encontrado na seção de ação: {action_json}")
                        return action_json
                    
                    # Se não tem JSON, analisa o texto da ação
                    return self._parse_action_text(action_section)
            
            # Estratégia 3: Busca por comandos específicos mencionados
            command_mentions = [
                ("list_classes", "listar classes", "mapear classes"),
                ("get_class_metadata", "metadata", "informações da classe"),
                ("get_code", "código", "implementação"),
                ("read_file", "ler arquivo", "arquivo"),
                ("continue_reading", "continuar lendo", "mais conteúdo"),
            ]
            
            for command, *keywords in command_mentions:
                if any(keyword in content_lower for keyword in keywords):
                    print(f"🔍 Comando mencionado detectado: {command}")
                    return {"command": command, "args": []}
            
            # Estratégia 4: Análise contextual inteligente
            print("🤖 Aplicando análise contextual inteligente...")
            return self._intelligent_fallback(response_content)
            
        except Exception as e:
            print(f"❌ Erro inesperado ao processar resposta: {e}")
            import traceback
            traceback.print_exc()
            return {"command": "error", "args": [f"Erro inesperado ao processar resposta: {e}"]}
    
    def _parse_action_text(self, action_text):
        """Analisa texto da seção de ação quando não há JSON"""
        import re
        
        action_lower = action_text.lower()
        
        # Padrões para comandos específicos
        if "list_classes" in action_lower:
            return {"command": "list_classes", "args": []}
        
        # Busca por get_class_metadata com nome da classe
        metadata_match = re.search(r'get_class_metadata.*?"([^"]+)"', action_text, re.IGNORECASE)
        if metadata_match:
            class_name = metadata_match.group(1)
            return {"command": "get_class_metadata", "args": [class_name]}
        
        # Busca por get_code com nome da classe
        code_match = re.search(r'get_code.*?"([^"]+)"', action_text, re.IGNORECASE)
        if code_match:
            class_name = code_match.group(1)
            return {"command": "get_code", "args": [class_name]}
        
        # Busca por read_file com nome do arquivo
        file_match = re.search(r'read_file.*?"([^"]+)"', action_text, re.IGNORECASE)
        if file_match:
            file_name = file_match.group(1)
            return {"command": "read_file", "args": [file_name]}
        
        # Busca por continue_reading com ID
        continue_match = re.search(r'continue_reading.*?"([^"]+)"', action_text, re.IGNORECASE)
        if continue_match:
            content_id = continue_match.group(1)
            return {"command": "continue_reading", "args": [content_id]}
        
        # Se não encontrou nada específico, aplica fallback
        print("🔍 Nenhum comando específico encontrado na ação, aplicando fallback...")
        return self._intelligent_fallback(action_text)

    def execute_tool(self, action_json):
        """Executa a ferramenta especificada na ação"""
        command = action_json.get("command")
        args = action_json.get("args", [])
        
        # Remove parênteses do comando se presente (ex: "list_classes()" -> "list_classes")
        if command and command.endswith("()"):
            command = command[:-2]
        
        print(f"🔧 Executando comando: '{command}' com args: {args}")
        
        try:
            if command == "list_classes":
                result = self.toolbox.list_classes()
                print(f"📋 list_classes retornou {len(result.split('\n')) if result else 0} classes")
                return result
                
            elif command == "get_class_metadata":
                if not args:
                    return "❌ Erro: get_class_metadata requer nome da classe como argumento"
                class_name = args[0]
                result = self.toolbox.get_class_metadata(class_name)
                print(f"📋 get_class_metadata('{class_name}') retornou {len(result)} chars")
                return result
                
            elif command == "get_code":
                if not args:
                    return "❌ Erro: get_code requer nome da classe como argumento"
                
                # Verifica se há parâmetro abstracted nos args
                abstracted = True  # padrão
                if len(args) > 2 and isinstance(args[2], bool):
                    abstracted = args[2]
                elif len(args) > 2 and args[2] in ['false', 'False', '0']:
                    abstracted = False
                
                class_name = args[0]
                method_name = args[1] if len(args) > 1 else None
                result = self.toolbox.get_code(class_name, method_name, abstracted=abstracted)
                print(f"📋 get_code('{class_name}', '{method_name}', abstracted={abstracted}) retornou {len(result)} chars")
                return result
                
            elif command == "read_file":
                if not args:
                    return "❌ Erro: read_file requer caminho do arquivo como argumento"
                
                # Verifica se há parâmetro abstracted nos args
                abstracted = True  # padrão
                if len(args) > 1 and isinstance(args[1], bool):
                    abstracted = args[1]
                elif len(args) > 1 and args[1] in ['false', 'False', '0']:
                    abstracted = False
                
                file_path = args[0]
                result = self.toolbox.read_file(file_path, abstracted=abstracted)
                print(f"📋 read_file('{file_path}', abstracted={abstracted}) retornou {len(result)} chars")
                return result
                
            elif command == "continue_reading":
                if not args:
                    return "❌ Erro: continue_reading requer ID de abstração como argumento"
                abstraction_id = args[0]
                page = args[1] if len(args) > 1 else 1
                result = self.toolbox.continue_reading(abstraction_id, page)
                print(f"📋 continue_reading('{abstraction_id}', page={page}) retornou {len(result)} chars")
                return result
                
            elif command == "save_code" or command == "create_file":
                if len(args) < 2:
                    return "❌ Erro: save_code/create_file requer [filename, code_content] como argumentos"
                
                filename = args[0]
                code_content = args[1]
                
                # Aplica correção automática se necessário
                corrected_code, corrections_log = self._apply_code_correction(filename, code_content)
                
                # Salva o arquivo no diretório do projeto
                output_dir = Path(self.project_path)
                file_path = output_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(corrected_code)
                    
                    # Atualiza o symbol_table após salvar
                    self.toolbox.symbol_table = build_symbol_table(str(output_dir))
                    
                    result = f"✅ Arquivo '{filename}' salvo com sucesso em {file_path}"
                    if corrections_log:
                        result += f"\n🔧 Correções aplicadas: {corrections_log}"
                    print(f"💾 {result}")
                    return result
                except Exception as e:
                    error_msg = f"❌ Erro ao salvar arquivo '{filename}': {e}"
                    print(error_msg)
                    return error_msg
                
            elif command == "final_answer":
                answer = args[0] if args else "[final_answer sem conteúdo]"
                print(f"🎯 final_answer retornando resposta com {len(answer)} chars")
                return answer
                
            elif command == "error":
                error_msg = args[0] if args else "Erro desconhecido"
                print(f"❌ Comando de erro: {error_msg}")
                return error_msg
                
            else:
                error_msg = f"Erro: Comando '{command}' desconhecido. Comandos disponíveis: list_classes, get_class_metadata, get_code, read_file, continue_reading, save_code, create_file, final_answer"
                print(f"❌ {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ Erro ao executar comando '{command}': {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg

    def run(self, mode="edit"):
        """Executa o loop principal do agente, agora com suporte a modos 'edit' e 'new'"""
        print("INFO: Agente iniciado. Objetivo:", self.user_goal)
        print(f"[MODO: {mode.upper()}]")
        print("="*50)
        
        self.mode = mode
        
        # Se não está em modo continue, reinicializa com o prompt correto
        if not self.continue_mode:
            self.initialize_new_conversation(mode)

        if mode == "edit":
            return self._run_edit_mode()
        elif mode == "new":
            return self._run_new_mode()
        else:
            print(f"❌ Modo '{mode}' não reconhecido. Use 'edit' ou 'new'.")
            return None

    def _run_edit_mode(self):
        # Determina o turno inicial baseado no modo
        if self.continue_mode:
            start_turn = self.turn_count
            print(f"🔄 Continuando do turno {start_turn + 1}")
        else:
            start_turn = 0
            self.turn_count = 0
            print("🆕 Iniciando nova análise (edit mode)")

        for turn in range(start_turn, self.max_turns):
            self.turn_count = turn + 1
            print(f"\n--- TURNO {self.turn_count} ---")

            # Se for modo continue e for o primeiro turno, não envia novo prompt
            # Em vez disso, processa a última mensagem do assistente
            if self.continue_mode and turn == start_turn and self.messages:
                last_message = self.messages[-1]
                if last_message["role"] == "assistant":
                    print("🔄 Processando última resposta do assistente...")
                    llm_response_content = last_message["content"]
                    self.messages.pop()
                else:
                    llm_response_content = self.call_llm(current_turn=self.turn_count)
                    self.messages.append({"role": "assistant", "content": llm_response_content})
            else:
                llm_response_content = self.call_llm(current_turn=self.turn_count)
                self.messages.append({"role": "assistant", "content": llm_response_content})

            self.save_current_state()

            action_json = self.parse_action_from_response(llm_response_content)
            if action_json.get("command") == "final_answer":
                print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
                print(action_json["args"][0])
                if self.state_file.exists():
                    self.state_file.unlink()
                return action_json["args"][0]

            execution_result = self.execute_tool(action_json)
            tool_observation_prompt = TOOL_OBSERVATION_PROMPT.format(execution_result=execution_result)
            self.messages.append({"role": "user", "content": tool_observation_prompt})

            self.save_current_state()

        print("INFO: Agente atingiu o número máximo de turnos.")
        return None

    def _run_new_mode(self):
        """
        Novo modo: criação de projeto do zero.
        - Cria diretório de output se não existir
        - Salva cada novo código gerado pelo LLM
        - Atualiza symbol_table a cada iteração
        """
        output_dir = Path(self.project_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"🆕 Criando projeto do zero em: {output_dir}")

        if self.continue_mode:
            start_turn = self.turn_count
            print(f"🔄 Continuando do turno {start_turn + 1}")
        else:
            start_turn = 0
            self.turn_count = 0
            print("🆕 Iniciando nova análise (new mode)")

        for turn in range(start_turn, self.max_turns):
            self.turn_count = turn + 1
            print(f"\n--- TURNO {self.turn_count} ---")

            if self.continue_mode and turn == start_turn and self.messages:
                last_message = self.messages[-1]
                if last_message["role"] == "assistant":
                    print("🔄 Processando última resposta do assistente...")
                    llm_response_content = last_message["content"]
                    self.messages.pop()
                else:
                    llm_response_content = self.call_llm(current_turn=self.turn_count)
                    self.messages.append({"role": "assistant", "content": llm_response_content})
            else:
                llm_response_content = self.call_llm(current_turn=self.turn_count)
                self.messages.append({"role": "assistant", "content": llm_response_content})

            self.save_current_state()

            # Processa a ação normalmente
            action_json = self.parse_action_from_response(llm_response_content)

            if action_json.get("command") == "final_answer":
                print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
                print(action_json["args"][0])
                if self.state_file.exists():
                    self.state_file.unlink()
                return action_json["args"][0]

            execution_result = self.execute_tool(action_json)
            tool_observation_prompt = TOOL_OBSERVATION_PROMPT.format(execution_result=execution_result)
            self.messages.append({"role": "user", "content": tool_observation_prompt})

            self.save_current_state()

        print("INFO: Agente atingiu o número máximo de turnos (new mode).")
        return None

    def _apply_code_correction(self, filename: str, code_content: str) -> tuple[str, str]:
        """
        Aplica correção automática de código usando o mini-compilador corretor.
        
        Args:
            filename: Nome do arquivo para detectar a linguagem
            code_content: Conteúdo do código a ser corrigido
            
        Returns:
            Tuple com (código_corrigido, log_de_correções)
        """
        try:
            # Detecta a linguagem baseada na extensão do arquivo
            language = self._detect_language_from_filename(filename)
            
            if not language:
                return code_content, ""
            
            # Obtém o corretor apropriado
            corrector = get_corrector_for_language(language)
            
            # Aplica as correções
            result = corrector.correct(code_content)
            
            # Prepara o log de correções
            corrections_log = ""
            if result.corrections_applied:
                corrections_log = f"{len(result.corrections_applied)} correções aplicadas: {', '.join(result.corrections_applied[:3])}"
                if len(result.corrections_applied) > 3:
                    corrections_log += f" (e mais {len(result.corrections_applied) - 3})"
            
            # Se a compilação falhou mesmo após correções, registra o aviso
            if not result.compilation_successful and result.error_messages:
                error_summary = result.error_messages[0] if result.error_messages else "erro desconhecido"
                corrections_log += f" | ⚠️ Ainda há erros: {error_summary}"
            
            return result.corrected_code, corrections_log
            
        except ValueError as e:
            # Linguagem não suportada
            return code_content, f"⚠️ {str(e)}"
        except Exception as e:
            # Erro durante correção
            return code_content, f"⚠️ Erro na correção automática: {str(e)}"
    
    def _detect_language_from_filename(self, filename: str) -> str:
        """
        Detecta a linguagem de programação baseada na extensão do arquivo.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Nome da linguagem ou None se não suportada
        """
        extension = Path(filename).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.mjs': 'javascript',
            '.cjs': 'javascript'
        }
        
        return language_map.get(extension, None)
