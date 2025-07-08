import sys
import os
from pathlib import Path
from core.agent.agent_core import Agent

def main():
    # Verifica comandos especiais
    if '--clean' in sys.argv:
        state_file = Path("agent_state.pkl")
        if state_file.exists():
            state_file.unlink()
            print("🧹 Estado anterior limpo!")
        else:
            print("📂 Nenhum estado anterior para limpar.")
        return
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("🤖 MyCopilot Agent - Uso:")
        print("  python main.py              # Nova conversa")
        print("  python main.py --continue   # Continua conversa anterior")
        print("  python main.py -c           # Continua conversa anterior (atalho)")
        print("  python main.py --clean      # Limpa estado salvo")
        print("  python main.py --help       # Mostra esta ajuda")
        return
    
    # Verifica se deve usar modo continue
    continue_mode = '--continue' in sys.argv or '-c' in sys.argv
    
    # Configuração do agente
    user_goal = "Quero entender o que exatamente esse sistema faz."
    # Define o caminho do projeto como o diretório atual do script
    project_path = str(Path(__file__).parent)
    
    if continue_mode:
        print("🔄 MODO CONTINUE: Retomando conversa anterior...")
        agent = Agent(
            user_goal=user_goal, 
            project_path=project_path,
            continue_mode=True
        )
    else:
        print("🆕 MODO NOVO: Iniciando nova conversa...")
        agent = Agent(
            user_goal=user_goal, 
            project_path=project_path,
            continue_mode=False
        )
    
    # Executa o agente
    result = agent.run()
    
    if result:
        print("\n" + "="*50)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ ANÁLISE NÃO CONCLUÍDA (limite de turnos atingido)")
        print("="*50)

if __name__ == "__main__":
    main()