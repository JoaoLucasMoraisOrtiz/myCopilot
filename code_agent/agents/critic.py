from typing import Dict, Any

from code_agent.agents._base import BaseAgent
from code_agent.core.sandbox import DockerSandbox
from code_agent.utils.llm_clients import LLMClient
import os


class CriticPolishAgent(BaseAgent):
    """
    Agente que revisa o código, executa análise de estilo e refatora para
    melhorar a qualidade e a conformidade com as convenções.
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.sandbox = DockerSandbox()

    def run(self, item: Dict[str, Any], mission_context: Dict[str, Any]):
        """
        Executa o agente crítico e de polimento.

        Args:
            item: A subtask ou task a ser polida.
            mission_context: O contexto da missão.
        """
        language = mission_context.get("language", "python")
        file_path = item.get("file_path")  # Pode não existir para tasks

        print(f"Iniciando o polimento para o item {item.get('subtask_id') or item.get('task_id')}.")

        # 1. Avaliar a qualidade do código (linting)
        quality_issues = self._evaluate_code_quality(file_path, language)

        if quality_issues:
            # 2. Refatorar o código se houver problemas
            self._refactor_code(file_path, quality_issues, language)
        else:
            print("Nenhum problema de qualidade encontrado.")

        # O orquestrador atualizará o status para POLISHED
        print("Polimento concluído.")


    def _evaluate_code_quality(self, file_path: str, language: str) -> Any:
        """
        Executa ferramentas de análise estática (ruff, checkstyle) no sandbox.
        """
        if not file_path:
            return ""

        print(f"Avaliando a qualidade do código em {file_path}.")
        if language == "python":
            cmd = ["ruff", "check", file_path]
            res = self.sandbox.execute(cmd, os.path.dirname(file_path), container_config="python-3.11-pytest")
            return [{
                "tool": "ruff",
                "success": res.get("success"),
                "stdout": res.get("stdout"),
                "stderr": res.get("stderr"),
                "exit_code": res.get("exit_code")
            }]
        elif language == "java":
            command = ["mvn", "checkstyle:check"]
            result = self.sandbox.execute(command, os.path.dirname(file_path), container_config="java-17-maven")
            return result.get("stdout", "") + result.get("stderr", "")
        return ""

    def _refactor_code(self, file_path: str, issues: str, language: str):
        """Usa um LLM para refatorar o código e corrigir os problemas."""
        print(f"Refatorando o código em {file_path} para corrigir: {issues}")

        with open(file_path, "r", encoding="utf-8") as f:
            current_code = f.read()

        prompt = (
            f"Linguagem: {language}\n"
            f"Código atual:\n{current_code}\n\n"
            f"Problemas de qualidade detectados:\n{issues}\n\n"
            "Refatore o código para corrigir esses problemas e melhorar a legibilidade."
        )

        refactored_code = self.llm_client.generate_code(prompt)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(refactored_code)

        print("Refatoração aplicada.")
