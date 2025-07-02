#!/usr/bin/env python3
"""
Java Reengineering Agent - Main Entry Point

Agente de IA para reengenharia completa de sistemas Java legados usando Amazon Q.

Usage:
    python main.py --help
    python main.py analyze --legacy-path /path/to/legacy/system
    python main.py generate --framework spring-boot
"""

import sys
from pathlib import Path

# Adicionar diretório CLI ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cli.commands import app
    
    def main():
        """Ponto de entrada principal"""
        app()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Erro ao importar CLI: {e}")
    print("📦 Certifique-se de que as dependências estão instaladas:")
    print("   pip install typer rich")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n👋 Operação cancelada pelo usuário")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    sys.exit(1)
