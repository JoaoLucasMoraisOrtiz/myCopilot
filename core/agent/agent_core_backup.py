import json
import re
import os
import pickle
from pathlib import Path
from analyzers.java_analyzer import build_symbol_table
from core.agent.callInfoFromDict import get_source_code_for_member, read_full_file
from core.llm.llm_client import LLMClient
from core.agent.agent_prompts import SYSTEM_PROMPT_TEMPLATE, USER_START_PROMPT, TOOL_OBSERVATION_PROMPT

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
            return f"Classe '{class_name}' não encontrada."
        
        # Limita o número de relacionamentos para evitar overflow
        relationships = entry.get('relationships', [])
        if len(relationships) > 20:
            relationships = relationships[:20]
            relationships.append({"type": "INFO", "target": f"... e mais {len(entry['relationships']) - 20} relacionamentos"})
        
        # Limita o número de métodos
        methods = entry.get('methods', [])
        if len(methods) > 15:
            methods = methods[:15]
            methods.append(f"... e mais {len(entry['methods']) - 15} métodos")
        
        metadata = {
            'file_path': entry['file_path'],
            'type': entry['type'],
            'extends': entry['extends'],
            'implements': entry['implements'],
            'fields': entry.get('fields', []),
            'constructors': entry.get('constructors', []),
            'methods': methods,
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

    def _abstract_class_code(self, class_content):
        """Abstrai métodos longos de uma classe, mantendo estrutura visível"""
        lines = class_content.split('\n')
        result_lines = []
        current_method = []
        in_method = False
        brace_count = 0
        method_brace_count = 0
        
        for line in lines:
            # Detecta início de método (heurística simples)
            stripped = line.strip()
            if (stripped and not stripped.startswith('//') and not stripped.startswith('/*') and 
                ('(' in line and ')' in line and '{' in line) and
                any(keyword in line for keyword in ['public', 'private', 'protected', 'static', 'final'])):
                
                # Se já estava em um método, processa o anterior
                if in_method and current_method:
                    method_content = '\n'.join(current_method)
                    if len(method_content) > 300:  # Métodos com mais de 300 chars são abstraídos
                        result_lines.append(self._abstract_method_body(method_content))
                    else:
                        result_lines.extend(current_method)
                
                # Inicia novo método
                current_method = [line]
                in_method = True
                method_brace_count = line.count('{') - line.count('}')
                
            elif in_method:
                current_method.append(line)
                method_brace_count += line.count('{') - line.count('}')
                
                # Se chegou ao fim do método
                if method_brace_count == 0:
                    method_content = '\n'.join(current_method)
                    if len(method_content) > 300:
                        result_lines.append(self._abstract_method_body(method_content))
                    else:
                        result_lines.extend(current_method)
                    
                    current_method = []
                    in_method = False
                    
            else:
                # Linha fora de método (campos, imports, etc.)
                result_lines.append(line)
        
        # Processa último método se necessário
        if in_method and current_method:
            method_content = '\n'.join(current_method)
            if len(method_content) > 300:
                result_lines.append(self._abstract_method_body(method_content))
            else:
                result_lines.extend(current_method)
        
        final_result = '\n'.join(result_lines)
        
        # Aplica limite de segurança mesmo na versão abstraída
        if len(final_result) > 6000:
            final_result = final_result[:6000] + "\n\n[... restante da classe abstraído - use continue_reading para ver partes específicas ...]"
        
        return final_result

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
        
        if continue_mode:
            self.load_previous_state()
        else:
            self.initialize_new_conversation()

    def initialize_new_conversation(self):
        """Inicializa uma nova conversa do zero"""
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(user_goal=self.user_goal)},
            {"role": "user", "content": USER_START_PROMPT}
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
        prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in self.messages])
        
        # Adiciona pressão temporal baseada no número de turnos
        pressure_message = self._get_pressure_message(current_turn)
        if pressure_message:
            print(f"🎯 APLICANDO PRESSÃO TEMPORAL (Turno {current_turn}): {pressure_message[:80]}...")
            prompt += f"\n\nUSER: {pressure_message}"
        
        # Gestão inteligente de contexto para respostas grandes
        original_length = len(prompt)
        
        # Limite mais flexível para permitir respostas grandes
        if original_length > 25000:  # 25k chars max (aumentado de 20k)
            print(f"⚠️ Prompt muito longo ({original_length} chars), aplicando compressão inteligente...")
            
            # Estratégia de compressão progressiva
            if original_length > 40000:  # Muito crítico
                # Mantém system prompt + últimas 2 mensagens
                truncated_messages = [self.messages[0]]
                truncated_messages.extend(self.messages[-2:])
                print("🔄 Compressão crítica: mantendo apenas 2 últimas mensagens")
            elif original_length > 30000:  # Crítico
                # Mantém system prompt + últimas 3 mensagens
                truncated_messages = [self.messages[0]]
                truncated_messages.extend(self.messages[-3:])
                print("🔄 Compressão alta: mantendo 3 últimas mensagens")
            else:  # Moderado
                # Mantém system prompt + últimas 4 mensagens
                truncated_messages = [self.messages[0]]
                truncated_messages.extend(self.messages[-4:])
                print("🔄 Compressão moderada: mantendo 4 últimas mensagens")
            
            # Reconstrói o prompt
            prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in truncated_messages])
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
        import re, json
        
        # 1) JSON em bloco markdown ```json ... ```
        block = re.search(r'```json\s*(\{.*?\})', response_text, re.DOTALL)
        if block:
            json_str = block.group(1).strip()
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                pass
            else:
                # remove parenteses no comando
                cmd = data.get('command','')
                if isinstance(cmd,str) and cmd.endswith('()'):
                    data['command'] = cmd[:-2]
                return data
        
        # 2) Procura JSON iniciando em {"command"
        start = response_text.find('{"command"')
        if start != -1:
            substr = response_text[start:]
            # detectar JSON balanceado
            stack = []
            for i, ch in enumerate(substr):
                if ch == '{': stack.append('{')
                elif ch == '}':
                    if stack: stack.pop()
                    if not stack:
                        candidate = substr[:i+1]
                        # limpa elipses e vírgulas antes de fechar
                        candidate = candidate.replace('...', '')
                        candidate = re.sub(r',\s*}', '}', candidate)
                        try:
                            data = json.loads(candidate)
                        except Exception:
                            break
                        # remove parenteses no comando
                        cmd = data.get('command','')
                        if isinstance(cmd,str) and cmd.endswith('()'):
                            data['command'] = cmd[:-2]
                        return data
        return None
    
    def _intelligent_fallback(self, response_content):
        """Aplica fallback inteligente baseado no contexto da resposta"""
        import re
        
        content_lower = response_content.lower()
        
        # Procura por IDs de abstração primeiro (prioridade)
        abs_match = re.search(r'abs_(\d+)', response_content)
        if abs_match:
            abs_id = f"abs_{abs_match.group(1)}"
            print(f"🔍 Fallback: ID de abstração encontrado '{abs_id}'")
            return {"command": "continue_reading", "args": [abs_id]}
        
        # Verifica se parece ser uma análise final (prioridade alta)
        final_indicators = [
            "em resumo", "concluindo", "conclusão", "final", "sistema é", 
            "arquitetura", "estrutura geral", "compreensão", "entendimento"
        ]
        
        # Indicadores de alta prioridade que sempre geram final_answer
        priority_indicators = ["em resumo", "concluindo", "conclusão"]
        
        final_count = sum(1 for indicator in final_indicators if indicator in content_lower)
        has_priority = any(indicator in content_lower for indicator in priority_indicators)
        
        if has_priority or (final_count >= 2):
            word_count = len(response_content.split())
            if word_count > 5:  # Reduzido de 20 para 5 palavras mínimas
                print("🔍 Fallback: Detectada análise final por conteúdo")
                return {"command": "final_answer", "args": [response_content]}
        
        # Procura por arquivos mencionados (.java)
        file_patterns = [
            r'arquivo\s+([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'([A-Za-z_][A-Za-z0-9_]*\.java)',
            r'examinar\s+([A-Za-z_][A-Za-z0-9_/]*\.java)',
            r'ler\s+([A-Za-z_][A-Za-z0-9_/]*\.java)'
        ]
        
        for pattern in json_patterns:
            for match in re.finditer(pattern, response_text):
                raw = match.group(0)
                # Limpeza: remove elipses e vírgulas antes de fechar arrays ou objetos
                json_str = raw.replace('...', '')
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                print(f"🔍 JSON encontrado (padrão): {raw[:100]}...")
                try:
                    parsed = json.loads(json_str)
                    # Verifica se é um comando válido
                    if parsed.get("command") in ["list_classes", "get_class_metadata", "get_code", "read_file", "continue_reading", "final_answer"]:
                        return parsed
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON após limpeza: {e}")
                    continue
        
        for pattern in class_patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                class_name = match.group(1)
                print(f"🔍 Fallback: Classe identificada '{class_name}'")
                # Decide comando baseado no contexto
                if any(word in content_lower for word in ['código', 'code', 'implementação', 'método', 'ver']):
                    return {"command": "get_code", "args": [class_name]}
                else:
                    return {"command": "get_class_metadata", "args": [class_name]}
        # Fallback padrão baseado no contexto geral
        print("🔍 Fallback: Aplicando comando padrão")
        if "list" in content_lower or "listar" in content_lower:
            return {"command": "list_classes", "args": []}
        else:
            return {"command": "list_classes", "args": []}

    def parse_action_from_response(self, response_content):
        try:
            # Log da resposta para debug - mostra mais contexto para respostas grandes
            char_count = len(response_content)
            preview_size = 500 if char_count > 10000 else 200
            print(f"� Resposta do LLM ({char_count} chars): {response_content[:preview_size]}...")
            
            # Para respostas muito grandes, foca na busca de JSON no final
            if char_count > 15000:
                # Procura JSON nas últimas 2000 chars (onde geralmente está o comando)
                search_content = response_content[-2000:]
                print("🔍 Resposta muito grande, focando na parte final para buscar JSON...")
            else:
                search_content = response_content
            
            # Extrai JSON usando método robusto
            json_result = self._extract_json_from_response(search_content)
            if json_result:
                return json_result
            
            # Se não encontrou JSON, tenta buscar na resposta completa
            if char_count > 15000:
                print("🔍 Buscando JSON na resposta completa...")
                json_result = self._extract_json_from_response(response_content)
                if json_result:
                    return json_result
            
            # Análise semântica para respostas grandes
            content_lower = response_content.lower()
            
            # Verifica se é uma resposta final
            if any(phrase in content_lower for phrase in [
                "final_answer", "resposta final", "conclusão", "resumo final",
                "em resumo", "concluindo", "portanto", "dessa forma"
            ]):
                print("🎯 Detectada resposta final por análise semântica")
                return {"command": "final_answer", "args": [response_content]}
            
            # Verifica se menciona classes específicas
            if "class" in content_lower and ("get_code" in content_lower or "código" in content_lower):
                # Tenta extrair nome de classe
                class_match = re.search(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', response_content, re.IGNORECASE)
                if class_match:
                    class_name = class_match.group(1)
                    print(f"🔍 Classe extraída: {class_name}")
                    return {"command": "get_code", "args": [class_name]}
            
            # Verifica se está pedindo metadata
            if any(phrase in content_lower for phrase in [
                "metadata", "informações", "estrutura", "relacionamentos", "herança"
            ]):
                return {"command": "get_class_metadata", "args": [""]}
            
            # Fallback inteligente baseado no contexto
            print("⚠️ Aplicando fallback inteligente baseado no contexto...")
            return self._intelligent_fallback(response_content)
            
        except Exception as e:
            print(f"❌ Erro inesperado ao processar resposta: {e}")
            return {"command": "error", "args": [f"Erro inesperado ao processar resposta: {e}"]}

    def execute_tool(self, action_json):
        command = action_json.get("command")
        args = action_json.get("args", [])
        
        # Remove parênteses do comando se presente (ex: "list_classes()" -> "list_classes")
        if command and command.endswith("()"):
            command = command[:-2]
        
        print(f"🔧 Executando comando: {command} com args: {args}")
        
        if command == "list_classes":
            return self.toolbox.list_classes()
        elif command == "get_class_metadata":
            return self.toolbox.get_class_metadata(*args)
        elif command == "get_code":
            # Verifica se há parâmetro abstracted nos args
            abstracted = True  # padrão
            if len(args) > 2 and isinstance(args[2], bool):
                abstracted = args[2]
            elif len(args) > 2 and args[2] in ['false', 'False', '0']:
                abstracted = False
            
            return self.toolbox.get_code(*args[:2], abstracted=abstracted)
        elif command == "read_file":
            # Verifica se há parâmetro abstracted nos args
            abstracted = True  # padrão
            if len(args) > 1 and isinstance(args[1], bool):
                abstracted = args[1]
            elif len(args) > 1 and args[1] in ['false', 'False', '0']:
                abstracted = False
                
            return self.toolbox.read_file(args[0], abstracted=abstracted)
        elif command == "continue_reading":
            return self.toolbox.continue_reading(*args)
        elif command == "final_answer":
            return args[0] if args else "[final_answer sem conteúdo]"
        else:
            return f"Erro: Comando '{command}' desconhecido. Comandos disponíveis: list_classes, get_class_metadata, get_code, read_file, continue_reading, final_answer"

    def run(self):
        print("INFO: Agente iniciado. Objetivo:", self.user_goal)
        print("="*50)
        
        # Determina o turno inicial baseado no modo
        if self.continue_mode:
            start_turn = self.turn_count
            print(f"🔄 Continuando do turno {start_turn + 1}")
        else:
            start_turn = 0
            self.turn_count = 0
            print("🆕 Iniciando nova análise")
        
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
                    # Remove a última mensagem do assistente para reprocessá-la
                    self.messages.pop()
                else:
                    # Se a última mensagem não for do assistente, continua normalmente
                    llm_response_content = self.call_llm(current_turn=self.turn_count)
                    self.messages.append({"role": "assistant", "content": llm_response_content})
            else:
                # Funcionamento normal
                llm_response_content = self.call_llm(current_turn=self.turn_count)
                self.messages.append({"role": "assistant", "content": llm_response_content})
            
            # Salva estado após cada turno
            self.save_current_state()
            
            # Processa a ação
            action_json = self.parse_action_from_response(llm_response_content)
            if action_json.get("command") == "final_answer":
                print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
                print(action_json["args"][0])
                # Limpa o estado após conclusão bem-sucedida
                if self.state_file.exists():
                    self.state_file.unlink()
                return action_json["args"][0]
            
            # Executa ferramenta e adiciona observação
            execution_result = self.execute_tool(action_json)
            tool_observation_prompt = TOOL_OBSERVATION_PROMPT.format(execution_result=execution_result)
            self.messages.append({"role": "user", "content": tool_observation_prompt})
            
            # Salva estado após observação da ferramenta
            self.save_current_state()
            
        print("INFO: Agente atingiu o número máximo de turnos.")
        return None
