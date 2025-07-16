import unittest
from unittest.mock import MagicMock
import tempfile
import os
from code_agent.agents.composer_mcts import ComposerMCTSAgent
from code_agent.agents.direct_generator import DirectGeneratorAgent
from code_agent.agents.critic import CriticPolishAgent

class TestComposerMCTSAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ComposerMCTSAgent(max_iterations=2)
        self.agent.sandbox = MagicMock()
        self.agent.sandbox.execute.return_value = {"success": True, "results": []}
        self.agent.llm_client = MagicMock()

    def test_run_success(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 1\n")
            file_path = f.name
        subtask = {"subtask_id": "1", "file_path": file_path}
        mission_context = {"language": "python"}
        result = self.agent.run(subtask, mission_context)
        self.assertEqual(result, "VERIFIED")
        os.remove(file_path)

    def test_run_failure(self):
        self.agent.sandbox.execute.return_value = {"success": False, "results": []}
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 1\n")
            file_path = f.name
        subtask = {"subtask_id": "1", "file_path": file_path}
        mission_context = {"language": "python"}
        result = self.agent.run(subtask, mission_context)
        self.assertEqual(result, "FAILED")
        os.remove(file_path)

class TestDirectGeneratorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DirectGeneratorAgent()
        self.agent.sandbox = MagicMock()
        self.agent.sandbox.execute.return_value = {"success": True, "results": []}
        self.agent.llm_client = MagicMock()
        self.agent.llm_client.generate_code.return_value = "def foo():\n    return 1\n"

    def test_validate_code_python(self):
        code = "def foo():\n    return 1\n"
        result = self.agent._validate_code(code, "python")
        self.assertTrue(result["success"])

    def test_run_success(self):
        task = {"task_id": "1", "description": "implementar foo"}
        mission_context = {"language": "python"}
        result = self.agent.run(task, mission_context)
        self.assertEqual(result, "AWAITING_CRITIC")

class TestCriticPolishAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CriticPolishAgent()
        self.agent.sandbox = MagicMock()
        self.agent.sandbox.execute.return_value = {"stdout": "", "stderr": "", "success": True}
        self.agent.llm_client = MagicMock()
        self.agent.llm_client.generate_code.return_value = "def foo():\n    return 1\n"

    def test_evaluate_code_quality_python(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 1\n")
            file_path = f.name
        result = self.agent._evaluate_code_quality(file_path, "python")
        self.assertIsInstance(result, str)
        os.remove(file_path)

    def test_refactor_code(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 1\n")
            file_path = f.name
        self.agent._refactor_code(file_path, "unused import", "python")
        with open(file_path) as f:
            content = f.read()
        self.assertIn("def foo()", content)
        os.remove(file_path)

if __name__ == "__main__":
    unittest.main()
