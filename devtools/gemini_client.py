"""
Cliente LLM para Gemini/Bard via Chrome DevTools
Implementa uma interface específica para interagir com o Gemini através do navegador.
"""

import time
import asyncio
from typing import Optional, List, Dict, Any
from .client import DevToolsClient
from core.llm.rag_context_manager import RAGContextManager


class GeminiClient:
    """Cliente para interação com Gemini/Bard via Chrome DevTools."""
    
    def __init__(self, websocket_url: str):
        """
        Inicializa o cliente Gemini.
        
        Args:
            websocket_url: URL do websocket do Chrome DevTools
        """
        self.devtools = DevToolsClient(websocket_url)
        self.is_connected = True  # DevToolsClient se conecta automaticamente
        
    def connect(self) -> bool:
        """
        Verifica se está conectado ao Chrome DevTools.
        
        Returns:
            True se conectou com sucesso
        """
        try:
            # Testa a conexão fazendo uma chamada simples
            result = self.devtools.send("Runtime.evaluate", {
                "expression": "1 + 1",
                "returnByValue": True
            })
            
            if result and result.get("result"):
                print("✅ Cliente Gemini conectado com sucesso")
                self.is_connected = True
                return True
            else:
                print("❌ Falha ao testar conexão com Gemini")
                self.is_connected = False
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar cliente Gemini: {e}")
            self.is_connected = False
            return False
            
    def disconnect(self):
        """Desconecta do Chrome DevTools."""
        if self.is_connected:
            self.devtools.close()
            self.is_connected = False
            print("✅ Cliente Gemini desconectado")
            
    def send_message(self, message: str) -> str:
        """
        Envia uma mensagem para o Gemini e aguarda a resposta.
        
        Args:
            message: Mensagem a ser enviada
            
        Returns:
            Resposta do Gemini
        """
        if not self.is_connected:
            raise RuntimeError("Cliente não está conectado")
            
        try:
            # Localiza o campo de entrada usando o seletor CSS fornecido
            input_selector = "#app-root > main > side-navigation-v2 > bard-sidenav-container > bard-sidenav-content > div.content-wrapper > div > div.content-container > chat-window > div > input-container > div > input-area-v2 > div > div > div.text-input-field_textarea-wrapper.ng-tns-c1185449887-74 > div > div > rich-textarea > div.ql-editor.textarea.new-input-ui.ql-blank"
            
            # XPath alternativo caso o CSS não funcione
            input_xpath = "/html/body/chat-app/main/side-navigation-v2/bard-sidenav-container/bard-sidenav-content/div[2]/div/div[2]/chat-window/div/input-container/div/input-area-v2/div/div/div[1]/div/div/rich-textarea/div[1]"
            
            print("🔍 Localizando campo de entrada...")
            
            # Tenta primeiro pelo CSS selector
            input_element = self._find_element_by_css(input_selector)
            
            if not input_element:
                # Se não encontrar, tenta pelo XPath
                input_element = self._find_element_by_xpath(input_xpath)
                
            if not input_element:
                raise RuntimeError("Não foi possível localizar o campo de entrada do Gemini")
                
            print("✅ Campo de entrada localizado")
            
            # Limpa o campo e insere a mensagem
            self._clear_and_type(input_element, message)
            print(f"✅ Mensagem inserida: {message[:100]}...")
            
            # Localiza e clica no botão de enviar
            send_button_selector = "#app-root > main > side-navigation-v2 > bard-sidenav-container > bard-sidenav-content > div.content-wrapper > div > div.content-container > chat-window > div > input-container > div > input-area-v2 > div > div > div.trailing-actions-wrapper.ng-tns-c1185449887-74 > div > div.mat-mdc-tooltip-trigger.send-button-container.ng-tns-c1185449887-74.inner.ng-star-inserted.visible > button > mat-icon"
            send_button_xpath = "/html/body/chat-app/main/side-navigation-v2/bard-sidenav-container/bard-sidenav-content/div[2]/div/div[2]/chat-window/div/input-container/div/input-area-v2/div/div/div[3]/div/div[2]/button/mat-icon"
            
            print("🔍 Localizando botão de enviar...")
            
            send_button = self._find_element_by_css(send_button_selector)
            if not send_button:
                send_button = self._find_element_by_xpath(send_button_xpath)
                
            if not send_button:
                raise RuntimeError("Não foi possível localizar o botão de enviar")
                
            print("✅ Botão de enviar localizado")
            
            # Clica no botão de enviar
            self._click_element(send_button)
            print("✅ Mensagem enviada")
            
            # Aguarda e captura a resposta
            response = self._wait_for_response()
            print(f"✅ Resposta recebida: {len(response)} caracteres")
            
            return response
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            raise
            
    def _find_element_by_css(self, selector: str) -> Optional[Dict[str, Any]]:
        """Encontra elemento pelo seletor CSS."""
        try:
            result = self.devtools.send("DOM.getDocument")
            if not result or "result" not in result:
                return None
                
            root_node_id = result["result"]["root"]["nodeId"]
            
            result = self.devtools.send("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": selector
            })
            
            if result and result.get("result", {}).get("nodeId"):
                return {"nodeId": result["result"]["nodeId"]}
            return None
            
        except Exception as e:
            print(f"Erro ao buscar por CSS '{selector}': {e}")
            return None
            
    def _find_element_by_xpath(self, xpath: str) -> Optional[Dict[str, Any]]:
        """Encontra elemento pelo XPath."""
        try:
            # Executa JavaScript para encontrar por XPath
            js_code = f"""
                (function() {{
                    try {{
                        var result = document.evaluate('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        var node = result.singleNodeValue;
                        if (node) {{
                            return node;
                        }}
                        return null;
                    }} catch(e) {{
                        return null;
                    }}
                }})()
            """
            
            result = self.devtools.send("Runtime.evaluate", {
                "expression": js_code,
                "returnByValue": False
            })
            
            if result and result.get("result", {}).get("result", {}).get("objectId"):
                object_id = result["result"]["result"]["objectId"]
                
                # Converte para node ID
                node_result = self.devtools.send("DOM.requestNode", {
                    "objectId": object_id
                })
                
                if node_result and node_result.get("result", {}).get("nodeId"):
                    return {"nodeId": node_result["result"]["nodeId"]}
                
            return None
            
        except Exception as e:
            print(f"Erro ao buscar por XPath '{xpath}': {e}")
            return None
            
    def _clear_and_type(self, element: Dict[str, Any], text: str):
        """Limpa o campo e digita o texto."""
        node_id = element["nodeId"]
        
        try:
            # Foca no elemento
            self.devtools.send("DOM.focus", {"nodeId": node_id})
            time.sleep(0.2)
            
            # Limpa o conteúdo existente usando JavaScript
            clear_js = """
                (function() {
                    var element = arguments[0];
                    if (element) {
                        element.innerHTML = '';
                        element.textContent = '';
                        element.innerText = '';
                        // Dispara eventos para notificar frameworks
                        element.dispatchEvent(new Event('input', {bubbles: true}));
                        element.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                })(arguments[0])
            """
            
            # Obtém referência ao elemento
            self.devtools.send("DOM.resolveNode", {"nodeId": node_id})
            
            # Simula Ctrl+A para selecionar tudo
            self.devtools.send("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "key": "Control"
            })
            time.sleep(0.1)
            
            self.devtools.send("Input.dispatchKeyEvent", {
                "type": "char",
                "text": "a"
            })
            time.sleep(0.1)
            
            self.devtools.send("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "key": "Control"
            })
            time.sleep(0.2)
            
            # Digita o novo texto
            for char in text:
                self.devtools.send("Input.dispatchKeyEvent", {
                    "type": "char",
                    "text": char
                })
                time.sleep(0.01)  # Pequena pausa entre caracteres
                
        except Exception as e:
            print(f"Erro ao digitar texto: {e}")
            raise
            
    def _click_element(self, element: Dict[str, Any]):
        """Clica no elemento."""
        node_id = element["nodeId"]
        
        try:
            # Obtém as coordenadas do elemento
            result = self.devtools.send("DOM.getBoxModel", {"nodeId": node_id})
            
            if result and result.get("result", {}).get("model"):
                quad = result["result"]["model"]["content"]
                # Calcula o centro do elemento
                x = (quad[0] + quad[2]) / 2
                y = (quad[1] + quad[5]) / 2
                
                # Clica no centro do elemento
                self.devtools.send("Input.dispatchMouseEvent", {
                    "type": "mousePressed",
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1
                })
                
                time.sleep(0.1)
                
                self.devtools.send("Input.dispatchMouseEvent", {
                    "type": "mouseReleased",
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1
                })
            else:
                print("❌ Não foi possível obter coordenadas do elemento")
                
        except Exception as e:
            print(f"Erro ao clicar no elemento: {e}")
            raise
            
    def _wait_for_response(self, timeout: int = 60) -> str:
        """
        Aguarda a resposta do Gemini aparecer na página.
        
        Args:
            timeout: Tempo limite em segundos
            
        Returns:
            Texto da resposta
        """
        start_time = time.time()
        last_response_elements = []
        
        print("⏳ Aguardando resposta do Gemini...")
        
        while time.time() - start_time < timeout:
            try:
                # Busca todos os elementos com a classe model-response-text
                js_code = """
                    (function() {
                        try {
                            var elements = Array.from(document.querySelectorAll('.model-response-text'));
                            return elements.map(function(el) {
                                return {
                                    text: el.innerText || el.textContent || '',
                                    html: el.innerHTML || ''
                                };
                            });
                        } catch(e) {
                            return [];
                        }
                    })()
                """
                
                result = self.devtools.send("Runtime.evaluate", {
                    "expression": js_code,
                    "returnByValue": True
                })
                
                if result and result.get("result", {}).get("result", {}).get("value"):
                    response_elements = result["result"]["result"]["value"]
                    
                    # Se encontrou novos elementos ou mudanças
                    if len(response_elements) > len(last_response_elements):
                        # Pega o último elemento (resposta mais recente)
                        if response_elements:
                            latest_response = response_elements[-1]
                            response_text = latest_response.get("text", "").strip()
                            
                            # Verifica se a resposta está completa (não está sendo digitada)
                            if response_text and len(response_text) > 10:
                                # Aguarda um pouco mais para garantir que terminou
                                time.sleep(2)
                                
                                # Verifica novamente se mudou
                                result2 = self.devtools.send("Runtime.evaluate", {
                                    "expression": js_code,
                                    "returnByValue": True
                                })
                                
                                if result2 and result2.get("result", {}).get("result", {}).get("value"):
                                    elements2 = result2["result"]["result"]["value"]
                                    if elements2 and len(elements2) >= len(response_elements):
                                        final_response = elements2[-1].get("text", "").strip()
                                        if final_response == response_text:
                                            # Resposta não mudou, provavelmente terminou
                                            return final_response
                                
                        last_response_elements = response_elements
                        
                time.sleep(1)  # Aguarda 1 segundo antes de tentar novamente
                
            except Exception as e:
                print(f"Erro ao verificar resposta: {e}")
                time.sleep(1)
                
        raise TimeoutError(f"Timeout aguardando resposta do Gemini ({timeout}s)")


class GeminiLLMInterface:
    """Interface LLM para Gemini que segue o padrão do sistema."""
    
    def __init__(self, websocket_url: str, use_rag: bool = False, rag_top_k: int = 5, rag_model: str = 'mixedbread-ai/mxbai-embed-large-v1'):
        """
        Inicializa a interface Gemini.
        
        Args:
            websocket_url: URL do websocket do Chrome DevTools
        """
        self.client = GeminiClient(websocket_url)
        self.is_connected = False
        self.use_rag = use_rag
        self.rag_manager = RAGContextManager(top_k=rag_top_k, embedding_model=rag_model) if use_rag else None

    def connect(self) -> bool:
        """Conecta ao Gemini."""
        self.is_connected = self.client.connect()
        return self.is_connected
        
    def disconnect(self):
        """Desconecta do Gemini."""
        if self.is_connected:
            self.client.disconnect()
            self.is_connected = False
            
    def send_message(self, message: str, messages: List[Dict[str, str]] = None) -> str:
        """
        Envia mensagem e retorna resposta.
        
        Args:
            message: Mensagem a enviar
            
        Returns:
            Resposta do Gemini
        """
        if not self.is_connected:
            raise RuntimeError("Interface não está conectada")
            
        if self.use_rag and self.rag_manager and messages:
            messages = self.rag_manager.find_relevant_messages(messages)
            # Combine as mensagens em um único prompt, se necessário
            message = "\n".join([msg['content'] for msg in messages])
            
        return self.client.send_message(message)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.is_connected:
            self.disconnect()
