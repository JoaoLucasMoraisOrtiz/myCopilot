"""
Agent Response Parser Module

Responsável por analisar e extrair ações e memória de trabalho das respostas do LLM.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple


class AgentResponseParser:
    """Classe responsável por parsear respostas do LLM e extrair comandos e world_state."""
    
    def __init__(self):
        self.valid_commands = {
            "list_files", "open_file", "search_dir", "create_file", "edit_code", 
            "run_test", "submit", "multi_create_file"
        }
    
    def parse(self, response_text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Analisa a resposta do LLM.

        Returns:
            Uma tupla contendo (world_state, action_json).
            Retorna (None, None) se não conseguir analisar.
        """
        try:
            print(f"🔍 Analisando resposta do LLM ({len(response_text)} chars)")
            
            # Extrai a seção de atualização do estado
            world_state = self._extract_section(response_text, "Atualização do Estado")
            if world_state:
                print(f"🧠 World State extraído: {world_state[:100]}...")
            
            # Extrai a seção de ação
            action_str = self._extract_section(response_text, "Ação")
            if not action_str:
                print("⚠️ Seção 'Ação' não encontrada, tentando fallback")
                # Fallback para método antigo se não encontrar seção Ação
                action_json = self._extract_json_from_response(response_text)
                return world_state, action_json

            print(f"📝 Seção Ação extraída: {action_str}")
            
            # Limpa e extrai o JSON do bloco de ação
            try:
                # Remove chaves triplas se presentes
                if action_str.startswith('{{{') and action_str.endswith('}}}'):
                    action_str = action_str[3:-3]
                    action_str = '{' + action_str + '}'
                
                # Tenta parsing direto
                action_json = json.loads(action_str)
                print(f"✅ JSON da ação parseado com sucesso: {action_json}")
                return world_state, action_json
                
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao parsear JSON da ação: {e}")
                print(f"JSON problemático: {action_str}")
                
                # Fallback: tenta extrair JSON com regex
                json_match = re.search(r'\{.*\}', action_str, re.DOTALL)
                if json_match:
                    try:
                        action_json = json.loads(json_match.group(0))
                        return world_state, action_json
                    except json.JSONDecodeError:
                        pass
                
                return world_state, None

        except Exception as e:
            print(f"🚨 Erro geral ao analisar resposta do LLM: {e}")
            print(f"Resposta recebida:\n{response_text}")
            return None, None

    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extrai o conteúdo de uma seção específica (ex: **Ação:**)."""
        # Padrão mais flexível que lida com diferentes formatações
        patterns = [
            rf'\*\*{section_name}:\*\*\s*(.*?)(?=\s*\*\*|$)',  # **Seção:**
            rf'\*\*{section_name}\*\*\s*(.*?)(?=\s*\*\*|$)',   # **Seção**
            rf'{section_name}:\s*(.*?)(?=\s*\*\*|$)',          # Seção:
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Se a seção é "Ação", tenta extrair apenas o JSON
                if section_name.lower() == "ação" or section_name.lower() == "action":
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        return json_match.group(0)
                return content
        return None
    
    # Mantenha seu método antigo para compatibilidade se necessário
    def parse_action_from_response(self, response_text: str) -> Optional[Dict]:
        """Mantém compatibilidade com código existente."""
        _, action_json = self.parse(response_text)
        return action_json

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON da resposta do LLM com parsing robusto."""
        
        # Estratégia 1: JSON em bloco markdown
        json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_block_match:
            json_str = json_block_match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Estratégia 2: JSON com chaves triplas {{{ }}} - comum em templates
        triple_brace_match = re.search(r'\{\{\{(.*?)\}\}\}', response_text, re.DOTALL)
        if triple_brace_match:
            json_str = '{' + triple_brace_match.group(1) + '}'
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Estratégia 3: JSON balanceado iniciando com {"command"
        json_match = re.search(r'\{[^}]*"command"[^}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Estratégia 4: Busca por qualquer estrutura JSON válida
        json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
        json_matches = re.findall(json_pattern, response_text)
        for json_candidate in json_matches:
            try:
                parsed = json.loads(json_candidate)
                if isinstance(parsed, dict) and 'command' in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        
        return None
