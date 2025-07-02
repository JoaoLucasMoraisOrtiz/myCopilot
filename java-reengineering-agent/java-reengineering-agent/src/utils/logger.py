"""
Sistema de logging centralizado usando loguru
Configuração estruturada para todo o agente de reengenharia
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

try:
    from loguru import logger
except ImportError:
    raise ImportError(
        "loguru é necessário para o sistema de logging. "
        "Instale com: pip install loguru"
    )


class LoggerConfig:
    """Configuração centralizada do sistema de logging"""
    
    def __init__(self, log_dir: str = "logs", enable_debug: bool = False):
        self.log_dir = Path(log_dir).resolve()
        self.enable_debug = enable_debug
        self._handlers = []
        
        # Criar diretório de logs se não existir
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Warning: Cannot create log directory {self.log_dir}, using temp directory")
            import tempfile
            self.log_dir = Path(tempfile.gettempdir()) / "java_reengineering_agent"
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar handlers personalizados
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configurar todos os handlers de logging"""
        # Remover handlers existentes apenas se necessário
        if len(logger._core.handlers) > 1:
            logger.remove()
        
        try:
            self._setup_console_handler()
            self._setup_file_handlers()
            self._setup_structured_handler()
        except Exception as e:
            print(f"Warning: Error setting up logging handlers: {e}")
            # Fallback para console simples
            self._setup_fallback_handler()
    
    def _setup_console_handler(self):
        """Handler para console com cores e formatação"""
        # Handler para info e debug (stdout)
        handler_id = logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="DEBUG" if self.enable_debug else "INFO",
            colorize=True,
            filter=lambda record: record["level"].name not in ["ERROR", "CRITICAL"]
        )
        self._handlers.append(handler_id)
        
        # Handler separado para erros (stderr)
        handler_id = logger.add(
            sys.stderr,
            format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="ERROR",
            colorize=True,
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"]
        )
        self._handlers.append(handler_id)
    
    def _setup_file_handlers(self):
        """Handlers para arquivos com rotação"""
        try:
            # Log geral (todas as mensagens)
            handler_id = logger.add(
                self.log_dir / "agent.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level="DEBUG",
                rotation="10 MB",
                retention="30 days",
                compression="zip",
                encoding="utf-8"
            )
            self._handlers.append(handler_id)
            
            # Log de análise (específico para operações de análise)
            handler_id = logger.add(
                self.log_dir / "analysis.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level="INFO",
                rotation="5 MB",
                retention="15 days",
                filter=lambda record: record["extra"].get("category") == "analysis",
                encoding="utf-8"
            )
            self._handlers.append(handler_id)
            
            # Log de geração (específico para geração de código)
            handler_id = logger.add(
                self.log_dir / "generation.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level="INFO",
                rotation="5 MB",
                retention="15 days",
                filter=lambda record: record["extra"].get("category") == "generation",
                encoding="utf-8"
            )
            self._handlers.append(handler_id)
            
            # Log de erros (apenas erros e critical)
            handler_id = logger.add(
                self.log_dir / "errors.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
                level="ERROR",
                rotation="5 MB",
                retention="60 days",
                encoding="utf-8"
            )
            self._handlers.append(handler_id)
            
        except Exception as e:
            print(f"Warning: Could not setup file handlers: {e}")
    
    def _setup_structured_handler(self):
        """Handler para logs estruturados em JSON"""
        try:
            # Usar serialização nativa do loguru para JSON
            handler_id = logger.add(
                self.log_dir / "structured.jsonl",
                level="INFO",
                rotation="10 MB",
                retention="30 days",
                serialize=True,  # Isso faz o loguru usar JSON automaticamente
                encoding="utf-8"
            )
            self._handlers.append(handler_id)
        except Exception as e:
            print(f"Warning: Could not setup structured handler: {e}")
    
    def _setup_fallback_handler(self):
        """Handler simples de fallback em caso de erro"""
        handler_id = logger.add(
            sys.stdout,
            format="{time:HH:mm:ss} | {level} | {message}",
            level="INFO"
        )
        self._handlers.append(handler_id)
    
    def cleanup(self):
        """Limpar handlers e recursos"""
        for handler_id in self._handlers:
            try:
                logger.remove(handler_id)
            except ValueError:
                pass  # Handler já removido
        self._handlers.clear()


class AgentLogger:
    """Wrapper para logger com métodos específicos do agente"""
    
    def __init__(self):
        self.logger = logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def analysis(self, message: str, **kwargs):
        """Log específico para operações de análise"""
        self.logger.bind(category="analysis").info(message, **kwargs)
    
    def generation(self, message: str, **kwargs):
        """Log específico para geração de código"""
        self.logger.bind(category="generation").info(message, **kwargs)
    
    def rag(self, message: str, **kwargs):
        """Log específico para operações RAG"""
        self.logger.bind(category="rag").info(message, **kwargs)
    
    def amazon_q(self, message: str, **kwargs):
        """Log específico para chamadas Amazon Q"""
        self.logger.bind(category="amazon_q").info(message, **kwargs)
    
    def pipeline(self, message: str, step: Optional[str] = None, **kwargs):
        """Log específico para pipeline de reengenharia"""
        extra = {"step": step} if step else {}
        extra.update(kwargs)
        self.logger.bind(category="pipeline", **extra).info(message)
    
    def feature(self, message: str, feature_name: Optional[str] = None, **kwargs):
        """Log específico para processamento de features"""
        extra = {"feature": feature_name} if feature_name else {}
        extra.update(kwargs)
        self.logger.bind(category="feature", **extra).info(message)
    
    def performance(self, message: str, duration: Optional[float] = None, **kwargs):
        """Log específico para métricas de performance"""
        extra = {"duration_seconds": duration} if duration is not None else {}
        extra.update(kwargs)
        self.logger.bind(category="performance", **extra).info(message)
    
    def legacy_system(self, message: str, file_path: Optional[str] = None, **kwargs):
        """Log específico para análise de sistema legacy"""
        extra = {"legacy_file": file_path} if file_path else {}
        extra.update(kwargs)
        self.logger.bind(category="legacy_system", **extra).info(message)
    
    def new_system(self, message: str, output_file: Optional[str] = None, **kwargs):
        """Log específico para geração do novo sistema"""
        extra = {"output_file": output_file} if output_file else {}
        extra.update(kwargs)
        self.logger.bind(category="new_system", **extra).info(message)


# Decorador para logging automático de funções
def log_execution(category: Optional[str] = None, log_args: bool = False):
    """
    Decorador para logging automático de execução de funções
    
    Args:
        category: Categoria do log
        log_args: Se deve logar os argumentos da função
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            module_name = func.__module__
            
            # Log de início
            start_msg = f"Starting {func_name}"
            if log_args and (args or kwargs):
                # Limitar args para evitar logs excessivos
                args_repr = str(args[:3]) if len(args) <= 3 else f"{str(args[:3])}... (truncated)"
                kwargs_repr = str(list(kwargs.keys())[:5]) if len(kwargs) <= 5 else f"{str(list(kwargs.keys())[:5])}... (truncated)"
                start_msg += f" with args={args_repr} kwargs={kwargs_repr}"
            
            try:
                if category:
                    logger.bind(category=category).info(start_msg)
                else:
                    logger.info(start_msg)
                
                # Executar função
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Log de sucesso
                success_msg = f"Completed {func_name} in {duration:.2f}s"
                if category:
                    logger.bind(category=category, duration_seconds=duration).info(success_msg)
                else:
                    logger.info(success_msg)
                
                return result
                
            except Exception as e:
                # Log de erro
                error_msg = f"Failed {func_name}: {str(e)}"
                if category:
                    logger.bind(category=category).error(error_msg)
                else:
                    logger.error(error_msg)
                raise
        
        return wrapper
    return decorator


# Instância global do logger (lazy initialization)
_agent_logger: Optional[AgentLogger] = None
_logger_config: Optional[LoggerConfig] = None


def get_logger() -> AgentLogger:
    """Retorna instância configurada do logger (lazy initialization)"""
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = AgentLogger()
    return _agent_logger


def setup_logging(log_dir: str = "logs", debug: bool = False) -> Optional[LoggerConfig]:
    """
    Configurar sistema de logging
    
    Args:
        log_dir: Diretório para arquivos de log
        debug: Se deve habilitar nível DEBUG
    
    Returns:
        Configuração do logger criada ou None em caso de erro
    """
    global _logger_config
    
    # Configurar baseado em variável de ambiente se não especificado
    if not debug and os.getenv("DEBUG", "false").lower() == "true":
        debug = True
    
    # Configurar baseado em variável de ambiente para diretório de logs
    env_log_dir = os.getenv("LOG_DIR")
    if env_log_dir:
        log_dir = env_log_dir
    
    try:
        _logger_config = LoggerConfig(log_dir, enable_debug=debug)
        return _logger_config
    except Exception as e:
        print(f"Warning: Failed to setup logging: {e}")
        # Fallback para logging básico
        logger.remove()
        logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
        _logger_config = None
        return None


def cleanup_logging():
    """Limpar recursos de logging"""
    global _logger_config, _agent_logger
    
    if _logger_config:
        _logger_config.cleanup()
        _logger_config = None
    
    _agent_logger = None


def is_logging_configured() -> bool:
    """Verificar se o logging foi configurado"""
    return _logger_config is not None


# Context manager para logging temporário
class TemporaryLogging:
    """Context manager para configuração temporária de logging"""
    
    def __init__(self, log_dir: str = "logs", debug: bool = False):
        self.log_dir = log_dir
        self.debug = debug
        self.original_config = None
    
    def __enter__(self):
        self.original_config = _logger_config
        setup_logging(self.log_dir, self.debug)
        return get_logger()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_logging()
        if self.original_config:
            global _logger_config
            _logger_config = self.original_config


# Exemplos de uso e conveniência
def configure_default_logging():
    """Configurar logging com configurações padrão para o agente"""
    setup_logging()
    return get_logger()


# Funciona como um singleton para a instância padrão do logger
agent_logger = None


def get_default_logger() -> AgentLogger:
    """Retorna o logger padrão configurado automaticamente"""
    global agent_logger
    if agent_logger is None:
        if not is_logging_configured():
            setup_logging()
        agent_logger = get_logger()
    return agent_logger


# Para compatibilidade com código existente
def get_agent_logger() -> AgentLogger:
    """Alias para get_default_logger()"""
    return get_default_logger()


if __name__ == "__main__":
    # Exemplo de uso
    print("Exemplo de uso do sistema de logging:")
    
    # Configurar logging
    config = setup_logging(debug=True)
    logger_instance = get_logger()
    
    # Testar diferentes tipos de log
    logger_instance.info("Sistema iniciado")
    logger_instance.analysis("Analisando código legacy", file_count=150)
    logger_instance.generation("Gerando novo código", feature="UserService")
    logger_instance.performance("Operação completada", duration=2.5)
    
    # Testar decorador
    @log_execution(category="test", log_args=True)
    def exemplo_funcao(x: int, y: str = "default") -> str:
        return f"Resultado: {x} - {y}"
    
    resultado = exemplo_funcao(42, y="teste")
    logger_instance.info(f"Resultado da função: {resultado}")
    
    # Testar context manager
    with TemporaryLogging(log_dir="temp_logs", debug=True) as temp_logger:
        temp_logger.info("Log temporário")
    
    # Cleanup
    cleanup_logging()
    print("Exemplo concluído")
