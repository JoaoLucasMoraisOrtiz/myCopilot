"""
Agent Tool Executor Module

Responsável por executar comandos/ferramentas do agente.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
from core.code_corrector import get_corrector_for_language


class AgentToolExecutor:
    """Classe responsável por executar ferramentas/comandos do agente."""
    
    def __init__(self, toolbox, project_path: str):
        self.toolbox = toolbox
        self.project_path = project_path
    
    def execute_tool(self, action_json: Dict[str, Any]) -> str:
        """
        Executa a ferramenta especificada na ação.
        
        Args:
            action_json: Dict com 'command' e 'args'
            
        Returns:
            Resultado da execução como string
        """
        command = action_json.get("command")
        args = action_json.get("args", [])
        
        # Remove parênteses do comando se presente
        if command and command.endswith("()"):
            command = command[:-2]
        
        print(f"🔧 Executando comando: '{command}' com args: {args}")
        
        try:
            if command == "list_classes":
                return self._execute_list_classes()
                
            elif command == "get_class_metadata":
                return self._execute_get_class_metadata(args)
                
            elif command == "get_code":
                return self._execute_get_code(args)
                
            elif command == "read_file":
                return self._execute_read_file(args)
                
            elif command == "continue_reading":
                return self._execute_continue_reading(args)
                
            elif command in ["save_code", "create_file"]:
                return self._execute_save_code(args, command)
                
            elif command == "final_answer":
                return self._execute_final_answer(args)
                
            elif command == "error":
                return self._execute_error(args)
                
            else:
                return self._execute_unknown_command(command)
                
        except Exception as e:
            error_msg = f"❌ Erro ao executar comando '{command}': {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def _execute_list_classes(self) -> str:
        """Executa comando list_classes."""
        result = self.toolbox.list_classes()
        print(f"📋 list_classes retornou {len(result.split('\n')) if result else 0} classes")
        return result
    
    def _execute_get_class_metadata(self, args: list) -> str:
        """Executa comando get_class_metadata."""
        if not args:
            return "❌ Erro: get_class_metadata requer nome da classe como argumento"
        
        class_name = args[0]
        result = self.toolbox.get_class_metadata(class_name)
        print(f"📋 get_class_metadata('{class_name}') retornou {len(result)} chars")
        return result
    
    def _execute_get_code(self, args: list) -> str:
        """Executa comando get_code."""
        if not args:
            return "❌ Erro: get_code requer nome da classe como argumento"
        
        # Verifica parâmetro abstracted
        abstracted = True  # padrão
        if len(args) > 2 and isinstance(args[2], bool):
            abstracted = args[2]
        elif len(args) > 2 and args[2] in ['false', 'False', '0']:
            abstracted = False
        
        class_name = args[0]
        method_name = args[1] if len(args) > 1 else None
        result = self.toolbox.get_code(class_name, method_name, abstracted=abstracted)
        print(f"📋 get_code('{class_name}', '{method_name}', abstracted={abstracted}) retornou {len(result)} chars")
        return result
    
    def _execute_read_file(self, args: list) -> str:
        """Executa comando read_file."""
        if not args:
            return "❌ Erro: read_file requer caminho do arquivo como argumento"
        
        # Verifica parâmetro abstracted
        abstracted = True  # padrão
        if len(args) > 1 and isinstance(args[1], bool):
            abstracted = args[1]
        elif len(args) > 1 and args[1] in ['false', 'False', '0']:
            abstracted = False
        
        file_path = args[0]
        result = self.toolbox.read_file(file_path, abstracted=abstracted)
        print(f"📋 read_file('{file_path}', abstracted={abstracted}) retornou {len(result)} chars")
        return result
    
    def _execute_continue_reading(self, args: list) -> str:
        """Executa comando continue_reading."""
        if not args:
            return "❌ Erro: continue_reading requer ID de abstração como argumento"
        
        abstraction_id = args[0]
        page = args[1] if len(args) > 1 else 1
        result = self.toolbox.continue_reading(abstraction_id, page)
        print(f"📋 continue_reading('{abstraction_id}', page={page}) retornou {len(result)} chars")
        return result
    
    def _execute_save_code(self, args: list, command: str) -> str:
        """Executa comando save_code ou create_file."""
        if len(args) < 2:
            return f"❌ Erro: {command} requer [filename, code_content] como argumentos"
        
        filename = args[0]
        code_content = args[1]
        
        # Aplica correção automática se necessário
        corrected_code, corrections_log = self._apply_code_correction(filename, code_content)
        
        # Salva o arquivo no diretório do projeto
        output_dir = Path(self.project_path)
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(corrected_code)
            
            # Atualiza o symbol_table após salvar
            from core.agent.agent_core import build_symbol_table
            self.toolbox.symbol_table = build_symbol_table(str(output_dir))
            
            result = f"✅ Arquivo '{filename}' salvo com sucesso em {file_path}"
            if corrections_log:
                result += f"\n🔧 Correções aplicadas: {corrections_log}"
            print(f"💾 {result}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Erro ao salvar arquivo '{filename}': {e}"
            print(error_msg)
            return error_msg
    
    def _execute_final_answer(self, args: list) -> str:
        """Executa comando final_answer."""
        answer = args[0] if args else "[final_answer sem conteúdo]"
        print(f"🎯 final_answer retornando resposta com {len(answer)} chars")
        return answer
    
    def _execute_error(self, args: list) -> str:
        """Executa comando error."""
        error_msg = args[0] if args else "Erro desconhecido"
        print(f"❌ Comando de erro: {error_msg}")
        return error_msg
    
    def _execute_unknown_command(self, command: str) -> str:
        """Trata comando desconhecido."""
        error_msg = (f"Erro: Comando '{command}' desconhecido. "
                    f"Comandos disponíveis: list_classes, get_class_metadata, get_code, "
                    f"read_file, continue_reading, save_code, create_file, final_answer")
        print(f"❌ {error_msg}")
        return error_msg
    
    def _apply_code_correction(self, filename: str, code_content: str) -> Tuple[str, str]:
        """
        Aplica correção automática de código usando o mini-compilador corretor.
        
        Args:
            filename: Nome do arquivo para detectar a linguagem
            code_content: Conteúdo do código a ser corrigido
            
        Returns:
            Tuple com (código_corrigido, log_de_correções)
        """
        try:
            # Detecta a linguagem baseada na extensão do arquivo
            language = self._detect_language_from_filename(filename)
            
            if not language:
                return code_content, ""
            
            print(f"🔍 Detectada linguagem '{language}' para arquivo '{filename}'")
            
            # Obtém o corretor apropriado
            corrector = get_corrector_for_language(language)
            
            # Aplica as correções
            print("🔧 Aplicando correções automáticas...")
            result = corrector.correct(code_content)
            
            # Prepara o log de correções
            corrections_log = ""
            if result.corrections_applied:
                corrections_count = len(result.corrections_applied)
                sample_corrections = result.corrections_applied[:3]
                corrections_log = f"{corrections_count} correções aplicadas: {', '.join(sample_corrections)}"
                if corrections_count > 3:
                    corrections_log += f" (e mais {corrections_count - 3})"
            
            # Se a compilação falhou mesmo após correções, registra o aviso
            if not result.compilation_successful and result.error_messages:
                error_summary = result.error_messages[0] if result.error_messages else "erro desconhecido"
                corrections_log += f" | ⚠️ Ainda há erros: {error_summary}"
            
            if result.corrections_applied:
                print(f"✅ {corrections_log}")
            else:
                print("✅ Nenhuma correção necessária - código já está correto")
            
            return result.corrected_code, corrections_log
            
        except ValueError as e:
            # Linguagem não suportada
            print(f"⚠️ {str(e)}")
            return code_content, f"⚠️ {str(e)}"
        except Exception as e:
            # Erro durante correção
            error_msg = f"⚠️ Erro na correção automática: {str(e)}"
            print(error_msg)
            return code_content, error_msg
    
    def _detect_language_from_filename(self, filename: str) -> str:
        """
        Detecta a linguagem de programação baseada na extensão do arquivo.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Nome da linguagem ou None se não suportada
        """
        extension = Path(filename).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.mjs': 'javascript',
            '.cjs': 'javascript'
        }
        
        return language_map.get(extension, None)
