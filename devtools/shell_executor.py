import subprocess
import os
from pathlib import Path

class ShellExecutor:
    """
    Gerencia a execução de comandos diretamente no shell do sistema operacional.
    Atua como a camada de execução para a ACI, substituindo o sandbox Docker.
    """
    def __init__(self, working_directory: str, timeout: int = 300):
        self.working_directory = Path(working_directory).resolve()
        self.timeout = timeout
        self.working_directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Executor de Shell inicializado. Diretório de trabalho: {self.working_directory}")

    def execute_command(self, command: str) -> tuple[int, str, str]:
        """
        Executa um comando de shell de forma segura no diretório de trabalho.
        Args:
            command: A string de comando a ser executada.
        Returns:
            Uma tupla (exit_code, stdout, stderr).
        """
        if not command:
            return -1, "", "Erro: Comando vazio."
        print(f"⚡ Executando comando: '{command}'")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'  # Substitui caracteres inválidos por '?'
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            print(f"  -> Exit Code: {result.returncode}")
            if stdout:
                print(f"  -> Stdout: {stdout[:200]}...")
            if stderr:
                print(f"  -> Stderr: {stderr[:200]}...")
            return result.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Erro: Comando '{command}' excedeu o timeout de {self.timeout} segundos."
        except UnicodeDecodeError as e:
            return -1, "", f"Erro de codificação: {e}. Tente usar um comando que produza saída ASCII."
        except Exception as e:
            return -1, "", f"Erro inesperado ao executar o comando: {e}"
