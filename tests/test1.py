import json
import websocket # from websocket-client
import requests
import time

# --- Como executar o Chrome para que isso funcione ---
# No Linux: google-chrome --remote-debugging-port=9222
# No macOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
# No Windows: "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

def get_debug_url():
    """Busca o URL do depurador WebSocket para a primeira página disponível."""
    try:
        response = requests.get("http://localhost:9222/json")
        response.raise_for_status()  # Lança uma exceção para códigos de status ruins
        tabs = response.json()
        if not tabs:
            print("Nenhuma aba depurável encontrada. O Chrome está rodando com --remote-debugging-port=9222?")
            return None
        # Encontra o primeiro alvo do tipo 'page'
        for tab in tabs:
            if tab.get("type") == "page" and "webSocketDebuggerUrl" in tab:
                return tab["webSocketDebuggerUrl"]
        print("Nenhuma página depurável encontrada.")
        return None
    except requests.exceptions.ConnectionError:
        print("A conexão com o Chrome falhou. Verifique se ele está rodando com a porta de depuração remota aberta.")
        return None

def send_command(ws, method, params, command_id=1):
    """Envia um comando para o navegador via WebSocket e retorna o resultado."""
    message = json.dumps({"id": command_id, "method": method, "params": params})
    # print(f"Enviando: {message}") # Descomente para depuração detalhada
    ws.send(message)

    # A recepção de respostas é complexa. O ideal é ter um loop em uma thread separada
    # que mapeia respostas para comandos usando o 'id'.
    # Para simplificar, vamos apenas esperar por uma resposta que corresponda ao nosso id.
    while True:
        try:
            result_str = ws.recv()
            # print(f"Recebido: {result_str}") # Descomente para depuração detalhada
            result = json.loads(result_str)
            if result.get('id') == command_id:
                return result
        except websocket.WebSocketConnectionClosedException:
            print("A conexão WebSocket foi fechada.")
            return None
        except json.JSONDecodeError:
            # Ignora mensagens que não são JSON (ex: notificações de eventos)
            pass
        except Exception as e:
            print(f"Erro ao receber/processar mensagem: {e}")
            return None

def get_node_id(ws, selector, root_node_id):
    """Encontra um nó na página usando um seletor CSS."""
    res = send_command(
        ws,
        "DOM.querySelector",
        {"nodeId": root_node_id, "selector": selector},
        command_id=100 # Usar IDs diferentes ajuda na depuração
    )
    if res and res.get('result', {}).get('nodeId'):
        return res['result']['nodeId']
    return None

def get_box_model(ws, node_id):
    """Obtém o modelo de caixa de um nó (inclui coordenadas e dimensões)."""
    res = send_command(
        ws,
        "DOM.getBoxModel",
        {"nodeId": node_id},
        command_id=101
    )
    if res and 'result' in res:
        return res['result']['model']
    return None

def main():
    # --- CONFIGURAR AQUI ---
    TARGET_URL = "https://vscode.dev"
    # Seletor CSS para o elemento que queremos clicar.
    # Este seletor visa o primeiro item na barra de atividades (geralmente o Explorer).
    ELEMENT_SELECTOR = "#workbench\.panel\.chat > div > div > div.monaco-scrollable-element > div.split-view-container > div > div > div.pane-body > div.interactive-session > div.interactive-input-part > div.interactive-input-and-side-toolbar > div > div.chat-editor-container > div > div > div > div.monaco-scrollable-element.editor-scrollable.vs-dark > div.lines-content.monaco-editor-background > div.view-lines.monaco-mouse-cursor-text"
    # ---------------------

    debugger_url = get_debug_url()
    if not debugger_url:
        return

    print(f"Conectando a: {debugger_url}")
    try:
        ws = websocket.create_connection(debugger_url)
    except Exception as e:
        print(f"Falha ao criar a conexão WebSocket: {e}")
        return

    try:
        # Habilita os domínios necessários
        send_command(ws, "Page.enable", {}, command_id=1)
        send_command(ws, "DOM.enable", {}, command_id=2) # Habilitar o domínio DOM
        send_command(ws, "Input.enable", {}, command_id=3)
        send_command(ws, "Overlay.enable", {}, command_id=4)

        # Exemplo: Navegar para uma URL
        #print(f"Navegando para {TARGET_URL}...")
        #send_command(ws, "Page.navigate", {"url": TARGET_URL}, command_id=5)
        
        # Em vez de um sleep fixo, o ideal seria esperar pelo evento 'Page.loadEventFired'.
        # Por simplicidade, vamos manter um sleep mais longo para garantir o carregamento.
        #print("Aguardando o carregamento da página (10s)...")
        #time.sleep(10)

        # Obter o nó raiz do documento
        doc_res = send_command(ws, "DOM.getDocument", {"depth": -1}, command_id=6)
        if not doc_res or 'root' not in doc_res.get('result', {}):
            print("Falha ao obter o documento DOM.")
            return
        root_node_id = doc_res['result']['root']['nodeId']

        # Encontrar o nosso elemento alvo usando o seletor
        print(f"Procurando pelo elemento com o seletor: {ELEMENT_SELECTOR}")
        node_id = get_node_id(ws, ELEMENT_SELECTOR, root_node_id)
        if not node_id:
            print("Elemento não encontrado. Verifique o seletor ou o tempo de carregamento.")
            return
        
        print("Elemento encontrado!")

        # Obter a posição do elemento
        box = get_box_model(ws, node_id)
        if not box or 'content' not in box:
            print("Não foi possível obter a posição do elemento.")
            return
        
        # O 'content' é uma lista de coordenadas [x1, y1, x2, y2, ...]. Pegamos o primeiro ponto.
        content_quad = box['content']
        click_x = int(content_quad[0] + (content_quad[2] - content_quad[0]) / 2) # Centro X
        click_y = int(content_quad[1] + (content_quad[5] - content_quad[1]) / 2) # Centro Y

        # Destaca a área de clique para visualização
        print(f"Destacando o elemento encontrado em ({click_x}, {click_y})...")
        send_command(ws, "Overlay.highlightNode", {"nodeId": node_id, "highlightConfig": {
            "contentColor": {"r": 255, "g": 0, "b": 0, "a": 0.4}
        }}, command_id=7)
        time.sleep(3)
        send_command(ws, "Overlay.hideHighlight", {}, command_id=8)

        # Simular clique no centro do elemento
        print(f"Simulando clique em ({click_x}, {click_y})...")
        send_command(ws, "Input.dispatchMouseEvent", {
            "type": "mousePressed", "x": click_x, "y": click_y, "button": "left", "clickCount": 1
        }, command_id=9)
        send_command(ws, "Input.dispatchMouseEvent", {
            "type": "mouseReleased", "x": click_x, "y": click_y, "button": "left", "clickCount": 1
        }, command_id=10)
        # Digitar texto 'OK' no campo de texto
        send_command(ws, "Input.insertText", {"text": "OK"}, command_id=11)
        time.sleep(0.5)

        print("Ações concluídas.")
        time.sleep(2)

    finally:
        ws.close()
        print("Conexão fechada.")

if __name__ == "__main__":
    main()