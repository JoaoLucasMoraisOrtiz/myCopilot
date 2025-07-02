#!/bin/bash

# Script para configurar e testar o CLI do Java Reengineering Agent

echo "=== Configuração e Teste do CLI ==="
echo

# 1. Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do agente"
    exit 1
fi

# 2. Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado. Execute setup_logging.sh primeiro."
    exit 1
fi

# 3. Instalar dependências CLI
echo "📥 Instalando dependências CLI..."
pip install typer>=0.9.0 rich>=13.0.0 > /dev/null 2>&1

# 4. Testar importação do CLI
echo "🧪 Testando CLI..."
python3 -c "
import sys
sys.path.append('src')
try:
    from cli.commands import app
    print('✓ CLI modules imported successfully')
except Exception as e:
    print(f'❌ Error importing CLI: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Falha no teste de importação"
    exit 1
fi

# 5. Testar comandos básicos
echo
echo "🚀 Testando comandos CLI..."

echo "📋 Testando --help:"
python3 src/main.py --help

echo
echo "📋 Testando version:"
python3 src/main.py version

# 6. Criar workspace de teste
echo
echo "🏗️  Testando init:"
TEST_WORKSPACE="test_workspace_cli"
if [ -d "$TEST_WORKSPACE" ]; then
    rm -rf "$TEST_WORKSPACE"
fi

mkdir "$TEST_WORKSPACE"
cd "$TEST_WORKSPACE"
python3 ../src/main.py init --force .

echo
echo "📊 Testando status:"
python3 ../src/main.py status

echo
echo "⚙️  Testando configure (modo não-interativo):"
echo -e "Test Project\n./legacy-system\n17\n3.2\ny\ny" | python3 ../src/main.py configure || true

# 7. Verificar arquivos criados
echo
echo "📁 Verificando estrutura criada:"
ls -la

echo
echo "📄 Conteúdo do agent.toml:"
if [ -f "agent.toml" ]; then
    cat agent.toml
fi

# 8. Limpar workspace de teste
cd ..
echo
echo "🧹 Limpando workspace de teste..."
rm -rf "$TEST_WORKSPACE"

echo
echo "🎉 Teste do CLI concluído com sucesso!"
echo
echo "Para usar o CLI:"
echo "1. source venv/bin/activate"
echo "2. python src/main.py --help"
echo "3. python src/main.py init my-project"
echo "4. cd my-project"
echo "5. python ../src/main.py analyze"
