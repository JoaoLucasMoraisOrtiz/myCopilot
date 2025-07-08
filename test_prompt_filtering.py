#!/usr/bin/env python3
"""
Script de teste para validar a filtragem de prompts no sistema de migração
"""

import os
import sys
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import load_previous_results_only, OUTPUT_DIR

def create_test_file_with_prompts():
    """Cria um arquivo de teste com prompts misturados"""
    
    test_content = """# Análise do Sistema Legado

## Componentes Principais

O sistema possui os seguintes componentes essenciais:
- Módulo de autenticação
- Sistema de processamento de dados
- Interface web responsiva

## Prompt 3.2: Planos de Execução

**Importante:** Detalhe a execução técnica completa para cada deliverable identificado, incluindo:

1. **Análise de Dependências**
   - Mapeamento de bibliotecas utilizadas
   - Identificação de conflitos potenciais

2. **Estratégia de Implementação**
   - Organize por sprints quinzenais
   - Deliverables claros para cada sprint

## Arquitetura Atual

A arquitetura do sistema legado apresenta:
- Monolito em Java
- Banco de dados Oracle
- Frontend em JSP

### Instruções para análise:

Desenvolva planos detalhados considerando as tecnologias identificadas.
Baseado na análise anterior, estruture as etapas.

## Recomendações Técnicas

Para a migração, recomenda-se:
- Adoção de microserviços
- Migração para PostgreSQL
- Frontend moderno em React

### Considerações de Performance

O sistema atual apresenta gargalos:
- Consultas SQL não otimizadas
- Ausência de cache
- Processamento síncrono

## Prompt Final: Validação

Importante:** Detalhe todos os aspectos técnicos identificados.
Organize por sprints e estabeleça deliverables claros.
"""
    
    test_file = os.path.join(OUTPUT_DIR, "test_prompt_contamination.md")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file, len(test_content)

def test_prompt_filtering():
    """Testa a filtragem de prompts"""
    
    print("🧪 TESTE DE FILTRAGEM DE PROMPTS")
    print("=" * 50)
    
    # Cria arquivo de teste
    test_file, original_size = create_test_file_with_prompts()
    print(f"📁 Arquivo de teste criado: {os.path.basename(test_file)}")
    print(f"📏 Tamanho original: {original_size:,} caracteres")
    
    # Testa a função de filtragem
    print("\n🔄 Aplicando filtro de prompts...")
    
    try:
        filtered_content = load_previous_results_only([test_file])
        filtered_size = len(filtered_content)
        
        print(f"📏 Tamanho filtrado: {filtered_size:,} caracteres")
        
        if filtered_size < original_size:
            reduction_pct = ((original_size - filtered_size) / original_size) * 100
            print(f"✅ Redução: {reduction_pct:.1f}%")
        else:
            print("⚠️  Nenhuma redução detectada")
        
        # Verifica se prompts foram removidos
        print("\n🔍 ANÁLISE DO CONTEÚDO FILTRADO:")
        print("-" * 30)
        
        prompt_indicators = [
            'prompt ', '**prompt', 'instruções para', 'desenvolva',
            'importante:** detalhe', 'organize por sprints',
            'baseado na análise', 'deliverables claros'
        ]
        
        prompts_found = []
        for indicator in prompt_indicators:
            if indicator in filtered_content.lower():
                prompts_found.append(indicator)
        
        if prompts_found:
            print("❌ PROMPTS AINDA PRESENTES:")
            for prompt in prompts_found:
                print(f"   - '{prompt}'")
        else:
            print("✅ Nenhum prompt detectado no conteúdo filtrado")
        
        # Mostra amostra do conteúdo filtrado
        print(f"\n📄 AMOSTRA DO CONTEÚDO FILTRADO ({min(500, filtered_size)} chars):")
        print("-" * 50)
        print(filtered_content[:500])
        if len(filtered_content) > 500:
            print("\n... (conteúdo truncado)")
        
        # Análise por seções
        sections = filtered_content.split('\n##')
        print(f"\n📊 SEÇÕES PRESERVADAS: {len(sections)}")
        for i, section in enumerate(sections[:3]):  # Mostra apenas 3 primeiras
            section_preview = section.strip()[:100].replace('\n', ' ')
            print(f"   {i+1}. {section_preview}...")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    
    # Limpa arquivo de teste
    try:
        os.remove(test_file)
        print(f"\n🗑️  Arquivo de teste removido")
    except:
        pass
    
    return True

def test_multiple_scenarios():
    """Testa múltiplos cenários de filtragem"""
    
    print("\n🧪 TESTE DE MÚLTIPLOS CENÁRIOS")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Arquivo com prompt no início",
            "content": """**Prompt 1.0:** Analise o sistema completo
            
# Análise Real
Este é conteúdo válido que deve ser preservado.
"""
        },
        {
            "name": "Arquivo com prompt no meio",
            "content": """# Análise Valid
Conteúdo importante aqui.

## Instruções para desenvolvimento:
Desenvolva planos detalhados considerando...

# Continuação válida
Mais conteúdo importante.
"""
        },
        {
            "name": "Arquivo sem prompts",
            "content": """# Documentação Técnica
## Componentes
- Módulo A
- Módulo B

### Detalhes de implementação
Informações técnicas relevantes.
"""
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Cenário {i}: {scenario['name']}")
        
        # Cria arquivo temporário
        temp_file = os.path.join(OUTPUT_DIR, f"test_scenario_{i}.md")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(scenario['content'])
        
        original_size = len(scenario['content'])
        
        # Testa filtragem
        try:
            filtered = load_previous_results_only([temp_file])
            filtered_size = len(filtered)
            
            if filtered_size < original_size:
                reduction = ((original_size - filtered_size) / original_size) * 100
                print(f"   ✅ Redução: {reduction:.1f}% ({original_size}→{filtered_size})")
            else:
                print(f"   ⚪ Sem redução ({original_size}→{filtered_size})")
        
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # Remove arquivo temporário
        try:
            os.remove(temp_file)
        except:
            pass

if __name__ == "__main__":
    print(f"🕒 Teste iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    
    success = test_prompt_filtering()
    test_multiple_scenarios()
    
    if success:
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS!")
    else:
        print("\n❌ Alguns testes falharam.")
    
    print(f"🕒 Teste finalizado em: {datetime.now().strftime('%H:%M:%S')}")
