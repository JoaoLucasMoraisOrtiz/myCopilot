"""
Agent Tool Executor Module

Responsável por executar comandos/ferramentas do agente.
"""

import json
import subprocess
import os
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
            if command == "analyze":
                return self._execute_analyze(args)
                
            elif command == "list_projects":
                return self._execute_list_projects()
                
            elif command == "list_classes":
                return self._execute_list_classes(args)
                
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
                
            elif command == "edit_code":
                return self._execute_edit_code(args)
                
            elif command == "final_answer":
                return self._execute_final_answer(args)
                
            elif command == "error":
                return self._execute_error(args)
                
            else:
                return self._execute_unknown_command(command or "unknown")
                
        except Exception as e:
            error_msg = f"❌ Erro ao executar comando '{command}': {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def _execute_analyze(self, args: list) -> str:
        """Executa comando analyze para analisar projeto externo."""
        if not args:
            return "❌ Erro: analyze requer caminho do projeto como argumento"
        
        project_path = args[0]
        result = self.toolbox.analyze_external_project(project_path)
        print(f"📊 analyze('{project_path}') concluído")
        return result
    
    def _execute_list_projects(self) -> str:
        """Executa comando list_projects."""
        result = self.toolbox.list_analyzed_projects()
        print("� list_projects retornou lista de projetos")
        return result
    
    def _execute_list_classes(self, args: list) -> str:
        """Executa comando list_classes com suporte a project_path."""
        project_path = args[0] if args else None
        result = self.toolbox.list_classes(project_path)
        print(f"📋 list_classes retornou classes do projeto '{project_path or 'principal'}'")
        return result
    
    def _execute_get_class_metadata(self, args: list) -> str:
        """Executa comando get_class_metadata com suporte a project_path."""
        if not args:
            return "❌ Erro: get_class_metadata requer nome da classe como argumento"
        
        class_name = args[0]
        project_path = args[1] if len(args) > 1 else None
        result = self.toolbox.get_class_metadata(class_name, project_path)
        print(f"📋 get_class_metadata('{class_name}', '{project_path or 'principal'}') retornou {len(result)} chars")
        return result
    
    def _execute_get_code(self, args: list) -> str:
        """Executa comando get_code com suporte a project_path."""
        if not args:
            return "❌ Erro: get_code requer nome da classe como argumento"
        
        class_name = args[0]
        method_name = args[1] if len(args) > 1 and args[1] else None
        
        # Verifica parâmetro abstracted
        abstracted = True  # padrão
        project_path = None
        
        # Processa argumentos opcionais
        for i in range(2, len(args)):
            arg = args[i]
            if isinstance(arg, bool):
                abstracted = arg
            elif arg in ['false', 'False', '0']:
                abstracted = False
            elif arg in ['true', 'True', '1']:
                abstracted = True
            elif isinstance(arg, str) and ('/' in arg or '\\' in arg):
                project_path = arg
        
        result = self.toolbox.get_code(class_name, method_name, abstracted, project_path)
        print(f"📋 get_code('{class_name}', '{method_name}', abstracted={abstracted}, project='{project_path or 'principal'}') retornou {len(result)} chars")
        return result
    
    def _execute_read_file(self, args: list) -> str:
        """Executa comando read_file com suporte a project_path."""
        if not args:
            return "❌ Erro: read_file requer caminho do arquivo como argumento"
        
        file_path = args[0]
        
        # Verifica parâmetros opcionais
        abstracted = True  # padrão
        project_path = None
        
        for i in range(1, len(args)):
            arg = args[i]
            if isinstance(arg, bool):
                abstracted = arg
            elif arg in ['false', 'False', '0']:
                abstracted = False
            elif arg in ['true', 'True', '1']:
                abstracted = True
            elif isinstance(arg, str) and ('/' in arg or '\\' in arg):
                project_path = arg
        
        result = self.toolbox.read_file(file_path, abstracted, project_path)
        print(f"📋 read_file('{file_path}', abstracted={abstracted}, project='{project_path or 'principal'}') retornou {len(result)} chars")
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
    
    def _execute_edit_code(self, args: list) -> str:
        """Executa comando edit_code para modificar trechos específicos de arquivos."""
        if len(args) < 3:
            return "❌ Erro: edit_code requer [file_path, old_code, new_code] como argumentos"
        
        file_path = args[0]
        old_code = args[1]
        new_code = args[2]
        
        # Validação e sanitização dos argumentos
        if not isinstance(file_path, str) or not file_path.strip():
            return "❌ Erro: file_path deve ser uma string não vazia"
        
        if not isinstance(old_code, str) or not old_code.strip():
            return "❌ Erro: old_code deve ser uma string não vazia"
        
        if not isinstance(new_code, str):
            return "❌ Erro: new_code deve ser uma string"
        
        # Resolve caminho absoluto do arquivo
        if not file_path.startswith('/'):
            full_path = Path(self.project_path) / file_path
        else:
            full_path = Path(file_path)
        
        try:
            # Verifica se o arquivo existe
            if not full_path.exists():
                return f"❌ Erro: Arquivo '{file_path}' não encontrado"
            
            # Lê o conteúdo atual do arquivo
            with open(full_path, "r", encoding="utf-8") as f:
                current_content = f.read()
            
            # Verifica se o trecho antigo existe no arquivo
            if old_code not in current_content:
                # Tenta versões com diferentes tipos de aspas
                old_code_variants = [
                    old_code.replace('"', "'"),  # Troca aspas duplas por simples
                    old_code.replace("'", '"'),  # Troca aspas simples por duplas
                    old_code.replace('\\"', '"'),  # Remove escape de aspas duplas
                    old_code.replace("\\'", "'"),  # Remove escape de aspas simples
                ]
                
                found_variant = None
                for variant in old_code_variants:
                    if variant in current_content:
                        found_variant = variant
                        old_code = variant  # Usa a variante encontrada
                        break
                
                if not found_variant:
                    return (f"❌ Erro: Trecho de código não encontrado no arquivo '{file_path}'\n"
                           f"🔍 Procurado: {repr(old_code)}\n"
                           f"💡 Dica: Verifique aspas e escape de caracteres")
            
            # Verifica quantas ocorrências existem
            occurrences = current_content.count(old_code)
            if occurrences > 1:
                return f"❌ Erro: Trecho ambíguo encontrado {occurrences} vezes no arquivo '{file_path}'. Use um trecho mais específico."
            
            # Aplica a substituição
            modified_content = current_content.replace(old_code, new_code)
            
            # Aplica correção automática se necessário
            corrected_content, corrections_log = self._apply_code_correction(file_path, modified_content)
            
            # Salva o arquivo modificado
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(corrected_content)
            
            # Atualiza o symbol_table após a modificação
            try:
                from analyzers.java_analyzer import build_symbol_table
                self.toolbox.symbol_table = build_symbol_table(str(Path(self.project_path)))
            except ImportError:
                print("⚠️ Aviso: Não foi possível atualizar symbol_table após edição")
            
            result = f"✅ Arquivo '{file_path}' editado com sucesso"
            if corrections_log:
                result += f"\n📝 Correções aplicadas:\n{corrections_log}"
            
            # Mostra um resumo da alteração
            result += f"\n📋 Alteração aplicada:"
            result += f"\n  - Linha(s) removida(s): {len(old_code.splitlines())} linha(s)"
            result += f"\n  - Linha(s) adicionada(s): {len(new_code.splitlines())} linha(s)"
            result += f"\n  - Trecho original: {repr(old_code[:50])}{'...' if len(old_code) > 50 else ''}"
            result += f"\n  - Novo trecho: {repr(new_code[:50])}{'...' if len(new_code) > 50 else ''}"
            
            print(f"✏️ {result}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Erro ao editar arquivo '{file_path}': {e}"
            print(error_msg)
            return error_msg
    
    def _execute_save_code(self, args: list, command: str) -> str:
        """Executa comando save_code ou create_file."""
        if len(args) < 2:
            return f"❌ Erro: {command} requer [filename, code_content] como argumentos"
        
        filename = args[0]
        code_content = args[1]
        
        # Tenta decodificar o conteúdo se for uma string JSON
        try:
            decoded_content = json.loads(code_content)
            # Se for um dict ou list, formata como JSON bonito
            if isinstance(decoded_content, (dict, list)):
                code_content = json.dumps(decoded_content, indent=2)
                print("ℹ️ Conteúdo decodificado e formatado como JSON.")
        except (json.JSONDecodeError, TypeError):
            # Se não for um JSON válido, usa o conteúdo como está
            print("ℹ️ Conteúdo não é uma string JSON, usando como texto plano.")
            pass
        
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
            from analyzers.java_analyzer import build_symbol_table
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
        """Executa comando final_answer com build automático."""
        answer = args[0] if args else "[final_answer sem conteúdo]"
        print(f"🎯 final_answer - iniciando verificação de build...")
        
        # Tenta executar build e corrigir erros automaticamente
        build_success = self._auto_build_and_fix()
        
        if build_success:
            print("✅ Build concluído com sucesso!")
            return f"{answer}\n\n✅ Projeto compilado com sucesso - sem erros!"
        else:
            print("❌ Build falhou mesmo após tentativas de correção")
            return f"{answer}\n\n❌ Aviso: Projeto ainda possui erros de compilação"
    
    def _execute_error(self, args: list) -> str:
        """Executa comando error."""
        error_msg = args[0] if args else "Erro desconhecido"
        print(f"❌ Comando de erro: {error_msg}")
        return error_msg
    
    def _execute_unknown_command(self, command: str) -> str:
        """Trata comando desconhecido."""
        error_msg = (f"Erro: Comando '{command}' desconhecido. "
                    f"Comandos disponíveis: analyze, list_projects, list_classes, get_class_metadata, get_code, "
                    f"read_file, continue_reading, save_code, create_file, edit_code, final_answer")
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
        
        return language_map.get(extension, "")
    
    def _auto_build_and_fix(self, max_iterations: int = 3) -> bool:
        """
        Executa build automático e tenta corrigir erros usando LLM.
        
        Args:
            max_iterations: Número máximo de tentativas de correção
            
        Returns:
            True se o build foi bem-sucedido, False caso contrário
        """
        print("🔨 Iniciando processo de build automático...")
        
        # Detecta tipo de projeto e comando de build
        build_command = self._detect_build_command()
        if not build_command:
            print("⚠️ Tipo de projeto não suportado para build automático")
            return False
        
        for iteration in range(max_iterations):
            print(f"\n🔄 Tentativa de build {iteration + 1}/{max_iterations}")
            
            # Executa build
            build_result = self._execute_build_command(build_command)
            
            if build_result["success"]:
                print("✅ Build executado com sucesso!")
                return True
            
            print(f"❌ Build falhou na tentativa {iteration + 1}")
            print(f"📝 Erros encontrados:\n{build_result['error_output']}")
            
            # Se não é a última iteração, tenta corrigir com LLM
            if iteration < max_iterations - 1:
                print("🤖 Chamando LLM para corrigir erros...")
                correction_success = self._fix_build_errors_with_llm(build_result["error_output"])
                
                if not correction_success:
                    print("⚠️ LLM não conseguiu corrigir os erros")
                    break
            else:
                print("⚠️ Número máximo de tentativas atingido")
        
        return False
    
    def _detect_build_command(self) -> str:
        """
        Detecta o comando de build apropriado baseado no projeto.
        
        Returns:
            Comando de build ou string vazia se não suportado
        """
        project_path = Path(self.project_path)
        
        # Maven
        if (project_path / "pom.xml").exists():
            return "mvn clean install"
        
        # Gradle
        if (project_path / "build.gradle").exists() or (project_path / "build.gradle.kts").exists():
            # Verifica se tem gradlew
            if (project_path / "gradlew").exists():
                return "./gradlew build"
            else:
                return "gradle build"
        
        # Ant (menos comum)
        if (project_path / "build.xml").exists():
            return "ant"
        
        print("⚠️ Nenhum arquivo de build reconhecido (pom.xml, build.gradle, build.xml)")
        return ""
    
    def _execute_build_command(self, command: str) -> Dict[str, Any]:
        """
        Executa o comando de build e captura output/erros.
        
        Args:
            command: Comando de build a ser executado
            
        Returns:
            Dict com 'success', 'output', 'error_output'
        """
        try:
            print(f"🔨 Executando: {command}")
            
            # Executa comando no diretório do projeto
            result = subprocess.run(
                command.split(),
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error_output": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error_output": "❌ Build timeout (mais de 5 minutos)",
                "return_code": -1
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error_output": f"❌ Comando '{command.split()[0]}' não encontrado. Certifique-se de que está instalado e no PATH.",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error_output": f"❌ Erro ao executar build: {str(e)}",
                "return_code": -1
            }
    
    def _fix_build_errors_with_llm(self, error_output: str) -> bool:
        """
        Usa o LLM para analisar erros de build e sugerir correções.
        
        Args:
            error_output: Output de erro do build
            
        Returns:
            True se conseguiu aplicar correções, False caso contrário
        """
        try:
            # Prepara prompt para o LLM
            prompt = self._create_error_fix_prompt(error_output)
            
            # Chama LLM através da interface do agente
            from core.agent.llm_interface import AgentLLMInterface
            llm = AgentLLMInterface()
            
            # Simula mensagens para chamar o LLM
            messages = [
                {"role": "system", "content": "Você é um especialista em correção de erros de build Java. Analise os erros e forneça correções específicas."},
                {"role": "user", "content": prompt}
            ]
            
            response = llm.call_llm(messages, 1)
            
            # Analisa resposta e aplica correções
            return self._apply_llm_corrections(response)
            
        except Exception as e:
            print(f"❌ Erro ao chamar LLM para correção: {e}")
            return False
    
    def _create_error_fix_prompt(self, error_output: str) -> str:
        """
        Cria prompt especializado para correção de erros de build.
        
        Args:
            error_output: Output de erro do build
            
        Returns:
            Prompt formatado para o LLM
        """
        # Lista arquivos do projeto para contexto
        project_files = self._get_project_files_list()
        
        prompt = f"""
ERROS DE BUILD DETECTADOS:

{error_output}

ARQUIVOS DO PROJETO:
{project_files}

INSTRUÇÕES:
1. Analise os erros de build acima
2. Identifique os arquivos que precisam ser corrigidos
3. Para cada correção necessária, use o formato JSON:

{{
    "command": "save_code",
    "args": ["caminho/arquivo.java", "conteúdo_corrigido_completo"]
}}

4. Forneça apenas as correções necessárias para resolver os erros de build
5. Mantenha toda a lógica existente, apenas corrija os problemas identificados
6. Se precisar de informações sobre algum arquivo específico, use:

{{
    "command": "read_file", 
    "args": ["caminho/arquivo.java"]
}}

Concentre-se em:
- Imports faltando ou incorretos
- Problemas de sintaxe
- Tipos incompatíveis
- Métodos ou classes não encontradas
- Problemas de dependências Maven/Gradle

Responda apenas com os comandos JSON necessários para corrigir os erros.
"""
        return prompt
    
    def _get_project_files_list(self) -> str:
        """
        Obtém lista dos arquivos do projeto para contexto.
        
        Returns:
            String com lista de arquivos relevantes
        """
        try:
            project_path = Path(self.project_path)
            java_files = list(project_path.rglob("*.java"))
            xml_files = list(project_path.rglob("pom.xml")) + list(project_path.rglob("*.gradle"))
            
            files_list = []
            
            # Adiciona arquivos Java (limitado para não sobrecarregar)
            for java_file in java_files[:20]:  # Máximo 20 arquivos
                rel_path = java_file.relative_to(project_path)
                files_list.append(f"  - {rel_path}")
            
            if len(java_files) > 20:
                files_list.append(f"  - ... e mais {len(java_files) - 20} arquivos .java")
            
            # Adiciona arquivos de build
            for build_file in xml_files:
                rel_path = build_file.relative_to(project_path)
                files_list.append(f"  - {rel_path}")
            
            return "\n".join(files_list)
            
        except Exception as e:
            return f"Erro ao listar arquivos: {e}"
    
    def _apply_llm_corrections(self, llm_response: str) -> bool:
        """
        Aplica as correções sugeridas pelo LLM.
        
        Args:
            llm_response: Resposta do LLM com correções
            
        Returns:
            True se conseguiu aplicar pelo menos uma correção
        """
        try:
            # Parse da resposta para extrair comandos JSON
            commands = self._extract_commands_from_response(llm_response)
            
            if not commands:
                print("⚠️ Nenhum comando de correção encontrado na resposta do LLM")
                return False
            
            corrections_applied = 0
            
            for command in commands:
                try:
                    if command.get("command") == "save_code":
                        result = self._execute_save_code(command.get("args", []), "save_code")
                        if "✅" in result:
                            corrections_applied += 1
                            print(f"✅ Correção aplicada: {command['args'][0]}")
                        else:
                            print(f"❌ Falha ao aplicar correção: {result}")
                    
                    elif command.get("command") == "read_file":
                        # LLM solicitou ler arquivo para mais contexto
                        file_content = self._execute_read_file(command.get("args", []))
                        print(f"📖 LLM solicitou leitura de arquivo: {command['args'][0]}")
                        # Aqui poderíamos chamar o LLM novamente com o conteúdo do arquivo
                        
                except Exception as e:
                    print(f"❌ Erro ao aplicar comando {command}: {e}")
                    continue
            
            print(f"📊 Total de correções aplicadas: {corrections_applied}")
            return corrections_applied > 0
            
        except Exception as e:
            print(f"❌ Erro ao aplicar correções do LLM: {e}")
            return False
    
    def _extract_commands_from_response(self, response: str) -> list:
        """
        Extrai comandos JSON da resposta do LLM.
        
        Args:
            response: Resposta completa do LLM
            
        Returns:
            Lista de comandos extraídos
        """
        import re
        
        commands = []
        
        # Procura por blocos JSON na resposta
        json_pattern = r'\{[^{}]*"command"[^{}]*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                command = json.loads(match)
                commands.append(command)
            except json.JSONDecodeError:
                continue
        
        # Se não encontrou JSONs simples, tenta extrair de blocos de código
        if not commands:
            code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            code_matches = re.findall(code_block_pattern, response, re.DOTALL)
            
            for match in code_matches:
                try:
                    command = json.loads(match)
                    if "command" in command:
                        commands.append(command)
                except json.JSONDecodeError:
                    continue
        
        return commands
