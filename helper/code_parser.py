import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class StructuredCodeBlock:
    """Representa um bloco de código estruturado com metadados"""
    filename: str
    location: str
    component: str
    description: str
    language: str
    code: str
    dependencies: List[str]

def extract_code_blocks(text):
    """Extrai todos os blocos de código markdown de um texto."""
    # Pattern para blocos de código com ```
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language if language else 'text',
            'code': code.strip()
        })
    
    return code_blocks

def extract_structured_code_blocks(text: str) -> List[StructuredCodeBlock]:
    """Extrai blocos de código estruturados com metadados do novo formato"""
    structured_blocks = []
    
    # Pattern mais flexível para capturar blocos estruturados
    # Procura por cada bloco individualmente
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Procura por início de bloco estruturado
        if line.startswith('ARQUIVO:'):
            filename = line.replace('ARQUIVO:', '').strip()
            location = ""
            component = ""
            description = ""
            language = ""
            code = ""
            dependencies_str = ""
            
            i += 1
            
            # Extrai metadados
            while i < len(lines) and not lines[i].strip().startswith('```'):
                line = lines[i].strip()
                if line.startswith('LOCALIZAÇÃO:'):
                    location = line.replace('LOCALIZAÇÃO:', '').strip()
                elif line.startswith('COMPONENTE:'):
                    component = line.replace('COMPONENTE:', '').strip()
                elif line.startswith('DESCRIÇÃO:'):
                    description = line.replace('DESCRIÇÃO:', '').strip()
                i += 1
            
            # Procura pelo início do bloco de código
            if i < len(lines) and lines[i].strip().startswith('```'):
                code_start_line = lines[i].strip()
                language = code_start_line.replace('```', '').strip()
                i += 1
                
                # Coleta o código
                code_lines = []
                while i < len(lines) and not lines[i].strip() == '```':
                    code_lines.append(lines[i])
                    i += 1
                
                code = '\n'.join(code_lines).strip()
                
                # Pula a linha de fechamento ```
                if i < len(lines) and lines[i].strip() == '```':
                    i += 1
                
                # Procura por dependências
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('DEPENDÊNCIAS:'):
                        dependencies_str = line.replace('DEPENDÊNCIAS:', '').strip()
                        break
                    elif line.startswith('ARQUIVO:'):
                        # Próximo bloco encontrado, volta uma linha
                        i -= 1
                        break
                    i += 1
            
            # Cria o bloco estruturado se temos dados suficientes
            if filename and code:
                dependencies = []
                if dependencies_str:
                    dependencies = [dep.strip() for dep in dependencies_str.split(',') if dep.strip()]
                
                structured_block = StructuredCodeBlock(
                    filename=filename,
                    location=location or "unknown",
                    component=component or "unknown",
                    description=description or "No description",
                    language=language or "text",
                    code=code,
                    dependencies=dependencies
                )
                
                structured_blocks.append(structured_block)
        
        i += 1
    
    return structured_blocks

def extract_first_code_block(text, language=None):
    """Extrai o primeiro bloco de código, opcionalmente filtrado por linguagem."""
    blocks = extract_code_blocks(text)
    
    if not blocks:
        return None
    
    if language:
        for block in blocks:
            if block['language'].lower() == language.lower():
                return block['code']
        return None
    
    return blocks[0]['code']

def save_code_to_file(code, filepath):
    """Salva código em um arquivo."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code)

def save_structured_code_block(block: StructuredCodeBlock, base_path: str, project_manager) -> str:
    """Salva um bloco de código estruturado usando o gerenciador de projeto"""
    return project_manager.save_generated_file(
        code_content=block.code,
        code_language=block.language,
        task_index=0,  # será atualizado pelo chamador
        task_description=block.description,
        component_hint=block.component
    )
