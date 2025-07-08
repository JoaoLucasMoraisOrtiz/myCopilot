import time

def enable_input(client):
    """Habilita o domínio Input no DevTools."""
    client.send('Input.enable')


def click(client, x: int, y: int, click_count: int = 1):
    """Simula um clique esquerdo em (x, y) de forma correta."""
    # 1. Pressiona o botão do mouse
    client.send('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': x,
        'y': y,
        'button': 'left',
        'clickCount': click_count
    })
    time.sleep(0.1)  # Aguarda um pouco para simular o clique
    # 2. Solta o botão do mouse para completar o clique
    client.send('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', # <-- A correção está aqui
        'x': x,
        'y': y,
        'button': 'left',
        'clickCount': click_count
    })


def insert_text(client, text: str):
    """Insere texto no elemento com foco."""
    client.send('Input.insertText', {'text': text})
    time.sleep(0.1)
