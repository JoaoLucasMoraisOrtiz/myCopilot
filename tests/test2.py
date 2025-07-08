import json
from urllib.request import urlopen
import time


from devtools.client import DevToolsClient
from devtools.dom import get_document, query_selector, get_box_model, enable_dom, find_first_element, find_element_by_selector
from devtools.page import enable_page
from devtools.input import enable_input, click, insert_text

def get_debug_url(filter_url: str = None):
    """Busca o URL de depuração de uma aba que corresponda a filter_url."""
    try:
        with urlopen('http://localhost:9222/json') as response:
            tabs = json.load(response)
            if filter_url:
                for tab in tabs:
                    if tab.get('type') == 'page' and tab.get('url', '').startswith(filter_url):
                        return tab['webSocketDebuggerUrl']
            # Fallback para a primeira aba, se nenhum filtro corresponder
            for tab in tabs:
                if tab.get('type') == 'page':
                    return tab['webSocketDebuggerUrl']
    except Exception as e:
        print(f'Erro ao obter URL de depuração: {e}')
    return None

def main():
    # --- CONFIGURAÇÃO ---
    TARGET_URL = 'https://vscode.dev'
    TEXT_TO_TYPE = "Olá, automação! Por favor, me diga como criar um olá mundo em Python."
    SEND_BUTTON_SELECTOR = '#workbench\\.panel\\.chat > div > div > div.monaco-scrollable-element > div.split-view-container > div > div > div.pane-body > div.interactive-session > div.interactive-input-part > div.interactive-input-and-side-toolbar > div > div.chat-input-toolbars > div.monaco-toolbar.chat-execute-toolbar > div > ul > li.action-item.monaco-dropdown-with-primary > div.action-container.menu-entry > a'
    # --------------------

    debug_url = get_debug_url(TARGET_URL)
    if not debug_url:
        print('URL de depuração não encontrado. Verifique se o Chrome está rodando e a aba correta está aberta.')
        return

    print(f'Conectando ao DevTools em: {debug_url}')
    client = DevToolsClient(debug_url)

    try:
        # Habilita os domínios necessários
        enable_page(client)
        enable_dom(client)
        enable_input(client)

        # NOVA ABORDAGEM: Busca robusta e paciente no DOM
        print("Iniciando busca robusta por 'textarea' em todos os frames...")
        node_id, frame_id = find_first_element(client, 'textarea')
        
        if not node_id:
            print('Nenhum elemento textarea encontrado com a nova abordagem.')
            print('Verifique a saída do console para mais detalhes sobre a busca nos frames.')
            return

        print("crie uma API python para criar um olá mundo. Retorne apenas o código.")
        print(f"NodeId: {node_id}, FrameId: {frame_id}")

        # Obtém a posição do elemento para o clique
        box = get_box_model(client, node_id)
        if not box or 'content' not in box:
             print("Não foi possível obter a posição do elemento.")
             return

        quad = box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
        print(f'Elemento localizado em: ({center_x}, {center_y})')

        # Clica e insere o texto
        click(client, center_x, center_y)
        time.sleep(0.5) # Pequena pausa para garantir que o foco foi definido
        insert_text(client, TEXT_TO_TYPE)
        print(f'Texto inserido: "{TEXT_TO_TYPE}"')
        time.sleep(1)

        # 2. Encontrar e clicar no botão de enviar
        print("Procurando o botão de enviar...")
        send_button_node_id, send_button_frame_id = find_element_by_selector(client, SEND_BUTTON_SELECTOR)

        if not send_button_node_id:
            print("Botão de enviar não encontrado. Verifique o seletor.")
            return
        
        print("SUCESSO! Botão de enviar encontrado.")
        send_button_box = get_box_model(client, send_button_node_id)
        if not send_button_box or 'content' not in send_button_box:
            print("Não foi possível obter a posição do botão de enviar.")
            return

        quad = send_button_box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)

        click(client, center_x, center_y)
        print("Botão de enviar clicado.")

        print('Teste concluído com sucesso!')

    finally:
        client.close()
        print("Conexão fechada.")


if __name__ == '__main__':
    main()
