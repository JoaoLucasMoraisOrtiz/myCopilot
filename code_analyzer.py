import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

@dataclass
class CodeElement:
    file_path: str
    element_type: str  # 'function', 'class', 'variable', 'import', 'method', 'field', 'interface', 'enum'
    name: str
    description: str
    dependencies: List[str]  # elementos que este elemento usa
    signature: str = ""  # para funções/métodos
    package: str = ""  # para Java/namespaces
    access_modifier: str = ""  # public, private, protected
    annotations: List[str] = None  # type: ignore # para Java annotations, Python decorators, etc.

    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []

class LanguageAnalyzer(ABC):
    """Interface base para analisadores de linguagem específica."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extrai dependências de um arquivo."""
        pass
    
    @abstractmethod
    def analyze_project_structure(self) -> Dict:
        """Analisa estrutura específica do projeto (Maven, package.json, etc.)."""
        pass
    
    @abstractmethod
    def build_analysis_prompt(self, file_path: str, content: str, context: str, external_deps: str) -> str:
        """Constrói prompt de análise específico para a linguagem."""
        pass
    
    @abstractmethod
    def parse_analysis_response(self, file_path: str, response: str) -> Dict[str, CodeElement]:
        """Parser específico para resposta da análise."""
        pass
    
    def is_local_dependency(self, import_name: str, current_file: Path) -> bool:
        """Verifica se um import é uma dependência local do projeto."""
        return False  # Implementação padrão - override conforme necessário

class CodeAnalyzer:
    """Orquestra a análise de código usando o analisador de linguagem apropriado."""

    def __init__(self, project_dir: str, output_dir: str):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.analyzer = self._create_analyzer()
        self.knowledge_base: Dict[str, CodeElement] = {}
        self.analysis_order: List[Path] = []

    def _create_analyzer(self) -> LanguageAnalyzer:
        """Detecta a linguagem e retorna a instância do analisador apropriada."""
        # Tenta importar os analisadores específicos da linguagem
        try:
            from analyzers.java_analyzer import JavaAnalyzer
            from analyzers.python_analyzer import PythonAnalyzer
        except ImportError as e:
            print(f"Erro ao importar analisadores: {e}")
            print("Certifique-se de que os arquivos dos analisadores existem e estão corretos.")
            raise

        # Lógica de detecção (pode ser melhorada)
        if any(self.project_dir.glob("**/*.java")):
            print("☕ Projeto Java detectado.")
            return JavaAnalyzer(self.project_dir)
        elif any(self.project_dir.glob("**/*.py")):
            print("🐍 Projeto Python detectado.")
            return PythonAnalyzer(self.project_dir)
        else:
            raise ValueError("Linguagem do projeto não suportada ou não detectada.")

    def discover_files(self) -> List[Path]:
        """Descobre todos os arquivos de código relevantes no projeto."""
        extensions = self.analyzer.get_file_extensions()
        files = []
        for ext in extensions:
            files.extend(self.project_dir.rglob(f"*{ext}"))
        return files

    def analyze_dependencies(self, files: List[Path]):
        """Constrói um grafo de dependências e determina a ordem de análise."""
        dependency_graph = {file: self.analyzer.extract_dependencies(file) for file in files}
        
        # Simplificação de nomes para o grafo (de Path para str)
        # E normalização de dependências para caminhos absolutos
        str_graph = {str(k): [str(dep) for dep in v] for k, v in dependency_graph.items()}

        # Ordenação topológica para resolver a ordem de análise
        sorted_nodes = []
        visited = set()
        
        for node in str_graph:
            if node not in visited:
                self._topological_sort_util(node, visited, str_graph, sorted_nodes)
        
        self.analysis_order = [Path(p) for p in sorted_nodes]

    def _topological_sort_util(self, node: str, visited: Set[str], graph: Dict[str, List[str]], sorted_nodes: List[str]):
        visited.add(node)
        # Garante que as dependências existam no grafo antes de tentar acessá-las
        dependencies = graph.get(node, [])
        for dep in dependencies:
            if dep in graph and dep not in visited:
                self._topological_sort_util(dep, visited, graph, sorted_nodes)
        sorted_nodes.append(node)

    def analyze_file_with_llm(self, llm_client, file_path: Path):
        """Analisa um único arquivo usando o LLM."""
        content = file_path.read_text(encoding='utf-8')
        
        # Constrói contexto com base nas dependências já analisadas
        dependencies = self.analyzer.extract_dependencies(file_path)
        context_elements = [self.knowledge_base[str(dep)] for dep in dependencies if str(dep) in self.knowledge_base]
        
        context_str = "\n".join([f"- `{elem.name}` ({elem.element_type}): {elem.description}" for elem in context_elements])
        
        # Obtém dependências externas da análise de estrutura
        project_structure = self.analyzer.analyze_project_structure()
        external_deps_str = json.dumps(project_structure.get('dependencies', {}), indent=2)

        prompt = self.analyzer.build_analysis_prompt(str(file_path), content, context_str, external_deps_str)
        
        response = llm_client.send_prompt(prompt)
        
        # Salva a resposta bruta da análise
        analysis_file_name = f"analysis_{file_path.stem}.md"
        (self.output_dir / analysis_file_name).write_text(response, encoding='utf-8')

        parsed_elements = self.analyzer.parse_analysis_response(str(file_path), response)
        self.knowledge_base.update(parsed_elements)

    def save_knowledge_base(self):
        """Salva a base de conhecimento em um arquivo JSON."""
        kb_path = self.output_dir / "knowledge_base.json"
        # Converte objetos para dicionários para serialização
        kb_dict = {k: asdict(v) for k, v in self.knowledge_base.items()}
        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(kb_dict, f, indent=4, ensure_ascii=False)
        print(f"📚 Base de conhecimento salva em: {kb_path}")

    def generate_summary_report(self):
        """Gera um relatório de resumo em Markdown."""
        report_path = self.output_dir / "code_summary.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Resumo da Análise de Código\n\n")
            f.write(f"Projeto analisado: `{self.project_dir.name}`\n")
            f.write(f"Total de elementos na base de conhecimento: {len(self.knowledge_base)}\n\n")
            
            for file_path_str, element in self.knowledge_base.items():
                f.write(f"### `{element.name}`\n\n")
                f.write(f"- **Arquivo:** `{element.file_path}`\n")
                f.write(f"- **Tipo:** `{element.element_type}`\n")
                if element.package:
                    f.write(f"- **Pacote/Namespace:** `{element.package}`\n")
                if element.signature:
                    f.write(f"- **Assinatura:** `{element.signature}`\n")
                f.write(f"- **Descrição:** {element.description}\n")
                if element.dependencies:
                    f.write(f"- **Dependências:** {', '.join(f'`{d}`' for d in element.dependencies)}\n")
                f.write("\n---\n")
        print(f"📄 Relatório de resumo gerado em: {report_path}")