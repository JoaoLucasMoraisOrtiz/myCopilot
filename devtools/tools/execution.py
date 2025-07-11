from devtools.shell_executor import ShellExecutor

def run_test(shell_executor: ShellExecutor, test_command: str) -> str:
    if not test_command.startswith(("mvn", "npm", "gradle")):
        return "Erro de segurança: Comando de teste não permitido."
    exit_code, stdout, stderr = shell_executor.execute_command(test_command)
    if exit_code == 0:
        return f"Teste bem-sucedido:\n{stdout}"
    else:
        return f"Teste falhou (exit code {exit_code}):\n{stdout}\n--- ERROS ---\n{stderr}"

def run_script(shell_executor: ShellExecutor, script_path: str) -> str:
    exit_code, stdout, stderr = shell_executor.execute_command(f"bash {script_path}")
    if exit_code == 0:
        return f"Script executado com sucesso:\n{stdout}"
    else:
        return f"Script falhou (exit code {exit_code}):\n{stdout}\n--- ERROS ---\n{stderr}"

def submit(patch_info: str) -> str:
    # Simples placeholder para submissão
    return f"Patch submetido: {patch_info}"
