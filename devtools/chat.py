import time
from .dom import find_element_by_xpath_in_frames, get_outer_html

def monitor_chat_response(client, chat_container_xpath, timeout_seconds=30, poll_interval=0.5, inactivity_timeout=5):
    """
    Monitora um contêiner de chat para capturar e imprimir respostas dinâmicas.

    :param client: O cliente DevTools.
    :param chat_container_xpath: O XPath para o elemento que contém as respostas do chat.
    :param timeout_seconds: O tempo máximo total para esperar por uma resposta.
    :param poll_interval: O intervalo em segundos entre cada verificação.
    :param inactivity_timeout: O tempo em segundos de inatividade de texto para considerar a resposta concluída.
    """
    print("\n--- Iniciando monitoramento do chat ---")
    print(f"Observando o elemento com XPath: ...{chat_container_xpath[-70:]}")

    last_text = ""
    last_change_time = time.time()
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        # Encontra o contêiner do chat a cada iteração para garantir que ele ainda existe
        node_id, frame_id = find_element_by_xpath_in_frames(client, chat_container_xpath)
        
        if not node_id:
            print("AVISO: Não foi possível encontrar o contêiner do chat. A resposta pode ter desaparecido ou a página mudou.")
            time.sleep(poll_interval)
            continue

        # Obtém o texto atual do contêiner
        current_html = get_outer_html(client, node_id)
        # Uma limpeza simples para focar no texto visível, pode ser melhorada
        import re
        current_text = re.sub('<[^<]+?>', '', current_html).strip()

        if current_text != last_text:
            new_text = current_text[len(last_text):].strip()
            if new_text:
                print(f"\n[NOVA RESPOSTA]...\n{new_text}\n...[/NOVA RESPOSTA]")
            
            last_text = current_text
            last_change_time = time.time()
        else:
            # Se não houver mudança, verifica se o tempo de inatividade foi atingido
            if time.time() - last_change_time > inactivity_timeout:
                print("\n--- Monitoramento concluído (inatividade) ---")
                return last_text # Retorna o texto final completo

        time.sleep(poll_interval)

    print("\n--- Monitoramento concluído (timeout geral) ---")
    return last_text
