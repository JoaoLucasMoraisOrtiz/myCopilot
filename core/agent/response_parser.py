"""
Agent Response Parser Module

Responsável por analisar e extrair ações das respostas do LLM.
"""

import json
import re
from typing import Dict, Any, Optional


class AgentResponseParser:
    """Classe responsável por parsear respostas do LLM e extrair comandos."""
    
    def __init__(self):
        self.valid_commands = {
            "list_classes", "get_class_metadata", "get_code", "read_file", 
            "continue_reading", "save_code", "create_file", "edit_code", 
            "final_answer", "multi_create_file"
        }
    
    def parse_action_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Analisa a resposta do LLM e extrai a ação a ser executada.
        
        Args:
            response_content: Conteúdo da resposta do LLM
            
        Returns:
            Dict com 'command' e 'args'
        """
        try:
            char_count = len(response_content)
            preview_size = 300 if char_count > 1000 else 200
            print(f"📋 Resposta do LLM ({char_count} chars):")
            print(f"{response_content}")
            # Estratégia 1: Extração direta de JSON
            json_result = self._extract_json_from_response(response_content)
            if json_result:
                print(f"✅ JSON extraído com sucesso: {json_result}")
                # Se vier um comando 'instruction', tenta converter para comandos de criação de arquivos
                if json_result.get('command') == 'instruction':
                    create_file_cmds = self._extract_create_file_commands(json_result['args'][0])
                    if create_file_cmds:
                        print(f"🔄 Convertendo 'instruction' em comandos 'create_file': {create_file_cmds}")
                        # Retorna múltiplos comandos para processamento sequencial
                        return {"command": "multi_create_file", "args": create_file_cmds}
                return json_result
            print("⚠️ Nenhum JSON válido encontrado, aplicando análise semântica...")
            # Estratégia 2: Análise semântica da resposta
            return self._semantic_analysis(response_content)
        except Exception as e:
            print(f"❌ Erro inesperado ao processar resposta: {e}")
            return {"command": "error", "args": [f"Erro inesperado ao processar resposta: {e}"]}
    
    def _extract_create_file_commands(self, instruction_text: str):
        """Extrai comandos de criação de arquivos e seus conteúdos das instruções do LLM."""
        # Padrões mais abrangentes para diferentes linguagens
        patterns = [
            r'```typescript\n//\s*(.*?)\n([\s\S]*?)```',
            r'```javascript\n//\s*(.*?)\n([\s\S]*?)```',
            r'```jsx\n//\s*(.*?)\n([\s\S]*?)```',
            r'```tsx\n//\s*(.*?)\n([\s\S]*?)```',
            r'```python\n#\s*(.*?)\n([\s\S]*?)```',
            r'```java\n//\s*(.*?)\n([\s\S]*?)```',
            r'```(\w+)\n(?://|#)\s*(.*?)\n([\s\S]*?)```',  # Padrão genérico
        ]
        
        cmds = []
        for pattern in patterns:
            matches = re.findall(pattern, instruction_text)
            for match in matches:
                if len(match) == 2:  # Padrão específico (linguagem + comentário + código)
                    filename, code = match
                elif len(match) == 3:  # Padrão genérico (linguagem + comentário + código)
                    _, filename, code = match
                else:
                    continue
                    
                filename = filename.strip()
                code = code.strip()
                if filename and code:
                    cmds.append({"file_path": filename, "content": code})
        
        return cmds if cmds else None
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON da resposta do LLM com parsing robusto."""
        
        # Estratégia 1: JSON em bloco markdown
        json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_block_match:
            json_str = json_block_match.group(1).strip()
            print(f"🔍 JSON encontrado em bloco: {json_str[:100]}...")
            try:
                data = json.loads(json_str)
                return self._clean_command(data)
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON do bloco: {e}")
        
        # Estratégia 2: JSON balanceado iniciando com {"command"
        json_result = self._extract_balanced_json(response_text)
        if json_result:
            return json_result
        
        # Estratégia 3: JSON simples com whitespace
        simple_json_match = re.search(r'\{\s*"command"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\[[^\]]*\]\s*\}', response_text, re.DOTALL)
        if simple_json_match:
            json_str = simple_json_match.group(0)
            print(f"🔍 JSON simples encontrado: {json_str[:100]}...")
            try:
                # Primeiro tenta parsing direto
                data = json.loads(json_str)
                return self._clean_command(data)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON simples direto falhou: {e}")
                try:
                    # Só aplica correção se necessário
                    cleaned_json = self._fix_json_quotes(json_str)
                    data = json.loads(cleaned_json)
                    return self._clean_command(data)
                except json.JSONDecodeError as e2:
                    print(f"❌ Erro ao decodificar JSON simples após correção: {e2}")
        
        # Estratégia 4: Extração manual com contagem de aspas para edit_code
        manual_result = self._extract_edit_code_with_quote_counting(response_text)
        if manual_result:
            return manual_result
        
        # Estratégia 5: Extração para comandos com JSON escapado (create_file, etc.)
        escaped_json_result = self._extract_command_with_escaped_json(response_text)
        if escaped_json_result:
            return escaped_json_result
        
        # Estratégia 6: Padrões específicos para comandos conhecidos
        return self._extract_by_patterns(response_text)
    
    def _clean_and_repair_json(self, json_str: str) -> str:
        """Limpa e repara a string JSON antes do parsing."""
        # Remove lixo no início (como **)
        if json_str.startswith("**"):
            json_str = json_str.lstrip("*")
        
        # Repara escapes de nova linha que quebram o parser
        # Substitui \n, \r, \t não escapados por suas versões escapadas \\n, \\r, \\t
        # Usa uma expressão regular com negative lookbehind para não substituir os já escapados
        json_str = re.sub(r'(?<!\\)\n', r'\\n', json_str)
        json_str = re.sub(r'(?<!\\)\r', r'\\r', json_str)
        json_str = re.sub(r'(?<!\\)\t', r'\\t', json_str)
        
        return json_str
    
    def _extract_balanced_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON balanceado da resposta."""
        start = response_text.find('{"command"')
        if start == -1:
            return None
            
        substr = response_text[start:]
        stack = []
        in_string = False
        escaped = False
        string_char = None  # Para rastrear se estamos em aspas duplas ou simples
        
        for i, ch in enumerate(substr):
            if escaped:
                escaped = False
                continue
                
            if ch == '\\' and in_string:
                escaped = True
                continue
                
            if ch in ['"', "'"] and not escaped:
                if not in_string:
                    in_string = True
                    string_char = ch
                elif ch == string_char:
                    in_string = False
                    string_char = None
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
                            # Limpa o JSON de escapes problemáticos antes de decodificar
                            cleaned_candidate = self._unescape_json_string(candidate)
                            data = json.loads(cleaned_candidate)
                            return self._clean_command(data)
                        except json.JSONDecodeError as e:
                            print(f"❌ Erro ao decodificar JSON balanceado: {e}")
                            print(f"  Contexto do erro (char {e.pos}): ...{e.doc[e.pos-10:e.pos+10]}...")
                            break
        return None
    
    def _unescape_json_string(self, s: str) -> str:
        """
        Substitui sequências de escape duplas (\\", \\n) por suas versões simples.
        Isso prepara a string para o json.loads do Python.
        """
        # Regex para encontrar "args": [...]
        args_match = re.search(r'("args"\s*:\s*\[)(.*?)(\])', s, re.DOTALL)
        if not args_match:
            return s # Retorna a string original se não encontrar o padrão de args

        prefix = s[:args_match.start(2)]
        args_content = args_match.group(2)
        suffix = s[args_match.end(2):]

        # Aplica as substituições apenas dentro do conteúdo dos argumentos
        cleaned_args = args_content.replace('\\\\"', '\\"')
        cleaned_args = cleaned_args.replace('\\\\n', '\\n')
        
        reconstructed = f"{prefix}{cleaned_args}{suffix}"
        print(f"ℹ️ JSON reconstruído após limpeza: {reconstructed[:200]}...")
        return reconstructed
    
    def _fix_json_quotes(self, json_str: str) -> str:
        """
        Corrige problemas comuns de aspas em JSON.
        
        Args:
            json_str: String JSON potencialmente malformada
            
        Returns:
            String JSON corrigida
        """
        try:
            # Primeiro tenta parsing direto
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
        
        # Estratégia 1: Escapar aspas dentro de strings do array args
        def escape_quotes_in_args(match):
            full_match = match.group(0)
            args_content = match.group(1)
            
            # Divide os argumentos respeitando aspas
            args = []
            current_arg = ""
            in_quotes = False
            quote_char = None
            i = 0
            
            while i < len(args_content):
                ch = args_content[i]
                
                if ch in ['"', "'"] and (i == 0 or args_content[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = ch
                        current_arg += ch
                    elif ch == quote_char:
                        in_quotes = False
                        current_arg += ch
                        quote_char = None
                    else:
                        # Aspas diferentes dentro da string - escapa
                        current_arg += '\\' + ch
                elif ch == ',' and not in_quotes:
                    args.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += ch
                i += 1
            
            if current_arg.strip():
                args.append(current_arg.strip())
            
            # Reconstrói o JSON
            args_str = ', '.join(args)
            return f'"args": [{args_str}]'
        
        # Aplica a correção
        pattern = r'"args"\s*:\s*\[(.*?)\]'
        corrected = re.sub(pattern, escape_quotes_in_args, json_str, flags=re.DOTALL)
        
        try:
            json.loads(corrected)
            return corrected
        except json.JSONDecodeError:
            # Se ainda não funciona, tenta escape mais agressivo
            return self._aggressive_quote_fix(json_str)
    
    def _aggressive_quote_fix(self, json_str: str) -> str:
        """
        Aplica correção mais agressiva de aspas.
        
        Args:
            json_str: String JSON malformada
            
        Returns:
            String JSON corrigida (melhor esforço)
        """
        # Extrai componentes do JSON manualmente
        command_match = re.search(r'"command"\s*:\s*"([^"]+)"', json_str)
        if not command_match:
            return json_str
        
        command = command_match.group(1)
        
        # Extrai a seção args de forma mais robusta
        args_match = re.search(r'"args"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if not args_match:
            return json_str
        
        args_content = args_match.group(1).strip()
        
        # Parse manual dos argumentos
        args = []
        if args_content:
            # Divide por vírgulas, mas respeita aspas
            current_arg = ""
            paren_depth = 0
            in_quotes = False
            quote_char = None
            
            for i, ch in enumerate(args_content):
                if ch in ['"', "'"] and (i == 0 or args_content[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = ch
                        current_arg += '"'  # Normaliza para aspas duplas
                    elif ch == quote_char:
                        in_quotes = False
                        current_arg += '"'  # Normaliza para aspas duplas
                        quote_char = None
                    else:
                        # Aspas internas - escapa
                        current_arg += '\\"'
                elif ch == ',' and not in_quotes and paren_depth == 0:
                    args.append(current_arg.strip())
                    current_arg = ""
                elif ch == '(' and not in_quotes:
                    paren_depth += 1
                    current_arg += ch
                elif ch == ')' and not in_quotes:
                    paren_depth -= 1
                    current_arg += ch
                else:
                    current_arg += ch
            
            if current_arg.strip():
                args.append(current_arg.strip())
        
        # Reconstrói o JSON corrigido
        args_str = ', '.join(args)
        corrected_json = f'{{"command": "{command}", "args": [{args_str}]}}'
        
        return corrected_json
    
    def _extract_by_patterns(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai comandos usando padrões regex."""
        
        # Padrões para comandos específicos
        patterns = [
            (r'list_classes\(\)', "list_classes", []),
            (r'get_class_metadata\("([^"]+)"\)', "get_class_metadata", lambda m: [m.group(1)]),
            (r'get_code\("([^"]+)"\)', "get_code", lambda m: [m.group(1)]),
            (r'read_file\("([^"]+)"\)', "read_file", lambda m: [m.group(1)]),
            (r'continue_reading\("([^"]+)"\)', "continue_reading", lambda m: [m.group(1)]),
            (r'edit_code\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', "edit_code", lambda m: [m.group(1), m.group(2), m.group(3)]),
            (r'final_answer\("([^"]+)"\)', "final_answer", lambda m: [m.group(1)]),
        ]
        
        for pattern, command, args_func in patterns:
            match = re.search(pattern, response_text)
            if match:
                args = args_func(match) if callable(args_func) else args_func
                print(f"🔍 Comando direto encontrado: {command} com args: {args}")
                return {"command": command, "args": args}
        
        return None
    
    def _semantic_analysis(self, response_content: str) -> Dict[str, Any]:
        """Aplica análise semântica quando não encontra JSON."""
        
        content_lower = response_content.lower()
        
        # Verifica se é uma resposta final
        final_keywords = [
            "final_answer", "resposta final", "conclusão", "resumo final",
            "em resumo", "concluindo", "portanto", "dessa forma", "assim",
            "baseado na análise", "com base em", "análise completa"
        ]
        
        for keyword in final_keywords:
            if keyword in content_lower:
                print(f"🎯 Palavra-chave de finalização detectada: '{keyword}'")
                return {"command": "final_answer", "args": [response_content]}
        
        # Verifica protocolo estruturado
        if "pensamento:" in content_lower and "ação:" in content_lower:
            return self._parse_structured_protocol(response_content)
        
        # Busca por comandos mencionados
        command_result = self._find_mentioned_commands(response_content)
        if command_result:
            return command_result
        
        # Fallback inteligente
        return self._intelligent_fallback(response_content)
    
    def _parse_structured_protocol(self, response_content: str) -> Dict[str, Any]:
        """Analisa protocolo estruturado com seções Pensamento/Ação."""
        
        action_match = re.search(r'ação:\s*(.+)', response_content, re.IGNORECASE | re.DOTALL)
        if action_match:
            action_section = action_match.group(1).strip()
            print(f"📝 Seção de ação: {action_section[:200]}...")
            
            # Tenta extrair JSON da seção de ação
            action_json = self._extract_json_from_response(action_section)
            if action_json:
                return action_json
            
            # Analisa texto da ação
            return self._parse_action_text(action_section)
        
        return self._intelligent_fallback(response_content)
    
    def _find_mentioned_commands(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Busca por comandos específicos mencionados no texto."""
        
        content_lower = response_content.lower()
        
        command_mentions = [
            ("list_classes", ["listar classes", "mapear classes", "todas as classes"]),
            ("get_class_metadata", ["metadata", "informações da classe", "estrutura da classe"]),
            ("get_code", ["código", "implementação", "ver código"]),
            ("read_file", ["ler arquivo", "abrir arquivo", "conteúdo do arquivo"]),
            ("continue_reading", ["continuar lendo", "mais conteúdo", "resto do código"]),
            ("edit_code", ["editar", "modificar", "alterar código", "substituir", "corrigir"]),
        ]
        
        for command, keywords in command_mentions:
            if any(keyword in content_lower for keyword in keywords):
                print(f"🔍 Comando mencionado detectado: {command}")
                return {"command": command, "args": []}
        
        return None
    
    def _parse_action_text(self, action_text: str) -> Dict[str, Any]:
        """Analisa texto da seção de ação quando não há JSON."""
        
        action_lower = action_text.lower()
        
        # Padrões para comandos com argumentos
        patterns = [
            (r'list_classes', "list_classes", []),
            (r'get_class_metadata.*?"([^"]+)"', "get_class_metadata", lambda m: [m.group(1)]),
            (r'get_code.*?"([^"]+)"', "get_code", lambda m: [m.group(1)]),
            (r'read_file.*?"([^"]+)"', "read_file", lambda m: [m.group(1)]),
            (r'continue_reading.*?"([^"]+)"', "continue_reading", lambda m: [m.group(1)]),
            (r'edit_code.*?"([^"]+)".*?"([^"]+)".*?"([^"]+)"', "edit_code", lambda m: [m.group(1), m.group(2), m.group(3)]),
        ]
        
        for pattern, command, args_func in patterns:
            match = re.search(pattern, action_text, re.IGNORECASE)
            if match:
                args = args_func(match) if callable(args_func) else args_func
                return {"command": command, "args": args}
        
        return self._intelligent_fallback(action_text)
    
    def _intelligent_fallback(self, response_content: str) -> Dict[str, Any]:
        """Aplica fallback inteligente baseado no contexto da resposta."""
        
        content_lower = response_content.lower()
        word_count = len(response_content.split())
        
        # Busca por IDs de abstração
        abs_match = re.search(r'abs_(\d+)', response_content)
        if abs_match:
            abs_id = f"abs_{abs_match.group(1)}"
            print(f"🔍 Fallback: ID de abstração encontrado '{abs_id}'")
            return {"command": "continue_reading", "args": [abs_id]}
        
        # Análise de contexto para identificar intenção
        final_indicators = [
            "em resumo", "concluindo", "conclusão", "final", "sistema é", 
            "arquitetura", "estrutura geral", "compreensão", "entendimento",
            "análise completa", "baseado na", "com base em", "portanto",
            "dessa forma", "assim", "logo", "concluímos"
        ]
        
        final_count = sum(1 for indicator in final_indicators if indicator in content_lower)
        
        # Se tem muitos indicadores finais ou é longo, provavelmente é final_answer
        if final_count >= 2 or (final_count >= 1 and word_count > 50):
            print(f"🔍 Fallback: Análise final detectada ({final_count} indicadores)")
            return {"command": "final_answer", "args": [response_content]}
        
        # Verifica se está solicitando listar classes
        if any(phrase in content_lower for phrase in [
            "listar", "list", "quais classes", "classes existem", "mapear",
            "visão geral", "panorama", "escopo"
        ]):
            print("🔍 Fallback: Solicitação de listagem detectada")
            return {"command": "list_classes", "args": []}
        
        # Busca por nomes de classes/arquivos
        class_result = self._find_class_or_file_references(response_content)
        if class_result:
            return class_result
        
        # Fallback final baseado no comprimento
        if word_count > 100:
            print(f"🔍 Fallback: Resposta longa ({word_count} palavras) - assumindo final_answer")
            return {"command": "final_answer", "args": [response_content]}
        elif word_count > 10:
            print(f"🔍 Fallback: Resposta média ({word_count} palavras) - assumindo list_classes")
            return {"command": "list_classes", "args": []}
        else:
            print(f"🔍 Fallback: Resposta curta ({word_count} palavras) - comando padrão")
            return {"command": "list_classes", "args": []}
    
    def _find_class_or_file_references(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Busca por referências de classes ou arquivos no conteúdo."""
        
        # Padrões para classes
        class_patterns = [
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)',
            r'classe\s+([A-Za-z_][A-Za-z0-9_]*)',
            r'([A-Za-z_][A-Zaelz0-9_]*)\s*class',
            r'([A-Za-z_][A-Za-z0-9_]*Service)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Manager)\b',
            r'([A-Za-z_][A-Za-z0-9_]*Controller)\b',
        ]
        
        for pattern in class_patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                class_name = match.group(1)
                print(f"🔍 Fallback: Classe identificada '{class_name}'")
                
                content_lower = response_content.lower()
                if any(word in content_lower for word in [
                    'código', 'code', 'implementação', 'método', 'ver', 'mostrar'
                ]):
                    return {"command": "get_code", "args": [class_name]}
                else:
                    return {"command": "get_class_metadata", "args": [class_name]}
        
        # Padrões para arquivos
        file_patterns = [
            r'arquivo\s+([A-Za-z_][A-Za-z0-9_/]*\.(java|py|js|ts))',
            r'([A-Za-z_][A-Za-z0-9_/]*\.(java|py|js|ts))',
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, response_content, re.IGNORECASE)
            if match:
                file_name = match.group(1)
                print(f"🔍 Fallback: Arquivo identificado '{file_name}'")
                return {"command": "read_file", "args": [file_name]}
        
        return None
    
    def _extract_edit_code_with_quote_counting(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai comando edit_code usando contagem de aspas para lidar com JSONs malformados.
        Procura pelo padrão: "command": "edit_code", "args": [...]
        """
        # Procura pelo início do comando edit_code
        command_match = re.search(r'"command"\s*:\s*"edit_code"', response_text, re.IGNORECASE)
        if not command_match:
            return None
        
        # Encontra o início do array args
        args_start = response_text.find('"args"', command_match.end())
        if args_start == -1:
            return None
        
        # Encontra o início do array [
        bracket_start = response_text.find('[', args_start)
        if bracket_start == -1:
            return None
        
        # Agora vamos extrair os argumentos usando contagem de aspas
        args = self._extract_args_with_quote_counting(response_text, bracket_start)
        if args and len(args) >= 3:
            print(f"🔍 edit_code extraído via contagem de aspas: {len(args)} args")
            return {"command": "edit_code", "args": args}
        
        return None
    
    def _extract_args_with_quote_counting(self, text: str, start_pos: int) -> Optional[list]:
        """
        Extrai argumentos de um array JSON usando heurísticas robustas.
        Especialmente projetado para lidar com aspas malformadas.
        """
        try:
            # Extrai o conteúdo entre colchetes
            end_bracket = text.find(']', start_pos)
            if end_bracket == -1:
                return None
            
            array_content = text[start_pos + 1:end_bracket]
            print(f"🔍 Conteúdo do array: {array_content}")
            
            # Estratégia: dividir por vírgulas e depois tentar "reparar" cada parte
            parts = []
            current_part = ""
            paren_depth = 0
            
            i = 0
            while i < len(array_content):
                char = array_content[i]
                
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ',' and paren_depth == 0:
                    # Vírgula no nível superior - fim de um argumento
                    parts.append(current_part.strip())
                    current_part = ""
                    i += 1
                    continue
                
                current_part += char
                i += 1
            
            # Adiciona a última parte
            if current_part.strip():
                parts.append(current_part.strip())
            
            print(f"🔍 Partes identificadas: {len(parts)}")
            for i, part in enumerate(parts):
                print(f"  Parte {i}: {part}")
            
            # Agora limpa cada parte (remove aspas externas)
            args = []
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith('"') and cleaned.endswith('"'):
                    # Remove aspas externas
                    arg_value = cleaned[1:-1]
                    args.append(arg_value)
                elif cleaned.startswith('"'):
                    # Aspa de abertura mas não de fechamento - pode ser malformado
                    # Vamos tentar encontrar onde deveria terminar
                    arg_value = cleaned[1:]  # Remove primeira aspa
                    args.append(arg_value)
                else:
                    # Sem aspas - adiciona como está
                    args.append(cleaned)
            
            print(f"🔍 Argumentos finais: {len(args)} items")
            for i, arg in enumerate(args):
                print(f"  Arg {i}: {arg[:50]}...")
            
            return args if args else None
            
        except Exception as e:
            print(f"❌ Erro na extração com heurísticas: {e}")
            return None
    
    def _extract_command_with_escaped_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai comandos que contêm JSON escapado como argumentos.
        Especialmente útil para create_file com conteúdo JSON.
        """
        # Procura por padrões de comando com JSON escapado
        pattern = r'\{\s*"command"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*\[(.*?)\]\s*\}'
        
        match = re.search(pattern, response_text, re.DOTALL)
        if not match:
            return None
        
        command = match.group(1)
        args_content = match.group(2)
        
        print(f"🔍 Comando com possível JSON escapado: {command}")
        print(f"🔍 Args brutos: {args_content[:100]}...")
        
        # Tenta extrair argumentos considerando aspas escapadas
        args = self._parse_escaped_args(args_content)
        if args:
            print(f"🔍 Argumentos extraídos com JSON escapado: {len(args)} items")
            return {"command": command, "args": args}
        
        return None
    
    def _parse_escaped_args(self, args_content: str) -> Optional[list]:
        """
        Analisa argumentos que podem conter JSON escapado.
        """
        args = []
        current_arg = ""
        in_string = False
        escaped = False
        i = 0
        
        while i < len(args_content):
            char = args_content[i]
            
            if escaped:
                current_arg += char
                escaped = False
                i += 1
                continue
            
            if char == '\\':
                current_arg += char
                escaped = True
                i += 1
                continue
            
            if char == '"':
                current_arg += char
                in_string = not in_string
                i += 1
                continue
            
            if not in_string:
                if char == ',':
                    # Fim de um argumento
                    arg_value = self._clean_escaped_arg(current_arg.strip())
                    if arg_value is not None:
                        args.append(arg_value)
                    current_arg = ""
                    i += 1
                    continue
                elif char.isspace():
                    if current_arg.strip():
                        current_arg += char
                    i += 1
                    continue
            
            current_arg += char
            i += 1
        
        # Adiciona o último argumento
        if current_arg.strip():
            arg_value = self._clean_escaped_arg(current_arg.strip())
            if arg_value is not None:
                args.append(arg_value)
        
        return args if args else None
    
    def _clean_escaped_arg(self, arg: str) -> Optional[str]:
        """
        Limpa um argumento que pode conter JSON escapado.
        """
        if not arg:
            return None
        
        # Remove aspas externas se presente
        if arg.startswith('"') and arg.endswith('"'):
            arg = arg[1:-1]
        
        # Decodifica escapes comuns
        arg = arg.replace('\\n', '\n')
        arg = arg.replace('\\"', '"')
        arg = arg.replace('\\\\', '\\')
        arg = arg.replace('\\t', '\t')
        arg = arg.replace('\\r', '\r')
        
        return arg
    
    def _extract_escaped_json_string(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair um comando cujo segundo argumento é uma string JSON escapada.
        Usa json.loads duas vezes para decodificar de forma robusta.
        """
        # Padrão para encontrar o comando e seus argumentos brutos
        match = re.search(r'"command"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*\[\s*"([^"]+)"\s*,\s*"(.+)"\s*\]', response_text, re.DOTALL)
        if not match:
            return None

        command, arg1, raw_arg2 = match.groups()
        
        # O segundo argumento é uma string que contém JSON.
        # O parser de JSON padrão do Python pode lidar com isso diretamente.
        try:
            # Primeiro, construímos um JSON válido para o parser principal
            # Isso garante que o json.loads principal funcione
            full_json_str = f'{{"command": "{command}", "args": ["{arg1}", "{raw_arg2}"]}}'
            
            # O parser do Python já decodifica a primeira camada de escape (ex: \\n -> \n)
            data = json.loads(full_json_str)
            
            # O segundo argumento ainda é uma string que precisa ser decodificada
            if len(data['args']) > 1 and isinstance(data['args'][1], str):
                # Não precisamos decodificar aqui, o executor fará isso.
                # Apenas garantimos que a extração foi bem-sucedida.
                print(f"✅ JSON com string aninhada extraído com sucesso para o comando '{command}'")
                return data

        except json.JSONDecodeError as e:
            print(f"❌ Erro ao tentar o parse duplo de JSON: {e}")
            return None
            
        return None

    def _find_next_non_space(self, text: str, start_pos: int) -> str:
        """Encontra o próximo caractere que não é espaço."""
        for i in range(start_pos, len(text)):
            if not text[i].isspace():
                return text[i]
        return ""
    
    def _clean_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove parênteses do comando se presente."""
        cmd = data.get('command', '')
        if isinstance(cmd, str) and cmd.endswith('()'):
            data['command'] = cmd[:-2]
        return data
