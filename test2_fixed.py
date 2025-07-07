import json
from urllib.request import urlopen
import time

from devtools.client import DevToolsClient
from devtools.dom import get_document, query_selector, get_box_model, enable_dom, find_element_by_xpath_in_frames, save_page_html, find_first_textarea
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
    # Use a URL base da página que você abriu manualmente
    TARGET_URL = 'https://vscode.dev'
    # XPath como fallback (caso a busca DOM direta falhe)
    XPATH_SELECTOR = "(//textarea)[1]"
    
    TEXT_TO_TYPE = "Olá, automação via busca DOM direta!"
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

        # PRIMEIRO: Salvar o HTML da página para análise
        print("Salvando HTML da página para análise...")
        save_page_html(client, "vscode_debug.html")
        print("HTML salvo! Abra o arquivo 'vscode_debug.html' no navegador para ver o que o sistema enxerga.")

        # NOVA ABORDAGEM: Busca direta no DOM sem JavaScript
        print("Tentando nova abordagem: busca direta no DOM...")
        node_id, frame_id = find_first_textarea(client)
        
        if node_id:
            print(f"SUCESSO! Textarea encontrado via busca DOM direta!")
            print(f"NodeId: {node_id}, FrameId: {frame_id}")
        else:
            print("Nenhum textarea encontrado via busca DOM direta.")
            print("Tentando abordagem XPath como fallback...")
            
            # Fallback para XPath (código original)
            for i in range(3): # Apenas 3 tentativas para o fallback
                node_id, frame_id = find_element_by_xpath_in_frames(client, XPATH_SELECTOR)
                if node_id:
                    break
                print(f"Tentativa XPath {i+1}/3: Elemento ainda não encontrado, aguardando 1s...")
                time.sleep(1)

        if not node_id:
            print('Elemento não encontrado após várias tentativas.')
            print('Verifique o arquivo vscode_debug.html para análise manual.')
            return

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
        time.sleep(1)

        print('Teste concluído com sucesso!')

    finally:
        client.close()
        print("Conexão fechada.")


if __name__ == '__main__':
    main()
