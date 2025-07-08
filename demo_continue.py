#!/usr/bin/env python3
"""
Script de demonstração do modo continue
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"💻 Comando: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd="/home/joao/Documentos/myCopilot/myCopilot")
    
    if result.stdout:
        print("📤 OUTPUT:")
        print(result.stdout)
    
    if result.stderr:
        print("⚠️ ERROR:")
        print(result.stderr)
    
    return result.returncode == 0

def demo_continue_mode():
    """Demonstra o funcionamento do modo continue"""
    
    print("🎯 DEMONSTRAÇÃO DO MODO CONTINUE")
    print("="*60)
    
    # 1. Limpa estado anterior se existir
    print("\n1. Limpando estado anterior...")
    run_command("python3 main.py --clean", "Limpeza do estado")
    
    # 2. Mostra ajuda
    print("\n2. Mostrando opções de uso...")
    run_command("python3 main.py --help", "Exibição da ajuda")
    
    # 3. Verifica se existe estado salvo
    state_file = Path("/home/joao/Documentos/myCopilot/myCopilot/agent_state.pkl")
    print(f"\n3. Estado salvo existe? {state_file.exists()}")
    
    print("\n" + "="*60)
    print("🎯 PARA TESTAR O MODO CONTINUE:")
    print("="*60)
    print("1. Execute: python3 main.py")
    print("   (Deixe executar alguns turnos e depois interrompa com Ctrl+C)")
    print()
    print("2. Execute: python3 main.py --continue")
    print("   (Irá retomar do ponto onde parou)")
    print()
    print("3. Execute: python3 main.py --clean")
    print("   (Para limpar o estado salvo)")
    print("="*60)

if __name__ == "__main__":
    demo_continue_mode()
