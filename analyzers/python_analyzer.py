import ast
from pathlib import Path
from typing import Dict, List
import sys
import os

# Adiciona o diretório pai ao path para importar code_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_analyzer import LanguageAnalyzer, CodeElement

class PythonAnalyzer(LanguageAnalyzer):
    """Analisador específico para projetos Python."""
    
    def get_file_extensions(self) -> List[str]:
        return ['.py']
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extrai imports Python de um arquivo."""
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps.append(node.module)
        except:
            pass  # Ignora erros de parsing
        
        return deps
    
    def analyze_project_structure(self) -> Dict:
        """Analisa estrutura de projeto Python."""
        return {
            'python_packages': self._discover_python_packages()
        }
    
    def _discover_python_packages(self) -> List[str]:
        """Descobre pacotes Python no projeto."""
        packages = []
        for init_file in self.project_dir.rglob('__init__.py'):
            package_path = init_file.parent.relative_to(self.project_dir)
            package_name = str(package_path).replace('/', '.').replace('\\', '.')
            packages.append(package_name)
        return packages
    
    def build_analysis_prompt(self, file_path: str, content: str, context: str, external_deps: str) -> str:
        """Constrói prompt específico para análise de arquivos Python."""
        return f"""
Analise o arquivo Python abaixo e descreva CADA elemento (função, classe, variável global, etc.) de forma concisa mas completa.

**CONTEXTO DAS DEPENDÊNCIAS:**
{context}

**ESTRUTURA DO PROJETO:**
{external_deps}

**ARQUIVO: {file_path}**
```python
{content}
```

**INSTRUÇÕES:**
Para cada elemento encontrado, forneça:

1. **FUNÇÕES:** Nome, parâmetros, retorno, e o que faz em 1-2 frases
2. **CLASSES:** Nome, propósito, principais métodos
3. **VARIÁVEIS GLOBAIS:** Nome, tipo, propósito
4. **IMPORTS:** O que importa e para que é usado

**FORMATO DE RESPOSTA:**
```
FUNÇÃO: nome_funcao(parametros) -> retorno
Descrição: O que a função faz...

CLASSE: NomeClasse
Descrição: Propósito da classe...
Métodos principais: metodo1, metodo2...

VARIÁVEL: nome_var (tipo)
Descrição: Para que serve...

IMPORT: módulo_importado
Uso: Como é usado no código...
```

Seja preciso e foque no que cada elemento FAZ, não como está implementado.
"""
    
    def parse_analysis_response(self, file_path: str, response: str) -> Dict[str, CodeElement]:
        """Parser robusto usando regex para respostas Python."""
        import re
        
        elements = {}
        
        # Padrões regex para diferentes tipos de elementos
        patterns = {
            'function': r'FUNÇÃO:\s*([^(\n]+)(?:\([^)]*\))?\s*(?:->\s*[^\n]+)?\n(?:Descrição:\s*([^\n]+(?:\n(?!FUNÇÃO:|CLASSE:|VARIÁVEL:|IMPORT:)[^\n]*)*)?)',
            'class': r'CLASSE:\s*([^\n]+)\n(?:Descrição:\s*([^\n]+(?:\n(?!FUNÇÃO:|CLASSE:|VARIÁVEL:|IMPORT:)[^\n]*)*)?)',
            'variable': r'VARIÁVEL:\s*([^(\n]+)(?:\([^)]*\))?\n(?:Descrição:\s*([^\n]+(?:\n(?!FUNÇÃO:|CLASSE:|VARIÁVEL:|IMPORT:)[^\n]*)*)?)',
            'import': r'IMPORT:\s*([^\n]+)\n(?:Uso:\s*([^\n]+(?:\n(?!FUNÇÃO:|CLASSE:|VARIÁVEL:|IMPORT:)[^\n]*)*)?)'
        }
        
        for element_type, pattern in patterns.items():
            matches = re.finditer(pattern, response, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                name_part = match.group(1).strip()
                description_part = match.group(2).strip() if match.group(2) else ""
                
                # Extrai o nome limpo
                if element_type == 'function':
                    name = name_part.split('(')[0].strip()
                    signature = name_part
                elif element_type == 'variable':
                    name = name_part.split('(')[0].strip()
                    signature = ""
                else:
                    name = name_part.split()[0] if name_part else "unknown"
                    signature = name_part if element_type == 'class' else ""
                
                if name and name != "unknown":
                    element = CodeElement(
                        file_path=file_path,
                        element_type=element_type,
                        name=name,
                        signature=signature,
                        description=description_part,
                        dependencies=[]
                    )
                    elements[f"{file_path}:{name}"] = element
        
        return elements
    
    def is_local_dependency(self, import_name: str, current_file: Path) -> bool:
        """Verifica se um import é uma dependência local do projeto Python."""
        if import_name.startswith('.'):  # relative import
            return True
        
        # Verifica se existe um arquivo correspondente no projeto
        possible_paths = [
            self.project_dir / f"{import_name}.py",
            self.project_dir / import_name / "__init__.py"
        ]
        return any(p.exists() for p in possible_paths)
