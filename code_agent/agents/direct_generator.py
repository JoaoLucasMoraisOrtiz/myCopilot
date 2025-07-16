from typing import Dict, Any

from code_agent.agents._base import BaseAgent
from code_agent.core.sandbox import DockerSandbox
from code_agent.utils.llm_clients import LLMClient


class DirectGeneratorAgent(BaseAgent):
    """
    Agente que tenta implementar uma Task inteira de uma só vez (caminho rápido).
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.sandbox = DockerSandbox()

    def run(self, task: Dict[str, Any], mission_context: Dict[str, Any]) -> str:
        """
        Executa o agente de geração direta.

        Args:
            task: A tarefa a ser implementada.
            mission_context: O contexto da missão, incluindo a linguagem.

        Returns:
            O novo status da tarefa ('AWAITING_CRITIC' ou 'PLANNING_REQUIRED').
        """
        language = mission_context.get("language", "python")
        prompt = self._create_prompt(task, language)

        generated_code = self.llm_client.generate_code(prompt)

        # Aqui, você salvaria o código em um arquivo temporário
        # e depois executaria a validação no sandbox.
        # A lógica de validação é um espaço reservado.
        validation_result = self._validate_code(generated_code, language)

        if validation_result["success"]:
            # Em um cenário real, você confirmaria as alterações no sistema de arquivos
            print(f"Task {task['task_id']} gerada e validada com sucesso.")
            return "AWAITING_CRITIC"
        else:
            print(f"Falha na validação para a Task {task['task_id']}.")
            return "PLANNING_REQUIRED"

    def _create_prompt(self, task: Dict[str, Any], language: str) -> str:
        """Cria o prompt para o LLM de geração de código."""
        return (
            f"Linguagem: {language}\n"
            f"Tarefa: {task['description']}\n"
            "Por favor, gere o código completo para implementar esta tarefa."
        )

    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        Valida o código gerado usando o sandbox.
        """
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            if language == "python":
                file_path = os.path.join(tmpdir, "main.py")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                # Executa pytest, mypy e ruff
                results = []
                for cmd in (["pytest", file_path], ["mypy", file_path], ["ruff", "check", file_path]):
                    res = self.sandbox.execute(cmd, tmpdir, container_config="python-3.11-pytest")
                    results.append(res)
                success = all(r.get("success") for r in results)
                return {"success": success, "results": results}
            elif language == "java":
                file_path = os.path.join(tmpdir, "Main.java")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                # Executa mvn test e checkstyle
                results = []
                for cmd in (["mvn", "test"], ["mvn", "checkstyle:check"]):
                    res = self.sandbox.execute(cmd, tmpdir, container_config="java-17-maven")
                    results.append(res)
                success = all(r.get("success") for r in results)
                return {"success": success, "results": results}
        return {"success": False, "error": "Unsupported language or error during validation."}
