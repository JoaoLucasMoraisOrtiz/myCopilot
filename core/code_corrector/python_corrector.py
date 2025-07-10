"""
Python Code Corrector

Implementação específica para correção de código Python.
"""

import ast
import subprocess
import tempfile
import os
import re
from typing import List, Dict, Any
from .base_corrector import BaseCodeCorrector


class PythonCorrector(BaseCodeCorrector):
    """Corretor específico para código Python."""
    
    def _compile_code(self, code: str) -> Dict[str, Any]:
        """
        Compila código Python usando ast.parse e python -m py_compile.
        """
        errors = []
        
        # Primeiro, tenta parsing com AST
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax Error (linha {e.lineno}): {e.msg}")
        except Exception as e:
            errors.append(f"Parse Error: {str(e)}")
        
        # Se AST passou, tenta compilação real
        if not errors:
            temp_file = self._create_temp_file(code, '.py')
            try:
                result = subprocess.run(
                    ['python', '-m', 'py_compile', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    errors.append(result.stderr.strip())
            except subprocess.TimeoutExpired:
                errors.append("Timeout durante compilação")
            except FileNotFoundError:
                errors.append("Python não encontrado no PATH")
            except Exception as e:
                errors.append(f"Erro durante compilação: {str(e)}")
            finally:
                self._cleanup_temp_file(temp_file)
        
        return {
            'success': len(errors) == 0,
            'errors': errors
        }
    
    def _fix_unclosed_comments(self, line: str) -> str:
        """Corrige comentários Python não fechados."""
        # Python usa # para comentários de linha, então não há muito a corrigir
        # Mas podemos detectar strings triplas não fechadas
        
        triple_single = line.count("'''")
        triple_double = line.count('"""')
        
        result = line
        
        if triple_single % 2 == 1:
            result += "'''"
            self.corrections_applied.append("Adicionada string tripla (''') faltante")
        
        if triple_double % 2 == 1:
            result += '"""'
            self.corrections_applied.append('Adicionada string tripla (""") faltante')
        
        return result
    
    def _fix_language_specific_errors(self, code: str, errors: List[str]) -> str:
        """Aplica correções específicas do Python."""
        corrected_code = code
        
        # Correção de indentação
        corrected_code = self._fix_indentation(corrected_code)
        
        # Correção de dois pontos faltantes
        corrected_code = self._fix_missing_colons(corrected_code)
        
        # Correção de imports
        corrected_code = self._fix_imports(corrected_code)
        
        # Correção de parênteses em print (Python 3)
        corrected_code = self._fix_print_statements(corrected_code)
        
        return corrected_code
    
    def _fix_indentation(self, code: str) -> str:
        """Corrige problemas básicos de indentação."""
        lines = code.split('\n')
        corrected_lines = []
        expected_indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                corrected_lines.append(line)
                continue
            
            # Detecta blocos que precisam de indentação
            if any(stripped.endswith(keyword + ':') for keyword in ['if', 'else', 'elif', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with']):
                corrected_lines.append(' ' * expected_indent + stripped)
                expected_indent += 4
            elif stripped in ['else:', 'elif', 'except:', 'finally:'] or stripped.startswith('elif ') or stripped.startswith('except '):
                expected_indent = max(0, expected_indent - 4)
                corrected_lines.append(' ' * expected_indent + stripped)
                expected_indent += 4
            else:
                # Detecta fim de bloco (dedent)
                if len(corrected_lines) > 0 and corrected_lines[-1].strip().endswith(':'):
                    pass  # Próxima linha deve estar indentada
                elif expected_indent > 0 and not line.startswith(' '):
                    # Pode precisar de indentação
                    corrected_lines.append(' ' * expected_indent + stripped)
                else:
                    corrected_lines.append(line)
        
        if corrected_lines != code.split('\n'):
            self.corrections_applied.append("Corrigida indentação Python")
        
        return '\n'.join(corrected_lines)
    
    def _fix_missing_colons(self, code: str) -> str:
        """Adiciona dois pontos faltantes em estruturas de controle."""
        lines = code.split('\n')
        corrected_lines = []
        
        # Padrões que precisam de dois pontos
        control_patterns = [
            r'^\s*(if\s+.+)$',
            r'^\s*(elif\s+.+)$', 
            r'^\s*(else\s*)$',
            r'^\s*(for\s+.+)$',
            r'^\s*(while\s+.+)$',
            r'^\s*(def\s+\w+\s*\([^)]*\)\s*)$',
            r'^\s*(class\s+\w+.*?)$',
            r'^\s*(try\s*)$',
            r'^\s*(except.*?)$',
            r'^\s*(finally\s*)$',
            r'^\s*(with\s+.+)$'
        ]
        
        for line in lines:
            corrected_line = line
            
            for pattern in control_patterns:
                match = re.match(pattern, line)
                if match and not line.rstrip().endswith(':'):
                    corrected_line = line.rstrip() + ':'
                    self.corrections_applied.append(f"Adicionado ':' faltante na linha: {line.strip()}")
                    break
            
            corrected_lines.append(corrected_line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_imports(self, code: str) -> str:
        """Corrige imports malformados."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Corrige "import from" para "from ... import"
            if stripped.startswith('import ') and ' from ' in stripped:
                parts = stripped.split(' from ')
                if len(parts) == 2:
                    module = parts[1].strip()
                    items = parts[0].replace('import ', '').strip()
                    corrected_line = f"from {module} import {items}"
                    corrected_lines.append(' ' * (len(line) - len(line.lstrip())) + corrected_line)
                    self.corrections_applied.append(f"Corrigido import: {stripped}")
                    continue
            
            corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_print_statements(self, code: str) -> str:
        """Converte print statements para print functions (Python 3)."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            # Detecta print sem parênteses
            print_pattern = r'^(\s*)print\s+([^(].*)$'
            match = re.match(print_pattern, line)
            
            if match:
                indent = match.group(1)
                content = match.group(2).strip()
                corrected_line = f"{indent}print({content})"
                corrected_lines.append(corrected_line)
                self.corrections_applied.append(f"Convertido print statement para function: {line.strip()}")
            else:
                corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
