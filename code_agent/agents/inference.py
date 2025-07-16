from typing import Dict, Any

from code_agent.agents._base import BaseAgent
from code_agent.utils.llm_clients import LLMClient


class InferenceAgent(BaseAgent):
    """
    Agente que gera o código para uma única Subtask atômica.
    """

    def __init__(self):
        self.llm_client = LLMClient()

    def run(self, subtask: Dict[str, Any], mission_context: Dict[str, Any]):
        """
        Executa o agente de inferência.

        Args:
            subtask: A subtask para a qual o código será gerado.
            mission_context: O contexto da missão, incluindo a linguagem e o
                             código fonte relevante.
        """
        language = mission_context.get("language", "python")
        prompt = self._create_prompt(subtask, language, mission_context)

        generated_code = self.llm_client.generate_code(prompt)

        # Salva o código gerado no caminho de arquivo especificado
        self._save_code(subtask["file_path"], generated_code)

        print(f"Código para a Subtask {subtask['subtask_id']} gerado e salvo.")
        # O orquestrador atualizará o status no manifest.json

    def _create_prompt(
        self, subtask: Dict[str, Any], language: str, context: Dict[str, Any]
    ) -> str:
        """Cria o prompt para a geração de código da subtask."""
        # Em uma implementação real, você pode querer incluir mais contexto,
        # como o código dos arquivos relevantes.
        return (
            f"Linguagem: {language}\n"
            f"Arquivo: {subtask['file_path']}\n"
            f"Subtask: {subtask['description']}\n"
            "Gere o trecho de código para esta subtask."
        )

    def _save_code(self, file_path: str, code: str):
        """Salva o código gerado em um arquivo."""
        # Este método pode precisar ser mais inteligente, por exemplo, para
        # inserir ou substituir código em vez de sobrescrever o arquivo.
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

    def run(self, *args, **kwargs):
        """
        O método principal que cada agente implementará para executar sua lógica.
        """
        pass
