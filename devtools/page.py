def enable_page(client):
    """Habilita o domínio Page no DevTools."""
    client.send('Page.enable')


def navigate(client, url: str):
    """Navega para a URL especificada."""
    client.send('Page.navigate', {'url': url})


def get_layout_metrics(client) -> dict:
    """Retorna o resultado de getLayoutMetrics."""
    return client.send('Page.getLayoutMetrics')
