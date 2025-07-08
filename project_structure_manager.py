"""
Gerenciador de Estrutura do Projeto Migrado
Organiza o código gerado em uma estrutura de diretórios apropriada
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class FileMetadata:
    """Metadados de um arquivo gerado"""
    file_path: str
    component: str
    layer: str  # presentation, business, data, etc.
    technology: str  # java, python, typescript, etc.
    dependencies: List[str]
    description: str
    task_index: int
    generated_at: str

class ProjectStructureManager:
    """Gerencia a estrutura do projeto migrado"""
    
    def __init__(self, output_base_dir: str):
        self.output_base_dir = Path(output_base_dir)
        self.new_system_dir = self.output_base_dir / "new_system"
        self.structure_config_file = self.output_base_dir / "project_structure.json"
        self.files_metadata = {}
        
        self._ensure_directories()
        self._load_or_create_structure_config()
    
    def _ensure_directories(self):
        """Cria diretórios base se não existirem"""
        self.output_base_dir.mkdir(exist_ok=True)
        self.new_system_dir.mkdir(exist_ok=True)
    
    def _load_or_create_structure_config(self):
        """Carrega ou cria configuração da estrutura do projeto"""
        if self.structure_config_file.exists():
            with open(self.structure_config_file, 'r', encoding='utf-8') as f:
                self.structure_config = json.load(f)
        else:
            self.structure_config = self._create_default_structure()
            self._save_structure_config()
    
    def _create_default_structure(self) -> Dict:
        """Cria estrutura padrão baseada em melhores práticas"""
        return {
            "project_name": "migrated_system",
            "architecture_type": "microservices",  # será atualizado baseado na análise
            "technology_stack": {
                "backend": "java_spring",
                "frontend": "react",
                "database": "postgresql",
                "infrastructure": "docker_kubernetes"
            },
            "directory_structure": {
                "backend": {
                    "path": "backend",
                    "subdirs": {
                        "src/main/java/com/company/app": "Main application code",
                        "src/main/java/com/company/app/controller": "REST controllers",
                        "src/main/java/com/company/app/service": "Business logic",
                        "src/main/java/com/company/app/repository": "Data access layer",
                        "src/main/java/com/company/app/model": "Domain models",
                        "src/main/java/com/company/app/config": "Configuration classes",
                        "src/main/java/com/company/app/dto": "Data transfer objects",
                        "src/main/java/com/company/app/exception": "Custom exceptions",
                        "src/test/java": "Unit and integration tests",
                        "src/main/resources": "Configuration files and resources"
                    }
                },
                "frontend": {
                    "path": "frontend",
                    "subdirs": {
                        "src": "Source code",
                        "src/components": "React components",
                        "src/pages": "Page components",
                        "src/services": "API services",
                        "src/utils": "Utility functions",
                        "src/hooks": "Custom React hooks",
                        "src/context": "React context providers",
                        "src/types": "TypeScript type definitions",
                        "src/assets": "Static assets",
                        "public": "Public files"
                    }
                },
                "database": {
                    "path": "database",
                    "subdirs": {
                        "migrations": "Database migration scripts",
                        "seeds": "Initial data scripts",
                        "schemas": "Database schema definitions"
                    }
                },
                "infrastructure": {
                    "path": "infrastructure",
                    "subdirs": {
                        "docker": "Docker configurations",
                        "kubernetes": "Kubernetes manifests",
                        "scripts": "Deployment and utility scripts",
                        "monitoring": "Monitoring configurations"
                    }
                },
                "docs": {
                    "path": "docs",
                    "subdirs": {
                        "api": "API documentation",
                        "architecture": "Architecture documentation",
                        "deployment": "Deployment guides"
                    }
                }
            }
        }
    
    def _save_structure_config(self):
        """Salva configuração da estrutura"""
        with open(self.structure_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.structure_config, f, indent=4, ensure_ascii=False)
    
    def update_structure_from_target_architecture(self, target_architecture_content: str):
        """Atualiza estrutura baseada na arquitetura alvo definida na Fase 3"""
        # Aqui você pode implementar parsing do conteúdo da arquitetura alvo
        # Por enquanto, vamos fazer uma implementação básica
        
        if "microservices" in target_architecture_content.lower():
            self.structure_config["architecture_type"] = "microservices"
            self._add_microservices_structure()
        elif "monolith" in target_architecture_content.lower():
            self.structure_config["architecture_type"] = "monolith"
        
        # Detecta tecnologias mencionadas
        if "spring boot" in target_architecture_content.lower():
            self.structure_config["technology_stack"]["backend"] = "java_spring"
        elif "node.js" in target_architecture_content.lower():
            self.structure_config["technology_stack"]["backend"] = "nodejs"
        elif "python" in target_architecture_content.lower():
            self.structure_config["technology_stack"]["backend"] = "python_fastapi"
        
        self._save_structure_config()
        self._create_directory_structure()
    
    def _add_microservices_structure(self):
        """Adiciona estrutura específica para microserviços"""
        microservices = {
            "user-service": "User management microservice",
            "product-service": "Product catalog microservice", 
            "order-service": "Order processing microservice",
            "notification-service": "Notification microservice",
            "api-gateway": "API Gateway service"
        }
        
        for service_name, description in microservices.items():
            self.structure_config["directory_structure"][service_name] = {
                "path": f"services/{service_name}",
                "description": description,
                "subdirs": {
                    "src/main/java/com/company/" + service_name.replace("-", ""): "Main service code",
                    "src/main/resources": "Configuration files",
                    "src/test/java": "Tests",
                    "Dockerfile": "Docker configuration"
                }
            }
    
    def _create_directory_structure(self):
        """Cria toda a estrutura de diretórios baseada na configuração"""
        for component, config in self.structure_config["directory_structure"].items():
            component_path = self.new_system_dir / config["path"]
            component_path.mkdir(parents=True, exist_ok=True)
            
            if "subdirs" in config:
                for subdir, description in config["subdirs"].items():
                    subdir_path = component_path / subdir
                    subdir_path.mkdir(parents=True, exist_ok=True)
                    
                    # Cria arquivo README em cada diretório
                    readme_path = subdir_path / "README.md"
                    if not readme_path.exists():
                        readme_content = f"# {subdir}\n\n{description}\n"
                        readme_path.write_text(readme_content, encoding='utf-8')
    
    def determine_file_location(self, code_content: str, code_language: str, 
                              component_hint: str = "", task_description: str = "") -> tuple:
        """Determina onde um arquivo deve ser colocado baseado no conteúdo e contexto"""
        
        # Análise baseada na linguagem
        if code_language.lower() == "java":
            return self._determine_java_location(code_content, component_hint, task_description)
        elif code_language.lower() in ["javascript", "typescript", "jsx", "tsx"]:
            return self._determine_frontend_location(code_content, component_hint, task_description)
        elif code_language.lower() == "sql":
            return self._determine_database_location(code_content, component_hint, task_description)
        elif code_language.lower() in ["yaml", "yml"]:
            return self._determine_infrastructure_location(code_content, component_hint, task_description)
        else:
            return self._determine_generic_location(code_content, code_language, component_hint)
    
    def _determine_java_location(self, code_content: str, component_hint: str, task_description: str) -> tuple:
        """Determina localização para código Java"""
        base_path = "backend/src/main/java/com/company/app"
        
        if "@RestController" in code_content or "@Controller" in code_content:
            return (f"{base_path}/controller", "controller")
        elif "@Service" in code_content:
            return (f"{base_path}/service", "service")
        elif "@Repository" in code_content:
            return (f"{base_path}/repository", "repository")
        elif "@Entity" in code_content or "class" in code_content and "Model" in code_content:
            return (f"{base_path}/model", "model")
        elif "@Configuration" in code_content:
            return (f"{base_path}/config", "config")
        elif "DTO" in code_content or "Request" in code_content or "Response" in code_content:
            return (f"{base_path}/dto", "dto")
        elif "Exception" in code_content:
            return (f"{base_path}/exception", "exception")
        elif "@Test" in code_content or "Test" in code_content:
            return ("backend/src/test/java", "test")
        else:
            return (f"{base_path}", "main")
    
    def _determine_frontend_location(self, code_content: str, component_hint: str, task_description: str) -> tuple:
        """Determina localização para código frontend"""
        base_path = "frontend/src"
        
        if "component" in task_description.lower() or "Component" in code_content:
            return (f"{base_path}/components", "component")
        elif "page" in task_description.lower() or "Page" in code_content:
            return (f"{base_path}/pages", "page")
        elif "service" in task_description.lower() or "api" in task_description.lower():
            return (f"{base_path}/services", "service")
        elif "hook" in task_description.lower() or "useHook" in code_content:
            return (f"{base_path}/hooks", "hook")
        elif "context" in task_description.lower() or "Context" in code_content:
            return (f"{base_path}/context", "context")
        elif "interface" in code_content or "type" in code_content:
            return (f"{base_path}/types", "type")
        else:
            return (f"{base_path}/utils", "util")
    
    def _determine_database_location(self, code_content: str, component_hint: str, task_description: str) -> tuple:
        """Determina localização para código SQL/Database"""
        if "CREATE TABLE" in code_content or "ALTER TABLE" in code_content:
            return ("database/migrations", "migration")
        elif "INSERT INTO" in code_content:
            return ("database/seeds", "seed")
        else:
            return ("database/schemas", "schema")
    
    def _determine_infrastructure_location(self, code_content: str, component_hint: str, task_description: str) -> tuple:
        """Determina localização para arquivos de infraestrutura"""
        if "apiVersion: apps/v1" in code_content or "kind: Deployment" in code_content:
            return ("infrastructure/kubernetes", "k8s")
        elif "docker" in task_description.lower():
            return ("infrastructure/docker", "docker")
        else:
            return ("infrastructure/scripts", "script")
    
    def _determine_generic_location(self, code_content: str, code_language: str, component_hint: str) -> tuple:
        """Determina localização genérica"""
        return (f"misc/{code_language}", "misc")
    
    def save_generated_file(self, code_content: str, code_language: str, task_index: int,
                          task_description: str, component_hint: str = "") -> str:
        """Salva arquivo gerado na localização apropriada"""
        
        # Determina localização
        relative_path, file_type = self.determine_file_location(
            code_content, code_language, component_hint, task_description
        )
        
        # Gera nome do arquivo
        file_name = self._generate_file_name(code_content, code_language, file_type, task_index)
        
        # Caminho completo
        full_dir_path = self.new_system_dir / relative_path
        full_dir_path.mkdir(parents=True, exist_ok=True)
        
        full_file_path = full_dir_path / file_name
        
        # Salva arquivo
        full_file_path.write_text(code_content, encoding='utf-8')
        
        # Registra metadados
        metadata = FileMetadata(
            file_path=str(full_file_path.relative_to(self.new_system_dir)),
            component=component_hint or "unknown",
            layer=file_type,
            technology=code_language,
            dependencies=[],  # pode ser melhorado para extrair dependências
            description=task_description[:100] + "..." if len(task_description) > 100 else task_description,
            task_index=task_index,
            generated_at=__import__('datetime').datetime.now().isoformat()
        )
        
        self.files_metadata[str(full_file_path)] = metadata
        self._save_files_metadata()
        
        return str(full_file_path)
    
    def _generate_file_name(self, code_content: str, code_language: str, file_type: str, task_index: int) -> str:
        """Gera nome apropriado para o arquivo"""
        
        # Tenta extrair nome de classe/componente do código
        class_name = self._extract_class_name(code_content, code_language)
        
        if class_name:
            base_name = class_name
        else:
            base_name = f"Task{task_index}_{file_type.title()}"
        
        # Extensão baseada na linguagem
        extensions = {
            "java": ".java",
            "javascript": ".js",
            "typescript": ".ts",
            "jsx": ".jsx",
            "tsx": ".tsx",
            "python": ".py",
            "sql": ".sql",
            "yaml": ".yml",
            "yml": ".yml",
            "json": ".json",
            "html": ".html",
            "css": ".css",
            "scss": ".scss"
        }
        
        extension = extensions.get(code_language.lower(), ".txt")
        return f"{base_name}{extension}"
    
    def _extract_class_name(self, code_content: str, code_language: str) -> Optional[str]:
        """Extrai nome da classe/componente do código"""
        import re
        
        if code_language.lower() == "java":
            match = re.search(r'class\s+(\w+)', code_content)
            if match:
                return match.group(1)
        elif code_language.lower() in ["javascript", "typescript", "jsx", "tsx"]:
            # Tenta encontrar componente React
            match = re.search(r'(?:function|const)\s+(\w+)', code_content)
            if match:
                return match.group(1)
        
        return None
    
    def _save_files_metadata(self):
        """Salva metadados dos arquivos"""
        metadata_file = self.output_base_dir / "files_metadata.json"
        metadata_dict = {k: asdict(v) for k, v in self.files_metadata.items()}
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4, ensure_ascii=False)
    
    def generate_project_summary(self) -> str:
        """Gera resumo do projeto gerado"""
        summary = f"""# Resumo do Projeto Migrado

## Estrutura Geral
- **Arquitetura:** {self.structure_config['architecture_type']}
- **Tecnologias:** {', '.join(self.structure_config['technology_stack'].values())}
- **Total de arquivos gerados:** {len(self.files_metadata)}

## Arquivos por Camada
"""
        
        files_by_layer = {}
        for metadata in self.files_metadata.values():
            layer = metadata.layer
            if layer not in files_by_layer:
                files_by_layer[layer] = []
            files_by_layer[layer].append(metadata)
        
        for layer, files in files_by_layer.items():
            summary += f"\n### {layer.title()} ({len(files)} arquivos)\n"
            for file_meta in files:
                summary += f"- `{file_meta.file_path}` - {file_meta.description}\n"
        
        return summary
    
    def get_structure_overview(self) -> str:
        """Retorna visão geral da estrutura criada"""
        overview = "📁 Estrutura do Novo Sistema:\n\n"
        
        for root, dirs, files in os.walk(self.new_system_dir):
            level = root.replace(str(self.new_system_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            folder_name = os.path.basename(root)
            if folder_name:
                overview += f"{indent}📂 {folder_name}/\n"
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if not file.startswith('.'):
                    overview += f"{subindent}📄 {file}\n"
        
        return overview
