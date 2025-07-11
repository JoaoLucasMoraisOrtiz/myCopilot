"""
Interface para comunicação com o Codestral (Mistral AI) via API REST.
"""
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.llm.rag_context_manager import RAGContextManager


class CodestralAPIInterface:
    """Interface para comunicação com Codestral via API REST."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa a interface com a API key.
        
        Args:
            api_key: Chave da API do Codestral (opcional, carrega do config.json se não fornecida)
        """
        self.api_key = api_key or self._load_api_key_from_config()
        self.chat_url = "https://codestral.mistral.ai/v1/chat/completions"
        self.fim_url = "https://codestral.mistral.ai/v1/fim/completions"
        self.model = "codestral-latest"
        self.session = requests.Session()
    
    def _load_api_key_from_config(self) -> str:
        """Carrega a API key do arquivo config.json"""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('codestral_api_key')
                if not api_key:
                    raise ValueError("codestral_api_key não encontrada no config.json")
                print("INFO: API key do Codestral carregada do config.json")
                return api_key
        except Exception as e:
            raise Exception(f"Erro ao carregar API key do Codestral: {e}")
    
    def _format_messages_for_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Converte mensagens do formato OpenAI para o formato Codestral chat.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            
        Returns:
            Payload formatado para a API Codestral
        """
        formatted_messages = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Codestral usa "user", "assistant" e "system"
            if role in ["user", "assistant", "system"]:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        return {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.95,
            "stream": False
        }
    
    def call_chat_endpoint(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """
        Chama o endpoint de chat do Codestral.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            max_retries: Número máximo de tentativas em caso de erro
            
        Returns:
            Resposta do modelo Codestral
            
        Raises:
            Exception: Se todas as tentativas falharem
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = self._format_messages_for_chat(messages)
        
        for attempt in range(max_retries):
            try:
                print(f"INFO: Chamando Codestral Chat API (tentativa {attempt + 1}/{max_retries})")
                
                response = self.session.post(
                    self.chat_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        if "message" in data["choices"][0] and "content" in data["choices"][0]["message"]:
                            return data["choices"][0]["message"]["content"]
                    
                    print(f"WARN: Resposta inesperada da API: {data}")
                    raise Exception("Formato de resposta inesperado")
                
                elif response.status_code == 429:
                    print(f"WARN: Rate limit atingido. Aguardando {2 ** attempt} segundos...")
                    time.sleep(2 ** attempt)
                    continue
                
                elif response.status_code == 401:
                    print(f"ERROR: Erro de autenticação (401). Verifique a API key.")
                    raise Exception("Erro de autenticação: API key inválida ou expirada")
                
                else:
                    print(f"ERROR: Erro HTTP {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"Erro HTTP {response.status_code}: {response.text}")
                        
            except requests.exceptions.Timeout:
                print(f"WARN: Timeout na tentativa {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Timeout após todas as tentativas")
                    
            except requests.exceptions.RequestException as e:
                print(f"WARN: Erro de rede na tentativa {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(f"Erro de rede: {e}")
        
        raise Exception("Todas as tentativas falharam")
    
    def call_fim_endpoint(self, prompt: str, suffix: str = "", max_retries: int = 3) -> str:
        """
        Chama o endpoint FIM (Fill-in-the-Middle) do Codestral.
        
        Args:
            prompt: Código antes do cursor
            suffix: Código depois do cursor (opcional)
            max_retries: Número máximo de tentativas em caso de erro
            
        Returns:
            Código completado pelo modelo
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "suffix": suffix,
            "temperature": 0.3,
            "max_tokens": 2048,
            "top_p": 0.95,
            "stream": False
        }
        
        for attempt in range(max_retries):
            try:
                print(f"INFO: Chamando Codestral FIM API (tentativa {attempt + 1}/{max_retries})")
                
                response = self.session.post(
                    self.fim_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        if "text" in data["choices"][0]:
                            return data["choices"][0]["text"]
                    
                    print(f"WARN: Resposta inesperada da API FIM: {data}")
                    raise Exception("Formato de resposta inesperado")
                
                else:
                    print(f"ERROR: Erro HTTP FIM {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"Erro HTTP FIM {response.status_code}: {response.text}")
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise e
        
        raise Exception("Todas as tentativas FIM falharam")

class CodestralLLMInterface:
    """Interface LLM para Codestral que segue o padrão do projeto."""
    
    def __init__(self, api_key: Optional[str] = None, use_rag: bool = True, rag_top_k: int = 5, rag_model: str = 'mixedbread-ai/mxbai-embed-large-v1'):
        """
        Inicializa a interface LLM.
        
        Args:
            api_key: Chave da API do Codestral (opcional, carrega do config.json se não fornecida)
        """
        self.codestral_client = CodestralAPIInterface(api_key)
        self.use_rag = use_rag
        self.rag_manager = RAGContextManager(top_k=rag_top_k, embedding_model=rag_model) if use_rag else None
    
    def call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Chama o LLM Codestral via API.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            
        Returns:
            Resposta do modelo
        """
        try:
            if self.use_rag and self.rag_manager:
                messages = self.rag_manager.find_relevant_messages(messages)
            return self.codestral_client.call_chat_endpoint(messages)
        except Exception as e:
            print(f"ERROR: Falha na chamada para Codestral API: {e}")
            raise


# Teste da interface
if __name__ == "__main__":
    # Teste básico - agora carrega do config.json
    client = CodestralAPIInterface()
    
    test_messages = [
        {"role": "system", "content": "Você é um assistente de programação especializado."},
        {"role": "user", "content": "Escreva uma função Python que calcula fibonacci."}
    ]
    
    try:
        response = client.call_chat_endpoint(test_messages)
        print("Resposta do Codestral:")
        print(response)
    except Exception as e:
        print(f"Erro no teste: {e}")
        
    # Teste FIM
    try:
        print("\n--- Teste FIM ---")
        fim_response = client.call_fim_endpoint(
            prompt="def fibonacci(n):\n    if n <= 1:\n        return n\n    # ",
            suffix="\n    return fibonacci(n-1) + fibonacci(n-2)"
        )
        print("Resposta FIM do Codestral:")
        print(fim_response)
    except Exception as e:
        print(f"Erro no teste FIM: {e}")
