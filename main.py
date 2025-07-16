import argparse
from typing import Optional

from code_agent.core.orchestrator import MainOrchestrator


def main(user_prompt: str, project_path: Optional[str]) -> None:
    """
    Ponto de entrada principal para o Code-Agent.

    Args:
        user_prompt: O prompt do usuário descrevendo a tarefa.
        project_path: O caminho para o diretório do projeto.
    """
    orchestrator = MainOrchestrator()
    orchestrator.run_pipeline(user_prompt, project_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Code-Agent Modular v2.1"
    )
    parser.add_argument(
        "user_prompt",
        type=str,
        help="O prompt do usuário descrevendo a tarefa de codificação.",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="O caminho opcional para o diretório do projeto.",
        default=None,
    )
    args = parser.parse_args()

    main(args.user_prompt, args.path)
