import time

def enable_input(client):
    """Habilita o domínio Input no DevTools."""
    client.send('Input.enable')


def click(client, x: int, y: int, click_count: int = 1):
    """Simula um clique esquerdo em (x, y)."""
    client.send('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': x, 'y': y,
        'button': 'left', 'clickCount': click_count
    })
    client.send('Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': x, 'y': y,
        'button': 'left', 'clickCount': click_count
    })
    time.sleep(0.1)


def insert_text(client, text: str):
    """Insere texto no elemento com foco."""
    client.send('Input.insertText', {'text': text})
    time.sleep(0.1)
