"""
JavaScript/TypeScript Code Corrector

Implementação específica para correção de código JavaScript e TypeScript.
"""

import subprocess
import re
from typing import List, Dict, Any
from .base_corrector import BaseCodeCorrector


class JavaScriptCorrector(BaseCodeCorrector):
    """Corretor específico para código JavaScript/TypeScript."""
    
    def _compile_code(self, code: str) -> Dict[str, Any]:
        """
        Valida código JavaScript usando Node.js ou ferramentas disponíveis.
        """
        errors = []
        
        # Cria arquivo temporário
        temp_file = self._create_temp_file(code, '.js')
        
        try:
            # Tenta validar sintaxe com Node.js
            result = subprocess.run(
                ['node', '--check', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                error_lines = result.stderr.strip().split('\n')
                for line in error_lines:
                    if line.strip():
                        errors.append(line.strip())
            
        except FileNotFoundError:
            # Se Node.js não estiver disponível, faz validação básica
            errors.extend(self._basic_js_validation(code))
        except subprocess.TimeoutExpired:
            errors.append("Timeout durante validação JavaScript")
        except Exception as e:
            errors.append(f"Erro durante validação JavaScript: {str(e)}")
        finally:
            self._cleanup_temp_file(temp_file)
        
        return {
            'success': len(errors) == 0,
            'errors': errors
        }
    
    def _basic_js_validation(self, code: str) -> List[str]:
        """Validação básica de sintaxe JavaScript quando Node.js não está disponível."""
        errors = []
        
        # Verifica balanceamento básico de chaves, parênteses, etc.
        brackets = {'(': 0, '[': 0, '{': 0}
        quote_count = {'\'': 0, '"': 0, '`': 0}
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Ignora comentários
            if '//' in line:
                line = line[:line.index('//')]
            
            for char in line:
                if char in brackets:
                    brackets[char] += 1
                elif char == ')':
                    brackets['('] -= 1
                elif char == ']':
                    brackets['['] -= 1
                elif char == '}':
                    brackets['{'] -= 1
                elif char in quote_count:
                    quote_count[char] += 1
        
        # Verifica desbalanceamentos
        for bracket, count in brackets.items():
            if count != 0:
                errors.append(f"Desbalanceamento de '{bracket}': {count} não fechados")
        
        for quote, count in quote_count.items():
            if count % 2 != 0:
                errors.append(f"Aspas {quote} não fechadas")
        
        return errors
    
    def _fix_unclosed_comments(self, line: str) -> str:
        """Corrige comentários JavaScript não fechados."""
        result = line
        
        # Conta comentários de bloco /* */
        block_start = line.count('/*')
        block_end = line.count('*/')
        
        if block_start > block_end:
            result += ' */'
            self.corrections_applied.append("Adicionado '*/' faltante")
        
        return result
    
    def _fix_language_specific_errors(self, code: str, errors: List[str]) -> str:
        """Aplica correções específicas do JavaScript."""
        corrected_code = code
        
        # Correção de ponto e vírgula faltante
        corrected_code = self._fix_missing_semicolons_js(corrected_code)
        
        # Correção de palavras-chave
        corrected_code = self._fix_js_keywords(corrected_code)
        
        # Correção de function declarations
        corrected_code = self._fix_function_declarations(corrected_code)
        
        # Correção de template literals
        corrected_code = self._fix_template_literals(corrected_code)
        
        return corrected_code
    
    def _fix_missing_semicolons_js(self, code: str) -> str:
        """Adiciona ponto e vírgula faltante em JavaScript."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Ignora linhas vazias, comentários e estruturas de controle
            if (not stripped or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*') or
                stripped.endswith('{') or
                stripped.endswith('}') or
                stripped.endswith(';') or
                stripped.endswith(',') or
                any(keyword in stripped for keyword in ['if', 'else', 'for', 'while', 'switch', 'case', 'default:', 'function', 'class'])):
                corrected_lines.append(line)
                continue
            
            # Padrões que precisam de ponto e vírgula
            needs_semicolon = (
                re.match(r'^\s*(var|let|const)\s+\w+.*[^;]$', line) or  # Declarações
                re.match(r'^\s*\w+\s*=\s*.*[^;]$', line) or  # Atribuições
                re.match(r'^\s*\w+\s*\([^)]*\)\s*[^;{]$', line) or  # Chamadas de função
                re.match(r'^\s*return\s+.*[^;]$', line) or  # Return
                re.match(r'^\s*throw\s+.*[^;]$', line) or  # Throw
                re.match(r'^\s*break\s*[^;]$', line) or  # Break
                re.match(r'^\s*continue\s*[^;]$', line)  # Continue
            )
            
            if needs_semicolon:
                corrected_lines.append(line.rstrip() + ';')
                self.corrections_applied.append(f"Adicionado ';' faltante na linha: {stripped}")
            else:
                corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_js_keywords(self, code: str) -> str:
        """Corrige uso incorreto de palavras-chave JavaScript."""
        corrections = {
            r'\bfuntion\b': 'function',  # Erro comum de digitação
            r'\bretrun\b': 'return',
            r'\bfrom\b': 'from',
            r'\bimport\b': 'import',
            r'\bexport\b': 'export',
            r'\bconst\b': 'const',
            r'\blet\b': 'let',
            r'\bvar\b': 'var'
        }
        
        corrected_code = code
        for wrong, correct in corrections.items():
            if re.search(wrong.replace('\\b', ''), code) and wrong != correct:
                corrected_code = re.sub(wrong, correct, corrected_code)
                self.corrections_applied.append(f"Corrigida palavra-chave: {wrong.replace('\\b', '')} → {correct}")
        
        return corrected_code
    
    def _fix_function_declarations(self, code: str) -> str:
        """Corrige declarações de função malformadas."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Corrige function sem parênteses
            if 'function' in stripped and '(' not in stripped:
                # Adiciona parênteses vazios
                corrected_line = re.sub(r'function\s+(\w+)\s*{', r'function \1() {', line)
                if corrected_line != line:
                    corrected_lines.append(corrected_line)
                    self.corrections_applied.append(f"Adicionados parênteses em function: {stripped}")
                    continue
            
            # Corrige arrow functions malformadas
            if '=>' in stripped and not any(char in stripped for char in ['(', ')']):
                if '=' in stripped and not stripped.startswith('='):
                    parts = stripped.split('=>')
                    if len(parts) == 2:
                        param = parts[0].split('=')[-1].strip()
                        body = parts[1].strip()
                        if not param.startswith('('):
                            corrected_line = line.replace(param + '=>', f'({param}) =>')
                            corrected_lines.append(corrected_line)
                            self.corrections_applied.append(f"Adicionados parênteses em arrow function: {stripped}")
                            continue
            
            corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_template_literals(self, code: str) -> str:
        """Corrige template literals malformados."""
        # Conta backticks não balanceados
        backtick_count = code.count('`')
        
        if backtick_count % 2 == 1:
            corrected_code = code + '`'
            self.corrections_applied.append("Adicionado backtick faltante em template literal")
            return corrected_code
        
        return code
