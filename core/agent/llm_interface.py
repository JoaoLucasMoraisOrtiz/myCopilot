"""
Agent LLM Interface Module

Responsável pela comunicação com o LLM e gestão de contexto.
"""

from core.llm.llm_client import LLMClient


class AgentLLMInterface:
    """Classe responsável pela comunicação e gestão de contexto com o LLM."""
    
    def __init__(self):
        pass
    
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
        pressure_message = self._get_pressure_message(current_turn)
        if pressure_message:
            print(f"🎯 APLICANDO PRESSÃO TEMPORAL (Turno {current_turn}): {pressure_message[:80]}...")
            prompt += f"\n\nUSER: {pressure_message}"
        
        # Gestão inteligente de contexto
        original_length = len(prompt)
        
        # Log do tamanho final do prompt
        print(f"📊 Enviando prompt de {len(prompt)} chars para o LLM...")
        
        # Conecta e envia para o LLM
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
            return None  # Sem pressão nos primeiros turnos
