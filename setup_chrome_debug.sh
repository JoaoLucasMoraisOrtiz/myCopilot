#!/bin/bash

# Script para resolver o problema de conexão com Chrome Debug
echo "🔧 Solucionando problema de conexão com Chrome Debug"
echo "================================================="

# Função para detectar o navegador instalado
detect_browser() {
    if command -v google-chrome &> /dev/null; then
        echo "google-chrome"
    elif command -v chromium-browser &> /dev/null; then
        echo "chromium-browser"
    elif command -v chromium &> /dev/null; then
        echo "chromium"
    else
        echo "none"
    fi
}

# Função para matar processos existentes do Chrome
kill_existing_chrome() {
    echo "🔄 Matando processos existentes do Chrome..."
    pkill -f "chrome" 2>/dev/null || true
    pkill -f "chromium" 2>/dev/null || true
    sleep 2
}

# Função para iniciar Chrome com debug
start_chrome_debug() {
    local browser=$1
    echo "🚀 Iniciando $browser com debug remoto..."
    
    # Cria diretório temporário para perfil
    local temp_profile="/tmp/chrome_debug_profile"
    rm -rf "$temp_profile"
    mkdir -p "$temp_profile"
    
    # Parâmetros para Chrome debug
    local chrome_args=(
        "--remote-debugging-port=9222"
        "--remote-debugging-address=127.0.0.1"
        "--remote-allow-origins=*"
        "--user-data-dir=$temp_profile"
        "--no-first-run"
        "--no-default-browser-check"
        "--disable-web-security"
        "--disable-features=VizDisplayCompositor"
        "--disable-dev-shm-usage"
        "--no-sandbox"
        "https://vscode.dev"
    )
    
    if [[ "$browser" == "google-chrome" ]]; then
        google-chrome "${chrome_args[@]}" > /dev/null 2>&1 &
    elif [[ "$browser" == "chromium-browser" ]]; then
        chromium-browser "${chrome_args[@]}" > /dev/null 2>&1 &
    elif [[ "$browser" == "chromium" ]]; then
        chromium "${chrome_args[@]}" > /dev/null 2>&1 &
    fi
    
    local chrome_pid=$!
    echo "✅ Chrome iniciado com PID: $chrome_pid"
    
    # Aguarda Chrome inicializar
    echo "⏳ Aguardando Chrome inicializar..."
    sleep 5
    
    # Verifica se o Chrome está rodando
    if ! kill -0 $chrome_pid 2>/dev/null; then
        echo "❌ Chrome não está rodando!"
        return 1
    fi
    
    # Testa conexão debug
    echo "🔍 Testando conexão debug..."
    if curl -s "http://localhost:9222/json" > /dev/null; then
        echo "✅ Conexão debug funcionando!"
        return 0
    else
        echo "❌ Conexão debug não está funcionando"
        return 1
    fi
}

# Função para verificar se VS Code está carregado
check_vscode_loaded() {
    echo "🔍 Verificando se VS Code está carregado..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://localhost:9222/json" | grep -q "vscode.dev"; then
            echo "✅ VS Code detectado no Chrome!"
            return 0
        fi
        
        echo "⏳ Aguardando VS Code carregar... (tentativa $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    echo "❌ VS Code não foi detectado após $max_attempts tentativas"
    return 1
}

# Função para ativar Copilot Chat
activate_copilot_chat() {
    echo "📋 Instruções para ativar Copilot Chat:"
    echo "1. Abra o VS Code no navegador"
    echo "2. Instale a extensão GitHub Copilot Chat"
    echo "3. Faça login na sua conta GitHub"
    echo "4. Abra o painel do Copilot Chat (Ctrl+Shift+P > 'Chat: Focus on Chat View')"
    echo "5. Certifique-se de que o chat está ativo e visível"
    echo ""
    echo "🎯 Quando estiver pronto, pressione Enter para continuar..."
    read -r
}

# Função principal
main() {
    echo "🔧 Iniciando configuração do Chrome Debug..."
    
    # Detecta navegador
    local browser=$(detect_browser)
    if [[ "$browser" == "none" ]]; then
        echo "❌ Nenhum navegador Chrome/Chromium encontrado!"
        echo "📥 Instale o Chrome ou Chromium:"
        echo "   Ubuntu/Debian: sudo apt install chromium-browser"
        echo "   Fedora: sudo dnf install chromium"
        echo "   Arch: sudo pacman -S chromium"
        exit 1
    fi
    
    echo "✅ Navegador encontrado: $browser"
    
    # Mata processos existentes
    kill_existing_chrome
    
    # Inicia Chrome com debug
    if start_chrome_debug "$browser"; then
        echo "✅ Chrome configurado com sucesso!"
    else
        echo "❌ Falha ao configurar Chrome"
        exit 1
    fi
    
    # Verifica se VS Code carregou
    if check_vscode_loaded; then
        echo "✅ VS Code carregado!"
    else
        echo "⚠️ VS Code não detectado automaticamente"
        echo "👉 Certifique-se de que https://vscode.dev está aberto na aba"
    fi
    
    # Instruções para Copilot Chat
    activate_copilot_chat
    
    echo "🎉 Configuração concluída!"
    echo "🚀 Agora você pode executar o MyCopilot:"
    echo "   python main.py new --goal 'Criar uma calculadora simples'"
    echo ""
    echo "🔍 Para verificar se está funcionando:"
    echo "   curl http://localhost:9222/json"
    echo ""
    echo "🛑 Para parar o Chrome debug:"
    echo "   pkill -f 'remote-debugging-port=9222'"
}

# Executa função principal
main "$@"
