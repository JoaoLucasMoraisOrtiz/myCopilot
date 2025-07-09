#!/bin/bash

# Exemplo de teste do modo NEW
echo "🚀 Testando o modo NEW do MyCopilot"
echo "=================================="

# Limpa estado anterior
echo "🧹 Limpando estado anterior..."
python main.py --clean

# Cria diretório de teste
mkdir -p /tmp/test_project
echo "📁 Diretório de teste criado: /tmp/test_project"

# Executa o agente no modo NEW
echo "🆕 Iniciando modo NEW..."
python main.py new \
    --project-path /tmp/test_project \
    --goal "Criar uma classe Java simples chamada Calculator com métodos básicos de soma, subtração, multiplicação e divisão" \
    --max-turns 5

echo "✅ Teste concluído!"
echo "📂 Verifique o diretório /tmp/test_project para ver os arquivos criados"
