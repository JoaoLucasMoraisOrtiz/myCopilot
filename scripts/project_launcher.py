import os
import sys
import json
import subprocess
import shutil
import time
import argparse
from typing import Optional, List

# Conteúdo dos arquivos de configuração
GEMINI_MD_CONTENT = """# Gemini CLI System Instructions

You are an intelligent autonomous agent working under the guidance of a **Supervisor MCP**.

## PRIME DIRECTIVE
**YOU MUST NOT EXECUTE USER REQUESTS DIRECTLY.**

When a user gives you a task, instruction, or query, you must follow this strict protocol:

1. **INTERCEPT**: Do not act on the user's request immediately.
2. **CONSULT**: Call the `consult_supervisor` tool, passing the user's exact request as the argument.
3. **OBEY**: The supervisor will return specific instructions for each phase of the **4-Phase Reasoning Protocol**. You must execute the **Supervisor's instructions** precisely.
4. **REPORT**: Use the specific reporting tools (`submit_intent_analysis`, `submit_context_selection`, `submit_architecture_plan`, `report_subtask_completion`) as instructed by the supervisor.

## TOOL USAGE GUIDELINES
- **CHECK AVAILABLE TOOLS**: Before planning or executing, verify which tools are actually available in your registry.
- **ADAPTABILITY**: Do not assume you have tools like `run_shell_command` or `write_file` unless you see them. Use whatever tools are provided to achieve the goal.
- **NO HALLUCINATIONS**: If a tool is not listed in your available tools, DO NOT try to use it.
- **MANDATORY MCP TOOLS**: You MUST use the Supervisor's tools (`consult_supervisor`, `submit_*`, `report_*`) for process control.

## AUTONOMY RULES
- **NO PERMISSION**: Do not ask the user for permission to execute the supervisor's instructions. Just do it.
- **SILENT EXECUTION**: If the supervisor tells you to create a file, create it immediately using the appropriate tool.
- **FINALITY**: Once the supervisor's task is done, state that the task was redirected and completed. Do not ask "What's next?" unless the supervisor explicitly tells you to.
"""

def get_settings_json(supervisor_exe_path):
    return {
        "general": {
            "vimMode": False,
            "disableUpdateNag": True
        },
        "model": {
            "name": "gemini-2.5-flash",
            "maxSessionTurns": -1
        },
        "output": {
            "format": "text"
        },
        "tools": {
            "autoAccept": True,
            "sandbox": False
        },
        "security": {
            "disableYoloMode": False
        },
        "mcpServers": {
            "supervisor": {
                "command": supervisor_exe_path,
                "args": [],
                "env": {
                    "PYTHONUNBUFFERED": "1"
                },
                "trust": True
            }
        },
        "context": {
            "fileName": "GEMINI.md"
        }
    }


def _run(cmd: List[str], *, check: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, shell=shell, text=True, capture_output=False)


def _which(exe_name: str) -> Optional[str]:
    return shutil.which(exe_name)


def ensure_gemini_cli() -> Optional[str]:
    """Ensure Gemini CLI is available.

    Returns a command path/name suitable for launching gemini.

    Strategy (best-effort, no prompts):
      1) Use existing `gemini` if on PATH
      2) If npm exists, install @google/gemini-cli locally under .gemini/runtime
      3) If npm missing but winget exists, install NodeJS LTS silently, then retry

    Notes:
      - This may require internet access.
      - winget may require admin rights depending on system policy.
    """

    gemini = _which("gemini")
    if gemini:
        return gemini

    npm = _which("npm")
    if not npm:
        winget = _which("winget")
        if winget:
            try:
                print("Node/npm não encontrado. Tentando instalar NodeJS LTS via winget...")
                _run(
                    [
                        winget,
                        "install",
                        "-e",
                        "--id",
                        "OpenJS.NodeJS.LTS",
                        "--silent",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                    check=True,
                    shell=False,
                )
            except Exception as e:
                print(f"Falha ao instalar NodeJS via winget: {e}")

        npm = _which("npm")

    if not npm:
        print(
            "Não foi possível encontrar/instalar Node+NPM automaticamente.\n"
            "Instale NodeJS (inclui npm) e tente novamente.\n"
            "Depois você também pode instalar o Gemini CLI com: npm install -g @google/gemini-cli"
        )
        return None

    runtime_dir = os.path.join(os.getcwd(), ".gemini", "runtime")
    gemini_install_dir = os.path.join(runtime_dir, "gemini-cli")
    os.makedirs(gemini_install_dir, exist_ok=True)

    print("Instalando Gemini CLI localmente (sem depender de instalação global)...")
    try:
        # Instala o pacote e cria binários em node_modules/.bin
        _run([npm, "install", "@google/gemini-cli", "--prefix", gemini_install_dir], check=True, shell=False)
    except subprocess.CalledProcessError as e:
        print(f"Falha ao instalar @google/gemini-cli: {e}")
        return None

    # Windows: gemini.cmd
    local_gemini_cmd = os.path.join(gemini_install_dir, "node_modules", ".bin", "gemini.cmd")
    local_gemini = os.path.join(gemini_install_dir, "node_modules", ".bin", "gemini")
    if os.path.exists(local_gemini_cmd):
        return local_gemini_cmd
    if os.path.exists(local_gemini):
        return local_gemini

    # Fallback: maybe npm put it on PATH
    gemini = _which("gemini")
    if gemini:
        return gemini

    print("Gemini CLI instalado, mas não foi possível localizar o binário gemini.")
    return None

def setup_project():
    print("--- Inicializando Ambiente de Agente Autônomo ---")
    
    cwd = os.getcwd()
    gemini_dir = os.path.join(cwd, ".gemini")
    
    if not os.path.exists(gemini_dir):
        os.makedirs(gemini_dir)
        print(f"Criada pasta {gemini_dir}")

    # 1. Criar GEMINI.md
    with open(os.path.join(cwd, "GEMINI.md"), "w", encoding="utf-8") as f:
        f.write(GEMINI_MD_CONTENT)
    print("Arquivo GEMINI.md criado.")

    docs_dir = os.path.join(cwd, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    # 2. Localizar o supervisor.exe (suporta execução via PyInstaller)
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como EXE (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Se estiver rodando como script
        base_path = os.path.dirname(__file__)

    source_supervisor = os.path.join(base_path, "supervisor.exe")
    dest_supervisor = os.path.join(gemini_dir, "supervisor.exe")
    
    if os.path.exists(source_supervisor):
        shutil.copy(source_supervisor, dest_supervisor)
        print(f"Supervisor copiado para {dest_supervisor}")
    else:
        print(f"Erro: supervisor.exe não encontrado em {source_supervisor}")
        return False

    # 3. Criar settings.json
    settings = get_settings_json(dest_supervisor)
    with open(os.path.join(gemini_dir, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    print("Arquivo .gemini/settings.json configurado.")
    return True

def _spawn_gemini_instance_with_args(
    gemini_cmd: str,
    prompt: str,
    *,
    model: Optional[str],
    keep_open: bool,
) -> subprocess.Popen:
    # Se for .cmd/.bat, precisa de cmd.exe /c
    extra: List[str] = []
    if model:
        extra += ["-m", model]

    # One-shot default uses positional prompt.
    # If keep_open=True, use -i/--prompt-interactive so the window stays open.
    if keep_open:
        gemini_args = ["-i", prompt, "-y", *extra]
    else:
        gemini_args = [prompt, "-y", *extra]

    if gemini_cmd.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd.exe", "/c", gemini_cmd, *gemini_args]
    else:
        cmd = [gemini_cmd, *gemini_args]

    print(f"DEBUG: Spawning Gemini: {' '.join(cmd)}")

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE

    return subprocess.Popen(cmd, cwd=os.getcwd(), creationflags=creationflags)


def run_codingos_single(
    task: str,
    *,
    model: Optional[str],
    keep_open: bool,
) -> None:
    """Launch ONLY the primary instance (Action Manager + Context Scout).
    
    The supervisor MCP will handle spawning additional instances via spawn_agent_pool.
    """
    print("\n--- Preparando dependências (Gemini CLI) ---\n")
    gemini_cmd = ensure_gemini_cli()
    if not gemini_cmd:
        return

    print("\n--- Iniciando instância principal (Action Manager + Context Scout) ---\n")
    
    # The primary instance gets the user task directly.
    # It will call consult_supervisor, which instructs it to bootstrap the pool.
    proc = _spawn_gemini_instance_with_args(gemini_cmd, task, model=model, keep_open=keep_open)
    
    print(f"Instância principal spawned (PID {proc.pid}).")
    print("A janela do Gemini deve ter aberto. Verifique a barra de tarefas se não estiver visível.")
    print("O launcher agora pode fechar (a janela do Gemini continua rodando em background).")

def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--model", type=str, default=None, help="Override do modelo (equivalente a gemini -m).")
    parser.add_argument(
        "--keep-open",
        action="store_true",
        default=True,
        help="Mantém a janela aberta após executar o prompt inicial (usa -i). Default: True.",
    )
    parser.add_argument("task", nargs=argparse.REMAINDER, help="A tarefa a ser executada (texto livre).")
    args = parser.parse_args()

    task = " ".join(args.task).strip()
    if not task:
        task = input("Qual tarefa você deseja que o agente execute? ").strip()

    if not task:
        print("Nenhuma tarefa fornecida.")
        return

    if not setup_project():
        return

    run_codingos_single(
        task,
        model=args.model,
        keep_open=args.keep_open,
    )

if __name__ == "__main__":
    main()
