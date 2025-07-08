from core.agent.agent_core import Agent

# Teste com um objetivo mais simples para ver pressão temporal rapidamente
agent = Agent(
    user_goal="Liste as 3 principais classes do sistema LDAP.", 
    project_path="/home/joao/Documentos/myCopilot/legacy/ldapws",
    max_turns=8  # Reduzido para testar pressão mais rápido
)

print("🧪 TESTE: Verificando se o mecanismo de pressão temporal está funcionando...")
print("Objetivo simples para ver turnos 4-8 com pressão")
print("="*60)

result = agent.run()

if result:
    print("\n" + "="*60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("🎯 Mecanismo de pressão temporal funcionou!")
else:
    print("\n" + "="*60)
    print("❌ Agente não conseguiu concluir")
