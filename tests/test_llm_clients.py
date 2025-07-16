import unittest
from unittest.mock import patch, MagicMock

from code_agent.utils.llm_clients import LLMClient
from mistralai.exceptions import MistralAPIException

class TestLLMClient(unittest.TestCase):

    def test_generate_code_success(self):
        """Testa o caso de sucesso da geração de código."""
        with patch('mistralai.client.MistralClient') as mock_mistral_client:
            # Configura o mock para a resposta da API
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "def hello():\n    print('Hello, World!')"

            # Configura o mock do cliente para retornar a resposta
            mock_mistral_instance = mock_mistral_client.return_value
            mock_mistral_instance.chat.return_value = mock_response

            # Inicializa o cliente (a chave da API pode ser qualquer coisa, pois está mockada)
            client = LLMClient(api_key="test_key")

            # Chama o método e verifica o resultado
            result = client.generate_code("Crie uma função hello world")
            self.assertEqual(result, "def hello():\n    print('Hello, World!')")
            mock_mistral_instance.chat.assert_called_once()

    @patch('time.sleep', return_value=None)
    def test_generate_code_retry_on_rate_limit(self, mock_sleep):
        """Testa a lógica de nova tentativa em erros de rate limit (429)."""
        with patch('mistralai.client.MistralClient') as mock_mistral_client:
            # Configura o mock para levantar um erro de rate limit nas duas primeiras chamadas
            # e depois retornar uma resposta de sucesso.
            mock_mistral_instance = mock_mistral_client.return_value
            mock_mistral_instance.chat.side_effect = [
                MistralAPIException(message="Status: 429 Rate limit exceeded"),
                MistralAPIException(message="Status: 429 Rate limit exceeded"),
                MagicMock(choices=[MagicMock(message=MagicMock(content="sucesso"))])
            ]

            client = LLMClient(api_key="test_key")

            # Chama o método
            result = client.generate_code("prompt")

            # Verifica se o resultado está correto e se o método foi chamado 3 vezes
            self.assertEqual(result, "sucesso")
            self.assertEqual(mock_mistral_instance.chat.call_count, 3)

    def test_authentication_error(self):
        """Testa se uma exceção é levantada em caso de erro de autenticação (401)."""
        with patch('mistralai.client.MistralClient') as mock_mistral_client:
            # Configura o mock para levantar um erro de autenticação
            mock_mistral_instance = mock_mistral_client.return_value
            mock_mistral_instance.chat.side_effect = MistralAPIException(
                message="Status: 401 Invalid API key"
            )

            client = LLMClient(api_key="invalid_key")

            # Verifica se a exceção correta é levantada
            with self.assertRaisesRegex(Exception, "Erro de autenticação"):
                client.generate_code("prompt")

if __name__ == '__main__':
    unittest.main()
