import os
import json
from mistralai import Mistral

class LLMClient:
    """
    Cliente real para interagir com o Codestral via SDK Mistral.
    """

    def __init__(self):
        self.api_key = os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            # Tenta carregar do secrets.json
            try:
                with open("secrets.json", "r") as f:
                    secrets = json.load(f)
                    self.api_key = secrets.get("codestralAPIKey")
                    print('Chave da API do Codestral/Mistral carregada do secrets.json: {}'.format(self.api_key))
            except Exception:
                pass
        if not self.api_key:
            raise RuntimeError("Chave da API do Codestral/Mistral não encontrada.")

        self.client = Mistral(api_key=self.api_key)
        self.model = "codestral-latest"

    def generate_code(self, prompt: str, chat: bool=False, message: list=None) -> str:
        """
        Chama o Codestral para gerar código com base em um prompt via API HTTP (curl-like).
        """
        import requests
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        if chat and message:
            # Permite passar mensagens adicionais para contexto de chat
            messages = message + [{"role": "user", "content": prompt}]
        else:
            messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.model,
            "messages": messages
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # A resposta segue o padrão OpenAI/Mistral
            return data["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"Erro na chamada ao Codestral/Mistral: {response.status_code} {response.text}")
    


if __name__ == "__main__":
    #Exemplo de uso
    client = LLMClient()
    prompt = "Escreva uma função Python que some dois números."
    generated_code = client.generate_code(prompt)
    print(generated_code)
