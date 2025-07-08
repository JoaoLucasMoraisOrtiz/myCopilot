from core.agent.agent_core import Agent

# Cria agente com objetivo simples para teste rápido
agent = Agent(
    user_goal="Liste apenas 2 classes principais do sistema.", 
    project_path="/home/joao/Documentos/myCopilot/legacy/ldapws",
    max_turns=6  # Reduzido para ver pressão mais cedo
)

print("🧪 TESTE DE PRESSÃO TEMPORAL")
print("="*50)
agent.run()
