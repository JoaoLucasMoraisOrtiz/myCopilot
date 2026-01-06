import logging
import os
import sys

# Garante que o src está no path se rodando localmente
repo_root = os.getcwd()
src_path = os.path.join(repo_root, "src")
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from codingos.mcp.supervisor import create_mcp_server

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupervisorServer")

def main():
    if any(arg in ("--help", "-h", "/?", "help") for arg in sys.argv[1:]):
        print("codingOS Supervisor (Analyst/Builder Mode)\nRun this via 'project_launcher.exe' or direct 'gemini mcp'.")
        sys.exit(0)

    try:
        # Cria o server usando o novo factory
        mcp = create_mcp_server(repo_root=repo_root)
        mcp.run(transport="stdio")
    except Exception as e:
        logger.exception("Supervisor crashed")
        sys.exit(1)

if __name__ == "__main__":
    main()