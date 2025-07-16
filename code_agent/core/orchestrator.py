from typing import Optional

from code_agent.agents.contextualizer import ContextualizerAgent
from code_agent.agents.direct_generator import DirectGeneratorAgent
from code_agent.agents.planner import HaloPlannerAgent
from code_agent.agents.inference import InferenceAgent
from code_agent.agents.composer_mcts import ComposerMCTSAgent
from code_agent.agents.critic import CriticPolishAgent
from code_agent.agents.final_composer import FinalComposerAgent
from code_agent.core.manifest import ManifestManager


class MainOrchestrator:
    """
    O maestro principal do pipeline, responsável por invocar os agentes
    corretos na sequência correta e gerenciar o estado da missão.
    """

    def __init__(self):
        self.contextualizer = ContextualizerAgent()
        self.direct_generator = DirectGeneratorAgent()
        self.planner = HaloPlannerAgent()
        self.inference = InferenceAgent()
        self.composer = ComposerMCTSAgent()
        self.critic = CriticPolishAgent()
        self.final_composer = FinalComposerAgent()
        self.manifest_manager = ManifestManager("manifest.json")

    def run_pipeline(self, user_prompt: str, project_path: Optional[str]):
        """
        Executa o pipeline completo de engenharia de software.
        """
        # 1. Contextualização
        mission_context = self.contextualizer.run(user_prompt, project_path)
        self.manifest_manager.initialize(mission_context)

        # Loop principal de tasks
        for task in self.manifest_manager.get_tasks():
            self._process_task(task, mission_context, project_path)

        # 7. Composição Final
        self.final_composer.run(mission_context, project_path)
        self.manifest_manager.update_main_status("COMPLETED")
        print("Pipeline concluído com sucesso!")

    def _process_task(self, task: dict, context: dict, path: str):
        # 2. Geração Direta
        task_status = self.direct_generator.run(task, context)
        self.manifest_manager.update_task_status(task["task_id"], task_status)

        # 3. Planejamento (se necessário)
        if task_status == "PLANNING_REQUIRED":
            language = context.get("language")
            subtasks = self.planner.run(task, language)
            self.manifest_manager.add_subtasks(task["task_id"], subtasks)

            # 4 & 5. Execução das Subtasks
            for subtask in self.manifest_manager.get_subtasks(task["task_id"]):
                self._process_subtask(subtask, context)

        # 6. Polimento da Task
        self.critic.run(task, context)
        self.manifest_manager.update_task_status(task["task_id"], "POLISHED")

    def _process_subtask(self, subtask: dict, context: dict):
        # 4. Inferência por subtask
        self.inference.run(subtask, context)
        self.manifest_manager.update_subtask_status(subtask["subtask_id"], "GENERATED")

        # 5. Composição e Correção
        subtask_status = self.composer.run(subtask, context)
        self.manifest_manager.update_subtask_status(subtask["subtask_id"], subtask_status)

        if subtask_status == "VERIFIED":
            # 6. Polimento da Subtask
            self.critic.run(subtask, context)
            self.manifest_manager.update_subtask_status(subtask["subtask_id"], "POLISHED")
        else:
            print(f"Não foi possível concluir a subtask {subtask['subtask_id']}.")
            # Lógica de tratamento de falhas aqui
            raise Exception(f"Falha ao processar a subtask {subtask['subtask_id']}")
