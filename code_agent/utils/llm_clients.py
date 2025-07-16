import os


class LLMClient:
    """
    Cliente para interagir com os LLMs (ex: Codestral).
    Esta é uma implementação de espaço reservado. Em um cenário real, você
    usaria a API do provedor do LLM.
    """

    def __init__(self):
        # A chave da API seria carregada de variáveis de ambiente ou de um
        # gerenciador de segredos.
        self.api_key = os.environ.get("CODESTRAL_API_KEY")
        if not self.api_key:
            print("Aviso: A variável de ambiente CODESTRAL_API_KEY não está definida.")

    def generate_code(self, prompt: str) -> str:
        """
        Chama o LLM para gerar código com base em um prompt.
        (Implementação de espaço reservado)

        Args:
            prompt: O prompt para enviar ao LLM.

        Returns:
            O código gerado pelo LLM.
        """
        print("--- Chamada (simulada) ao LLM ---")
        print(f"Prompt:\n{prompt}")

        # Simula uma resposta do LLM baseada no prompt
        if "Implementar: criar uma função que soma dois números" in prompt:
            if "java" in prompt.lower():
                return """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""
            else:
                return "def add(a, b):\n    return a + b\n"

        if "Refatore o código" in prompt:
             return "def some_function():\n    pass\n"

        print("--- Fim da chamada (simulada) ao LLM ---")
        return "# Código gerado (simulado)\n"
