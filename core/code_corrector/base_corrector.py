"""
Base Code Corrector

Classe base abstrata para implementar corretores de código específicos por linguagem.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass
import subprocess
import tempfile
import os


@dataclass
class CorrectionResult:
    """Resultado de uma correção de código."""
    original_code: str
    corrected_code: str
    corrections_applied: List[str]
    compilation_successful: bool
    error_messages: List[str]


class BaseCodeCorrector(ABC):
    """
    Classe base para corretores de código específicos por linguagem.
    
    Implementa o fluxo geral:
    1. Tenta compilar o código original
    2. Se houver erros, aplica heurísticas de correção
    3. Recompila para verificar se foi corrigido
    """
    
    def __init__(self):
        self.corrections_applied = []
        
    def correct(self, code: str) -> CorrectionResult:
        """
        Corrige automaticamente erros comuns no código.
        
        Args:
            code: Código fonte a ser corrigido
            
        Returns:
            CorrectionResult com o código corrigido e metadados
        """
        original_code = code
        self.corrections_applied = []
        
        # Primeiro, tenta compilar o código original
        compilation_result = self._compile_code(code)
        
        if compilation_result['success']:
            # Código já está correto
            return CorrectionResult(
                original_code=original_code,
                corrected_code=code,
                corrections_applied=[],
                compilation_successful=True,
                error_messages=[]
            )
        
        # Se há erros, tenta corrigir
        corrected_code = self._apply_corrections(code, compilation_result['errors'])
        
        # Verifica se a correção funcionou
        final_compilation = self._compile_code(corrected_code)
        
        return CorrectionResult(
            original_code=original_code,
            corrected_code=corrected_code,
            corrections_applied=self.corrections_applied.copy(),
            compilation_successful=final_compilation['success'],
            error_messages=final_compilation['errors']
        )
    
    @abstractmethod
    def _compile_code(self, code: str) -> Dict[str, Any]:
        """
        Compila/valida o código usando o compilador padrão da linguagem.
        
        Args:
            code: Código fonte
            
        Returns:
            Dict com 'success' (bool) e 'errors' (List[str])
        """
        pass
    
    def _apply_corrections(self, code: str, errors: List[str]) -> str:
        """
        Aplica correções heurísticas baseadas nos erros encontrados.
        
        Args:
            code: Código fonte original
            errors: Lista de erros de compilação
            
        Returns:
            Código corrigido
        """
        corrected_code = code
        
        # Correções gerais aplicáveis a qualquer linguagem
        corrected_code = self._fix_common_syntax_errors(corrected_code)
        
        # Correções específicas por linguagem
        corrected_code = self._fix_language_specific_errors(corrected_code, errors)
        
        return corrected_code
    
    def _fix_common_syntax_errors(self, code: str) -> str:
        """
        Corrige erros de sintaxe comuns a várias linguagens.
        """
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            corrected_line = line
            
            # Balanceamento de parênteses, chaves e colchetes
            corrected_line = self._balance_brackets(corrected_line)
            
            # Correção de aspas não fechadas
            corrected_line = self._fix_unclosed_quotes(corrected_line)
            
            # Correção de comentários não fechados
            corrected_line = self._fix_unclosed_comments(corrected_line)
            
            corrected_lines.append(corrected_line)
        
        return '\n'.join(corrected_lines)
    
    def _balance_brackets(self, line: str) -> str:
        """Balanceia parênteses, chaves e colchetes."""
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        result = list(line)
        
        for i, char in enumerate(line):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if stack and brackets.get(stack[-1][0]) == char:
                    stack.pop()
        
        # Adiciona fechamentos faltantes no final da linha
        while stack:
            opening, _ = stack.pop()
            result.append(brackets[opening])
            self.corrections_applied.append(f"Adicionado '{brackets[opening]}' faltante")
        
        return ''.join(result)
    
    def _fix_unclosed_quotes(self, line: str) -> str:
        """Corrige aspas não fechadas."""
        # Conta aspas simples e duplas
        single_quotes = line.count("'")
        double_quotes = line.count('"')
        
        result = line
        
        # Se há número ímpar de aspas, adiciona uma no final
        if single_quotes % 2 == 1:
            result += "'"
            self.corrections_applied.append("Adicionada aspa simples faltante")
        
        if double_quotes % 2 == 1:
            result += '"'
            self.corrections_applied.append("Adicionada aspa dupla faltante")
        
        return result
    
    @abstractmethod
    def _fix_unclosed_comments(self, line: str) -> str:
        """Corrige comentários não fechados (específico por linguagem)."""
        pass
    
    @abstractmethod
    def _fix_language_specific_errors(self, code: str, errors: List[str]) -> str:
        """
        Aplica correções específicas da linguagem.
        
        Args:
            code: Código fonte
            errors: Erros de compilação
            
        Returns:
            Código corrigido
        """
        pass
    
    def _create_temp_file(self, code: str, extension: str) -> str:
        """
        Cria um arquivo temporário com o código.
        
        Args:
            code: Código fonte
            extension: Extensão do arquivo (ex: '.py', '.java')
            
        Returns:
            Caminho para o arquivo temporário
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
            f.write(code)
            return f.name
    
    def _cleanup_temp_file(self, filepath: str):
        """Remove arquivo temporário."""
        try:
            os.unlink(filepath)
        except OSError:
            pass
