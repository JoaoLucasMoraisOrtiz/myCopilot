from typing import Dict, Any, List

from code_agent.agents._base import BaseAgent


class HaloPlannerAgent(BaseAgent):
    """
    Agente que decompõe uma Task complexa em Subtasks atômicas quando a
    geração direta falha (caminho de fallback).
    """

    def run(self, task: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
        """
        Executa o agente de planejamento HALO.

        Args:
            task: A tarefa que falhou na geração direta.
            language: A linguagem do projeto.

        Returns:
            Uma lista de Subtasks atômicas.
        """
        print(f"Iniciando o planejamento de fallback para a Task {task['task_id']}...")
        # Em uma implementação real, um LLM seria usado para decompor a tarefa.
        return self._decompose_task_into_subtasks(task, language)

    def _decompose_task_into_subtasks(
        self, task: Dict[str, Any], language: str
    ) -> List[Dict[str, Any]]:
        """
        Decompõe a tarefa em subtasks.
        (Implementação de espaço reservado)
        """
        subtasks = []
        if language == "python":
            subtasks.append(
                {
                    "subtask_id": "1.1",
                    "description": "Definir a estrutura da classe principal.",
                    "file_path": "module.py",
                    "status": "PENDING",
                }
            )
            subtasks.append(
                {
                    "subtask_id": "1.2",
                    "description": "Implementar o método principal.",
                    "file_path": "module.py",
                    "status": "PENDING",
                }
            )
        elif language == "java":
            subtasks.append(
                {
                    "subtask_id": "1.1",
                    "description": "Definir a classe e seus atributos.",
                    "file_path": "Main.java",
                    "status": "PENDING",
                }
            )
            subtasks.append(
                {
                    "subtask_id": "1.2",
                    "description": "Implementar o método main.",
                    "file_path": "Main.java",
                    "status": "PENDING",
                }
            )
        print(f"Task decomposta em {len(subtasks)} subtasks.")
        return subtasks

    def run(self, *args, **kwargs):
        """
        O método principal que cada agente implementará para executar sua lógica.
        """
        pass
