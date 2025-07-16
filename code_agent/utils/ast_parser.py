from tree_sitter import Language, Parser
from typing import Optional, Any, List

class ASTParser:
    def __init__(self):
        self.parsers: dict[str, Parser] = {}

    def _load_language(self, language: str) -> Optional[Parser]:
        if language in self.parsers:
            return self.parsers[language]
        try:
            module = __import__(f"tree_sitter_{language}", fromlist=["language"])
            lang = Language(module.language())
            parser = Parser(lang)
            self.parsers[language] = parser
            return parser
        except ImportError:
            print(f"Gramática tree-sitter para '{language}' não instalada. Instale o pacote 'tree_sitter_{language}'.")
        except Exception as e:
            print(f"Erro ao carregar a gramática para '{language}': {e}")
        return None

    def parse(self, code: str, language: str) -> Optional[Any]:
        parser = self._load_language(language)
        if not parser:
            print(f"Parser para '{language}' não disponível.")
            return None
        tree = parser.parse(code.encode('utf8'))
        return tree

    def get_root_node(self, code: str, language: str):
        tree = self.parse(code, language)
        if tree:
            return tree.root_node
        return None

    def find_nodes_by_type(self, node, type_name: str) -> List[Any]:
        """Recursivamente encontra todos os nós de um tipo específico."""
        result = []
        if node.type == type_name:
            result.append(node)
        for child in node.children:
            result.extend(self.find_nodes_by_type(child, type_name))
        return result

    def get_node_text(self, node, code: str) -> str:
        """Extrai o texto correspondente a um nó do código fonte."""
        return code[node.start_byte:node.end_byte]

    def extract_functions_and_classes(self, code: str, language: str):
        """Retorna listas de nós de funções e classes do código, adaptado por linguagem."""
        root = self.get_root_node(code, language)
        if not root:
            return [], []
        # Tipos por linguagem
        if language == 'python':
            function_types = ['function_definition']
            class_types = ['class_definition']
        elif language == 'java':
            function_types = ['method_declaration']
            class_types = ['class_declaration']
        elif language == 'javascript':
            function_types = ['function_declaration']
            class_types = ['class_declaration']
        else:
            function_types = ['function_definition', 'method_definition', 'function_declaration']
            class_types = ['class_definition', 'class_declaration']
        functions = []
        for t in function_types:
            functions.extend(self.find_nodes_by_type(root, t))
        classes = []
        for t in class_types:
            classes.extend(self.find_nodes_by_type(root, t))
        return functions, classes

    def find_node_by_line(self, code: str, language: str, line_number: int):
        """Encontra o nó mais interno que cobre a linha fornecida (0-based)."""
        root = self.get_root_node(code, language)
        if not root:
            return None
        def search(node):
            if node.start_point[0] <= line_number <= node.end_point[0]:
                for child in node.children:
                    result = search(child)
                    if result:
                        return result
                return node
            return None
        return search(root)

    def decompose_by_functions(self, code: str, language: str):
        """Gera subtasks para cada função/método encontrada no código."""
        root = self.get_root_node(code, language)
        if not root:
            return []
        if language == 'python':
            function_types = ['function_definition']
        elif language == 'java':
            function_types = ['method_declaration']
        elif language == 'javascript':
            function_types = ['function_declaration']
        else:
            function_types = ['function_definition', 'method_declaration', 'function_declaration']
        functions = []
        for t in function_types:
            functions.extend(self.find_nodes_by_type(root, t))
        subtasks = []
        for func in functions:
            # Nome do identificador pode variar
            name_node = None
            for child in func.children:
                if child.type in ('identifier', 'name'):  # 'name' para JS
                    name_node = child
                    break
            name = self.get_node_text(name_node, code) if name_node else 'unknown'
            subtasks.append({'type': 'function', 'name': name, 'node': func})
        return subtasks


if __name__ == "__main__":
    # Exemplo de uso
    parser = ASTParser()
    code = """
    class DirectGeneratorAgent(BaseAgent):

        def __init__(self):
            self.llm_client = LLMClient()
            self.sandbox = DockerSandbox()

        def run(self, task: Dict[str, Any], mission_context: Dict[str, Any]) -> str:
        
            language = mission_context.get("language", "python")
            prompt = self._create_prompt(task, language)

            generated_code = self.llm_client.generate_code(prompt)

            # Aqui, você salvaria o código em um arquivo temporário
            # e depois executaria a validação no sandbox.
            # A lógica de validação é um espaço reservado.
            validation_result = self._validate_code(generated_code, language)

            if validation_result["success"]:
                # Em um cenário real, você confirmaria as alterações no sistema de arquivos
                print(f"Task {task['task_id']} gerada e validada com sucesso.")
                return "AWAITING_CRITIC"
            else:
                print(f"Falha na validação para a Task {task['task_id']}.")
                return "PLANNING_REQUIRED"

        def _create_prompt(self, task: Dict[str, Any], language: str) -> str:
            return (
                f"Linguagem: {language}\n"
                f"Tarefa: {task['description']}\n"
                "Por favor, gere o código completo para implementar esta tarefa."
            )

        def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
            if language == "python":
                # Exemplo: command = ["python", "-m", "pytest"]
                pass
            elif language == "java":
                # Exemplo: command = ["mvn", "clean", "install"]
                pass

            # resultado_execucao = self.sandbox.execute(command, ...)
            # Esta é uma simulação.
            if "error" not in code.lower():
                return {"success": True}
            return {"success": False, "error": "Simulated validation error"}

        def run(self, *args, **kwargs):
            pass
    """
    language = 'python'
    functions, classes = parser.extract_functions_and_classes(code, language)
    print("Funções:", [parser.get_node_text(f, code) for f in classes])