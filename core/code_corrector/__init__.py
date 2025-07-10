"""
Code Corrector Module

Um mini-compilador corretor que identifica e corrige automaticamente
erros comuns de sintaxe em código gerado por LLMs.
"""

from .base_corrector import BaseCodeCorrector
from .python_corrector import PythonCorrector
from .java_corrector import JavaCorrector
from .javascript_corrector import JavaScriptCorrector


def get_corrector_for_language(language: str) -> BaseCodeCorrector:
    """
    Factory function para obter o corretor apropriado para uma linguagem.
    
    Args:
        language: Nome da linguagem (python, java, javascript, etc.)
        
    Returns:
        Instância do corretor apropriado
        
    Raises:
        ValueError: Se a linguagem não for suportada
    """
    language = language.lower().strip()
    
    correctors = {
        'python': PythonCorrector,
        'py': PythonCorrector,
        'java': JavaCorrector,
        'javascript': JavaScriptCorrector,
        'js': JavaScriptCorrector,
        'typescript': JavaScriptCorrector,  # Usa o mesmo corretor JS por ora
        'ts': JavaScriptCorrector,
    }
    
    if language not in correctors:
        raise ValueError(f"Linguagem '{language}' não suportada. Linguagens suportadas: {list(correctors.keys())}")
    
    return correctors[language]()


__all__ = [
    'BaseCodeCorrector',
    'PythonCorrector', 
    'JavaCorrector',
    'JavaScriptCorrector',
    'get_corrector_for_language'
]
