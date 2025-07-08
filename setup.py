#!/usr/bin/env python3
"""
Script de Inicialização do Sistema de Migração
Configura rapidamente um novo projeto de migração
"""

import os
import sys
import yaml
from pathlib import Path

def create_quick_config():
    """Cria uma configuração básica interativamente"""
    
    print("🚀 CONFIGURAÇÃO RÁPIDA DE MIGRAÇÃO")
    print("=" * 40)
    print("Vou ajudar você a criar uma configuração básica.\n")
    
    # Coleta informações básicas
    project_name = input("📝 Nome do projeto: ").strip()
    if not project_name:
        project_name = "MinhaMigracao"
    
    print(f"\n🎯 Qual é o objetivo principal da migração?")
    print("1. Modernizar tecnologia")
    print("2. Melhorar performance")
    print("3. Reduzir custos")
    print("4. Facilitar manutenção")
    print("5. Outro")
    
    objetivo_choice = input("Escolha (1-5): ").strip()
    objetivos = {
        "1": "Modernizar stack tecnológico para versões atuais",
        "2": "Melhorar performance e escalabilidade do sistema",
        "3": "Reduzir custos de infraestrutura e manutenção",
        "4": "Facilitar manutenção e desenvolvimento futuro",
        "5": "Objetivo personalizado"
    }
    
    if objetivo_choice == "5":
        objetivo = input("Descreva o objetivo: ").strip()
    else:
        objetivo = objetivos.get(objetivo_choice, objetivos["1"])
    
    # Stack atual
    print(f"\n💻 Tecnologia atual:")
    current_lang = input("Linguagem principal: ").strip() or "Java"
    current_version = input(f"Versão do {current_lang}: ").strip() or "8"
    current_framework = input("Framework principal: ").strip() or "Spring"
    
    # Stack alvo
    print(f"\n🎯 Tecnologia alvo:")
    target_lang = input("Linguagem alvo: ").strip() or "Java"
    target_version = input(f"Versão do {target_lang}: ").strip() or "17"
    target_framework = input("Framework alvo: ").strip() or "Spring Boot"
    
    # Arquitetura
    print(f"\n🏗️ Arquitetura alvo:")
    print("1. Monolito")
    print("2. Microsserviços")
    print("3. Serverless")
    print("4. Híbrida")
    
    arch_choice = input("Escolha (1-4): ").strip()
    arquiteturas = {
        "1": {"type": "monolith", "api_style": "REST"},
        "2": {"type": "microservices", "api_style": "REST"},
        "3": {"type": "serverless", "api_style": "REST"},
        "4": {"type": "hybrid", "api_style": "REST"}
    }
    
    target_arch = arquiteturas.get(arch_choice, arquiteturas["1"])
    
    # Restrições
    timeline = input("\n⏰ Timeline desejado (ex: 3 meses): ").strip() or "3 meses"
    
    # Cria a configuração
    config = {
        "migration_config": {
            "project_name": project_name,
            "migration_objective": objetivo,
            "current_stack": {
                "language": current_lang,
                "version": current_version,
                "framework": current_framework
            },
            "target_stack": {
                "language": target_lang,
                "version": target_version,
                "framework": target_framework
            },
            "target_architecture": target_arch,
            "constraints": {
                "timeline": timeline,
                "budget_limit": "A definir",
                "max_downtime": "4 horas"
            },
            "critical_components": [
                {
                    "name": "Sistema principal",
                    "criticality": "high",
                    "notes": "Componente core do sistema"
                }
            ]
        }
    }
    
    # Salva o arquivo
    filename = f"migration_{project_name.lower().replace(' ', '_')}.yaml"
    
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"\n✅ Configuração criada: {filename}")
    print(f"\n🎉 Pronto! Agora você pode:")
    print(f"   1. Editar {filename} se necessário")
    print(f"   2. Validar: python validate_config.py {filename}")
    print(f"   3. Executar: python main.py")
    
    return filename

def setup_legacy_directory():
    """Ajuda a configurar o diretório do sistema legado"""
    
    print("\n📁 CONFIGURAÇÃO DO DIRETÓRIO LEGADO")
    print("=" * 40)
    
    print("Onde está localizado seu sistema legado?")
    print("1. Diretório local")
    print("2. Repositório Git")
    print("3. Arquivo compactado")
    print("4. Já está configurado")
    
    choice = input("Escolha (1-4): ").strip()
    
    if choice == "1":
        legacy_path = input("Caminho completo do diretório: ").strip()
        if Path(legacy_path).exists():
            print(f"✅ Diretório encontrado: {legacy_path}")
            print(f"💡 Use este caminho na Fase 0 do sistema")
        else:
            print(f"❌ Diretório não encontrado: {legacy_path}")
    
    elif choice == "2":
        repo_url = input("URL do repositório: ").strip()
        local_path = input("Onde clonar (pasta local): ").strip() or "./legacy_system"
        print(f"📥 Clone o repositório:")
        print(f"   git clone {repo_url} {local_path}")
        print(f"💡 Depois use o caminho: {os.path.abspath(local_path)}")
    
    elif choice == "3":
        archive_path = input("Caminho do arquivo compactado: ").strip()
        extract_path = input("Onde extrair: ").strip() or "./legacy_system"
        print(f"📦 Extraia o arquivo:")
        print(f"   unzip {archive_path} -d {extract_path}")
        print(f"   # ou")
        print(f"   tar -xzf {archive_path} -C {extract_path}")
        print(f"💡 Depois use o caminho: {os.path.abspath(extract_path)}")
    
    else:
        print("✅ Ótimo! Continue com a execução.")

def main():
    print("🔧 SETUP INICIAL - SISTEMA DE MIGRAÇÃO")
    print("=" * 50)
    print("Este script ajuda você a configurar rapidamente uma nova migração.\n")
    
    print("O que você gostaria de fazer?")
    print("1. Criar configuração rápida")
    print("2. Configurar diretório do sistema legado")
    print("3. Usar configuração existente")
    print("4. Ver ajuda")
    
    choice = input("\nEscolha (1-4): ").strip()
    
    if choice == "1":
        config_file = create_quick_config()
        setup_legacy = input(f"\nConfigurar diretório legado agora? (s/n): ").strip().lower()
        if setup_legacy in ['s', 'sim', 'y', 'yes']:
            setup_legacy_directory()
    
    elif choice == "2":
        setup_legacy_directory()
    
    elif choice == "3":
        print("\n📋 Arquivos de configuração encontrados:")
        yaml_files = list(Path(".").glob("*.yaml")) + list(Path(".").glob("*.yml"))
        json_files = list(Path(".").glob("*config*.json"))
        
        all_configs = yaml_files + json_files
        
        if all_configs:
            for i, config_file in enumerate(all_configs, 1):
                print(f"   {i}. {config_file}")
            
            print(f"\n💡 Para validar um arquivo:")
            print(f"   python validate_config.py <nome_do_arquivo>")
            print(f"\n🚀 Para executar:")
            print(f"   python main.py")
        else:
            print("   Nenhum arquivo de configuração encontrado.")
            print("   Execute a opção 1 para criar um novo.")
    
    else:
        print("\n📖 AJUDA - SISTEMA DE MIGRAÇÃO")
        print("=" * 30)
        print("1. 📝 migration_config_example.yaml - Exemplo completo")
        print("2. 📚 GUIA_DE_USO.md - Documentação completa")
        print("3. 🧪 validate_config.py - Validador de configuração")
        print("4. 🚀 main.py - Sistema principal")
        print("\n🔗 Fluxo recomendado:")
        print("   1. Criar/editar configuração")
        print("   2. Validar configuração")
        print("   3. Executar migração")

if __name__ == "__main__":
    main()
