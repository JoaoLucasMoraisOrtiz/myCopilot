import subprocess
import docker
from typing import List, Dict, Any


class DockerSandbox:
    """
    Executor de código seguro que usa contêineres Docker para isolar
    o ambiente de execução.
    """

    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException:
            print("Erro: O Docker não parece estar em execução. O sandbox não funcionará.")
            self.client = None

    def execute(
        self, command: List[str], project_path: str, container_config: str
    ) -> Dict[str, Any]:
        """
        Executa um comando dentro de um contêiner Docker.

        Args:
            command: O comando a ser executado.
            project_path: O caminho do projeto a ser montado no contêiner.
            container_config: Identificador para a imagem a ser usada (ex: 'python-3.11-pytest').

        Returns:
            Um dicionário com o resultado da execução.
        """
        if not self.client:
            return {"success": False, "error": "Docker não está disponível."}

        image_map = {
            "python-3.11-pytest": "python:3.11-slim",
            "java-17-maven": "maven:3.9-eclipse-temurin-17",
        }
        image_name = image_map.get(container_config)

        if not image_name:
            return {"success": False, "error": f"Configuração de contêiner desconhecida: {container_config}"}

        try:
            container = self.client.containers.run(
                image=image_name,
                command=command,
                volumes={project_path: {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=True,
            )
            result = container.wait()
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
            container.remove()

            return {
                "success": result["StatusCode"] == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result["StatusCode"],
            }
        except docker.errors.ImageNotFound:
             return {"success": False, "error": f"A imagem Docker '{image_name}' não foi encontrada. Por favor, puxe-a."}
        except Exception as e:
            return {"success": False, "error": str(e)}
