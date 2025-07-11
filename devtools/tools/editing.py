from pathlib import Path

def edit_code(file_path: str, changes: list) -> str:
    """
    Aplica mudanças em um arquivo. 'changes' é uma lista de tuplas (linha, novo_conteudo).
    """
    path = Path(file_path)
    if not path.exists():
        return f"Erro: Arquivo '{file_path}' não encontrado."
    try:
        with path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        for line_num, new_content in changes:
            if 0 <= line_num < len(lines):
                lines[line_num] = new_content + '\n'
        with path.open('w', encoding='utf-8') as f:
            f.writelines(lines)
        return "Arquivo editado com sucesso."
    except Exception as e:
        return f"Erro ao editar arquivo: {e}"

def create_file(file_path: str, content: str) -> str:
    path = Path(file_path)
    try:
        with path.open('w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo '{file_path}' criado com sucesso."
    except Exception as e:
        return f"Erro ao criar arquivo: {e}"
