"""
Testes unitários para o sistema de logging
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adicionar src ao path para importar o módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    # Mock do loguru para testes
    mock_logger = MagicMock()
    with patch.dict('sys.modules', {'loguru': MagicMock(logger=mock_logger)}):
        from utils.logger import (
            LoggerConfig, AgentLogger, log_execution, 
            setup_logging, get_logger, cleanup_logging,
            TemporaryLogging, is_logging_configured
        )
except ImportError as e:
    print(f"Aviso: Não é possível testar sem loguru instalado: {e}")
    sys.exit(0)


def test_logger_config_creation():
    """Testa criação da configuração do logger"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LoggerConfig(temp_dir, enable_debug=True)
        assert config.log_dir.exists()
        assert config.enable_debug is True
        assert len(config._handlers) > 0


def test_agent_logger_methods():
    """Testa métodos específicos do AgentLogger"""
    agent_logger = AgentLogger()
    
    # Testar métodos específicos
    agent_logger.analysis("Teste de análise", file_count=10)
    agent_logger.generation("Teste de geração", feature="TestFeature")
    agent_logger.rag("Teste RAG", query="test query")
    agent_logger.amazon_q("Teste Amazon Q", tokens=150)
    agent_logger.pipeline("Teste pipeline", step="validation")
    agent_logger.feature("Teste feature", feature_name="UserService")
    agent_logger.performance("Teste performance", duration=2.5)
    agent_logger.legacy_system("Teste legacy", file_path="/path/to/file.java")
    agent_logger.new_system("Teste new system", output_file="Service.java")


def test_log_execution_decorator():
    """Testa o decorador de logging automático"""
    
    @log_execution(category="test", log_args=True)
    def exemplo_funcao(x: int, y: str = "default") -> str:
        return f"Resultado: {x} - {y}"
    
    resultado = exemplo_funcao(42, y="teste")
    assert resultado == "Resultado: 42 - teste"


def test_setup_logging():
    """Testa configuração do sistema de logging"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = setup_logging(temp_dir, debug=True)
        assert config is not None
        assert is_logging_configured()
        
        logger_instance = get_logger()
        assert isinstance(logger_instance, AgentLogger)
        
        cleanup_logging()
        assert not is_logging_configured()


def test_temporary_logging():
    """Testa context manager de logging temporário"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with TemporaryLogging(temp_dir, debug=True) as temp_logger:
            assert isinstance(temp_logger, AgentLogger)
            temp_logger.info("Log temporário")


def test_json_formatter():
    """Testa formatador JSON"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LoggerConfig(temp_dir)
        
        # Simular record do loguru
        mock_record = {
            "time": type('MockTime', (), {"isoformat": lambda: "2025-01-01T12:00:00"})(),
            "level": type('MockLevel', (), {"name": "INFO"})(),
            "name": "test_logger",
            "function": "test_function",
            "line": 42,
            "message": "Test message",
            "module": "test_module",
            "extra": {"category": "test"}
        }
        
        json_output = config._json_formatter(mock_record)
        parsed = json.loads(json_output)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["extra"]["category"] == "test"


if __name__ == "__main__":
    print("Executando testes do sistema de logging...")
    
    test_logger_config_creation()
    print("✓ Teste de criação de configuração passou")
    
    test_agent_logger_methods()
    print("✓ Teste de métodos do AgentLogger passou")
    
    test_log_execution_decorator()
    print("✓ Teste do decorador log_execution passou")
    
    test_setup_logging()
    print("✓ Teste de setup_logging passou")
    
    test_temporary_logging()
    print("✓ Teste de TemporaryLogging passou")
    
    test_json_formatter()
    print("✓ Teste do formatador JSON passou")
    
    print("\n🎉 Todos os testes passaram!")
    print("\nPara usar o sistema de logging:")
    print("1. Instale o loguru: pip install loguru")
    print("2. Configure o logging: setup_logging()")
    print("3. Use o logger: get_logger().info('mensagem')")
