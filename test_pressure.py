#!/usr/bin/env python3
"""
Teste demonstrando o sistema de pressão temporal
"""

from core.agent.agent_core import Agent

def test_pressure_messages():
    """Testa as mensagens de pressão temporal"""
    
    print("=== TESTE: Sistema de Pressão Temporal ===\n")
    
    # Cria um agente para testar
    agent = Agent(
        user_goal="Teste de pressão temporal", 
        project_path="/caminho/ficticio"
    )
    
    # Testa as mensagens em diferentes turnos
    print("Testando mensagens de pressão por turno:\n")
    
    for turno in range(1, 11):
        message = agent._get_pressure_message(turno)
        status = "🔹 SEM PRESSÃO" if message is None else "⚠️ COM PRESSÃO"
        print(f"Turno {turno:2d}: {status}")
        if message:
            print(f"         Mensagem: {message}")
        print()
    
    print("="*60)
    print("\nCOMO FUNCIONA:")
    print("- Turnos 1-3: Exploração livre")
    print("- Turno 4: Lembrete de foco")
    print("- Turno 5: Reflexão sobre suficiência")
    print("- Turno 6: Atenção para convergência")
    print("- Turnos 8+: Urgência máxima")
    print("\nOBJETIVO: Incentiva convergência gradual sem prejudicar qualidade")

if __name__ == "__main__":
    test_pressure_messages()
