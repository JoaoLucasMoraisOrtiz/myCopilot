import json
from urllib.request import urlopen
import time
from typing import Optional

from devtools.client import DevToolsClient
from devtools.dom import get_box_model, enable_dom, find_last_element, find_element_by_selector
from devtools.page import enable_page
from devtools.input import enable_input, click, insert_text
from devtools.chat import stream_chat_response

class LLMClient:
    def __init__(self, target_url='https://vscode.dev', max_retries=3):
        self.target_url = target_url
        self.max_retries = max_retries
        self.client = None
        self.send_button_selector = '#workbench\\.panel\\.chat > div > div > div.monaco-scrollable-element > div.split-view-container > div > div > div.pane-body > div.interactive-session > div.interactive-input-part > div.interactive-input-and-side-toolbar > div > div.chat-input-toolbars > div.monaco-toolbar.chat-execute-toolbar > div > ul > li.action-item.monaco-dropdown-with-primary > div.action-container.menu-entry > a'
        self.chat_response_selector = 'div[data-last-element]'
        
    def get_debug_url(self) -> Optional[str]:
        """Obtém URL de debug com retry."""
        for attempt in range(self.max_retries):
            try:
                with urlopen('http://localhost:9222/json', timeout=10) as response:
                    tabs = json.load(response)
                    for tab in tabs:
                        if tab.get('type') == 'page' and tab.get('url', '').startswith(self.target_url):
                            return tab['webSocketDebuggerUrl']
                print(f"⚠️ Aba do VS Code não encontrada (tentativa {attempt + 1})")
                            
            except Exception as e:
                print(f'❌ Erro ao obter URL de depuração (tentativa {attempt + 1}): {e}')
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    
        return None
    
    def connect(self):
        """Conecta com retry automático."""
        debug_url = self.get_debug_url()
        if not debug_url:
            raise Exception('❌ URL de depuração não encontrado após múltiplas tentativas. Verifique se o Chrome está rodando com --remote-debugging-port=9222.')
        
        try:
            if self.client:
                self.client.close()
                
            self.client = DevToolsClient(debug_url, max_retries=self.max_retries)
            
            # Habilita domínios com verificação
            enable_page(self.client)
            enable_dom(self.client)
            enable_input(self.client)
            
            print("✅ Cliente LLM conectado com sucesso")
            
        except Exception as e:
            print(f"💥 Falha crítica ao conectar cliente LLM: {e}")
            raise
        
    def send_prompt(self, prompt_text):
        """Envia prompt com retry e melhor tratamento de erros."""
        if not self.client:
            raise Exception('❌ Cliente não conectado. Chame connect() primeiro.')
        
        # Reconecta se necessário
        try:
            # Teste de conectividade
            test_response = self.client.send('Runtime.enable')
            if not test_response:
                print("🔄 Conexão perdida, reconectando...")
                self.connect()
        except:
            print("🔄 Erro de conexão detectado, reconectando...")
            self.connect()
        
        # Encontrar textarea com retry
        node_id, frame_id = None, None
        for attempt in range(self.max_retries):
            try:
                node_id, frame_id = find_last_element(self.client, 'textarea')
                if node_id:
                    break
                print(f"⚠️ Textarea não encontrado (tentativa {attempt + 1})")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Erro ao buscar textarea (tentativa {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
        
        if not node_id:
            raise Exception('❌ Textarea não encontrado após múltiplas tentativas.')
        
        # Clicar e inserir texto com retry
        for attempt in range(self.max_retries):
            try:
                box = get_box_model(self.client, node_id)
                if not box:
                    raise Exception("Não foi possível obter box model")
                    
                quad = box['content']
                center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
                center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
                
                # Clica no textarea
                click(self.client, center_x, center_y)
                
                # Insere o novo texto (substitui o selecionado)
                insert_text(self.client, prompt_text)
                time.sleep(0.5)
                break
                
            except Exception as e:
                print(f"❌ Erro ao inserir texto (tentativa {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise Exception("Falha ao inserir texto após múltiplas tentativas")

        
        # Capturar estado atual do chat
        expression_count = f"document.querySelectorAll('{self.chat_response_selector}').length"
        resp = self.client.send('Runtime.evaluate', {
            'expression': expression_count,
            'returnByValue': True
        })
        prev_count = 0
        if resp and resp.get('result', {}).get('result'):
            prev_count = resp.get('result', {}).get('result', {}).get('value', 0)
        
        # Encontrar e clicar no botão de enviar com retry
        for attempt in range(self.max_retries):
            try:
                send_button_node_id, _ = find_element_by_selector(self.client, self.send_button_selector)
                if not send_button_node_id:
                    print(f"⚠️ Botão de enviar não encontrado (tentativa {attempt + 1})")
                    time.sleep(2)
                    continue
                
                send_button_box = get_box_model(self.client, send_button_node_id)
                if not send_button_box:
                    raise Exception("Não foi possível obter box model do botão")
                    
                quad = send_button_box['content']
                center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
                center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
                time.sleep(1)
                click(self.client, center_x, center_y)
                break
                
            except Exception as e:
                print(f"❌ Erro ao clicar no botão (tentativa {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    raise Exception("Falha ao clicar no botão após múltiplas tentativas")
        
        # Aguardar nova resposta com timeout otimizado para respostas grandes
        max_wait_time = 25  # Aumenta timeout para 120 segundos para respostas grandes
        wait_interval = 5
        total_waited = 0
        
        print("⏳ Aguardando resposta do LLM...")
        response_detected = False
        
        while total_waited < max_wait_time:
            #time.sleep(wait_interval)
            total_waited += wait_interval
            
            try:
                resp = self.client.send('Runtime.evaluate', {
                    'expression': expression_count,
                    'returnByValue': True
                })
                
                curr_count = 0
                if resp and resp.get('result', {}).get('result'):
                    curr_count = resp.get('result', {}).get('result', {}).get('value', 0)
                
                print(f"📊 Aguardando... {total_waited}s (elementos: {curr_count})")
                
                if curr_count != prev_count:
                    print("✅ Nova resposta detectada!")
                    response_detected = True
                    
                    # Para respostas grandes, aguarda mais tempo para completar
                    if total_waited < 30:  # Se detectou rapidamente, aguarda mais
                        print("⏳ Aguardando resposta completar...")
                        time.sleep(3)  # Aguarda mais para respostas grandes
                        total_waited += 10
                    else:
                        time.sleep(3)  # Aguarda normal
                        total_waited += 5
                    break
                    
            except Exception as e:
                print(f"⚠️ Erro ao verificar resposta: {e}")
                
        if not response_detected:
            print(f"⏰ Timeout de {max_wait_time}s atingido. Tentando capturar resposta atual...")
        
        # Capturar resposta
        return self._capture_response()
    
    def _capture_response(self):
        """Captura a resposta do chat com timeout e melhor tratamento de erros"""
        if not self.client:
            return "❌ Erro: Cliente não conectado."
            
        response_parts = []
        prev_text = ""
        has_update = False
        max_attempts = 30  # Reduz para 30 tentativas (30 segundos)
        attempt = 0
        
        print("📥 Capturando resposta do chat...")
        
        while attempt < max_attempts:
            try:
                expression = f"""
                    (() => {{
                        const elems = document.querySelectorAll('{self.chat_response_selector}');
                        if (!elems || elems.length === 0) return '';
                        const lastElem = elems[elems.length - 1]; // Pega o último elemento
                        return lastElem ? (lastElem.getAttribute('aria-label') || lastElem.innerText || '') : '';
                    }})()
                """
                
                resp = self.client.send('Runtime.evaluate', {
                    'expression': expression,
                    'returnByValue': True
                })

                # Verifica se houve erro na resposta
                if not resp:
                    print(f"⚠️ Resposta vazia do DevTools (tentativa {attempt + 1})")
                    attempt += 1
                    time.sleep(1)
                    continue
                    
                if 'error' in resp:
                    print(f"❌ Erro na avaliação JavaScript: {resp['error']}")
                    attempt += 1
                    time.sleep(1)
                    continue
                
                # Extrai o texto da resposta
                result = resp.get('result', {})
                if not result or 'result' not in result:
                    attempt += 1
                    time.sleep(1)
                    continue
                    
                current = result.get('result', {}).get('value', '') or ''
                
                # Remove texto indesejado
                if 'Inspect this in the accessible view with Shift+Alt+F2' in current:
                    current = current.replace('Inspect this in the accessible view with Shift+Alt+F2', '').strip()

                if current and current != prev_text:
                    diff = current[len(prev_text):]
                    response_parts.append(diff)
                    prev_text = current
                    has_update = True
                    
                    char_count = len(current)
                    print(f"📝 Resposta parcial capturada ({char_count} chars)")
                    
                    # Aguarda tempo diferente baseado no tamanho da resposta
                    if char_count > 15000:
                        print("⏳ Resposta grande detectada, aguardando estabilização...")
                        time.sleep(3)
                    elif char_count > 5000:
                        time.sleep(2)
                    else:
                        time.sleep(4)
                        
                elif has_update and current:
                    # Se já temos atualizações e o texto não mudou, provavelmente terminou
                    print("✅ Resposta completa capturada!")
                    final_text = prev_text
                    print(f"📊 Resposta final: {len(final_text)} caracteres")
                    
                    # Validação final - se resposta muito pequena, tenta mais uma vez
                    if len(final_text) < 10 and attempt < max_attempts - 5:
                        print("⚠️ Resposta muito pequena, tentando novamente...")
                        time.sleep(2)
                        attempt += 1
                        continue
                    
                    break
                
                attempt += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Erro ao capturar resposta (tentativa {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        
        final_response = ''.join(response_parts)
        
        if not final_response:
            print("⚠️ Nenhuma resposta capturada. Tentando método alternativo...")
            # Método alternativo - captura diretamente o último elemento
            try:
                alt_expression = f"""
                    (() => {{
                        // Tenta diferentes seletores para capturar a resposta
                        const selectors = [
                            '[data-last-element]',
                            '.interactive-response',
                            '.chat-response',
                            '.message',
                            '.monaco-list-row'
                        ];
                        
                        for (const selector of selectors) {{
                            const elements = document.querySelectorAll(selector);
                            if (elements.length > 0) {{
                                const lastElement = elements[elements.length - 1];
                                const text = lastElement.innerText || lastElement.textContent || '';
                                if (text.trim().length > 0) {{
                                    return text;
                                }}
                            }}
                        }}
                        
                        // Fallback final - procura por qualquer elemento com texto
                        const chatContainer = document.querySelector('.interactive-session');
                        if (chatContainer) {{
                            const allElements = chatContainer.querySelectorAll('*');
                            for (let i = allElements.length - 1; i >= 0; i--) {{
                                const element = allElements[i];
                                const text = element.innerText || element.textContent || '';
                                if (text.trim().length > 50) {{ // Só pega textos com pelo menos 50 chars
                                    return text;
                                }}
                            }}
                        }}
                        
                        return 'Nenhuma resposta encontrada';
                    }})()
                """
                
                resp = self.client.send('Runtime.evaluate', {
                    'expression': alt_expression,
                    'returnByValue': True
                })
                
                if resp and resp.get('result', {}).get('result'):
                    alt_response = resp.get('result', {}).get('result', {}).get('value', '')
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
        """Fecha conexão e libera recursos adequadamente."""
        try:
            if self.client:
                self.client.close()
                self.client = None
                print("✅ Cliente LLM desconectado e recursos liberados")
        except Exception as e:
            print(f"⚠️ Erro ao fechar cliente LLM: {e}")

    def __del__(self):
        """Destructor para garantir limpeza de recursos."""
        self.close()
