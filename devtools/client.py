import json
import time
import websocket
from typing import Optional, Dict, Any

class DevToolsClient:
    """
    Cliente robusto para interação com o Chrome DevTools Protocol via WebSocket.
    Inclui mecanismos de retry e gerenciamento de memória.
    """
    def __init__(self, debugger_url: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.debugger_url = debugger_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.ws = None
        self._next_id = 1
        self._pending_responses = {}  # Cache para respostas pendentes
        self._connect()

    def _connect(self):
        """Estabelece conexão WebSocket com retry automático."""
        for attempt in range(self.max_retries):
            try:
                if self.ws:
                    try:
                        self.ws.close()
                    except:
                        pass
                
                self.ws = websocket.create_connection(
                    self.debugger_url,
                    timeout=10  # Timeout de 10 segundos para conexão
                )
                print(f"✅ Conexão DevTools estabelecida (tentativa {attempt + 1})")
                return
                
            except Exception as e:
                print(f"❌ Falha na conexão DevTools (tentativa {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Não foi possível conectar após {self.max_retries} tentativas")

    def _is_connection_alive(self) -> bool:
        """Verifica se a conexão WebSocket ainda está ativa."""
        try:
            if not self.ws:
                return False
            # Tenta um ping simples
            self.ws.ping()
            return True
        except:
            return False

    def _ensure_connection(self):
        """Garante que a conexão está ativa, reconectando se necessário."""
        if not self._is_connection_alive():
            print("🔄 Conexão perdida, tentando reconectar...")
            self._connect()

    def send(self, method: str, params: Optional[dict] = None) -> Optional[Dict[Any, Any]]:
        """
        Envia comando ao DevTools com retry automático e timeout.
        """
        for attempt in range(self.max_retries):
            try:
                self._ensure_connection()
                
                if not self.ws:
                    print(f"❌ Conexão não disponível (tentativa {attempt + 1})")
                    continue
                
                request_id = self._next_id
                self._next_id += 1
                
                message = json.dumps({
                    "id": request_id,
                    "method": method,
                    "params": params or {}
                })
                
                self.ws.send(message)
                
                # Aguarda resposta com timeout
                max_wait_time = 30  # 30 segundos de timeout
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    try:
                        # Timeout mais baixo para recv para não travar
                        self.ws.settimeout(1.0)
                        raw = self.ws.recv()
                        
                        try:
                            response = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        if response.get("id") == request_id:
                            # Limpa cache de respostas antigas para evitar memory leak
                            self._cleanup_old_responses()
                            return response
                        else:
                            # Armazena resposta para outro request
                            resp_id = response.get("id")
                            if resp_id:
                                self._pending_responses[resp_id] = response
                                
                    except websocket.WebSocketTimeoutException:
                        continue
                    except Exception as e:
                        print(f"⚠️ Erro ao receber resposta: {e}")
                        break
                
                print(f"⏰ Timeout aguardando resposta para {method} (tentativa {attempt + 1})")
                
            except Exception as e:
                print(f"❌ Erro ao enviar comando {method} (tentativa {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    # Força reconexão na próxima tentativa
                    self.ws = None
                else:
                    print(f"💥 Falha definitiva ao executar {method}")
                    return None
        
        return None

    def _cleanup_old_responses(self):
        """Remove respostas antigas do cache para evitar memory leak."""
        if len(self._pending_responses) > 100:  # Limita cache a 100 entradas
            # Remove as 50 entradas mais antigas
            old_keys = list(self._pending_responses.keys())[:50]
            for key in old_keys:
                del self._pending_responses[key]
            print(f"🧹 Cache de respostas limpo ({len(old_keys)} entradas removidas)")

    def close(self):
        """Fecha a conexão WebSocket e limpa recursos."""
        try:
            if self.ws:
                self.ws.close()
                self.ws = None
            
            # Limpa cache para liberar memória
            self._pending_responses.clear()
            print("✅ Conexão DevTools fechada e recursos liberados")
            
        except Exception as e:
            print(f"⚠️ Erro ao fechar conexão: {e}")

    def __del__(self):
        """Destructor para garantir limpeza de recursos."""
        self.close()
