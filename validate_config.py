#!/usr/bin/env python3
"""
Validador de Configuração de Migração
Valida se o arquivo YAML/JSON está correto antes de executar a migração
"""

import yaml
import json
import sys
from pathlib import Path

def validate_migration_config(config_path):
    """Valida um arquivo de configuração de migração"""
    
    print(f"🔍 Validando arquivo: {config_path}")
    
    # Verifica se arquivo existe
    if not Path(config_path).exists():
        print(f"❌ Erro: Arquivo não encontrado: {config_path}")
        return False
    
    try:
        # Tenta carregar como YAML primeiro
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                config = json.load(f)
            else:
                config = yaml.safe_load(f)
        
        print("✅ Arquivo carregado com sucesso")
        
    except yaml.YAMLError as e:
        print(f"❌ Erro de sintaxe YAML: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Erro de sintaxe JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return False
    
    # Valida estrutura
    if 'migration_config' not in config:
        print("❌ Erro: Chave 'migration_config' não encontrada")
        return False
    
    migration_config = config['migration_config']
    
    # Campos obrigatórios
    required_fields = [
        'project_name',
        'migration_objective', 
        'current_stack',
        'target_stack'
    ]
    
    print("\n📋 Validando campos obrigatórios...")
    for field in required_fields:
        if field not in migration_config:
            print(f"❌ Campo obrigatório ausente: {field}")
            return False
        else:
            print(f"✅ {field}: {migration_config[field] if isinstance(migration_config[field], str) else '(configurado)'}")
    
    # Valida current_stack
    print("\n🔧 Validando stack atual...")
    current_stack = migration_config.get('current_stack', {})
    if 'language' in current_stack and 'version' in current_stack:
        print(f"✅ Stack atual: {current_stack['language']} {current_stack['version']}")
    else:
        print("⚠️ Aviso: Informações do stack atual incompletas")
    
    # Valida target_stack  
    print("🎯 Validando stack alvo...")
    target_stack = migration_config.get('target_stack', {})
    if 'language' in target_stack and 'version' in target_stack:
        print(f"✅ Stack alvo: {target_stack['language']} {target_stack['version']}")
    else:
        print("⚠️ Aviso: Informações do stack alvo incompletas")
    
    # Valida arquitetura alvo
    if 'target_architecture' in migration_config:
        arch = migration_config['target_architecture']
        print(f"🏗️ Arquitetura alvo: {arch.get('type', 'não especificado')}")
        print(f"📡 API Style: {arch.get('api_style', 'não especificado')}")
    
    # Valida componentes críticos
    if 'critical_components' in migration_config:
        components = migration_config['critical_components']
        print(f"\n🔥 Componentes críticos identificados: {len(components)}")
        for comp in components:
            if 'name' in comp:
                criticality = comp.get('criticality', 'medium')
                print(f"   • {comp['name']} ({criticality})")
    
    # Valida restrições
    if 'constraints' in migration_config:
        constraints = migration_config['constraints']
        print(f"\n⏰ Restrições:")
        if 'timeline' in constraints:
            print(f"   • Timeline: {constraints['timeline']}")
        if 'budget_limit' in constraints:
            print(f"   • Orçamento: {constraints['budget_limit']}")
        if 'max_downtime' in constraints:
            print(f"   • Downtime máximo: {constraints['max_downtime']}")
    
    print(f"\n🎉 Configuração válida! Arquivo pronto para uso.")
    return True

def main():
    if len(sys.argv) != 2:
        print("Uso: python validate_config.py <caminho_do_arquivo>")
        print("\nExemplos:")
        print("  python validate_config.py migration_config.yaml")
        print("  python validate_config.py /caminho/para/config.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    print("🧪 VALIDADOR DE CONFIGURAÇÃO DE MIGRAÇÃO")
    print("=" * 50)
    
    if validate_migration_config(config_path):
        print("\n✅ Sucesso! Sua configuração está pronta para uso.")
        print("Execute: python main.py")
        print("Escolha: [0] Fase 0: Configuração da Migração")
        sys.exit(0)
    else:
        print("\n❌ Falha na validação. Corrija os erros e tente novamente.")
        print("\n💡 Dicas:")
        print("  • Use o arquivo migration_config_example.yaml como base")
        print("  • Verifique a sintaxe YAML em: https://yaml-online-parser.appspot.com/")
        print("  • Consulte o GUIA_DE_USO.md para mais detalhes")
        sys.exit(1)

if __name__ == "__main__":
    main()
