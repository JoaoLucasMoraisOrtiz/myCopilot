import json
from typing import Dict, Any, List


class ManifestManager:
    """
    Gerencia o estado da missão lendo e escrevendo em um arquivo manifest.json.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = {}

    def initialize(self, mission_context: Dict[str, Any]):
        """Cria e salva o manifest inicial."""
        self.data = mission_context
        self.data["status"] = "IN_PROGRESS"
        self._save()
        print(f"Manifest inicializado em {self.filepath}")

    def _load(self):
        """Carrega o manifest do arquivo."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            # Se o arquivo não existe, começa com um dicionário vazio
            self.data = {}

    def _save(self):
        """Salva o estado atual no arquivo manifest."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Retorna a lista de tasks."""
        self._load()
        return self.data.get("tasks", [])

    def add_subtasks(self, task_id: str, subtasks: List[Dict[str, Any]]):
        """Adiciona subtasks a uma task existente."""
        self._load()
        for task in self.data.get("tasks", []):
            if task["task_id"] == task_id:
                task["subtasks"] = subtasks
                break
        self._save()

    def get_subtasks(self, task_id: str) -> List[Dict[str, Any]]:
        """Retorna as subtasks de uma task específica."""
        self._load()
        for task in self.data.get("tasks", []):
            if task["task_id"] == task_id:
                return task.get("subtasks", [])
        return []

    def update_task_status(self, task_id: str, status: str):
        """Atualiza o status de uma task."""
        self._load()
        for task in self.data.get("tasks", []):
            if task["task_id"] == task_id:
                task["status"] = status
                break
        self._save()

    def update_subtask_status(self, subtask_id: str, status: str):
        """Atualiza o status de uma subtask."""
        self._load()
        for task in self.data.get("tasks", []):
            for subtask in task.get("subtasks", []):
                if subtask["subtask_id"] == subtask_id:
                    subtask["status"] = status
                    break
        self._save()

    def update_main_status(self, status: str):
        """Atualiza o status principal da missão."""
        self._load()
        self.data["status"] = status
        self._save()
