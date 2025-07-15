import os
import shlex
import subprocess
from typing import List, Set

# Assumindo que ShellExecutor existe conforme o seu código
from devtools.shell_executor import ShellExecutor

class ACIOrchestrator:
    """
    Orquestrador otimizado para reduzir o consumo de tokens.
    Filtra saídas verbosas e resume resultados para fornecer
    apenas informações relevantes ao LLM.
    """
    # Diretórios e padrões a serem ignorados para reduzir o ruído.
    IGNORED_DIRS: Set[str] = {
        ".git", "node_modules", "__pycache__", "target", 
        "build", "dist", ".vscode", ".idea"
    }
    # Limite máximo de linhas para saídas de busca para evitar sobrecarga.
    MAX_OUTPUT_LINES: int = 50

    def __init__(self, shell_executor: ShellExecutor):
        self.shell_executor = shell_executor
        self.tools = {
            "list_files": self._execute_list_files,
            "search_dir": self._execute_search_dir,
            "run_test": self._execute_run_test,
            # Ferramentas que não usam shell podem ser adicionadas aqui
            # "open_file": self._execute_open_file,
            # "edit_code": self._execute_edit_code,
        }

    def run_test_in_container(self, test_command: str, container_config: str = "default"):
        """
        Executes a test command in a specified Docker container.
        This assumes pre-built Docker images are available.
        """
        print(f"📦 Attempting to run tests with command '{test_command}' using config '{container_config}'...")

        # This is a mapping from a simple config name to a full Docker image name.
        # In a real setup, these images would be pre-built and stored in a registry.
        image_map = {
            "java-maven": "my-registry/java-maven-runner:latest",
            "nodejs-18": "my-registry/nodejs-18-runner:latest",
            "python-3.9": "my-registry/python-3.9-runner:latest",
            "default": "my-registry/generic-runner:latest"
        }
        
        docker_image = image_map.get(container_config, image_map["default"])

        # The project directory is mounted into the container's working directory.
        # This gives the container access to the code.
        project_path = self.shell_executor.working_directory
        volume_mount = f"-v {os.path.abspath(project_path)}:/app"

        # Construct the full docker run command.
        # --rm cleans up the container after it exits.
        # -w sets the working directory inside the container.
        docker_command = [
            "docker", "run", "--rm",
            volume_mount,
            "-w", "/app",
            docker_image,
            "/bin/sh", "-c", test_command # Execute the command in a shell
        ]

        try:
            result = subprocess.run(docker_command, capture_output=True, text=True, timeout=300)

            output = f"--- DOCKER EXECUTION REPORT ---\n"
            output += f"COMMAND: {' '.join(docker_command)}\n"
            output += f"EXIT CODE: {result.returncode}\n"

            if result.returncode == 0:
                output += "STATUS: SUCCESS\n"
            else:
                output += "STATUS: FAILED\n"

            output += f"\n--- STDOUT ---\n{result.stdout}\n"
            if result.stderr:
                output += f"\n--- STDERR ---\n{result.stderr}\n"

            return output

        except FileNotFoundError:
            return "Error: 'docker' command not found. Is Docker installed and in the system's PATH?"
        except Exception as e:
            return f"An unexpected error occurred while running Docker: {e}"

    def dispatch_command(self, command: str, args: list) -> str:
        """Despacha um comando para o handler correspondente."""
        if command not in self.tools:
            return f"Erro: Comando '{command}' não encontrado."
        
        handler = self.tools[command]
        try:
            print(f"Orquestrador despachando '{command}' com args: {args}")
            result = handler(*args)
            return str(result)
        except TypeError as e:
            return f"Erro: Argumentos inválidos para o comando '{command}'. Detalhes: {e}"
        except Exception as e:
            return f"Erro inesperado ao executar '{command}': {e}"

    def _execute_list_files(self, path: str = ".", recursive: bool = False) -> str:
        """
        Lista arquivos e diretórios, ignorando diretórios irrelevantes
        para reduzir drasticamente a contagem de tokens.
        """
        try:
            if recursive:
                file_list = []
                for root, dirs, files in os.walk(path, topdown=True):
                    # Filtra os diretórios a serem ignorados
                    dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
                    
                    for name in files:
                        file_list.append(os.path.join(root, name))
                
                return "\n".join(sorted(file_list)) if file_list else "Nenhum arquivo encontrado (após filtragem)."
            else:
                # O comando 'ls' não recursivo geralmente não é muito verboso.
                cmd_str = f"ls -F {shlex.quote(path)}"
                exit_code, stdout, stderr = self.shell_executor.execute_command(cmd_str)
                return stdout if exit_code == 0 else f"Erro na execução: {stderr}"
        except Exception as e:
            return f"Erro ao listar arquivos: {e}"

    def _execute_search_dir(self, query: str, path: str = ".") -> str:
        """
        Busca em arquivos, mas ignora diretórios irrelevantes e limita
        o tamanho da saída para economizar tokens.
        """
        # Constrói um comando 'find' para listar arquivos, excluindo diretórios ignorados
        path_filter = ""
        for ignored_dir in self.IGNORED_DIRS:
            path_filter += f" -not -path '*/{ignored_dir}/*'"

        # Usa 'grep' para buscar nos arquivos encontrados pelo 'find'
        # -I ignora arquivos binários
        cmd_str = f"find {shlex.quote(path)} -type f {path_filter} | xargs grep -I -n {shlex.quote(query)}"
        
        exit_code, stdout, stderr = self.shell_executor.execute_command(cmd_str)

        if exit_code == 0:
            lines = stdout.strip().split('\n')
            if len(lines) > self.MAX_OUTPUT_LINES:
                # Trunca a saída e informa o LLM
                truncated_output = "\n".join(lines[:self.MAX_OUTPUT_LINES])
                return (f"Resultado da busca (exibindo as primeiras {self.MAX_OUTPUT_LINES} de {len(lines)} linhas):\n"
                        f"{truncated_output}\n"
                        f"[AVISO] A saída foi truncada. Refine sua busca se necessário.")
            return stdout
        elif exit_code == 1: # grep retorna 1 quando não encontra nada
            return "Nenhum resultado encontrado."
        else:
            # Retorna o erro, que geralmente é curto
            return f"Erro na execução da busca: {stderr}"

    def _execute_run_test(self, test_command: str) -> str:
        """
        Executa testes e retorna um resumo inteligente, não o log completo,
        para economizar uma quantidade massiva de tokens.
        """
        # Validação de segurança básica
        allowed_commands = ["mvn", "npm", "gradle", "pytest", "go test"]
        if not any(test_command.startswith(cmd) for cmd in allowed_commands):
            return "Erro de segurança: Comando de teste não permitido."

        exit_code, stdout, stderr = self.shell_executor.execute_command(test_command)

        if exit_code == 0:
            # Se os testes passaram, retorne uma mensagem simples e concisa.
            # O LLM não precisa do log de sucesso completo.
            return "SUCESSO: Todos os testes passaram."
        else:
            # Se falhou, extraia apenas as partes mais importantes do erro.
            full_log = f"--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}"
            lines = full_log.split('\n')
            
            # Filtra por palavras-chave que indicam o erro real.
            error_keywords = ["FAIL", "ERROR", "FAILURE", "failed", "Exception", "Traceback"]
            error_summary = [line for line in lines if any(kw in line for kw in error_keywords)]
            
            if not error_summary: # Se nenhuma palavra-chave for encontrada, retorne o log truncado
                summary = (f"FALHA: Testes falharam com exit code {exit_code}.\n"
                           f"Resumo do log (últimas 20 linhas):\n"
                           f"{'\n'.join(lines[-20:])}")
            else:
                 summary = (f"FALHA: Testes falharam com exit code {exit_code}.\n"
                           f"Resumo dos erros encontrados:\n"
                           f"{'\n'.join(error_summary)}")

            return summary[:3000] # Garante um limite máximo para o resumo do erro.