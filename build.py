#!/usr/bin/env python3
"""
Build script para codingOS.

Constrói o supervisor.exe e depois o project_launcher.exe.
"""

import os
import subprocess
import sys

def run_command(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller não encontrado. Instale com: pip install pyinstaller")
        sys.exit(1)

    # Construir supervisor.exe
    print("Construindo supervisor.exe...")
    run_command([sys.executable, '-m', 'PyInstaller', '--clean', 'supervisor.spec'], cwd=base_dir)

    # Verificar se supervisor.exe foi criado
    supervisor_exe = os.path.join('dist', 'supervisor.exe')
    if not os.path.exists(os.path.join(base_dir, supervisor_exe)):
        print("Erro: supervisor.exe não foi criado.")
        sys.exit(1)

    # Construir project_launcher.exe
    print("Construindo project_launcher.exe...")
    run_command([sys.executable, '-m', 'PyInstaller', '--clean', 'project_launcher.spec'], cwd=base_dir)

    print("Build concluído!")
    print(f"Executáveis criados em: {os.path.join('dist', 'project_launcher.exe')}")

if __name__ == "__main__":
    main()