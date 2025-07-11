"""
Interface para comunicação com o Gemini via API REST.
"""
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.llm.rag_context_manager import RAGContextManager

class GeminiAPIInterface:
    """Interface para comunicação com Gemini via API REST."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa a interface com a API key.
        
        Args:
            api_key: Chave da API do Google Gemini (opcional, carrega do config.json se não fornecida)
        """
        self.api_key = api_key or self._load_api_key_from_config()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-1.5-flash"
        self.session = requests.Session()
    
    def _load_api_key_from_config(self) -> str:
        """Carrega a API key do arquivo config.json"""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('gemini_api_key')
                if not api_key:
                    raise ValueError("gemini_api_key não encontrada no config.json")
                print("INFO: API key do Gemini carregada do config.json")
                return api_key
        except Exception as e:
            raise Exception(f"Erro ao carregar API key do Gemini: {e}")
        
    def _format_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Converte mensagens do formato OpenAI para o formato Gemini.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            
        Returns:
            Payload formatado para a API Gemini
        """
        # Combina system e user messages em um único prompt
        combined_content = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                combined_content += f"Sistema: {content}\n\n"
            elif role == "user":
                combined_content += f"Usuário: {content}\n\n"
            elif role == "assistant":
                combined_content += f"Assistente: {content}\n\n"
        
        return {
            "contents": [{
                "parts": [{
                    "text": combined_content.strip()
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
    
    def call_llm(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """
        Chama a API do Gemini com as mensagens fornecidas.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            max_retries: Número máximo de tentativas em caso de erro
            
        Returns:
            Resposta do modelo Gemini
            
        Raises:
            Exception: Se todas as tentativas falharem
        """
        url = f"{self.base_url}/{self.model}:generateContent"
        params = {"key": self.api_key}
        
        payload = self._format_messages(messages)
        
        for attempt in range(max_retries):
            try:
                print(f"INFO: Chamando Gemini API (tentativa {attempt + 1}/{max_retries})")
                
                response = self.session.post(
                    url,
                    params=params,
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            if len(candidate["content"]["parts"]) > 0:
                                return candidate["content"]["parts"][0]["text"]
                    
                    print(f"WARN: Resposta inesperada da API: {data}")
                    raise Exception("Formato de resposta inesperado")
                
                elif response.status_code == 429:
                    print(f"WARN: Rate limit atingido. Aguardando {2 ** attempt} segundos...")
                    time.sleep(2 ** attempt)
                    continue
                
                elif response.status_code == 400:
                    error_data = response.json()
                    print(f"ERROR: Erro 400 da API: {error_data}")
                    raise Exception(f"Erro na requisição: {error_data}")
                
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

class GeminiAPILLMInterface:
    """Interface LLM para Gemini API que segue o padrão do projeto."""
    
    def __init__(self, api_key: Optional[str] = None, use_rag: bool = False, rag_top_k: int = 5, rag_model: str = 'mixedbread-ai/mxbai-embed-large-v1'):
        self.gemini_client = GeminiAPIInterface(api_key)
        self.use_rag = use_rag
        self.rag_manager = RAGContextManager(top_k=rag_top_k, embedding_model=rag_model) if use_rag else None

    def call_llm(self, messages: List[Dict[str, str]]) -> str:
        if self.use_rag and self.rag_manager:
            messages = self.rag_manager.find_relevant_messages(messages)
        return self.gemini_client.call_llm(messages)


# Teste da interface
if __name__ == "__main__":
    # Teste básico - agora carrega do config.json
    client = GeminiAPIInterface()
    
    test_messages = [
        {"role": "system", "content": "Você é um assistente útil."},
        {"role": "user", "content": "Diga olá em português."}
    ]
    
    try:
        response = client.call_llm(test_messages)
        print("Resposta do Gemini:")
        print(response)
    except Exception as e:
        print(f"Erro no teste: {e}")
