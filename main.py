""" 
    Antes de iniciar execute em outro terminal: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug --remote-allow-origins=*
"""

import os
import sys
import json
from datetime import datetime
from migration_prompts import PROMPTS
from helper.context_manager import save_md, load_context, append_to_context
from llm_client import LLMClient
from helper.code_parser import extract_code_blocks, save_code_to_file, extract_structured_code_blocks, save_structured_code_block
from helper.task_manager import TaskManager
from code_analyzer import CodeAnalyzer
from project_structure_manager import ProjectStructureManager
from migration_config_manager import MigrationConfigManager
from smart_context_manager import SmartContextManager

OUTPUT_DIR = "migration_docs"
CODE_DIR = os.path.join(OUTPUT_DIR, "generated_code")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CODE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Variável global para diretório do sistema legado
LEGACY_DIRECTORY = None

# Inicializa os gerenciadores
project_manager = ProjectStructureManager(OUTPUT_DIR)
config_manager = MigrationConfigManager(OUTPUT_DIR)
smart_context = SmartContextManager(OUTPUT_DIR, max_context_size=8000)

def log_llm_interaction(prompt_key, prompt_text, response_text, context_size=0, token_estimate=0):
    """Registra interações com o LLM para análise e debug"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Cria log estruturado
    log_entry = {
        "timestamp": timestamp,
        "prompt_key": prompt_key,
        "context_size_chars": context_size,
        "token_estimate": token_estimate,
        "prompt_text": prompt_text,
        "response_text": response_text,
        "response_size_chars": len(response_text)
    }
    
    # Salva log JSON para análise programática
    json_log_file = os.path.join(LOGS_DIR, f"llm_log_{timestamp}.json")
    with open(json_log_file, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, ensure_ascii=False, indent=2)
    
    # Salva log markdown para leitura humana
    md_log_file = os.path.join(LOGS_DIR, f"llm_log_{timestamp}.md")
    log_content = f"""# Log LLM Interaction - {timestamp}

## 📋 Metadados
- **Prompt Key:** {prompt_key}
- **Timestamp:** {timestamp}
- **Context Size:** {context_size:,} caracteres
- **Token Estimate:** {token_estimate:,} tokens
- **Response Size:** {len(response_text):,} caracteres

## 📤 PROMPT ENVIADO
```
{prompt_text}
```

## 📥 RESPOSTA RECEBIDA
{response_text}

---
*Log gerado automaticamente pelo sistema de migração*
"""
    
    save_md(md_log_file, log_content)
    
    # Adiciona entrada ao log consolidado
    consolidated_log = os.path.join(LOGS_DIR, "consolidated_log.md")
    summary_entry = f"""
## {timestamp} - {prompt_key}
- **Context:** {context_size:,} chars
- **Response:** {len(response_text):,} chars
- **Files:** `llm_log_{timestamp}.json`, `llm_log_{timestamp}.md`

"""
    append_to_context(consolidated_log, summary_entry)
    
    print(f"📝 Log salvo: llm_log_{timestamp}.json/.md")
    return json_log_file, md_log_file

def run_prompt_with_llm(llm_client, prompt_key, doc_filename, context_files=None, legacy_directory=None):
    print(f"\n=== {prompt_key} ===")
    print("Enviando prompt para o LLM...")
    
    # Constrói contexto completo
    full_context = build_comprehensive_context(context_files, legacy_directory)
    
    # Combina contexto com prompt
    if full_context:
        full_prompt = f"{full_context}\n\n---\n\n{PROMPTS[prompt_key]}"
    else:
        full_prompt = PROMPTS[prompt_key]
    
    # Calcula estimativa de tokens (aproximadamente 4 caracteres por token)
    context_size = len(full_context) if full_context else 0
    total_prompt_size = len(full_prompt)
    token_estimate = total_prompt_size // 4
    
    print(f"📊 Context: {context_size:,} chars | Total: {total_prompt_size:,} chars | ~{token_estimate:,} tokens")
    
    # Envia para LLM
    response = llm_client.send_prompt(full_prompt)
    
    # Registra interação no log
    log_llm_interaction(prompt_key, full_prompt, response, context_size, token_estimate)
    
    # Salva resposta
    save_md(os.path.join(OUTPUT_DIR, doc_filename), response)
    print(f"Resposta salva em: {doc_filename}")
    
    # Extrai código se houver
    code_blocks = extract_code_blocks(response)
    if code_blocks:
        print(f"Encontrados {len(code_blocks)} blocos de código")
        for i, block in enumerate(code_blocks):
            code_filename = f"{doc_filename[:-3]}_{i}.{block['language']}"
            code_path = os.path.join(CODE_DIR, code_filename)
            save_code_to_file(block['code'], code_path)
            print(f"Código salvo em: {code_filename}")
    
    return response

def build_comprehensive_context(context_files=None, legacy_directory=None):
    """Constrói contexto completo incluindo Fase 0, workspace legado e contexto anterior"""
    context_parts = []
    
    # 1. CONTEXTO DA FASE 0 (Configuração de Migração) - SEMPRE INCLUIR SE DISPONÍVEL
    try:
        # Verifica se há configuração carregada
        if hasattr(config_manager, 'requirements') and config_manager.requirements:
            migration_context = config_manager.generate_migration_context()
            if migration_context and migration_context.strip():
                # Remove header duplicado se existir
                clean_migration = migration_context.replace("## 🎯 CONFIGURAÇÃO DE MIGRAÇÃO (FASE 0)", "")
                context_parts.append(f"# CONFIGURAÇÃO DA MIGRAÇÃO (FASE 0)\n{clean_migration.strip()}")
    except Exception as e:
        print(f"⚠️ Erro ao carregar contexto da migração: {e}")
    
    # 2. CONTEXTO DO WORKSPACE LEGADO  
    if legacy_directory and os.path.exists(legacy_directory):
        legacy_context = build_legacy_workspace_context(legacy_directory)
        if legacy_context:
            context_parts.append(f"# SISTEMA LEGADO ANALISADO\n{legacy_context}")
    
    # 3. CONTEXTO ANTERIOR DAS FASES (apenas resultados principais, muito limitado)
    if context_files:
        previous_results = load_previous_results_only([os.path.join(OUTPUT_DIR, f) for f in context_files])
        if previous_results:
            # Limita drasticamente o contexto anterior já que temos RAG
            if len(previous_results) > 800:  # Reduz de 1500 para 800 chars
                previous_results = previous_results[:800] + "\n[...análises anteriores truncadas - use RAG para detalhes]"
            context_parts.append(f"# ANÁLISES ANTERIORES (RESUMO MÍNIMO)\n{previous_results}")
    
    return "\n\n".join(context_parts) if context_parts else ""

def build_smart_context_for_task(task_description: str, task_type: str = "implementation") -> str:
    """Constrói contexto otimizado tipo RAG para tasks específicas"""
    print(f"🧠 Construindo contexto inteligente para task ({task_type})...")
    
    # Usa o sistema de contexto inteligente
    smart_context_result = smart_context.build_smart_context_for_task(task_description, task_type)
    
    # Adiciona informações específicas do sistema legado se disponível
    if LEGACY_DIRECTORY and os.path.exists(LEGACY_DIRECTORY):
        legacy_summary = get_compact_legacy_summary(LEGACY_DIRECTORY)
        if legacy_summary:
            smart_context_result += f"\n\n# SISTEMA LEGADO (RESUMO)\n{legacy_summary}"
    
    return smart_context_result

def get_compact_legacy_summary(legacy_directory: str) -> str:
    """Obtém resumo super compacto do sistema legado (máximo 1000 chars)"""
    try:
        # Tecnologias detectadas (mais conciso)
        technologies = detect_technologies(legacy_directory)
        tech_summary = []
        for tech, indicators in technologies.items():
            tech_summary.append(f"{tech}({len(indicators)})")
        
        summary_parts = []
        
        if tech_summary:
            summary_parts.append(f"**Tecnologias**: {', '.join(tech_summary[:5])}")
        
        # Estrutura super compacta (só diretórios principais)
        main_dirs = []
        try:
            items = os.listdir(legacy_directory)
            for item in items[:10]:
                item_path = os.path.join(legacy_directory, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    main_dirs.append(item)
        except:
            pass
        
        if main_dirs:
            summary_parts.append(f"**Estrutura**: {', '.join(main_dirs[:8])}")
        
        # Arquivos de configuração importantes
        config_files = []
        try:
            for root, dirs, files in os.walk(legacy_directory):
                dirs[:] = [d for d in dirs if not d.startswith('.')][:3]  # Limita profundidade
                for file in files:
                    if file in ['pom.xml', 'web.xml', 'application.properties', 'package.json']:
                        rel_path = os.path.relpath(os.path.join(root, file), legacy_directory)
                        config_files.append(rel_path)
                        if len(config_files) >= 3:
                            break
                if len(config_files) >= 3:
                    break
        except:
            pass
        
        if config_files:
            summary_parts.append(f"**Configs**: {', '.join(config_files)}")
        
        return ' | '.join(summary_parts)
        
    except Exception as e:
        return f"Erro ao analisar sistema legado: {str(e)[:100]}"

def update_knowledge_base_after_phase(context_files):
    """Atualiza a base de conhecimento após cada fase"""
    print("📚 Atualizando base de conhecimento...")
    smart_context.update_from_files(context_files)
    
    # Mostra estatísticas
    stats = smart_context.get_context_stats()
    print(f"📊 KB Stats: {stats['total_documents']} docs, {stats['total_size']:,} chars")

def load_previous_results_only(file_paths):
    """Carrega apenas os resultados das fases anteriores, filtrando prompts de forma mais agressiva"""
    results = []
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Estratégia mais agressiva para remover prompts
                lines = content.split('\n')
                filtered_lines = []
                skip_section = False
                
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    
                    # Detecta início de seções de prompt (mais abrangente)
                    prompt_indicators = [
                        'prompt ', '**prompt', 'instruções para', 'desenvolva',
                        'importante:** detalhe', 'organize por sprints',
                        'considere as tecnologias', 'baseado na análise'
                    ]
                    
                    if any(indicator in line_lower for indicator in prompt_indicators):
                        skip_section = True
                        continue
                    
                    # Detecta fim de seção de prompt
                    if skip_section:
                        # Se encontra nova seção principal (# título), para de pular
                        if line.startswith('#') and not line.startswith('###'):
                            skip_section = False
                        # Se linha em branco seguida de texto sem indentação, pode ser fim de prompt
                        elif line.strip() == '' and i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith(' ') and not any(indicator in next_line.lower() for indicator in prompt_indicators):
                                skip_section = False
                        else:
                            continue
                    
                    # Remove linhas que claramente são instruções
                    if any(phrase in line_lower for phrase in [
                        'detalhe a execução', 'organize por sprints', 'deliverables claros',
                        'importante:**', 'instruções:', 'desenvolva planos'
                    ]):
                        continue
                    
                    # Inclui linha se não estiver em seção de prompt
                    if not skip_section:
                        filtered_lines.append(line)
                
                # Remove linhas vazias consecutivas e limita tamanho
                filtered_content = '\n'.join(filtered_lines)
                
                # Remove múltiplas linhas vazias consecutivas
                import re
                filtered_content = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_content)
                
                # Limita drasticamente o tamanho do contexto anterior
                if len(filtered_content) > 1000:  # Reduz de 2000 para 1000 caracteres
                    filtered_content = filtered_content[:1000] + "\n[...resumo truncado para otimização]"
                
                if filtered_content.strip():
                    filename = os.path.basename(file_path)
                    
                    # Extrai apenas as primeiras seções importantes
                    important_sections = []
                    current_section = []
                    section_title = None
                    
                    for line in filtered_content.split('\n'):
                        if line.startswith('##') and not line.startswith('###'):
                            # Salva seção anterior se tiver conteúdo relevante
                            if section_title and current_section:
                                section_content = '\n'.join(current_section)
                                if len(section_content.strip()) > 50:  # Só inclui seções com conteúdo substancial
                                    important_sections.append(f"{section_title}\n{section_content}")
                            
                            section_title = line
                            current_section = []
                        else:
                            current_section.append(line)
                    
                    # Salva última seção
                    if section_title and current_section:
                        section_content = '\n'.join(current_section)
                        if len(section_content.strip()) > 50:
                            important_sections.append(f"{section_title}\n{section_content}")
                    
                    # Usa apenas as 2 primeiras seções importantes
                    if important_sections:
                        final_content = '\n\n'.join(important_sections[:2])
                        results.append(f"## {filename}\n{final_content}")
                    
            except Exception as e:
                print(f"Erro ao carregar {file_path}: {e}")
    
    return '\n\n'.join(results)

def build_legacy_workspace_context(legacy_directory):
    """Constrói contexto compacto do workspace do sistema legado"""
    context_parts = []
    
    try:
        # Estrutura compacta de diretórios (máximo 1000 chars)
        structure = get_directory_structure(legacy_directory, max_depth=2)
        if structure:
            # Limita o tamanho da estrutura
            if len(structure) > 1000:
                lines = structure.split('\n')
                structure = '\n'.join(lines[:30]) + '\n[...truncated]'
            context_parts.append(f"## Estrutura\n```\n{structure}\n```")
        
        # Tecnologias detectadas (mais conciso)
        technologies = detect_technologies(legacy_directory)
        if technologies:
            tech_summary = []
            for tech, indicators in technologies.items():
                count = len(indicators)
                tech_summary.append(f"{tech}({count})")
            context_parts.append(f"## Tecnologias\n{', '.join(tech_summary[:8])}")  # Máximo 8 tecnologias
        
        # Apenas 2 amostras de código mais relevantes
        code_samples = get_code_samples(legacy_directory)
        if code_samples:
            context_parts.append("## Código Principal")
            sample_count = 0
            for file_path, content in code_samples.items():
                if sample_count >= 2:  # Reduz de 5 para 2 amostras
                    break
                relative_path = os.path.relpath(file_path, legacy_directory)
                # Limita cada amostra a 300 caracteres
                truncated_content = content[:300] + '...' if len(content) > 300 else content
                context_parts.append(f"### {relative_path}\n```{get_file_extension(file_path)}\n{truncated_content}\n```")
                sample_count += 1
        
    except Exception as e:
        context_parts.append(f"❌ Erro: {str(e)[:100]}")
    
    return "\n\n".join(context_parts) if context_parts else ""

def get_directory_structure(directory, max_depth=3, current_depth=0):
    """Obtém estrutura de diretórios de forma compacta"""
    if current_depth >= max_depth:
        return ""
    
    structure = []
    try:
        items = sorted(os.listdir(directory))
        # Filtra itens importantes e limita quantidade
        important_items = []
        other_items = []
        
        for item in items:  # aqui era limitado a 15 itens
            if item.startswith('.'):
                continue  # Pula arquivos ocultos
            item_path = os.path.join(directory, item)
            
            # Prioriza arquivos/pastas importantes
            if any(keyword in item.lower() for keyword in ['src', 'main', 'config', 'pom.xml', 'web.xml', 'service', 'controller']):
                important_items.append((item, item_path))
            else:
                other_items.append((item, item_path))
        
        # Combina priorizando importantes
        selected_items = important_items + other_items[:max(0, 15-len(important_items))]
        
        for item, item_path in selected_items:
            if os.path.isdir(item_path):
                structure.append(f"{item}/")
                if current_depth < max_depth - 1:
                    sub_structure = get_directory_structure(item_path, max_depth, current_depth + 1)
                    if sub_structure:
                        # Formato compacto: pasta/subpasta/arquivo
                        for line in sub_structure.split('\n'):
                            if line.strip():
                                structure.append(f"{item}/{line}")
            else:
                structure.append(item)
                
    except PermissionError:
        structure.append("[Access Denied]")
    
    return '\n'.join(structure)

def find_main_files(directory):
    """Encontra arquivos principais por tipo"""
    main_files = {
        "Configuração": [],
        "Build": [],
        "Código Principal": [],
        "Testes": [],
        "Documentação": []
    }
    
    config_files = [
        'pom.xml', 'build.gradle', 'package.json', 'requirements.txt',
        'web.xml', 'application.properties', 'application.yml',
        'Dockerfile', 'docker-compose.yml'
    ]
    
    build_files = ['Makefile', 'build.xml', 'build.gradle', 'pom.xml']
    doc_files = ['README.md', 'README.txt', 'CHANGELOG.md', 'docs']
    
    try:
        for root, dirs, files in os.walk(directory):
            # Evita diretórios de build/cache
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'node_modules', '__pycache__']]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_lower = file.lower()
                
                # Arquivos de configuração
                if file in config_files:
                    main_files["Configuração"].append(file_path)
                # Arquivos de build
                elif file in build_files:
                    main_files["Build"].append(file_path)
                # Testes
                elif 'test' in file_lower or file.endswith(('Test.java', 'test.py', 'spec.js')):
                    main_files["Testes"].append(file_path)
                # Documentação
                elif file in doc_files or file.endswith(('.md', '.txt', '.doc')):
                    main_files["Documentação"].append(file_path)
                # Código principal
                elif file.endswith(('.java', '.py', '.js', '.ts', '.cs', '.cpp', '.c')):
                    main_files["Código Principal"].append(file_path)
    
    except Exception as e:
        print(f"Erro ao analisar arquivos: {e}")
    
    return {k: v for k, v in main_files.items() if v}

def detect_technologies(directory):
    """Detecta tecnologias baseadas em arquivos encontrados (versão otimizada)"""
    technologies = {}
    file_count = 0
    max_files = 100  # Limita análise a 100 arquivos
    
    try:
        for root, dirs, files in os.walk(directory):
            if file_count >= max_files:
                break
                
            # Evita diretórios desnecessários
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'node_modules', '__pycache__']]
            
            for file in files[:10]:  # Máximo 10 arquivos por diretório
                if file_count >= max_files:
                    break
                    
                file_count += 1
                
                # Detecta tecnologias principais apenas
                if file.endswith('.java'):
                    technologies.setdefault('Java', []).append(file)
                elif file == 'pom.xml':
                    technologies.setdefault('Maven', []).append(file)
                elif file == 'web.xml':
                    technologies.setdefault('JavaEE', []).append(file)
                elif file.endswith('.py'):
                    technologies.setdefault('Python', []).append(file)
                elif file == 'package.json':
                    technologies.setdefault('NodeJS', []).append(file)
                elif file.endswith(('.html', '.jsp')):
                    technologies.setdefault('Web', []).append(file)
                elif file.endswith('.sql'):
                    technologies.setdefault('SQL', []).append(file)
    
    except Exception as e:
        print(f"Erro ao detectar tecnologias: {e}")
    
    # Retorna apenas as 5 tecnologias mais encontradas
    sorted_tech = sorted(technologies.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_tech[:5])

def get_code_samples(directory):
    """Obtém amostras compactas dos arquivos mais relevantes"""
    samples = {}
    sample_count = 0
    max_samples = 2  # Reduz de 5 para 2
    
    try:
        for root, dirs, files in os.walk(directory):
            if sample_count >= max_samples:
                break
                
            # Evita diretórios desnecessários
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'node_modules', '__pycache__', 'logs']]
            
            # Foca apenas em arquivos críticos
            critical_files = [f for f in files if any(keyword in f.lower() for keyword in [
                'main', 'app', 'service', 'controller', 'config', 'web.xml', 'pom.xml', 'application'
            ])]
            
            for file in critical_files:
                if sample_count >= max_samples:
                    break
                    
                if file.endswith(('.java', '.xml', '.properties', '.yml')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content.strip() and len(content) > 50:  # Apenas arquivos não vazios e relevantes
                                samples[file_path] = content
                                sample_count += 1
                    except Exception:
                        continue
    
    except Exception as e:
        print(f"Erro ao obter amostras de código: {e}")
    
    return samples

def get_file_extension(file_path):
    """Obtém extensão do arquivo para syntax highlighting"""
    ext = os.path.splitext(file_path)[1].lower()
    extension_map = {
        '.java': 'java',
        '.py': 'python', 
        '.js': 'javascript',
        '.ts': 'typescript',
        '.xml': 'xml',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.properties': 'properties',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json'
    }
    return extension_map.get(ext, 'text')

def fase0(llm_client=None):
    """Fase 0: Configuração de Migração - Coleta requisitos do usuário"""
    print("\n🚀 FASE 0: Configuração de Migração")
    print("Esta fase coleta suas preferências para personalizar todo o processo.")
    
    choice = input("\nComo deseja fornecer os requisitos?\n[1] Interativo [2] Arquivo YAML/JSON [3] Pular (usar padrão): ").strip()
    
    if choice == '1':
        # Coleta interativa
        requirements = config_manager.collect_user_requirements_interactive()
    elif choice == '2':
        # Carrega de arquivo
        file_path = input("Caminho do arquivo de configuração: ").strip()
        if os.path.exists(file_path):
            requirements = config_manager.load_requirements_from_file(file_path)
        else:
            print("❌ Arquivo não encontrado. Usando configuração padrão.")
            return None
    else:
        # Pula configuração
        print("⏭️ Pulando configuração personalizada. Usando padrão.")
        return None
    
    # Gera contexto inicial e salva
    migration_context = config_manager.generate_migration_context()
    
    # Inicializa contexto global com configuração do usuário
    global_context_file = os.path.join(OUTPUT_DIR, "global_context.md")
    initial_content = f"""# Contexto Global da Migração

**Iniciado em:** {__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{migration_context}

## 📊 Histórico de Feedback

Este arquivo contém o feedback acumulado de todas as validações e integrações realizadas durante o processo de migração.

"""
    save_md(global_context_file, initial_content)
    
    # Atualiza estrutura do projeto baseada nos requisitos
    config_manager.update_project_structure_config(project_manager)
    
    # Gera relatório de configuração
    summary = config_manager.generate_summary_report()
    summary_file = os.path.join(OUTPUT_DIR, "migration_configuration.md")
    save_md(summary_file, summary)
    
    print("✅ Configuração concluída!")
    print(f"📄 Configuração salva em: {summary_file}")
    print(f"🔧 Contexto global inicializado com suas preferências")
    
    return requirements

def fase1(llm_client):
    print("\n🏗️  FASE 1: Análise do Sistema Legado")
    
    # Solicita diretório do sistema legado se não foi definido
    global LEGACY_DIRECTORY
    if not LEGACY_DIRECTORY or not os.path.exists(LEGACY_DIRECTORY):
        LEGACY_DIRECTORY = input("\n📁 Caminho do diretório do sistema legado: ").strip()
        
        if not os.path.exists(LEGACY_DIRECTORY):
            print(f"❌ Diretório não encontrado: {LEGACY_DIRECTORY}")
            print("💡 Dica: Use um caminho absoluto para o diretório do código legado")
            return []
    
    print(f"✅ Analisando sistema legado em: {LEGACY_DIRECTORY}")
    
    context_files = []
    
    run_prompt_with_llm(llm_client, "P1_1", "architecture-analysis.md", context_files, LEGACY_DIRECTORY)
    context_files.append("architecture-analysis.md")
    
    run_prompt_with_llm(llm_client, "P1_2", "business-flows.md", context_files, LEGACY_DIRECTORY)
    context_files.append("business-flows.md")
    
    run_prompt_with_llm(llm_client, "P1_3", "dependencies-analysis.md", context_files, LEGACY_DIRECTORY)
    context_files.append("dependencies-analysis.md")
    
    # Atualiza base de conhecimento após Fase 1
    update_knowledge_base_after_phase(context_files)
    
    return context_files

def fase2(llm_client, context_files):
    print("\n🗺️  FASE 2: Construção do Roadmap")
    
    run_prompt_with_llm(llm_client, "P2_1", "technical-glossary.md", context_files, LEGACY_DIRECTORY)
    context_files.append("technical-glossary.md")
    
    run_prompt_with_llm(llm_client, "P2_2", "component-roadmap.md", context_files, LEGACY_DIRECTORY)
    context_files.append("component-roadmap.md")
    
    run_prompt_with_llm(llm_client, "P2_3", "risk-analysis.md", context_files, LEGACY_DIRECTORY)
    context_files.append("risk-analysis.md")
    
    # Atualiza base de conhecimento após Fase 2
    update_knowledge_base_after_phase(context_files)
    
    return context_files

def fase3(llm_client, context_files):
    print("\n📋 FASE 3: Criação de Tasks")
    
    run_prompt_with_llm(llm_client, "P3_1", "target-architecture.md", context_files, LEGACY_DIRECTORY)
    context_files.append("target-architecture.md")
    
    # Configura estrutura do projeto baseada na arquitetura alvo
    target_arch_file = os.path.join(OUTPUT_DIR, "target-architecture.md")
    if os.path.exists(target_arch_file):
        with open(target_arch_file, 'r', encoding='utf-8') as f:
            target_architecture_content = f.read()
        
        print("🏗️ Configurando estrutura do novo sistema...")
        project_manager.update_structure_from_target_architecture(target_architecture_content)
        print("✅ Estrutura do projeto configurada")
        print(project_manager.get_structure_overview())
    
    run_prompt_with_llm(llm_client, "P3_2", "migration-backlog.md", context_files, LEGACY_DIRECTORY)
    context_files.append("migration-backlog.md")
    
    run_prompt_with_llm(llm_client, "P3_3", "testing-strategy.md", context_files, LEGACY_DIRECTORY)
    context_files.append("testing-strategy.md")
    
    # Atualiza base de conhecimento após Fase 3
    update_knowledge_base_after_phase(context_files)
    
    return context_files

def fase4(llm_client, context_files):
    print("\n⚡ FASE 4: Iteração e Implementação")
    
    # Inicializa contexto global se necessário
    initialize_global_context()
    
    task_manager = TaskManager(OUTPUT_DIR)
    
    while True:
        task_index, task = task_manager.get_next_task()
        if not task:
            print("✅ Todas as tasks foram concluídas!")
            break
        
        print(f"\n📝 Próxima Task: {task['title']}")
        print(f"Descrição: {task['description'][:100]}...")
        
        choice = input("\n[1] Implementar [2] Pular [3] Sair: ").strip()
        
        if choice == '1':
            # Carrega contexto melhorado (incluindo feedback global)
            enhanced_context = load_enhanced_context(context_files)
            implement_task(llm_client, task, enhanced_context, task_index, task_manager)
        elif choice == '2':
            continue
        elif choice == '3':
            break
        else:
            print("Opção inválida")

def implement_task(llm_client, task, context, task_index, task_manager):
    # P4.1: Implementação com contexto inteligente
    project_structure = project_manager.get_structure_overview()
    
    # *** NOVA IMPLEMENTAÇÃO: Usa contexto inteligente em vez do contexto tradicional ***
    print("🧠 Construindo contexto otimizado para implementação...")
    smart_context_result = build_smart_context_for_task(task['description'], "implementation")
    
    implementation_prompt = PROMPTS["P4_1"].format(
        task_description=task['description'],
        project_structure=project_structure
    )
    
    # Usa o contexto inteligente em vez do contexto original
    full_prompt = f"CONTEXTO OTIMIZADO:\n{smart_context_result}\n\n{implementation_prompt}"
    
    # Calcula métricas do prompt otimizado
    context_size = len(smart_context_result)
    total_prompt_size = len(full_prompt)
    token_estimate = total_prompt_size // 4
    
    print(f"🔨 Implementando...")
    print(f"📊 Context Otimizado: {context_size:,} chars | Total: {total_prompt_size:,} chars | ~{token_estimate:,} tokens")
    
    # Compara com contexto original para mostrar economia
    original_context_size = len(context) if context else 0
    if original_context_size > 0:
        reduction_pct = ((original_context_size - context_size) / original_context_size) * 100
        print(f"💡 Redução de contexto: {reduction_pct:.1f}% ({original_context_size:,} → {context_size:,} chars)")
    
    code_response = llm_client.send_prompt(full_prompt)
    
    # Registra interação da implementação
    log_llm_interaction(f"P4_1_Task_{task_index}", full_prompt, code_response, context_size, token_estimate)
    
    # Salva código
    impl_file = f"task_{task_index}_implementation.md"
    save_md(os.path.join(OUTPUT_DIR, impl_file), code_response)
    
    # Tenta extrair blocos estruturados primeiro
    structured_blocks = extract_structured_code_blocks(code_response)
    saved_files = []
    
    if structured_blocks:
        print(f"📁 Encontrados {len(structured_blocks)} blocos de código estruturados")
        for i, block in enumerate(structured_blocks):
            try:
                file_path = project_manager.save_generated_file(
                    code_content=block.code,
                    code_language=block.language,
                    task_index=task_index,
                    task_description=block.description,
                    component_hint=block.component
                )
                saved_files.append(file_path)
                print(f"📄 {block.filename} → {file_path}")
            except Exception as e:
                print(f"❌ Erro ao salvar {block.filename}: {e}")
    else:
        # Fallback para extração tradicional
        print("⚠️ Formato estruturado não encontrado, usando extração tradicional...")
        code_blocks = extract_code_blocks(code_response)
        for i, block in enumerate(code_blocks):
            file_path = project_manager.save_generated_file(
                code_content=block['code'],
                code_language=block['language'],
                task_index=task_index,
                task_description=task['description'],
                component_hint=""
            )
            saved_files.append(file_path)
    
    if saved_files:
        print(f"✅ Arquivos gerados e organizados: {len(saved_files)}")
        for file_path in saved_files:
            print(f"   📄 {file_path}")
        
        # Gera resumo do projeto atualizado
        summary = project_manager.generate_project_summary()
        summary_file = os.path.join(OUTPUT_DIR, "project_summary.md")
        save_md(summary_file, summary)
        
        # P4.2: Validação (otimizada)
        print("🔍 Validando com contexto otimizado...")
        
        # Constrói contexto específico para validação (mais compacto)
        validation_context = build_smart_context_for_task(task['description'], "validation")
        
        # Combina o prompt de validação com contexto otimizado
        base_validation_prompt = PROMPTS["P4_2"].format(code_to_validate=code_response)
        validation_prompt_with_context = f"CONTEXTO PARA VALIDAÇÃO:\n{validation_context[:2000]}\n\n{base_validation_prompt}"
        
        validation = llm_client.send_prompt(validation_prompt_with_context)
        
        # Registra interação da validação
        log_llm_interaction(f"P4_2_Task_{task_index}", validation_prompt_with_context, validation, 
                          len(validation_context[:2000]), len(validation_prompt_with_context) // 4)
        
        validation_file = f"task_{task_index}_validation.md"
        save_md(os.path.join(OUTPUT_DIR, validation_file), validation)
        
        if "✅ APROVADO" in validation:
            # ✅ P4_2 -.-> Context3: Atualiza contexto global com validação bem-sucedida
            update_global_context_with_validation(task_index, task['title'], validation, is_approved=True)
            
            # P4.3: Integração (otimizada)
            print("🔗 Planejando integração com contexto otimizado...")
            
            # Constrói contexto específico para integração (mais compacto)
            integration_context = build_smart_context_for_task(task['description'], "integration")
            
            # Combina o prompt de integração com contexto otimizado
            base_integration_prompt = PROMPTS["P4_3"].format(implemented_code=code_response)
            integration_prompt_with_context = f"CONTEXTO PARA INTEGRAÇÃO:\n{integration_context[:2000]}\n\n{base_integration_prompt}"
            
            integration = llm_client.send_prompt(integration_prompt_with_context)
            
            # Registra interação da integração
            log_llm_interaction(f"P4_3_Task_{task_index}", integration_prompt_with_context, integration, 
                              len(integration_context[:2000]), len(integration_prompt_with_context) // 4)
            
            integration_file = f"task_{task_index}_integration.md"
            save_md(os.path.join(OUTPUT_DIR, integration_file), integration)
            
            # ✅ P4_3 -.-> Context3: Atualiza contexto global com plano de integração
            update_global_context_with_integration(task_index, task['title'], integration, success=True)
            
            task_manager.mark_task_completed(task_index)
            print("✅ Task concluída com sucesso!")
        else:
            # ❌ P4_2 -.-> Context3: Atualiza contexto global com validação rejeitada
            update_global_context_with_validation(task_index, task['title'], validation, is_approved=False)
            
            print("❌ Código rejeitado na validação.")
            print("🔄 Iniciando ciclo de refinamento...")
            
            # Ciclo de refinamento (mantém a lógica existente)
            max_attempts = 3
            attempt = 1
            
            while attempt <= max_attempts:
                print(f"\n🔨 Tentativa de refinamento {attempt}/{max_attempts}")
                
                # Extrai motivo da falha da validação
                failure_reason = extract_failure_reason(validation)
                
                # Prompt de refinamento
                refinement_prompt = f"""
REFINAMENTO DE CÓDIGO - Tentativa {attempt}

CÓDIGO ORIGINAL QUE FALHOU:
{code_response}

MOTIVO DA FALHA NA VALIDAÇÃO:
{failure_reason}

VALIDAÇÃO COMPLETA:
{validation}

ESTRUTURA DO PROJETO:
{project_structure}

INSTRUÇÕES PARA REFINAMENTO:
1. Analise cuidadosamente o motivo da falha
2. Corrija os problemas identificados
3. Mantenha a funcionalidade original intacta
4. Melhore a qualidade do código conforme sugerido
5. Use o FORMATO ESTRUTURADO para a resposta
6. Forneça uma explicação das correções feitas

Por favor, gere uma versão corrigida do código que atenda aos critérios de validação.
"""
                
                print("🔨 Refinando código...")
                refined_response = llm_client.send_prompt(refinement_prompt)
                
                # Registra interação do refinamento
                log_llm_interaction(f"P4_1_Refinement_{attempt}_Task_{task_index}", refinement_prompt, refined_response, 0, len(refinement_prompt) // 4)
                
                # Salva a tentativa de refinamento
                refinement_file = f"task_{task_index}_refinement_{attempt}.md"
                save_md(os.path.join(OUTPUT_DIR, refinement_file), refined_response)
                
                # Processa código refinado
                refined_structured_blocks = extract_structured_code_blocks(refined_response)
                if refined_structured_blocks:
                    for block in refined_structured_blocks:
                        try:
                            file_path = project_manager.save_generated_file(
                                code_content=block.code,
                                code_language=block.language,
                                task_index=task_index,
                                task_description=f"REFINEMENT_{attempt}_{block.description}",
                                component_hint=block.component
                            )
                            print(f"🔄 Refinado: {block.filename} → {file_path}")
                        except Exception as e:
                            print(f"❌ Erro ao salvar refinamento: {e}")
                    
                    # Valida código refinado (otimizado)
                    print("🔍 Validando código refinado com contexto otimizado...")
                    
                    # Usa contexto otimizado para validação do refinamento
                    refined_validation_context = build_smart_context_for_task(task['description'], "validation")
                    base_refined_validation_prompt = PROMPTS["P4_2"].format(code_to_validate=refined_response)
                    refined_validation_prompt = f"CONTEXTO PARA VALIDAÇÃO:\n{refined_validation_context[:1500]}\n\n{base_refined_validation_prompt}"
                    
                    refined_validation = llm_client.send_prompt(refined_validation_prompt)
                    
                    # Registra interação da validação refinada
                    log_llm_interaction(f"P4_2_Refinement_{attempt}_Task_{task_index}", refined_validation_prompt, 
                                      refined_validation, len(refined_validation_context[:1500]), len(refined_validation_prompt) // 4)
                    
                    refined_validation_file = f"task_{task_index}_validation_refined_{attempt}.md"
                    save_md(os.path.join(OUTPUT_DIR, refined_validation_file), refined_validation)
                    
                    if "✅ APROVADO" in refined_validation:
                        # Código aprovado após refinamento
                        print(f"✅ Código aprovado na tentativa {attempt}!")
                        
                        # ✅ P4_2 -.-> Context3: Atualiza contexto com validação refinada bem-sucedida
                        refinement_context = f"Código aprovado após {attempt} tentativa(s) de refinamento"
                        update_global_context_with_validation(task_index, task['title'], f"{refinement_context}\n\n{refined_validation}", is_approved=True)
                        
                        # P4.3: Integração (otimizada pós-refinamento)
                        print("🔗 Planejando integração pós-refinamento com contexto otimizado...")
                        
                        # Usa contexto otimizado para integração do refinamento
                        refined_integration_context = build_smart_context_for_task(task['description'], "integration")
                        base_integration_prompt = PROMPTS["P4_3"].format(implemented_code=refined_response)
                        integration_prompt = f"CONTEXTO PARA INTEGRAÇÃO:\n{refined_integration_context[:1500]}\n\n{base_integration_prompt}"
                        
                        integration = llm_client.send_prompt(integration_prompt)
                        
                        # Registra interação da integração pós-refinamento
                        log_llm_interaction(f"P4_3_Refinement_{attempt}_Task_{task_index}", integration_prompt, 
                                          integration, len(refined_integration_context[:1500]), len(integration_prompt) // 4)
                        
                        integration_file = f"task_{task_index}_integration.md"
                        save_md(os.path.join(OUTPUT_DIR, integration_file), integration)
                        
                        # ✅ P4_3 -.-> Context3: Atualiza contexto global com integração pós-refinamento
                        refinement_integration_context = f"Integração planejada após {attempt} refinamento(s)"
                        update_global_context_with_integration(task_index, task['title'], f"{refinement_integration_context}\n\n{integration}", success=True)
                        
                        task_manager.mark_task_completed(task_index)
                        print("✅ Task concluída com sucesso após refinamento!")
                        return
                    else:
                        print(f"❌ Código ainda rejeitado na tentativa {attempt}")
                        # ❌ P4_2 -.-> Context3: Atualiza contexto com validação refinada rejeitada
                        if attempt == max_attempts:
                            failed_refinement_context = f"Código rejeitado após {max_attempts} tentativas de refinamento"
                            update_global_context_with_validation(task_index, task['title'], f"{failed_refinement_context}\n\n{refined_validation}", is_approved=False)
                        
                        validation = refined_validation  # Usa a nova validação para a próxima iteração
                        code_response = refined_response  # Usa o código refinado para a próxima iteração
                        attempt += 1
                else:
                    print(f"⚠️ Nenhum código estruturado gerado na tentativa {attempt}")
                    attempt += 1
            
            print(f"❌ Falha após {max_attempts} tentativas de refinamento.")
            print("📝 Verifique os arquivos de validação para entender os problemas.")
            
            # ❌ P4_2 -.-> Context3: Atualiza contexto global com falha completa
            failure_context = f"Task falhou após {max_attempts} tentativas de refinamento. Necessária análise manual."
            update_global_context_with_validation(task_index, task['title'], failure_context, is_approved=False)
    else:
        print("⚠️ Nenhum código foi gerado.")

def initialize_global_context():
    """Inicializa o arquivo de contexto global se não existir"""
    global_context_file = os.path.join(OUTPUT_DIR, "global_context.md")
    if not os.path.exists(global_context_file):
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_content = f"""# Contexto Global da Migração

**Iniciado em:** {timestamp}

Este arquivo contém o feedback acumulado de todas as validações e integrações realizadas durante o processo de migração. Ele é automaticamente atualizado conforme o fluxograma Mermaid:

- **P4_2 -.-> Context3**: Feedback de validações
- **P4_3 -.-> Context3**: Feedback de integrações

## 📊 Histórico de Feedback

"""
        save_md(global_context_file, initial_content)
        print(f"🔧 Contexto global inicializado em: global_context.md")

def update_global_context_with_validation(task_index, task_title, validation_result, is_approved):
    """Atualiza o contexto global com resultados de validação (P4_2 -.-> Context3)"""
    timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    context_update = f"""

## 🔍 Feedback de Validação - Task {task_index} ({timestamp})
**Task:** {task_title}
**Status:** {"✅ APROVADO" if is_approved else "❌ REJEITADO"}

### Resultado da Validação:
{validation_result}

### Lições Aprendidas:
"""
    
    if is_approved:
        context_update += """- Código atendeu aos critérios de qualidade
- Padrões arquiteturais foram seguidos corretamente
- Integração deve funcionar conforme esperado
"""
    else:
        failure_reason = extract_failure_reason(validation_result)
        context_update += f"""- Problemas identificados: {failure_reason}
- Necessário refinamento antes da integração
- Revisar padrões de qualidade para futuras implementações
"""
    
    context_update += "\n---\n"
    
    # Salva no arquivo de contexto global
    global_context_file = os.path.join(OUTPUT_DIR, "global_context.md")
    append_to_context(global_context_file, context_update)
    print(f"📝 Contexto global atualizado com feedback de validação")

def update_global_context_with_integration(task_index, task_title, integration_plan, success=True):
    """Atualiza o contexto global com resultados de integração (P4_3 -.-> Context3)"""
    timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    context_update = f"""

## 🔗 Feedback de Integração - Task {task_index} ({timestamp})
**Task:** {task_title}
**Status:** {"✅ INTEGRAÇÃO PLANEJADA" if success else "❌ PROBLEMAS DE INTEGRAÇÃO"}

### Plano de Integração:
{integration_plan}

### Impacto no Sistema:
"""
    
    if success:
        context_update += """- Nova funcionalidade pronta para deploy
- Dependências mapeadas e resolvidas
- Testes de integração definidos
- Estratégia de rollback estabelecida
"""
    else:
        context_update += """- Problemas de integração identificados
- Necessário revisar dependências
- Possível impacto em outras funcionalidades
- Requer análise adicional antes do deploy
"""
    
    context_update += "\n---\n"
    
    # Salva no arquivo de contexto global
    global_context_file = os.path.join(OUTPUT_DIR, "global_context.md")
    append_to_context(global_context_file, context_update)
    print(f"📝 Contexto global atualizado com feedback de integração")

def load_enhanced_context(context_files):
    """Carrega contexto incluindo feedback global acumulado e configuração do usuário"""
    # Carrega contexto original das fases
    base_context = load_context([os.path.join(OUTPUT_DIR, f) for f in context_files])
    
    # Adiciona configuração do usuário (Fase 0)
    requirements = config_manager.load_requirements()
    if requirements:
        migration_context = config_manager.generate_migration_context()
        base_context = f"{migration_context}\n\n{base_context}"
    
    # Adiciona contexto global se existir
    global_context_file = os.path.join(OUTPUT_DIR, "global_context.md")
    if os.path.exists(global_context_file):
        global_context = load_context([global_context_file])
        return f"{base_context}\n\n## CONTEXTO GLOBAL ACUMULADO\n{global_context}"
    
    return base_context

def extract_failure_reason(validation_text):
    """Extrai o motivo principal da falha da validação."""
    lines = validation_text.split('\n')
    reasons = []
    
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['erro', 'problema', 'falha', 'incorreto', 'inválido', 'rejeitado']):
            reasons.append(line)
    
    if reasons:
        return '\n'.join(reasons[:5])  # Retorna no máximo 5 motivos principais
    else:
        return "Motivo da falha não claramente identificado na validação."

def analyze_project_code(llm_client):
    print("\n🔍 ANÁLISE DE CÓDIGO DO PROJETO")
    
    project_dir = input("Digite o caminho do projeto para analisar: ").strip()
    if not os.path.exists(project_dir):
        print("❌ Diretório não encontrado.")
        return
    
    try:
        analyzer = CodeAnalyzer(project_dir, OUTPUT_DIR)
        
        # Descobre arquivos
        files = analyzer.discover_files()
        print(f"📁 Encontrados {len(files)} arquivos de código")
        
        if not files:
            print("⚠️ Nenhum arquivo de código encontrado no projeto.")
            return
        
        # Analisa dependências
        analyzer.analyze_dependencies(files)
        print(f"📊 Ordem de análise determinada: {len(analyzer.analysis_order)} arquivos")
        
        # Analisa cada arquivo na ordem correta
        for i, file_path in enumerate(analyzer.analysis_order, 1):
            print(f"\n[{i}/{len(analyzer.analysis_order)}] Analisando...")
            try:
                analyzer.analyze_file_with_llm(llm_client, file_path)
            except Exception as e:
                print(f"❌ Erro ao analisar {file_path}: {e}")
                continue
        
        # Salva knowledge base
        analyzer.save_knowledge_base()
        analyzer.generate_summary_report()
        
        print("\n✅ Análise de código concluída!")
        print(f"📄 Verifique os arquivos em {OUTPUT_DIR}/")
        
    except ImportError as e:
        print(f"❌ Erro ao importar analisadores: {e}")
        print("Certifique-se de que os arquivos dos analisadores foram criados:")
        print("- analyzers/__init__.py")
        print("- analyzers/java_analyzer.py") 
        print("- analyzers/python_analyzer.py")
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")

def generate_logs_report():
    """Gera relatório de análise dos logs de interação com LLM"""
    print("\n📊 ANÁLISE DOS LOGS LLM")
    
    if not os.path.exists(LOGS_DIR):
        print("❌ Nenhum log encontrado.")
        return
    
    # Lista arquivos de log JSON
    log_files = [f for f in os.listdir(LOGS_DIR) if f.startswith('llm_log_') and f.endswith('.json')]
    
    if not log_files:
        print("❌ Nenhum log JSON encontrado.")
        return
    
    print(f"📂 Analisando {len(log_files)} logs...")
    
    # Coleta estatísticas
    total_interactions = 0
    total_tokens = 0
    total_context_chars = 0
    total_response_chars = 0
    prompt_types = {}
    
    logs_data = []
    
    for log_file in sorted(log_files):
        log_path = os.path.join(LOGS_DIR, log_file)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                logs_data.append(log_data)
                
                total_interactions += 1
                total_tokens += log_data.get('token_estimate', 0)
                total_context_chars += log_data.get('context_size_chars', 0)
                total_response_chars += log_data.get('response_size_chars', 0)
                
                prompt_key = log_data.get('prompt_key', 'unknown')
                prompt_types[prompt_key] = prompt_types.get(prompt_key, 0) + 1
                
        except Exception as e:
            print(f"⚠️ Erro ao ler {log_file}: {e}")
    
    # Gera relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_content = f"""# Relatório de Análise dos Logs LLM

**Gerado em:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Estatísticas Gerais

- **Total de Interações:** {total_interactions:,}
- **Total de Tokens Estimados:** {total_tokens:,}
- **Total de Caracteres de Contexto:** {total_context_chars:,}
- **Total de Caracteres de Resposta:** {total_response_chars:,}
- **Média de Tokens por Interação:** {total_tokens // max(total_interactions, 1):,}
- **Média de Contexto por Interação:** {total_context_chars // max(total_interactions, 1):,} chars

## 🎯 Distribuição por Tipo de Prompt

"""
    
    for prompt_type, count in sorted(prompt_types.items()):
        percentage = (count / total_interactions) * 100
        report_content += f"- **{prompt_type}:** {count} ({percentage:.1f}%)\n"
    
    report_content += f"""

## 📈 Timeline de Interações

| Timestamp | Prompt Type | Context | Tokens | Response |
|-----------|------------|---------|--------|----------|
"""
    
    for log_data in logs_data[-20:]:  # Últimas 20 interações
        timestamp = log_data.get('timestamp', 'N/A')
        prompt_key = log_data.get('prompt_key', 'N/A')
        context_size = log_data.get('context_size_chars', 0)
        tokens = log_data.get('token_estimate', 0)
        response_size = log_data.get('response_size_chars', 0)
        
        report_content += f"| {timestamp} | {prompt_key} | {context_size:,} | {tokens:,} | {response_size:,} |\n"
    
    report_content += f"""

## 🔍 Análise de Eficiência

### Contexto vs Resposta
- **Ratio Contexto/Resposta:** {(total_context_chars / max(total_response_chars, 1)):.2f}
- **Eficiência de Token:** {(total_response_chars / max(total_tokens, 1)):.2f} chars/token

### Recomendações
"""
    
    if total_context_chars / max(total_interactions, 1) > 5000:
        report_content += "- ⚠️ Contexto médio muito alto (>5k chars) - considerar otimização\n"
    else:
        report_content += "- ✅ Contexto médio dentro do esperado\n"
    
    if total_tokens / max(total_interactions, 1) > 2000:
        report_content += "- ⚠️ Tokens médios altos (>2k) - considerar redução de contexto\n"
    else:
        report_content += "- ✅ Uso de tokens eficiente\n"
    
    # Salva relatório
    report_file = os.path.join(LOGS_DIR, f"logs_analysis_report_{timestamp}.md")
    save_md(report_file, report_content)
    
    print("✅ Relatório de análise gerado!")
    print(f"📄 Arquivo: {report_file}")
    print(f"📊 {total_interactions} interações analisadas")
    print(f"🎯 {total_tokens:,} tokens estimados")
    
    return report_file

def cleanup_old_logs(keep_days=30):
    """Remove logs mais antigos que X dias para economizar espaço"""
    if not os.path.exists(LOGS_DIR):
        return
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    removed_count = 0
    total_count = 0
    
    for filename in os.listdir(LOGS_DIR):
        if filename.startswith('llm_log_') and ('.' in filename):
            total_count += 1
            try:
                # Extrai timestamp do nome do arquivo
                timestamp_str = filename.split('_')[2].split('.')[0]  # YYYYMMDD_HHMMSS
                file_date = datetime.strptime(timestamp_str, '%H%M%S')
                
                # Para comparação, usa apenas a data atual como base
                file_date = file_date.replace(year=datetime.now().year, 
                                             month=datetime.now().month, 
                                             day=datetime.now().day)
                
                if file_date < cutoff_date:
                    file_path = os.path.join(LOGS_DIR, filename)
                    os.remove(file_path)
                    removed_count += 1
                    
            except (ValueError, IndexError):
                # Ignora arquivos com formato de nome inválido
                continue
    
    if removed_count > 0:
        print(f"🧹 Limpeza de logs: {removed_count}/{total_count} arquivos removidos")
    else:
        print(f"✅ Logs atualizados: {total_count} arquivos mantidos")

def show_logs_menu():
    """Menu específico para gerenciamento de logs"""
    while True:
        print("\n📊 GERENCIAMENTO DE LOGS LLM")
        print("[1] Gerar relatório de análise")
        print("[2] Listar logs disponíveis")
        print("[3] Limpar logs antigos (>30 dias)")
        print("[4] Ver log consolidado")
        print("[0] Voltar ao menu principal")
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            generate_logs_report()
        elif choice == '2':
            list_available_logs()
        elif choice == '3':
            cleanup_old_logs()
        elif choice == '4':
            show_consolidated_log()
        elif choice == '0':
            break
        else:
            print("Opção inválida")

def list_available_logs():
    """Lista todos os logs disponíveis com informações básicas"""
    if not os.path.exists(LOGS_DIR):
        print("❌ Nenhum log encontrado.")
        return
    
    log_files = [f for f in os.listdir(LOGS_DIR) if f.startswith('llm_log_') and f.endswith('.json')]
    
    if not log_files:
        print("❌ Nenhum log JSON encontrado.")
        return
    
    print(f"\n📂 {len(log_files)} logs disponíveis:")
    print("=" * 80)
    print(f"{'Timestamp':<20} {'Prompt Key':<25} {'Tokens':<10} {'Context':<10}")
    print("=" * 80)
    
    for log_file in sorted(log_files, reverse=True):  # Mais recentes primeiro
        log_path = os.path.join(LOGS_DIR, log_file)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                timestamp = data.get('timestamp', 'N/A')
                prompt_key = data.get('prompt_key', 'N/A')[:24]  # Trunca se muito longo
                tokens = data.get('token_estimate', 0)
                context = data.get('context_size_chars', 0)
                
                print(f"{timestamp:<20} {prompt_key:<25} {tokens:<10} {context:<10}")
                
        except Exception as e:
            print(f"⚠️ Erro ao ler {log_file}: {e}")

def show_consolidated_log():
    """Mostra o log consolidado"""
    consolidated_file = os.path.join(LOGS_DIR, "consolidated_log.md")
    if os.path.exists(consolidated_file):
        print("\n📋 LOG CONSOLIDADO:")
        print("=" * 60)
        with open(consolidated_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Mostra apenas as últimas 20 linhas para não sobrecarregar
            lines = content.split('\n')
            for line in lines[-20:]:
                print(line)
    else:
        print("❌ Log consolidado não encontrado.")

def clean_existing_files_from_prompts():
    """Remove prompts dos arquivos já existentes para limpeza retroativa"""
    print("\n🧹 LIMPEZA DE PROMPTS EM ARQUIVOS EXISTENTES")
    
    # Lista arquivos .md no diretório de saída
    md_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md') and not f.startswith('logs')]
    
    if not md_files:
        print("❌ Nenhum arquivo .md encontrado para limpeza.")
        return
    
    print(f"📁 Encontrados {len(md_files)} arquivos para análise...")
    
    cleaned_count = 0
    
    for filename in md_files:
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_size = len(content)
            
            # Aplica a mesma lógica de limpeza da função load_previous_results_only
            lines = content.split('\n')
            filtered_lines = []
            skip_section = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Detecta seções de prompt
                prompt_indicators = [
                    'prompt ', '**prompt', 'instruções para', 'desenvolva',
                    'importante:** detalhe', 'organize por sprints',
                    'considere as tecnologias', 'baseado na análise'
                ]
                
                if any(indicator in line_lower for indicator in prompt_indicators):
                    skip_section = True
                    continue
                
                # Detecta fim de seção de prompt
                if skip_section:
                    if line.startswith('#') and not line.startswith('###'):
                        skip_section = False
                    elif line.strip() == '' and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith(' ') and not any(indicator in next_line.lower() for indicator in prompt_indicators):
                            skip_section = False
                    else:
                        continue
                
                # Remove linhas que são claramente instruções
                if any(phrase in line_lower for phrase in [
                    'detalhe a execução', 'organize por sprints', 'deliverables claros',
                    'importante:**', 'instruções:', 'desenvolva planos'
                ]):
                    continue
                
                if not skip_section:
                    filtered_lines.append(line)
            
            # Remove múltiplas linhas vazias
            import re
            filtered_content = '\n'.join(filtered_lines)
            filtered_content = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_content)
            
            new_size = len(filtered_content)
            
            # Só salva se houve mudança significativa
            if new_size < original_size * 0.9:  # Se reduziu mais de 10%
                # Faz backup do original
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Salva versão limpa
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(filtered_content)
                
                reduction_pct = ((original_size - new_size) / original_size) * 100
                print(f"✅ {filename}: {original_size:,} → {new_size:,} chars ({reduction_pct:.1f}% redução)")
                cleaned_count += 1
            else:
                print(f"⚪ {filename}: Já limpo ou sem prompts detectados")
                
        except Exception as e:
            print(f"❌ Erro ao processar {filename}: {e}")
    
    if cleaned_count > 0:
        print(f"\n🎉 Limpeza concluída: {cleaned_count} arquivos otimizados")
        print("💾 Backups salvos com extensão .backup")
    else:
        print("\n✅ Nenhum arquivo precisou de limpeza")

def main():
    print("🚀 MIGRADOR DE SISTEMAS LEGADOS")
    print("Certifique-se de que o VS Code Web está aberto com o Copilot Chat ativo.")
    
    # Conecta com LLM
    try:
        llm_client = LLMClient()
        llm_client.connect()
        print("✅ Conectado ao LLM")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    try:
        print("\nEscolha a operação:")
        print("[0] Fase 0: Configuração da Migração (Coletamento de Requisitos)")
        print("[1] Executar todas as fases de migração")
        print("[2] Fase 1: Análise do Sistema Legado")
        print("[3] Fase 2: Construção do Roadmap")
        print("[4] Fase 3: Criação de Tasks")
        print("[5] Fase 4: Implementação")
        print("[6] Analisar código de projeto existente")
        print("[7] Gerenciar logs LLM (relatórios, limpeza, análise)")
        print("[8] 🧹 Limpar prompts de arquivos existentes")
        
        choice = input("Opção: ").strip()
        
        if choice == '0':
            fase0()
        elif choice == '1':
            fase0()  # Sempre começa com Fase 0
            context_files = fase1(llm_client)
            context_files = fase2(llm_client, context_files)
            context_files = fase3(llm_client, context_files)
            fase4(llm_client, context_files)
        elif choice == '2':
            fase1(llm_client)
        elif choice == '3':
            context_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
            fase2(llm_client, context_files)
        elif choice == '4':
            context_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
            fase3(llm_client, context_files)
        elif choice == '5':
            context_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
            fase4(llm_client, context_files)
        elif choice == '6':
            analyze_project_code(llm_client)
        elif choice == '7':
            show_logs_menu()
        elif choice == '8':
            clean_existing_files_from_prompts()
        else:
            print("Opção inválida")
            
        print(f"\n✅ Processo concluído! Verifique os arquivos em {OUTPUT_DIR}/")
        
    finally:
        llm_client.close()

if __name__ == "__main__":
    main()
