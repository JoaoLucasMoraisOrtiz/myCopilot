import json
import time
import websocket

class DevToolsClient:
    """
    Cliente para interação com o Chrome DevTools Protocol via WebSocket.
    Usa IDs de requisição incrementais para mapear respostas.
    """
    def __init__(self, debugger_url: str):
        self.ws = websocket.create_connection(debugger_url)
        self._next_id = 1

    def send(self, method: str, params: dict = None) -> dict:
        """
        Envia comando ao DevTools e aguarda a resposta correspondente ao ID.
        """
        request_id = self._next_id
        self._next_id += 1
        message = json.dumps({
            "id": request_id,
            "method": method,
            "params": params or {}
        })
        self.ws.send(message)

        time.sleep(1)
        while True:
            raw = self.ws.recv()
            try:
                response = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if response.get("id") == request_id:
                return response

    def close(self):
        """Fecha a conexão WebSocket."""
        self.ws.close()
