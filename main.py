import sys
import argparse
from pathlib import Path
from core.agent.agent_core import Agent

""" 
Start chrome with:
google-chrome --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --remote-allow-origins=* --user-data-dir=/tmp/chrome_debug_profile --no-first-run --no-default-browser-check --disable-web-security --disable-features=VizDisplayCompositor --disable-dev-shm-usage --no-sandbox https://vscode.dev

"""


def main():
    # Configuração do parser de argumentos
    parser = argparse.ArgumentParser(description='MyCopilot Agent - Análise e criação de código')
    parser.add_argument('mode', choices=['edit', 'new'], 
                       help='Modo de operação: edit (analisar projeto existente) ou new (criar projeto do zero)')
    parser.add_argument('--continue', '-c', action='store_true', dest='continue_mode',
                       help='Continua conversa anterior')
    parser.add_argument('--clean', action='store_true',
                       help='Limpa estado salvo')
    parser.add_argument('--project-path', '-p', type=str,
                       help='Caminho do projeto (para edit) ou diretório de output (para new)')
    parser.add_argument('--goal', '-g', type=str,
                       help='Objetivo específico para o agente')
    parser.add_argument('--max-turns', '-t', type=int, default=10,
                       help='Número máximo de turnos (padrão: 10)')
    parser.add_argument('--llm-type', choices=['vscode', 'gemini', 'gemini_api', 'codestral'], default='vscode',
                       help='Tipo de LLM a usar: vscode (padrão), gemini (Chrome), gemini_api (Gemini API) ou codestral (Codestral API)')
    
    # Verifica comandos especiais antes do parsing
    if '--clean' in sys.argv:
        state_file = Path("agent_state.pkl")
        if state_file.exists():
            state_file.unlink()
            print("🧹 Estado anterior limpo!")
        else:
            print("📂 Nenhum estado anterior para limpar.")
        return
    
    if '--help' in sys.argv or '-h' in sys.argv:
        parser.print_help()
        return
    
    # Parse dos argumentos
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    # Configuração baseada no modo
    if args.mode == 'edit':
        # Modo edit: analisa projeto existente
        if args.project_path:
            project_path = args.project_path
        else:
            project_path = str(Path(__file__).parent)
        
        if args.goal:
            user_goal = args.goal
        else:
            user_goal = "Quero entender o que exatamente esse sistema faz."
        
        print(f"📂 MODO EDIT: Analisando projeto em '{project_path}'")
        
    elif args.mode == 'new':
        # Modo new: cria projeto do zero
        if args.project_path:
            project_path = args.project_path
        else:
            project_path = str(Path(__file__).parent / "output_project")
        
        if args.goal:
            user_goal = args.goal
        else:
            user_goal = "Quero criar um novo projeto do zero."
        
        print(f"🆕 MODO NEW: Criando projeto em '{project_path}'")
    
    # Verifica se deve usar modo continue
    continue_mode = args.continue_mode
    
    if continue_mode:
        print("🔄 MODO CONTINUE: Retomando conversa anterior...")
        agent = Agent(
            user_goal=user_goal, 
            project_path=project_path,
            max_turns=args.max_turns,
            continue_mode=True,
            llm_type=args.llm_type,
            api_key=None  # API key carregada automaticamente do config.json
        )
    else:
        print("🆕 MODO NOVO: Iniciando nova conversa...")
        agent = Agent(
            user_goal=user_goal, 
            project_path=project_path,
            max_turns=args.max_turns,
            continue_mode=False,
            llm_type=args.llm_type,
            api_key=None  # API key carregada automaticamente do config.json
        )
    
    # Executa o agente no modo especificado
    result = agent.run(mode=args.mode)
    
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