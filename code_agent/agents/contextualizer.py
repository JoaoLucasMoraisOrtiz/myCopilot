import os
from typing import Dict, Any, Optional, List

from code_agent.agents._base import BaseAgent
from code_agent.utils.ast_parser import ASTParser

class ContextualizerAgent(BaseAgent):
    """
    Agente responsável por entender a intenção do usuário, analisar a base de
    código, detectar a linguagem e decompor o objetivo em tarefas.
    """

    def __init__(self):
        self.ast_parser = ASTParser()

    def run(self, user_prompt: str, project_path: Optional[str]) -> Dict[str, Any]:
        """
        Executa o agente de contextualização.

        Args:
            user_prompt: O prompt bruto do usuário.
            project_path: O caminho para o diretório do projeto.

        Returns:
            Um Objeto de Contexto de Missão estruturado.
        """
        if not project_path or not os.path.isdir(project_path):
            # Lida com o caso de não haver projeto (greenfield)
            # A detecção de linguagem pode ser baseada no prompt ou assumida
            language = "python"  # Ou uma lógica mais sofisticada
            tasks = self._generate_tasks(user_prompt, language)
            return {
                "language": language,
                "objetivo_principal": user_prompt,
                "tasks": tasks,
            }

        language = self._detect_language(project_path)
        # Em uma implementação real, você faria a análise com tree-sitter aqui
        # e a busca por palavras-chave para refinar as tarefas.
        tasks = self._generate_tasks(user_prompt, language)

        mission_context = {
            "language": language,
            "objetivo_principal": user_prompt,
            "tasks": tasks,
        }
        return mission_context

    def _detect_language(self, project_path: str) -> str:
        """
        Detecta a linguagem principal do projeto (Python ou Java).
        """
        if any(fname.endswith('.py') for fname in os.listdir(project_path)):
             return "python"
        if os.path.exists(os.path.join(project_path, "pom.xml")):
            return "java"
        if any(fname.endswith('.java') for fname in os.listdir(project_path)):
            return "java"
        # Fallback ou lógica mais complexa
        return "python"

    def _analyze_with_treesitter(self, file_path: str, language: str):
        """
        Analisa um único arquivo usando o tree-sitter.
        (Implementação de espaço reservado)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return self.ast_parser.parse(code, language)

    def _generate_tasks(self, user_prompt: str, language: str) -> List[Dict[str, Any]]:
        """
        Gera uma lista de tarefas de alto nível a partir do prompt do usuário.
        (Implementação de espaço reservado)
        """
        # Esta é uma implementação muito simplista. Uma versão real usaria um LLM.
        if language == "python":
            return [
                {
                    "task_id": "1",
                    "description": f"Implementar: {user_prompt} em um arquivo python.",
                    "status": "PENDING",
                }
            ]
        elif language == "java":
            return [
                {
                    "task_id": "1",
                    "description": f"Implementar: {user_prompt} em uma classe Java.",
                    "status": "PENDING",
                }
            ]
        return []

    def run(self, *args, **kwargs):
        """
        O método principal que cada agente implementará para executar sua lógica.
        """
        pass
