from pathlib import Path

def open_file(file_path: str, window_start: int = 0, window_size: int = 50) -> str:
    """
    Lê um arquivo e retorna uma janela de linhas (paginado).
    """
    path = Path(file_path)
    if not path.exists():
        return f"Erro: Arquivo '{file_path}' não encontrado."
    try:
        with path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        end = min(window_start + window_size, len(lines))
        window = lines[window_start:end]
        return ''.join(window)
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"
