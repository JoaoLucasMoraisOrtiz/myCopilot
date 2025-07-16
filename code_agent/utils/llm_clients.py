import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from mistralai.client import MistralClient as Mistral
from mistralai.models.chat_completion import ChatMessage
from mistralai.exceptions import MistralAPIException, MistralConnectionException

class LLMClient:
    """
    Cliente para interagir com a API do Codestral usando a biblioteca oficial mistralai.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente.
        A chave da API é buscada na seguinte ordem:
        1. Argumento `api_key`
        2. Variável de ambiente `MISTRAL_API_KEY`
        3. Arquivo `config.json` na raiz do projeto
        """
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY") or self._load_api_key_from_config()
        if not self.api_key:
            raise ValueError("Nenhuma chave de API do Codestral/Mistral foi fornecida.")

        self.client = Mistral(api_key=self.api_key)
        self.model = "codestral-latest"

    def _load_api_key_from_config(self) -> Optional[str]:
        """Carrega a chave da API do arquivo config.json."""
        try:
            # Assume que o config.json está na raiz do projeto
            config_path = Path(__file__).parent.parent.parent / "config.json"
            if not config_path.exists():
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('codestral_api_key')
                if api_key and api_key != "SUA_CHAVE_API_AQUI":
                    print("INFO: Chave da API carregada do config.json")
                    return api_key
        except Exception as e:
            print(f"WARN: Erro ao carregar a chave da API do config.json: {e}")
        return None

    def generate_code(self, prompt: str, max_retries: int = 3) -> str:
        """
        Chama o endpoint de chat para gerar código.

        Args:
            prompt: O prompt detalhado para a geração de código.
            max_retries: Número máximo de tentativas.

        Returns:
            O código gerado pelo modelo.
        """
        messages = [ChatMessage(role="user", content=prompt)]

        for attempt in range(max_retries):
            try:
                print(f"INFO: Chamando a API Codestral (tentativa {attempt + 1}/{max_retries})")
                chat_response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    temperature=0.5,
                )
                return chat_response.choices[0].message.content

            except MistralAPIException as e:
                # Trata erros da API como rate limit, autenticação, etc.
                print(f"WARN: Erro da API Mistral na tentativa {attempt + 1}: {e}")
                error_message = str(e)
                if "Status: 429" in error_message: # Rate limit
                    wait_time = 2 ** attempt
                    print(f"Rate limit atingido. Aguardando {wait_time} segundos...")
                    time.sleep(wait_time)
                elif "Status: 401" in error_message: # Erro de autenticação
                     raise Exception("Erro de autenticação (401). Verifique sua chave de API.")
                else: # Outros erros de API
                    if attempt >= max_retries - 1:
                        raise e
                    time.sleep(2 ** attempt)

            except (MistralConnectionException, Exception) as e:
                # Trata erros de conexão ou outros erros inesperados
                print(f"WARN: Erro de conexão na tentativa {attempt + 1}: {e}")
                if attempt >= max_retries - 1:
                    raise Exception(f"Falha na conexão após {max_retries} tentativas.")
                time.sleep(2 ** attempt)

        raise Exception("Todas as tentativas de chamada à API falharam.")

    def fill_in_the_middle(self, prompt: str, suffix: str, max_retries: int = 3) -> str:
        """
        Chama o endpoint FIM (Fill-in-the-Middle) do Codestral.

        Args:
            prompt: Código antes do cursor.
            suffix: Código depois do cursor.
            max_retries: Número máximo de tentativas.

        Returns:
            Código completado pelo modelo.
        """
        for attempt in range(max_retries):
            try:
                print(f"INFO: Chamando a API FIM do Codestral (tentativa {attempt + 1}/{max_retries})")
                fim_response = self.client.fim(
                    model=self.model,
                    prompt=prompt,
                    suffix=suffix,
                )
                return fim_response.choices[0].message.content
            except (MistralAPIException, MistralConnectionException, Exception) as e:
                print(f"WARN: Erro na chamada FIM na tentativa {attempt + 1}: {e}")
                if attempt >= max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)

        raise Exception("Todas as tentativas de chamada à API FIM falharam.")
