import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
import sys
import os

# Adiciona o diretório pai ao path para importar code_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_analyzer import LanguageAnalyzer, CodeElement

class JavaAnalyzer(LanguageAnalyzer):
    """Analisador específico para projetos Java."""
    
    def __init__(self, project_dir: Path):
        super().__init__(project_dir)
        self.java_packages = {}  # package -> [arquivos]
        self.maven_dependencies = []  # dependências do Maven
        self.gradle_dependencies = []  # dependências do Gradle
        self._structure_analyzed = False
    
    def get_file_extensions(self) -> List[str]:
        return ['.java', '.kt', '.scala']
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extrai imports Java de um arquivo."""
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex para imports Java
            import_pattern = r'import\s+(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*(?:\.\*)?)\s*;'
            matches = re.findall(import_pattern, content)
            
            for import_name in matches:
                # Remove .* se presente
                clean_import = import_name.replace('.*', '')
                deps.append(clean_import)
                
        except Exception:
            pass  # Ignora erros de parsing
        
        return deps
    
    def analyze_project_structure(self) -> Dict:
        """Analisa estrutura de projeto Java (Maven/Gradle)."""
        if not self._structure_analyzed:
            print("☕ Analisando estrutura do projeto Java...")
            
            # Procura por pom.xml (Maven)
            pom_files = list(self.project_dir.rglob('pom.xml'))
            for pom_file in pom_files:
                self._parse_maven_pom(pom_file)
            
            # Procura por build.gradle (Gradle)
            gradle_files = list(self.project_dir.rglob('build.gradle*'))
            for gradle_file in gradle_files:
                self._parse_gradle_build(gradle_file)
            
            # Mapeia pacotes Java
            java_files = list(self.project_dir.rglob('*.java'))
            for java_file in java_files:
                package = self._extract_java_package(java_file)
                if package:
                    if package not in self.java_packages:
                        self.java_packages[package] = []
                    self.java_packages[package].append(str(java_file))
            
            self._structure_analyzed = True
        
        return {
            'maven_dependencies': self.maven_dependencies,
            'gradle_dependencies': self.gradle_dependencies,
            'java_packages': self.java_packages
        }
    
    def _parse_maven_pom(self, pom_file: Path):
        """Extrai dependências do pom.xml."""
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Namespace do Maven
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            dependencies = root.findall('.//maven:dependency', ns)
            for dep in dependencies:
                group_id = dep.find('maven:groupId', ns)
                artifact_id = dep.find('maven:artifactId', ns)
                version = dep.find('maven:version', ns)
                
                if group_id is not None and artifact_id is not None:
                    dep_info = {
                        'groupId': group_id.text,
                        'artifactId': artifact_id.text,
                        'version': version.text if version is not None else 'unknown',
                        'type': 'maven',
                        'name': f"{group_id.text}:{artifact_id.text}"
                    }
                    self.maven_dependencies.append(dep_info)
                    
        except Exception as e:
            print(f"⚠️ Erro ao parsear {pom_file}: {e}")
    
    def _parse_gradle_build(self, gradle_file: Path):
        """Extrai dependências do build.gradle."""
        try:
            with open(gradle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex para encontrar dependências
            dep_pattern = r'(?:implementation|compile|testImplementation|api)\s+[\'"]([^:]+):([^:]+):([^\'"]+)[\'"]'
            matches = re.findall(dep_pattern, content)
            
            for group_id, artifact_id, version in matches:
                dep_info = {
                    'groupId': group_id,
                    'artifactId': artifact_id,
                    'version': version,
                    'type': 'gradle',
                    'name': f"{group_id}:{artifact_id}"
                }
                self.gradle_dependencies.append(dep_info)
                
        except Exception as e:
            print(f"⚠️ Erro ao parsear {gradle_file}: {e}")
    
    def _extract_java_package(self, java_file: Path) -> str:
        """Extrai o nome do pacote de um arquivo Java."""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            package_match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;', content)
            return package_match.group(1) if package_match else ""
            
        except Exception:
            return ""
    
    def build_analysis_prompt(self, file_path: str, content: str, context: str, external_deps: str) -> str:
        """Constrói prompt específico para análise de arquivos Java."""
        return f"""
Analise o arquivo Java abaixo e descreva CADA elemento (classe, interface, enum, método, campo, etc.) de forma concisa mas completa.

**CONTEXTO DAS DEPENDÊNCIAS:**
{context}

**DEPENDÊNCIAS MAVEN/GRADLE:**
{external_deps}

**ARQUIVO: {file_path}**
```java
{content}
```

**INSTRUÇÕES ESPECÍFICAS PARA JAVA:**
Para cada elemento encontrado, forneça:

1. **CLASSES:** Nome, propósito, herança/implementações, principais métodos
2. **INTERFACES:** Nome, propósito, métodos declarados
3. **ENUMS:** Nome, propósito, valores principais
4. **MÉTODOS:** Nome, parâmetros, retorno, modificadores de acesso, o que faz
5. **CAMPOS/ATRIBUTOS:** Nome, tipo, modificadores, propósito
6. **IMPORTS:** O que importa e para que é usado
7. **ANNOTATIONS:** Quais são usadas e onde

**FORMATO DE RESPOSTA:**
```
CLASSE: NomeClasse extends SuperClasse implements Interface
Modificadores: public/private/protected, abstract/final
Descrição: Propósito da classe...
Métodos principais: metodo1, metodo2...
Campos principais: campo1, campo2...

INTERFACE: NomeInterface extends SuperInterface
Descrição: Propósito da interface...
Métodos declarados: metodo1, metodo2...

ENUM: NomeEnum
Descrição: Propósito do enum...
Valores: VALOR1, VALOR2...

MÉTODO: modificador tipoRetorno nomeMetodo(parametros)
Descrição: O que o método faz...
Annotations: @Override, @Deprecated...

CAMPO: modificador Tipo nomeCampo
Descrição: Para que serve...
Annotations: @Autowired, @Column...

IMPORT: pacote.Classe
Uso: Como é usado no código...
```

Seja preciso e inclua informações sobre modificadores de acesso, herança, annotations e padrões de design utilizados.
"""
    
    def parse_analysis_response(self, file_path: str, response: str) -> Dict[str, CodeElement]:
        """Parser robusto usando regex para respostas de análise Java."""
        import re
        
        elements = {}
        
        # Padrões regex para diferentes tipos de elementos Java
        patterns = {
            'class': r'CLASSE:\s*([^\n]+)\n(?:.*?\n)*?(?:Descrição:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)',
            'interface': r'INTERFACE:\s*([^\n]+)\n(?:.*?\n)*?(?:Descrição:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)',
            'enum': r'ENUM:\s*([^\n]+)\n(?:.*?\n)*?(?:Descrição:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)',
            'method': r'MÉTODO:\s*([^\n]+)\n(?:.*?\n)*?(?:Descrição:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)',
            'field': r'CAMPO:\s*([^\n]+)\n(?:.*?\n)*?(?:Descrição:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)',
            'import': r'IMPORT:\s*([^\n]+)\n(?:.*?\n)*?(?:Uso:\s*([^\n]+(?:\n(?!CLASSE:|INTERFACE:|ENUM:|MÉTODO:|CAMPO:|IMPORT:)[^\n]*)*)?)'
        }
        
        for element_type, pattern in patterns.items():
            matches = re.finditer(pattern, response, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                signature_part = match.group(1).strip()
                description_part = match.group(2).strip() if match.group(2) else ""
                
                # Extrai o nome limpo dependendo do tipo
                name = "unknown"
                if element_type in ['class', 'interface', 'enum']:
                    name = signature_part.split()[0]
                elif element_type == 'method':
                    # Para métodos, procura o nome antes dos parênteses
                    method_match = re.search(r'(\w+)\s*\(', signature_part)
                    if method_match:
                        name = method_match.group(1)
                elif element_type == 'field':
                    # Para campos, o nome geralmente é a última palavra
                    field_parts = signature_part.split()
                    if field_parts:
                        name = field_parts[-1]
                elif element_type == 'import':
                    name = signature_part
                
                if name and name != "unknown":
                    # Extrai informações adicionais do bloco
                    access_modifier = ""
                    annotations = []
                    
                    # Procura por modificadores no texto
                    modifier_match = re.search(r'Modificadores:\s*([^\n]+)', match.group(0))
                    if modifier_match:
                        access_modifier = modifier_match.group(1).strip()
                    
                    # Procura por annotations
                    annotation_match = re.search(r'Annotations:\s*([^\n]+)', match.group(0))
                    if annotation_match:
                        annotations = [a.strip() for a in annotation_match.group(1).split(',')]
                    
                    element = CodeElement(
                        file_path=file_path,
                        element_type=element_type,
                        name=name,
                        signature=signature_part,
                        description=description_part,
                        dependencies=[],
                        package=self._extract_java_package(Path(file_path)),
                        access_modifier=access_modifier,
                        annotations=annotations
                    )
                    elements[f"{file_path}:{name}"] = element
        
        return elements
    
    def is_local_dependency(self, import_name: str, current_file: Path) -> bool:
        """Verifica se um import é uma dependência local do projeto Java."""
        # Verifica se é um pacote do projeto
        for package in self.java_packages.keys():
            if import_name.startswith(package):
                return True
        
        # Verifica se existe um arquivo correspondente no projeto
        import_path = import_name.replace('.', '/')
        possible_paths = [
            self.project_dir / f"{import_path}.java",
            self.project_dir / "src" / "main" / "java" / f"{import_path}.java",
            self.project_dir / "src" / f"{import_path}.java"
        ]
        return any(p.exists() for p in possible_paths)
