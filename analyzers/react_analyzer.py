# Blueprint: React/Next.js Code Graph Analyzer
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any

def extract_imports(content: str) -> Dict[str, str]:
    """
    Extrai imports de um arquivo React/TypeScript/JavaScript
    Retorna: mapeamento de nome -> caminho/origem
    """
    import_map = {}
    
    # Padrões de import comuns
    patterns = [
        # import React from 'react'
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        # import { Component } from 'react'
        r"import\s+\{\s*([^}]+)\s*\}\s+from\s+['\"]([^'\"]+)['\"]",
        # import * as React from 'react'
        r"import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        # const Component = require('module')
        r"const\s+(\w+)\s*=\s*require\(['\"]([^'\"]+)['\"]\)",
        # Dynamic imports
        r"import\(['\"]([^'\"]+)['\"]\)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if len(match) == 2:
                names, path = match[0], match[1]
                # Processa múltiplos nomes em destructuring
                if '{' not in names:
                    import_map[names.strip()] = path
                else:
                    # Destructuring imports
                    for name in names.split(','):
                        clean_name = name.strip().split(' as ')[-1]  # Handle 'as' alias
                        import_map[clean_name] = path
    
    return import_map

def extract_component_info(content: str, file_path: str) -> Dict[str, Any]:
    """
    Extrai informações de componentes React de um arquivo
    """
    component_info = {
        'file_path': file_path,
        'components': [],
        'hooks': [],
        'exports': [],
        'props_interfaces': [],
        'state_variables': [],
        'effects': [],
        'api_calls': [],
        'routes': [],
        'relationships': []
    }
    
    # Detecta componentes funcionais
    func_component_patterns = [
        r"(?:export\s+)?(?:default\s+)?(?:const|function)\s+(\w+)\s*(?::\s*React\.FC(?:<[^>]*>)?)?\s*=?\s*(?:\([^)]*\))?\s*(?::\s*[^=]*?)?\s*=>\s*\{",
        r"(?:export\s+)?(?:default\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]*?)?\s*\{",
        r"(?:export\s+)?(?:default\s+)?const\s+(\w+)\s*=\s*React\.memo\s*\(",
    ]
    
    for pattern in func_component_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            component_name = match if isinstance(match, str) else match[0]
            if component_name and component_name[0].isupper():  # React components start with uppercase
                component_info['components'].append({
                    'name': component_name,
                    'type': 'functional',
                    'line': content[:content.find(component_name)].count('\n') + 1
                })
    
    # Detecta componentes de classe
    class_component_pattern = r"class\s+(\w+)\s+extends\s+(?:React\.)?Component"
    class_matches = re.findall(class_component_pattern, content)
    for class_name in class_matches:
        component_info['components'].append({
            'name': class_name,
            'type': 'class',
            'line': content[:content.find(f"class {class_name}")].count('\n') + 1
        })
    
    # Detecta hooks
    hook_patterns = [
        r"const\s+\[([^,\]]+)(?:,\s*([^,\]]+))?\]\s*=\s*useState\s*\(",
        r"const\s+(\w+)\s*=\s*useEffect\s*\(",
        r"const\s+(\w+)\s*=\s*useContext\s*\(",
        r"const\s+(\w+)\s*=\s*useReducer\s*\(",
        r"const\s+(\w+)\s*=\s*useCallback\s*\(",
        r"const\s+(\w+)\s*=\s*useMemo\s*\(",
        r"const\s+(\w+)\s*=\s*useRef\s*\(",
        r"const\s+(\w+)\s*=\s*use\w+\s*\(",  # Custom hooks
    ]
    
    for pattern in hook_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                for item in match:
                    if item:
                        component_info['hooks'].append(item.strip())
            else:
                component_info['hooks'].append(match.strip())
    
    # Detecta interfaces/types para props
    interface_patterns = [
        r"interface\s+(\w+(?:Props|Properties))\s*\{([^}]+)\}",
        r"type\s+(\w+(?:Props|Properties))\s*=\s*\{([^}]+)\}",
    ]
    
    for pattern in interface_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            interface_name, interface_body = match
            component_info['props_interfaces'].append({
                'name': interface_name,
                'properties': [prop.strip() for prop in interface_body.split(',') if prop.strip()]
            })
    
    # Detecta chamadas de API
    api_patterns = [
        r"fetch\s*\(\s*['\"]([^'\"]+)['\"]",
        r"axios\.[get|post|put|delete|patch]+\s*\(\s*['\"]([^'\"]+)['\"]",
        r"api\.\w+\s*\(\s*['\"]([^'\"]+)['\"]",
        r"useSWR\s*\(\s*['\"]([^'\"]+)['\"]",
        r"useQuery\s*\(\s*['\"]([^'\"]+)['\"]",
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, content)
        component_info['api_calls'].extend(matches)
    
    # Detecta rotas Next.js
    route_patterns = [
        r"useRouter\s*\(\s*\)",
        r"router\.push\s*\(\s*['\"]([^'\"]+)['\"]",
        r"Link.*href\s*=\s*['\"]([^'\"]+)['\"]",
        r"getStaticPaths|getStaticProps|getServerSideProps",
    ]
    
    for pattern in route_patterns:
        matches = re.findall(pattern, content)
        if matches:
            component_info['routes'].extend(matches if isinstance(matches[0], str) else ['Next.js routing detected'])
    
    # Detecta exports
    export_patterns = [
        r"export\s+(?:default\s+)?(?:const|function|class)\s+(\w+)",
        r"export\s+\{\s*([^}]+)\s*\}",
        r"export\s+default\s+(\w+)",
    ]
    
    for pattern in export_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if isinstance(match, str):
                if ',' in match:  # Multiple exports
                    component_info['exports'].extend([exp.strip() for exp in match.split(',')])
                else:
                    component_info['exports'].append(match.strip())
    
    return component_info

def detect_next_js_features(file_path: str, content: str) -> List[str]:
    """
    Detecta características específicas do Next.js
    """
    features = []
    
    # Características do Next.js
    nextjs_patterns = {
        'App Router': r"app/.*\.(tsx?|jsx?)$",
        'Pages Router': r"pages/.*\.(tsx?|jsx?)$",
        'API Routes': r"(pages|app)/api/.*\.(tsx?|jsx?)$",
        'Layout': r"layout\.(tsx?|jsx?)$",
        'Loading': r"loading\.(tsx?|jsx?)$",
        'Error': r"error\.(tsx?|jsx?)$",
        'Not Found': r"not-found\.(tsx?|jsx?)$",
        'Middleware': r"middleware\.(tsx?|jsx?)$",
        'Server Components': r"['\"]use server['\"]",
        'Client Components': r"['\"]use client['\"]",
        'Static Generation': r"getStaticProps|getStaticPaths",
        'Server Side Rendering': r"getServerSideProps",
        'Image Optimization': r"next/image",
        'Font Optimization': r"next/font",
        'Head Management': r"next/head",
        'Router': r"next/router|next/navigation",
        'Dynamic Imports': r"dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(",
    }
    
    for feature, pattern in nextjs_patterns.items():
        if re.search(pattern, str(file_path)) or re.search(pattern, content):
            features.append(feature)
    
    return features

def build_symbol_table(project_dir: str) -> Dict[str, Any]:
    """
    Percorre todos os arquivos React/Next.js do projeto e constrói a tabela de símbolos
    """
    symbol_table = {}
    
    # Extensões de arquivo para React/Next.js
    extensions = ['*.tsx', '*.jsx', '*.ts', '*.js']
    
    for ext in extensions:
        for file_path in Path(project_dir).rglob(ext):
            # Ignora node_modules, .next, e outros diretórios de build
            if any(ignore in str(file_path) for ignore in [
                'node_modules', '.next', 'dist', 'build', '.git', 
                'coverage', '__tests__', '.storybook'
            ]):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"⚠️ Erro ao ler {file_path}: {e}")
                continue
            
            # Extrai informações do arquivo
            imports = extract_imports(content)
            component_info = extract_component_info(content, str(file_path))
            nextjs_features = detect_next_js_features(file_path, content)
            
            # Monta entrada da tabela de símbolos
            relative_path = str(file_path.relative_to(project_dir))
            
            entry = {
                'file_path': str(file_path),
                'relative_path': relative_path,
                'file_type': file_path.suffix,
                'imports': imports,
                'components': component_info['components'],
                'hooks': component_info['hooks'],
                'exports': component_info['exports'],
                'props_interfaces': component_info['props_interfaces'],
                'api_calls': component_info['api_calls'],
                'routes': component_info['routes'],
                'nextjs_features': nextjs_features,
                'relationships': []
            }
            
            # Detecta relacionamentos
            for component in component_info['components']:
                comp_name = component['name']
                
                # Relacionamentos por imports
                for imported_name, import_path in imports.items():
                    if imported_name in content:
                        entry['relationships'].append({
                            'type': 'IMPORT',
                            'target': import_path,
                            'usage': f'importado como {imported_name}'
                        })
                
                # Relacionamentos por componentes filhos
                for other_comp in component_info['components']:
                    if other_comp['name'] != comp_name and f"<{other_comp['name']}" in content:
                        entry['relationships'].append({
                            'type': 'COMPOSITION',
                            'target': other_comp['name'],
                            'usage': 'usado como componente filho'
                        })
            
            symbol_table[relative_path] = entry
    
    return symbol_table

def generate_report(symbol_table: Dict[str, Any]) -> str:
    """
    Gera um relatório Markdown estruturado a partir da tabela de símbolos
    """
    lines = ["# 📦 Relatório de Análise de Código React/Next.js\n"]
    
    # Estatísticas gerais
    total_files = len(symbol_table)
    total_components = sum(len(entry['components']) for entry in symbol_table.values())
    nextjs_files = sum(1 for entry in symbol_table.values() if entry['nextjs_features'])
    
    lines.append("## 📊 Estatísticas Gerais")
    lines.append(f"- **Total de arquivos:** {total_files}")
    lines.append(f"- **Total de componentes:** {total_components}")
    lines.append(f"- **Arquivos com recursos Next.js:** {nextjs_files}")
    lines.append("")
    
    # Análise por arquivo
    for file_path, entry in symbol_table.items():
        lines.append(f"\n---\n\n### 📄 {file_path}")
        lines.append(f"**Tipo:** `{entry['file_type']}`  ")
        lines.append(f"**Caminho:** `{entry['file_path']}`  ")
        
        if entry['nextjs_features']:
            lines.append(f"**Recursos Next.js:** {', '.join(f'`{f}`' for f in entry['nextjs_features'])}  ")
        
        if entry['components']:
            lines.append("\n**🧩 Componentes:**")
            for comp in entry['components']:
                lines.append(f"- **{comp['name']}** (linha {comp['line']}) - Tipo: {comp['type']}")
        
        if entry['hooks']:
            lines.append("\n**🪝 Hooks:**")
            for hook in set(entry['hooks']):  # Remove duplicatas
                lines.append(f"- {hook}")
        
        if entry['props_interfaces']:
            lines.append("\n**🔧 Interfaces de Props:**")
            for interface in entry['props_interfaces']:
                lines.append(f"- **{interface['name']}**")
                for prop in interface['properties'][:3]:  # Limita a 3 propriedades
                    lines.append(f"  - {prop}")
                if len(interface['properties']) > 3:
                    lines.append(f"  - ... e mais {len(interface['properties']) - 3} propriedades")
        
        if entry['api_calls']:
            lines.append("\n**🌐 Chamadas de API:**")
            for api in set(entry['api_calls'][:5]):  # Limita a 5 chamadas
                lines.append(f"- `{api}`")
            if len(entry['api_calls']) > 5:
                lines.append(f"- ... e mais {len(entry['api_calls']) - 5} chamadas")
        
        if entry['routes']:
            lines.append("\n**🛣️ Rotas:**")
            for route in set(entry['routes'][:3]):  # Limita a 3 rotas
                lines.append(f"- `{route}`")
            if len(entry['routes']) > 3:
                lines.append(f"- ... e mais {len(entry['routes']) - 3} rotas")
        
        if entry['imports']:
            lines.append("\n**📥 Imports principais:**")
            main_imports = [f"{name} from '{path}'" for name, path in list(entry['imports'].items())[:5]]
            for imp in main_imports:
                lines.append(f"- {imp}")
            if len(entry['imports']) > 5:
                lines.append(f"- ... e mais {len(entry['imports']) - 5} imports")
        
        if entry['relationships']:
            lines.append("\n**🔗 Relacionamentos:**")
            for rel in entry['relationships'][:5]:  # Limita a 5 relacionamentos
                if rel['type'] == 'IMPORT':
                    lines.append(f"- **IMPORT** de `{rel['target']}` - {rel['usage']}")
                elif rel['type'] == 'COMPOSITION':
                    lines.append(f"- **COMPOSIÇÃO** com `{rel['target']}` - {rel['usage']}")
            if len(entry['relationships']) > 5:
                lines.append(f"- ... e mais {len(entry['relationships']) - 5} relacionamentos")
    
    return '\n'.join(lines)

def analyze_project_structure(symbol_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa a estrutura geral do projeto React/Next.js
    """
    analysis = {
        'architecture_type': 'Unknown',
        'routing_strategy': 'Unknown',
        'state_management': [],
        'styling_approach': [],
        'testing_setup': [],
        'build_tools': [],
        'recommendations': []
    }
    
    all_imports = {}
    all_files = list(symbol_table.keys())
    
    # Coleta todos os imports
    for entry in symbol_table.values():
        all_imports.update(entry['imports'])
    
    # Detecta arquitetura
    if any('app/' in path for path in all_files):
        analysis['architecture_type'] = 'Next.js App Router'
    elif any('pages/' in path for path in all_files):
        analysis['architecture_type'] = 'Next.js Pages Router'
    elif any('src/components' in path for path in all_files):
        analysis['architecture_type'] = 'Component-based React'
    
    # Detecta estratégia de roteamento
    router_imports = [path for name, path in all_imports.items() if 'router' in path.lower()]
    if 'next/navigation' in router_imports:
        analysis['routing_strategy'] = 'Next.js App Router Navigation'
    elif 'next/router' in router_imports:
        analysis['routing_strategy'] = 'Next.js Pages Router'
    elif 'react-router' in str(router_imports):
        analysis['routing_strategy'] = 'React Router'
    
    # Detecta gerenciamento de estado
    state_libs = {
        'redux': ['redux', '@reduxjs/toolkit'],
        'zustand': ['zustand'],
        'recoil': ['recoil'],
        'jotai': ['jotai'],
        'context': ['useContext', 'createContext'],
        'swr': ['swr'],
        'react-query': ['@tanstack/react-query', 'react-query']
    }
    
    for lib_name, lib_indicators in state_libs.items():
        if any(indicator in str(all_imports.values()).lower() for indicator in lib_indicators):
            analysis['state_management'].append(lib_name)
    
    # Detecta abordagem de styling
    styling_libs = {
        'tailwind': ['tailwindcss'],
        'styled-components': ['styled-components'],
        'emotion': ['@emotion'],
        'mui': ['@mui/material'],
        'chakra': ['@chakra-ui'],
        'ant-design': ['antd'],
        'css-modules': ['.module.css'],
        'sass': ['.scss', '.sass']
    }
    
    for style_name, style_indicators in styling_libs.items():
        if any(indicator in str(all_imports.values()).lower() or 
               any(indicator in path for path in all_files) 
               for indicator in style_indicators):
            analysis['styling_approach'].append(style_name)
    
    # Detecta setup de testes
    test_patterns = ['test', 'spec', '__tests__', '.test.', '.spec.']
    if any(pattern in path for path in all_files for pattern in test_patterns):
        analysis['testing_setup'].append('test-files-present')
    
    test_libs = ['jest', 'vitest', '@testing-library', 'cypress', 'playwright']
    for lib in test_libs:
        if lib in str(all_imports.values()).lower():
            analysis['testing_setup'].append(lib)
    
    # Gera recomendações
    if not analysis['state_management']:
        analysis['recommendations'].append("Considere implementar uma solução de gerenciamento de estado")
    
    if len(analysis['styling_approach']) > 2:
        analysis['recommendations'].append("Múltiplas abordagens de styling detectadas - considere padronizar")
    
    if not analysis['testing_setup']:
        analysis['recommendations'].append("Nenhum setup de testes detectado - considere adicionar testes")
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description="Analisador de Grafo de Código React/Next.js")
    parser.add_argument('project_dir', help="Diretório raiz do projeto React/Next.js")
    parser.add_argument('--pergunta', help="Pergunta para o LLM (opcional)")
    parser.add_argument('--relatorio', help="Arquivo de saída do relatório (opcional)")
    parser.add_argument('--analise', action='store_true', help="Incluir análise estrutural do projeto")
    args = parser.parse_args()

    print(f"🔎 Analisando projeto React/Next.js: {args.project_dir}")
    symbol_table = build_symbol_table(args.project_dir)
    print(f"✅ {len(symbol_table)} arquivos analisados.")

    report = generate_report(symbol_table)
    
    if args.analise:
        print("📊 Realizando análise estrutural...")
        project_analysis = analyze_project_structure(symbol_table)
        
        # Adiciona análise ao relatório
        analysis_section = [
            "\n\n---\n\n## 🏗️ Análise Estrutural do Projeto\n",
            f"**Arquitetura:** {project_analysis['architecture_type']}  ",
            f"**Roteamento:** {project_analysis['routing_strategy']}  ",
        ]
        
        if project_analysis['state_management']:
            analysis_section.append(f"**Gerenciamento de Estado:** {', '.join(project_analysis['state_management'])}  ")
        
        if project_analysis['styling_approach']:
            analysis_section.append(f"**Styling:** {', '.join(project_analysis['styling_approach'])}  ")
        
        if project_analysis['testing_setup']:
            analysis_section.append(f"**Testes:** {', '.join(project_analysis['testing_setup'])}  ")
        
        if project_analysis['recommendations']:
            analysis_section.append("\n**💡 Recomendações:**")
            for rec in project_analysis['recommendations']:
                analysis_section.append(f"- {rec}")
        
        report += '\n'.join(analysis_section)

    if args.relatorio:
        with open(args.relatorio, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📝 Relatório salvo em: {args.relatorio}")
    else:
        print(report)

    if args.pergunta:
        print("\n---\n\nPergunta para o LLM:")
        print(args.pergunta)
        print("\n(Integração com LLM pode ser implementada conforme necessário)")

if __name__ == "__main__":
    main()
