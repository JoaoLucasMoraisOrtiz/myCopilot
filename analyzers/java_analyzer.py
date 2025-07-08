
# Blueprint: Java Code Graph Analyzer
import os
import sys
import argparse
import javalang
from pathlib import Path

def build_symbol_table(project_dir):
    """
    Percorre todos os arquivos .java do projeto, parseia e constrói a tabela de símbolos global.
    Retorna: symbol_table (dict)
    """
    symbol_table = {}
    for java_file in Path(project_dir).rglob('*.java'):
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = javalang.parse.parse(content)
        except Exception as e:
            print(f"⚠️ Erro ao parsear {java_file}: {e}")
            continue

        # 1. Mapeia imports
        import_map = {}
        if hasattr(tree, 'imports'):
            for imp in tree.imports:
                if imp.path:
                    simple = imp.path.split('.')[-1]
                    import_map[simple] = imp.path

        # 2. Descobre o pacote
        package = tree.package.name if tree.package else None

        # 3. Itera sobre declarações de tipos (classes/interfaces)
        for path, node in tree.filter(javalang.tree.TypeDeclaration):
            if not hasattr(node, 'name'):
                continue
            full_name = f"{package}.{node.name}" if package else node.name
            entry = {
                'file_path': str(java_file),
                'type': 'Interface' if isinstance(node, javalang.tree.InterfaceDeclaration) else 'Class',
                'extends': node.extends.name if hasattr(node, 'extends') and node.extends else None,
                'implements': [i.name for i in (getattr(node, 'implements', []) or [])],
                'fields': [],
                'constructors': [],
                'methods': [],
                'relationships': []
            }

            # 4. Itera sobre membros
            for member in node.body:
                # Campos
                if isinstance(member, javalang.tree.FieldDeclaration):
                    for decl in member.declarators:
                        field_type = member.type.name if hasattr(member.type, 'name') else str(member.type)
                        field_str = f"{' '.join(member.modifiers)} {field_type} {decl.name}".strip()
                        entry['fields'].append(field_str)
                        # Relação de composição
                        rel_type = resolve_type(field_type, import_map, package)
                        if rel_type:
                            entry['relationships'].append({'type': 'COMPOSITION', 'target': rel_type})
                # Métodos
                elif isinstance(member, javalang.tree.MethodDeclaration):
                    params = ', '.join([f"{p.type.name if hasattr(p.type, 'name') else str(p.type)} {p.name}" for p in member.parameters])
                    method_str = f"{' '.join(member.modifiers)} {member.return_type.name if member.return_type else 'void'} {member.name}({params})".strip()
                    entry['methods'].append(method_str)
                    # Dependências por parâmetro
                    for p in member.parameters:
                        param_type = p.type.name if hasattr(p.type, 'name') else str(p.type)
                        dep_type = resolve_type(param_type, import_map, package)
                        if dep_type:
                            entry['relationships'].append({'type': 'DEPENDENCY', 'target': dep_type, 'usage': f'no método {member.name}'})
                # Construtores
                elif isinstance(member, javalang.tree.ConstructorDeclaration):
                    params = ', '.join([f"{p.type.name if hasattr(p.type, 'name') else str(p.type)} {p.name}" for p in member.parameters])
                    constr_str = f"{member.name}({params})"
                    entry['constructors'].append(constr_str)
                    # Dependências por parâmetro
                    for p in member.parameters:
                        param_type = p.type.name if hasattr(p.type, 'name') else str(p.type)
                        dep_type = resolve_type(param_type, import_map, package)
                        if dep_type:
                            entry['relationships'].append({'type': 'DEPENDENCY', 'target': dep_type, 'usage': f'no construtor'})
            symbol_table[full_name] = entry
    return symbol_table

def resolve_type(type_name, import_map, package):
    """Resolve o nome completo do tipo usando o import_map e o pacote atual."""
    if not type_name:
        return None
    if type_name in import_map:
        return import_map[type_name]
    if package:
        return f"{package}.{type_name}"
    return type_name

def generate_report(symbol_table):
    """
    Gera um relatório Markdown estruturado a partir da tabela de símbolos.
    """
    lines = ["# 📦 Relatório de Análise de Código Java\n"]
    for name, entry in symbol_table.items():
        lines.append(f"\n---\n\n### {name}  ")
        lines.append(f"Arquivo: `{entry['file_path']}`  ")
        lines.append(f"Tipo: **{entry['type']}**  ")
        if entry['extends']:
            lines.append(f"Extende: `{entry['extends']}`  ")
        if entry['implements']:
            lines.append(f"Implementa: {', '.join('`'+i+'`' for i in entry['implements'])}  ")
        if entry['fields']:
            lines.append("\n**Campos:**")
            for f in entry['fields']:
                lines.append(f"- {f}")
        if entry['constructors']:
            lines.append("\n**Construtores:**")
            for c in entry['constructors']:
                lines.append(f"- {c}")
        if entry['methods']:
            lines.append("\n**Métodos:**")
            for m in entry['methods']:
                lines.append(f"- {m}")
        if entry['relationships']:
            lines.append("\n**Relações:**")
            for rel in entry['relationships']:
                if rel['type'] == 'COMPOSITION':
                    lines.append(f"- COMPOSIÇÃO com `{rel['target']}`")
                elif rel['type'] == 'DEPENDENCY':
                    usage = rel.get('usage', '')
                    lines.append(f"- DEPENDÊNCIA de `{rel['target']}` {usage}")
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description="Analisador de Grafo de Código Java (Blueprint)")
    parser.add_argument('project_dir', help="Diretório raiz do projeto Java")
    parser.add_argument('--pergunta', help="Pergunta para o LLM (opcional)")
    parser.add_argument('--relatorio', help="Arquivo de saída do relatório (opcional)")
    args = parser.parse_args()

    print(f"🔎 Analisando projeto: {args.project_dir}")
    symbol_table = build_symbol_table(args.project_dir)
    print(f"✅ {len(symbol_table)} classes/interfaces analisadas.")

    report = generate_report(symbol_table)
    if args.relatorio:
        with open(args.relatorio, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📝 Relatório salvo em: {args.relatorio}")
    else:
        print(report)

    if args.pergunta:
        print("\n---\n\nPergunta para o LLM:")
        print(args.pergunta)
        print("\n(Chamada ao LLM seria feita aqui, ignorada conforme instrução)")

if __name__ == "__main__":
    main()
