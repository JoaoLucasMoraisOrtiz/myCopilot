
import json
from urllib.request import urlopen
import time

from devtools.client import DevToolsClient
from devtools.dom import get_box_model, enable_dom, find_first_element, find_element_by_selector
from devtools.page import enable_page
from devtools.input import enable_input, click, insert_text
from devtools.chat import monitor_chat_response

def get_debug_url(filter_url: str = None):
    """Busca o URL de depuração de uma aba que corresponda a filter_url."""
    try:
        with urlopen('http://localhost:9222/json') as response:
            tabs = json.load(response)
            if filter_url:
                for tab in tabs:
                    if tab.get('type') == 'page' and tab.get('url', '').startswith(filter_url):
                        return tab['webSocketDebuggerUrl']
            for tab in tabs:
                if tab.get('type') == 'page':
                    return tab['webSocketDebuggerUrl']
    except Exception as e:
        print(f'Erro ao obter URL de depuração: {e}')
    return None

def main():
    # --- CONFIGURAÇÃO ---
    TARGET_URL = 'https://vscode.dev'
    TEXT_TO_TYPE = "Crie uma API em Python usando Flask que tenha um endpoint /hello e retorne 'Olá, Mundo!'. Retorne apenas o código."
    SEND_BUTTON_SELECTOR = '#workbench\\.panel\\.chat > div > div > div.monaco-scrollable-element > div.split-view-container > div > div > div.pane-body > div.interactive-session > div.interactive-input-part > div.interactive-input-and-side-toolbar > div > div.chat-input-toolbars > div.monaco-toolbar.chat-execute-toolbar > div > ul > li.action-item.monaco-dropdown-with-primary > div.action-container.menu-entry > a'
    CHAT_CONTAINER_XPATH = '//*[@id="workbench.panel.chat"]/div/div/div[2]/div[1]/div/div/div[2]/div[2]/div[2]/div[2]/div'
    # --------------------

    debug_url = get_debug_url(TARGET_URL)
    if not debug_url:
        print('URL de depuração não encontrado. Verifique se o Chrome está rodando e a aba correta está aberta.')
        return

    print(f'Conectando ao DevTools em: {debug_url}')
    client = DevToolsClient(debug_url)

    try:
        # 1. Habilitar domínios e encontrar o campo de texto
        enable_page(client)
        enable_dom(client)
        enable_input(client)
        
        print("Buscando o campo de texto (textarea)...")
        node_id, frame_id = find_first_element(client, 'textarea')
        if not node_id:
            print('Textarea não encontrado.')
            return
        print("Textarea encontrado!")

        # 2. Clicar, limpar e inserir o texto da pergunta
        box = get_box_model(client, node_id)
        quad = box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
        click(client, center_x, center_y)
        time.sleep(0.5)
        insert_text(client, TEXT_TO_TYPE)
        print(f'Pergunta enviada: "{TEXT_TO_TYPE[:50]}..."')
        time.sleep(1)

        # 3. Encontrar e clicar no botão de enviar
        print("Buscando o botão de enviar...")
        send_button_node_id, _ = find_element_by_selector(client, SEND_BUTTON_SELECTOR)
        if not send_button_node_id:
            print("Botão de enviar não encontrado.")
            return
        
        send_button_box = get_box_model(client, send_button_node_id)
        quad = send_button_box['content']
        center_x = int(quad[0] + (quad[2] - quad[0]) / 2)
        center_y = int(quad[1] + (quad[5] - quad[1]) / 2)
        click(client, center_x, center_y)
        print("Botão de enviar clicado.")

        # 4. Monitorar o chat para capturar a resposta
        final_response = monitor_chat_response(client, CHAT_CONTAINER_XPATH)

        print("\n--- RESPOSTA FINAL CAPTURADA ---")
        print(final_response)
        print("----------------------------------")

        print('\nProcesso concluído com sucesso!')

    finally:
        client.close()
        print("Conexão fechada.")

if __name__ == '__main__':
    main()
