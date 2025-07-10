"""
Java Code Corrector

Implementação específica para correção de código Java.
"""

import subprocess
import re
from typing import List, Dict, Any
from .base_corrector import BaseCodeCorrector


class JavaCorrector(BaseCodeCorrector):
    """Corretor específico para código Java."""
    
    def _compile_code(self, code: str) -> Dict[str, Any]:
        """
        Compila código Java usando javac.
        """
        errors = []
        
        # Extrai o nome da classe do código
        class_name = self._extract_class_name(code)
        if not class_name:
            errors.append("Não foi possível identificar o nome da classe Java")
            return {'success': False, 'errors': errors}
        
        # Cria arquivo temporário com o nome correto da classe
        temp_file = self._create_temp_file(code, '.java')
        
        # Renomeia para o nome correto da classe
        import os
        temp_dir = os.path.dirname(temp_file)
        correct_name = os.path.join(temp_dir, f'{class_name}.java')
        os.rename(temp_file, correct_name)
        temp_file = correct_name
        
        try:
            result = subprocess.run(
                ['javac', temp_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                # Processa erros do javac
                error_lines = result.stderr.strip().split('\n')
                for line in error_lines:
                    if line.strip() and not line.startswith('Note:'):
                        errors.append(line.strip())
            
        except subprocess.TimeoutExpired:
            errors.append("Timeout durante compilação Java")
        except FileNotFoundError:
            errors.append("javac não encontrado no PATH")
        except Exception as e:
            errors.append(f"Erro durante compilação Java: {str(e)}")
        finally:
            self._cleanup_temp_file(temp_file)
            # Remove também o .class se foi gerado
            class_file = temp_file.replace('.java', '.class')
            self._cleanup_temp_file(class_file)
        
        return {
            'success': len(errors) == 0,
            'errors': errors
        }
    
    def _extract_class_name(self, code: str) -> str:
        """Extrai o nome da classe principal do código Java."""
        # Procura por "public class ClassName"
        pattern = r'public\s+class\s+(\w+)'
        match = re.search(pattern, code)
        if match:
            return match.group(1)
        
        # Se não encontrou, procura por "class ClassName"
        pattern = r'class\s+(\w+)'
        match = re.search(pattern, code)
        if match:
            return match.group(1)
        
        return None
    
    def _fix_unclosed_comments(self, line: str) -> str:
        """Corrige comentários Java não fechados."""
        result = line
        
        # Conta comentários de bloco /* */
        block_start = line.count('/*')
        block_end = line.count('*/')
        
        if block_start > block_end:
            result += ' */'
            self.corrections_applied.append("Adicionado '*/' faltante")
        
        return result
    
    def _fix_language_specific_errors(self, code: str, errors: List[str]) -> str:
        """Aplica correções específicas do Java."""
        corrected_code = code
        
        # Correção de ponto e vírgula faltante
        corrected_code = self._fix_missing_semicolons(corrected_code)
        
        # Correção de chaves faltantes
        corrected_code = self._fix_missing_braces(corrected_code)
        
        # Correção de imports
        corrected_code = self._fix_java_imports(corrected_code)
        
        # Correção de modificadores de acesso
        corrected_code = self._fix_access_modifiers(corrected_code)
        
        return corrected_code
    
    def _fix_missing_semicolons(self, code: str) -> str:
        """Adiciona ponto e vírgula faltante em statements Java."""
        lines = code.split('\n')
        corrected_lines = []
        
        # Padrões que precisam de ponto e vírgula
        statement_patterns = [
            r'^\s*\w+\s+\w+.*[^;{}\s]$',  # Declarações de variáveis
            r'^\s*\w+\s*\([^)]*\)\s*[^;{]$',  # Chamadas de método
            r'^\s*return\s+.*[^;]$',  # Return statements
            r'^\s*\w+\s*=\s*.*[^;]$',  # Atribuições
            r'^\s*\w+\s*\+\+\s*$',  # Incrementos
            r'^\s*\w+\s*--\s*$',  # Decrementos
        ]
        
        for line in lines:
            stripped = line.strip()
            
            # Ignora linhas vazias, comentários e algumas estruturas
            if (not stripped or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*') or
                stripped.endswith('{') or
                stripped.endswith('}') or
                stripped.endswith(';') or
                any(keyword in stripped for keyword in ['if', 'else', 'for', 'while', 'switch', 'case', 'default:', 'class', 'interface', 'enum'])):
                corrected_lines.append(line)
                continue
            
            # Verifica se precisa de ponto e vírgula
            needs_semicolon = any(re.match(pattern, line) for pattern in statement_patterns)
            
            if needs_semicolon:
                corrected_lines.append(line.rstrip() + ';')
                self.corrections_applied.append(f"Adicionado ';' faltante na linha: {stripped}")
            else:
                corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_missing_braces(self, code: str) -> str:
        """Adiciona chaves faltantes em estruturas de controle."""
        lines = code.split('\n')
        corrected_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Detecta estruturas de controle sem chaves
            control_keywords = ['if', 'else', 'for', 'while']
            
            if any(keyword in stripped for keyword in control_keywords) and not stripped.endswith('{'):
                corrected_lines.append(line.rstrip() + ' {')
                
                # Procura a próxima linha com código
                i += 1
                while i < len(lines) and lines[i].strip() == '':
                    corrected_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    # Adiciona a linha seguinte com indentação
                    next_line = lines[i]
                    corrected_lines.append('    ' + next_line.lstrip())
                    corrected_lines.append('}')
                    self.corrections_applied.append(f"Adicionadas chaves para: {stripped}")
                
            else:
                corrected_lines.append(line)
            
            i += 1
        
        return '\n'.join(corrected_lines)
    
    def _fix_java_imports(self, code: str) -> str:
        """Corrige imports Java malformados."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Corrige import sem ponto e vírgula
            if stripped.startswith('import ') and not stripped.endswith(';'):
                corrected_line = line.rstrip() + ';'
                corrected_lines.append(corrected_line)
                self.corrections_applied.append(f"Adicionado ';' em import: {stripped}")
            else:
                corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _fix_access_modifiers(self, code: str) -> str:
        """Corrige problemas com modificadores de acesso."""
        lines = code.split('\n')
        corrected_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Adiciona 'public' em métodos main sem modificador
            if 'static void main' in stripped and not any(mod in stripped for mod in ['public', 'private', 'protected']):
                corrected_line = line.replace('static void main', 'public static void main')
                corrected_lines.append(corrected_line)
                self.corrections_applied.append("Adicionado 'public' ao método main")
            else:
                corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
