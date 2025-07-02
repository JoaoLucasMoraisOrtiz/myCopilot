"""
Exemplo de uso do sistema de logging no Java Reengineering Agent
"""

import os
import sys
from pathlib import Path

# Configurar path para importar módulos do agente
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from utils.logger import (
        setup_logging, get_logger, log_execution, 
        TemporaryLogging, cleanup_logging, get_default_logger
    )
    LOGURU_AVAILABLE = True
except ImportError:
    print("Loguru não instalado. Instale com: pip install loguru")
    LOGURU_AVAILABLE = False


def exemplo_analise_legacy():
    """Exemplo de como usar logging em análise de sistema legacy"""
    if not LOGURU_AVAILABLE:
        return
    
    logger = get_logger()
    
    # Log de início da análise
    logger.analysis("Iniciando análise do sistema legacy", 
                   system_path="/path/to/legacy/system",
                   estimated_files=150)
    
    # Simular análise de arquivos
    for i in range(3):
        file_path = f"/path/to/legacy/File{i+1}.java"
        logger.legacy_system(f"Analisando arquivo {i+1}/3", 
                           file_path=file_path,
                           size_kb=45 + i*10)
    
    # Log de conclusão
    logger.analysis("Análise concluída", 
                   files_processed=3,
                   god_classes_found=1,
                   issues_found=12)


@log_execution(category="generation", log_args=True)
def exemplo_geracao_codigo(feature_name: str, output_dir: str):
    """Exemplo de função com logging automático"""
    logger = get_logger()
    
    logger.generation(f"Gerando código para feature: {feature_name}")
    
    # Simular geração
    output_files = ["Service.java", "Repository.java", "Controller.java"]
    
    for file_name in output_files:
        logger.new_system(f"Arquivo gerado: {file_name}",
                         output_file=f"{output_dir}/{file_name}")
    
    return output_files


def exemplo_pipeline_completo():
    """Exemplo de logging em pipeline completo"""
    if not LOGURU_AVAILABLE:
        return
    
    logger = get_logger()
    
    # Pipeline steps
    steps = ["analysis", "decomposition", "generation", "validation"]
    
    for i, step in enumerate(steps, 1):
        logger.pipeline(f"Executando etapa {i}/{len(steps)}: {step.title()}", 
                       step=step,
                       progress=f"{i}/{len(steps)}")
        
        # Simular trabalho
        if step == "analysis":
            exemplo_analise_legacy()
        elif step == "generation":
            exemplo_geracao_codigo("UserManagement", "/output/user")


def exemplo_metricas_performance():
    """Exemplo de logging de métricas de performance"""
    if not LOGURU_AVAILABLE:
        return
    
    logger = get_logger()
    
    # Diferentes tipos de métricas
    logger.performance("Parsing de código Java", duration=3.2, files_parsed=85)
    logger.performance("Embedding generation", duration=12.7, tokens_processed=15000)
    logger.performance("RAG query", duration=0.8, chunks_retrieved=5)


def exemplo_integracao_amazon_q():
    """Exemplo de logging para integração com Amazon Q"""
    if not LOGURU_AVAILABLE:
        return
    
    logger = get_logger()
    
    # Log de chamadas para Amazon Q
    logger.amazon_q("Enviando prompt para análise de código",
                   prompt_tokens=1200,
                   max_response_tokens=2000)
    
    logger.amazon_q("Resposta recebida do Amazon Q",
                   response_tokens=1850,
                   code_blocks_generated=3)


def main():
    """Função principal demonstrando uso completo do sistema"""
    if not LOGURU_AVAILABLE:
        print("Este exemplo requer loguru. Instale com:")
        print("pip install loguru")
        return
    
    print("=== Exemplo de Sistema de Logging ===")
    
    # 1. Configurar logging
    print("1. Configurando sistema de logging...")
    config = setup_logging(log_dir="logs/examples", debug=True)
    
    if config is None:
        print("Erro ao configurar logging")
        return
    
    # 2. Obter logger
    logger = get_logger()
    logger.info("Sistema de logging configurado com sucesso")
    
    # 3. Exemplos de uso
    print("2. Executando exemplos de logging...")
    
    logger.info("Iniciando demonstração do sistema de logging")
    
    # Análise legacy
    exemplo_analise_legacy()
    
    # Geração de código
    files_generated = exemplo_geracao_codigo("UserService", "/output/user")
    logger.info(f"Arquivos gerados: {files_generated}")
    
    # Pipeline completo
    exemplo_pipeline_completo()
    
    # Métricas de performance
    exemplo_metricas_performance()
    
    # Integração Amazon Q
    exemplo_integracao_amazon_q()
    
    # 4. Exemplo com context manager
    print("3. Testando logging temporário...")
    with TemporaryLogging(log_dir="logs/temp", debug=False) as temp_logger:
        temp_logger.info("Este é um log temporário")
        temp_logger.generation("Geração temporária de código")
    
    # 5. Finalizar
    logger.info("Demonstração concluída")
    
    print("4. Limpando recursos...")
    cleanup_logging()
    
    print("\n✅ Exemplo concluído!")
    print(f"Verifique os logs em: {Path('logs/examples').absolute()}")


if __name__ == "__main__":
    main()
