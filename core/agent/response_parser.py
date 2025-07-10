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
            "continue_reading", "save_code", "create_file", "final_answer"
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
            return self._semantic_analysis(response_content)
            
        except Exception as e:
            print(f"❌ Erro inesperado ao processar resposta: {e}")
            return {"command": "error", "args": [f"Erro inesperado ao processar resposta: {e}"]}
    
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
        
        # Estratégia 3: Padrões específicos para comandos conhecidos
        return self._extract_by_patterns(response_text)
    
    def _extract_balanced_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON balanceado da resposta."""
        start = response_text.find('{"command"')
        if start == -1:
            return None
            
        substr = response_text[start:]
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
                            return self._clean_command(data)
                        except json.JSONDecodeError as e:
                            print(f"❌ Erro ao decodificar JSON balanceado: {e}")
                            break
        return None
    
    def _extract_by_patterns(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai comandos usando padrões regex."""
        
        # Padrões para comandos específicos
        patterns = [
            (r'list_classes\(\)', "list_classes", []),
            (r'get_class_metadata\("([^"]+)"\)', "get_class_metadata", lambda m: [m.group(1)]),
            (r'get_code\("([^"]+)"\)', "get_code", lambda m: [m.group(1)]),
            (r'read_file\("([^"]+)"\)', "read_file", lambda m: [m.group(1)]),
            (r'continue_reading\("([^"]+)"\)', "continue_reading", lambda m: [m.group(1)]),
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
            r'([A-Za-z_][A-Za-z0-9_]*)\s*class',
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
    
    def _clean_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove parênteses do comando se presente."""
        cmd = data.get('command', '')
        if isinstance(cmd, str) and cmd.endswith('()'):
            data['command'] = cmd[:-2]
        return data
