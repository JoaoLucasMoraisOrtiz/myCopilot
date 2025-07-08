import json
from urllib.request import urlopen
import time

from devtools.client import DevToolsClient
from devtools.dom import get_box_model, enable_dom, find_last_element, find_element_by_selector
from devtools.page import enable_page
from devtools.input import enable_input, click, insert_text
from devtools.chat import stream_chat_response

class LLMClient:
    def __init__(self, target_url='https://vscode.dev'):
        self.target_url = target_url
        self.client = None
        self.send_button_selector = '#workbench\\.panel\\.chat > div > div > div.monaco-scrollable-element > div.split-view-container > div > div > div.pane-body > div.interactive-session > div.interactive-input-part > div.interactive-input-and-side-toolbar > div > div.chat-input-toolbars > div.monaco-toolbar.chat-execute-toolbar > div > ul > li.action-item.monaco-dropdown-with-primary > div.action-container.menu-entry > a'
        self.chat_response_selector = 'div[data-last-element]'
        
    def get_debug_url(self):
        try:
            with urlopen('http://localhost:9222/json') as response:
                tabs = json.load(response)
                for tab in tabs:
                    if tab.get('type') == 'page' and tab.get('url', '').startswith(self.target_url):
                        return tab['webSocketDebuggerUrl']
        except Exception as e:
            print(f'Erro ao obter URL de depuração: {e}')
        return None
    
    def connect(self):
        debug_url = self.get_debug_url()
        if not debug_url:
            raise Exception('URL de depuração não encontrado. Verifique se o Chrome está rodando.')
        
        self.client = DevToolsClient(debug_url)
        enable_page(self.client)
        enable_dom(self.client)
        enable_input(self.client)
        
    def send_prompt(self, prompt_text):
        if not self.client:
            raise Exception('Cliente não conectado. Chame connect() primeiro.')
        
        # Encontrar textarea
        node_id, frame_id = find_last_element(self.client, 'textarea')
        if not node_id:
            raise Exception('Textarea não encontrado.')
        
        # Clicar e inserir texto
        box = get_box_model(self.client, node_id)
        quad = box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
        click(self.client, center_x, center_y)
        time.sleep(0.5)
        insert_text(self.client, prompt_text)

        
        # Capturar estado atual do chat
        expression_count = f"document.querySelectorAll('{self.chat_response_selector}').length"
        resp = self.client.send('Runtime.evaluate', {
            'expression': expression_count,
            'returnByValue': True
        })
        prev_count = resp.get('result', {}).get('result', {}).get('value', 0)
        
        # Encontrar e clicar no botão de enviar
        send_button_node_id, _ = find_element_by_selector(self.client, self.send_button_selector)
        if not send_button_node_id:
            raise Exception("Botão de enviar não encontrado.")
        
        send_button_box = get_box_model(self.client, send_button_node_id)
        quad = send_button_box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
        click(self.client, center_x, center_y)
        
        # Aguardar nova resposta com timeout
        max_wait_time = 25  # 5 minutos máximo
        wait_interval = 5    # Verifica a cada 5 segundos
        total_waited = 0
        
        print("⏳ Aguardando resposta do LLM...")
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            resp = self.client.send('Runtime.evaluate', {
                'expression': expression_count,
                'returnByValue': True
            })
            
            # Corrige o acesso ao valor
            curr_count = resp.get('result', {}).get('result', {}).get('value', 0)
            
            print(f"📊 Aguardando... {total_waited}s (elementos: {curr_count})")
            
            if curr_count != prev_count:
                print("✅ Nova resposta detectada!")
                time.sleep(5)
                break
        else:
            # Timeout atingido
            print(f"⏰ Timeout de {max_wait_time}s atingido. Tentando capturar resposta atual...")
            # Continua para tentar capturar o que estiver disponível
            
        
        # Capturar resposta
        return self._capture_response()
    
    def _capture_response(self):
        """Captura a resposta do chat com timeout e melhor tratamento de erros"""
        response_parts = []
        prev_text = ""
        has_update = False
        max_attempts = 60  # 60 tentativas (1 minuto)
        attempt = 0
        
        print("📥 Capturando resposta do chat...")
        
        while attempt < max_attempts:
            try:
                expression = f"""
                    (() => {{
                        const elems = document.querySelectorAll('{self.chat_response_selector}');
                        if (!elems || elems.length === 0) return '';
                        const lastElem = elems[elems.length - 2]; // Pega o penúltimo elemento para evitar o botão de enviar
                        return lastElem ? (lastElem.getAttribute('aria-label') || lastElem.innerText || '') : '';
                    }})()
                """
                
                resp = self.client.send('Runtime.evaluate', {
                    'expression': expression,
                    'returnByValue': True
                })

                # Verifica se houve erro na avaliação
                if 'error' in resp:
                    print(f"❌ Erro na avaliação JavaScript: {resp['error']}")
                    attempt += 1
                    time.sleep(1)
                    continue
                
                # Extrai o texto da resposta
                current = resp.get('result', {}).get('result', {}).get('value', '') or ''
                
                if 'Inspect this in the accessible view with Shift+Alt+F2' in str(resp):
                    current = current.replace('Inspect this in the accessible view with Shift+Alt+F2', '').strip()
                    expression = f"""
                        (() => {{
                            const elems = document.querySelectorAll('{self.chat_response_selector}');
                            if (!elems || elems.length === 0) return '';
                            const lastElem = elems[elems.length - 2]; // Pega o penúltimo elemento para evitar o botão de enviar
                            return lastElem ? (lastElem.getAttribute('aria-label') || lastElem.innerText || '') : '';
                        }})()
                    """
                    
                    resp = self.client.send('Runtime.evaluate', {
                        'expression': expression,
                        'returnByValue': True
                    })

                    if 'error' in resp:
                        print(f"❌ Erro na avaliação JavaScript: {resp['error']}")
                        attempt += 1
                        time.sleep(1)
                        continue
                

                if current and current != prev_text:
                    diff = current[len(prev_text):]
                    response_parts.append(diff)
                    prev_text = current
                    has_update = True
                    print(f"📝 Resposta parcial capturada ({len(current)} chars)")
                elif has_update and current:
                    # Se já temos atualizações e o texto não mudou, provavelmente terminou
                    print("✅ Resposta completa capturada!")
                    break
                
                attempt += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Erro ao capturar resposta (tentativa {attempt}): {e}")
                attempt += 1
                time.sleep(2)
        
        final_response = ''.join(response_parts)
        
        if not final_response:
            print("⚠️ Nenhuma resposta capturada. Tentando método alternativo...")
            # Método alternativo - captura diretamente o último elemento
            try:
                alt_expression = f"""
                    (() => {{
                        const chatContainer = document.querySelector('.interactive-session');
                        if (!chatContainer) return 'Chat container não encontrado';
                        const messages = chatContainer.querySelectorAll('[data-last-element], .message, .chat-response');
                        if (messages.length === 0) return 'Nenhuma mensagem encontrada';
                        const lastMessage = messages[messages.length - 1];
                        return lastMessage.innerText || lastMessage.textContent || 'Conteúdo não disponível';
                    }})()
                """
                
                resp = self.client.send('Runtime.evaluate', {
                    'expression': alt_expression,
                    'returnByValue': True
                })
                
                alt_response = resp.get('result', {}).get('value', '')
                if alt_response:
                    final_response = alt_response
                    print("✅ Resposta capturada via método alternativo!")
                
            except Exception as e:
                print(f"❌ Método alternativo também falhou: {e}")
        
        if not final_response:
            final_response = "❌ Erro: Não foi possível capturar a resposta do LLM. Verifique se o Copilot Chat está ativo e funcionando."
        
        print(f"📊 Resposta final: {len(final_response)} caracteres")
        return final_response
    
    def close(self):
        if self.client:
            self.client.close()
