"""
Agent LLM Interface Module

Responsável pela comunicação com o LLM e gestão de contexto.
"""

import os
from core.llm.llm_client import LLMClient
from devtools.gemini_client import GeminiLLMInterface
from devtools.gemini_api_client import GeminiAPILLMInterface
from devtools.codestral_api_client import CodestralLLMInterface


class AgentLLMInterface:
    """Classe responsável pela comunicação e gestão de contexto com o LLM."""
    
    def __init__(self, llm_type="vscode", api_key=None):
        """
        Inicializa a interface do LLM.
        
        Args:
            llm_type: Tipo de LLM a usar ("vscode", "gemini", "gemini_api", ou "codestral")
            api_key: Chave da API (necessária para gemini_api e codestral)
        """
        self.llm_type = llm_type
        self.gemini_interface = None
        self.gemini_api_interface = None
        self.codestral_interface = None
        
        if llm_type == "gemini":
            # Inicializa interface Gemini via Chrome DevTools se especificado
            try:
                # URL padrão do Chrome DevTools (pode ser configurável)
                websocket_url = "ws://127.0.0.1:9222"
                self.gemini_interface = GeminiLLMInterface(websocket_url)
                print("🔗 Interface Gemini (Chrome) inicializada")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Gemini Chrome, fallback para VS Code: {e}")
                self.llm_type = "vscode"
        elif llm_type == "gemini_api":
            # Inicializa interface Gemini via API se especificado
            try:
                self.gemini_api_interface = GeminiAPILLMInterface(api_key)
                print("🔗 Interface Gemini (API) inicializada")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Gemini API, fallback para VS Code: {e}")
                self.llm_type = "vscode"
        elif llm_type == "codestral":
            # Inicializa interface Codestral via API se especificado
            try:
                self.codestral_interface = CodestralLLMInterface(api_key)
                print("🔗 Interface Codestral (API) inicializada")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Codestral API, fallback para VS Code: {e}")
                self.llm_type = "vscode"
    
    def call_llm(self, messages: list, current_turn: int = 0) -> str:
        """
        Chama o LLM com gestão inteligente de contexto.
        
        Args:
            messages: Lista de mensagens da conversa
            current_turn: Turno atual para aplicar pressão temporal
            
        Returns:
            Resposta do LLM
        """
        # Limita o tamanho total do contexto para evitar overflow
        # Apenas as últimas mensagens são enviadas para evitar duplicação de contexto
        last_messages = messages[-4:]
        prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in last_messages])
        
        # Adiciona pressão temporal baseada no número de turnos
        # pressure_message = self._get_pressure_message(current_turn)
        # if pressure_message:
        #     print(f"🎯 APLICANDO PRESSÃO TEMPORAL (Turno {current_turn}): {pressure_message[:80]}...")
        #     prompt += f"\n\nUSER: {pressure_message}"
        
        # Log do tamanho final do prompt
        print(f"📊 Enviando prompt de {len(prompt)} chars para o LLM...")
        
        # Escolhe a interface baseada no tipo
        if self.llm_type == "gemini" and self.gemini_interface:
            try:
                response = self.gemini_interface.send_message(prompt)
                print(f"💬 Resposta do Gemini (Chrome) recebida: {len(response)} chars")
                return response
            except Exception as e:
                print(f"⚠️ Erro no Gemini Chrome, fallback para VS Code: {e}")
                # Fallback para VS Code em caso de erro
        elif self.llm_type == "gemini_api" and self.gemini_api_interface:
            try:
                # Converte o prompt para formato de mensagens se necessário
                if isinstance(messages, list) and len(messages) > 0:
                    response = self.gemini_api_interface.call_llm(messages)
                else:
                    # Fallback: converte prompt para mensagens
                    messages_fallback = [{"role": "user", "content": prompt}]
                    response = self.gemini_api_interface.call_llm(messages_fallback)
                print(f"🤖 Resposta do Gemini (API) recebida: {len(response)} chars")
                return response
            except Exception as e:
                print(f"⚠️ Erro no Gemini API, fallback para VS Code: {e}")
                # Fallback para VS Code em caso de erro
        elif self.llm_type == "codestral" and self.codestral_interface:
            try:
                # Converte o prompt para formato de mensagens se necessário
                if isinstance(messages, list) and len(messages) > 0:
                    response = self.codestral_interface.call_llm(messages)
                else:
                    # Fallback: converte prompt para mensagens
                    messages_fallback = [{"role": "user", "content": prompt}]
                    response = self.codestral_interface.call_llm(messages_fallback)
                print(f"� Resposta do Codestral (API) recebida: {len(response)} chars")
                return response
            except Exception as e:
                print(f"⚠️ Erro no Codestral API, fallback para VS Code: {e}")
                # Fallback para VS Code em caso de erro
        
        # Interface padrão VS Code
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
    
    def _get_pressure_message(self, current_turn: int) -> str:
        """Gera mensagens de pressão temporal baseadas no número de turnos."""
        
        if current_turn >= 8:
            return ("URGENTE: Você está no turno 8/10. DEVE fornecer final_answer no PRÓXIMO turno "
                   "ou perderá a oportunidade de responder. Analise se já tem informação suficiente "
                   "para uma resposta útil.")
        elif current_turn >= 6:
            return ("ATENÇÃO: Você está no turno 6/10. Comece a considerar seriamente usar final_answer. "
                   "Você tem informação suficiente para uma resposta parcial útil?")
        elif current_turn >= 5:
            return ("REFLEXÃO: Já coletou bastante informação. Avalie se pode fornecer uma resposta útil "
                   "ou se precisa de apenas mais 1-2 observações específicas.")
        elif current_turn >= 4:
            return ("FOCO: Você está na metade do caminho. Mantenha o foco no objetivo principal "
                   "e evite explorações tangenciais.")
        else:
            return ""  # Sem pressão nos primeiros turnos
