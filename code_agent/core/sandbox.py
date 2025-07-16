import subprocess
import docker
from typing import List, Dict, Any, Optional
import os


class DockerSandbox:
    """
    Executor de código seguro que usa contêineres Docker para isolar
    o ambiente de execução.
    """

    def __init__(self):
        try:
            """ 
                - Docker (https://docs.docker.com/get-docker/)
                    - O serviço Docker deve estar rodando (`sudo systemctl start docker` ou equivalente)
                    - O usuário deve ter permissão para rodar containers (adicione ao grupo `docker` se necessário)
                - Python package: `docker`
                    - Instale com: `pip install docker` 
            """
            self.client = docker.from_env()
            # Testa se o daemon está acessível
            self.client.ping()
        except Exception as e:
            raise RuntimeError(
                "Docker não está disponível ou não está rodando. "
                "Certifique-se de que o Docker está instalado e o serviço está ativo. "
                f"Detalhes: {e}"
            )

    def execute(
        self,
        command: List[str],
        project_path: str,
        container_config: Optional[str] = None,
        workdir: str = "/app",
        custom_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa um comando dentro de um contêiner Docker.

        Args:
            command: O comando a ser executado (ex: ["pytest"], ["ls", "-la"], etc).
            project_path: O caminho do projeto a ser montado no contêiner.
            container_config: Identificador para a imagem a ser usada (opcional, ex: 'python-3.11-pytest').
            workdir: Diretório de trabalho dentro do contêiner (default: /app)
            custom_image: Imagem personalizada a ser usada (opcional).

        Returns:
            Um dicionário com o resultado da execução.
        """
        if not self.client:
            return {"success": False, "error": "Docker não está disponível."}

        # Permite execução arbitrária, mas define imagens padrão para validação
        image_map = {
            "python-3.11-pytest": "python:3.11-slim",
            "python-3.11": "python:3.11-slim",
            "java-17-maven": "maven:3.9-eclipse-temurin-17",
            "java-17": "eclipse-temurin:17-jdk",
        }
        

        if custom_image:
            image_name = custom_image
        else:
            # Se container_config não for passado, usa python por padrão
            image_name = image_map.get(container_config, "python:3.11-slim")

        try:
            try:
                container = self.client.containers.run(
                    image=image_name,
                    command=command,
                    volumes={os.path.abspath(project_path): {"bind": workdir, "mode": "rw"}},
                    working_dir=workdir,
                    detach=True,
                    stdout=True,
                    stderr=True,
                    tty=False,
                    remove=True
                )
            except docker.errors.ImageNotFound:
                # Faz pull automático da imagem e tenta novamente
                print(f"Imagem '{image_name}' não encontrada localmente. Fazendo pull...")
                self.client.images.pull(image_name)
                container = self.client.containers.run(
                    image=image_name,
                    command=command,
                    volumes={os.path.abspath(project_path): {"bind": workdir, "mode": "rw"}},
                    working_dir=workdir,
                    detach=True,
                    stdout=True,
                    stderr=True,
                    tty=False,
                    remove=True
                )
            result = container.wait()
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8")

            return {
                "success": result["StatusCode"] == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result["StatusCode"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
