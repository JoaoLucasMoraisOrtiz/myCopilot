#!/usr/bin/env python3
"""
Teste específico do mecanismo de pressão temporal
"""

from core.agent.agent_core import Agent

def test_pressure_simulation():
    """Simula vários turnos para ver as mensagens de pressão"""
    
    print("=== TESTE: Simulação de Pressão Temporal ===\n")
    
    # Cria um agente
    agent = Agent(
        user_goal="Teste", 
        project_path="/home/joao/Documentos/myCopilot/legacy/ldapws",
        max_turns=10
    )
    
    # Simula chamadas para diferentes turnos
    print("Simulando diferentes turnos para ver quando a pressão é aplicada:\n")
    
    for turno in range(1, 11):
        print(f"--- SIMULAÇÃO TURNO {turno} ---")
        
        # Chama o método de pressão diretamente
        pressure_msg = agent._get_pressure_message(turno)
        
        if pressure_msg:
            print(f"🎯 PRESSÃO APLICADA: {pressure_msg}")
        else:
            print("🔹 Sem pressão - exploração livre")
        
        print()

if __name__ == "__main__":
    test_pressure_simulation()
