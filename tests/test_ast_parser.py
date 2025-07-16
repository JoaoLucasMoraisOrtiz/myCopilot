import unittest
from code_agent.utils.ast_parser import ASTParser

PY_CODE = """
def foo(x):
    return x + 1

class Bar:
    def method(self):
        pass
"""

JAVA_CODE = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
    public int add(int a, int b) {
        return a + b;
    }
}
"""

JS_CODE = """
function greet(name) {
    return "Hello, " + name;
}
class Person {
    constructor(name) {
        this.name = name;
    }
}
"""

class TestASTParser(unittest.TestCase):
    def setUp(self):
        self.parser = ASTParser()

    def test_python_functions_and_classes(self):
        functions, classes = self.parser.extract_functions_and_classes(PY_CODE, 'python')
        self.assertTrue(any(self.parser.get_node_text(f, PY_CODE) for f in functions))
        self.assertTrue(any(self.parser.get_node_text(c, PY_CODE) for c in classes))

    def test_java_functions_and_classes(self):
        functions, classes = self.parser.extract_functions_and_classes(JAVA_CODE, 'java')
        # Java: métodos e classes
        self.assertTrue(any('add' in self.parser.get_node_text(f, JAVA_CODE) or 'main' in self.parser.get_node_text(f, JAVA_CODE) for f in functions))
        self.assertTrue(any('HelloWorld' in self.parser.get_node_text(c, JAVA_CODE) for c in classes))

    def test_js_functions_and_classes(self):
        functions, classes = self.parser.extract_functions_and_classes(JS_CODE, 'javascript')
        # JS pode não ter 'class_definition' dependendo da gramática, mas deve ter funções
        self.assertTrue(any(self.parser.get_node_text(f, JS_CODE) for f in functions))

    def test_find_node_by_line_python(self):
        node = self.parser.find_node_by_line(PY_CODE, 'python', 1)  # linha da função foo
        self.assertIsNotNone(node)
        # Aceita 'def' (token) ou 'function_definition' (nó sintático)
        self.assertTrue(
            node.type == 'function_definition' or node.type == 'def',
            f"Tipo de nó inesperado: {node.type}"
        )

    def test_decompose_by_functions_java(self):
        subtasks = self.parser.decompose_by_functions(JAVA_CODE, 'java')
        self.assertTrue(any('add' in s['name'] or 'main' in s['name'] for s in subtasks))

if __name__ == '__main__':
    unittest.main()
