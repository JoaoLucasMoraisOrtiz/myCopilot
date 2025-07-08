#!/usr/bin/env python3
"""
Teste do sistema de estrutura de projeto e geração de código organizado
"""

import os
import sys
import tempfile
import shutil

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_structure_manager import ProjectStructureManager
from helper.code_parser import extract_structured_code_blocks, StructuredCodeBlock

def test_project_structure_system():
    """Testa o sistema completo de estrutura de projeto"""
    
    # Cria diretório temporário para testes
    test_dir = tempfile.mkdtemp()
    
    try:
        print("🧪 Testando Sistema de Estrutura de Projeto...")
        
        # 1. Testa inicialização do gerenciador
        print("\n1. Testando inicialização do gerenciador...")
        manager = ProjectStructureManager(test_dir)
        
        assert (manager.new_system_dir).exists(), "Diretório do novo sistema não foi criado"
        assert manager.structure_config_file.exists(), "Arquivo de configuração não foi criado"
        print("✅ Gerenciador inicializado com sucesso")
        
        # 2. Testa criação de estrutura
        print("\n2. Testando criação de estrutura de diretórios...")
        manager._create_directory_structure()
        
        # Verifica se diretórios foram criados
        expected_dirs = [
            "backend/src/main/java/com/company/app/controller",
            "backend/src/main/java/com/company/app/service",
            "backend/src/main/java/com/company/app/repository",
            "frontend/src/components",
            "frontend/src/pages",
            "database/migrations"
        ]
        
        for dir_path in expected_dirs:
            full_path = manager.new_system_dir / dir_path
            assert full_path.exists(), f"Diretório {dir_path} não foi criado"
        
        print("✅ Estrutura de diretórios criada com sucesso")
        
        # 3. Testa detecção de localização de arquivos
        print("\n3. Testando detecção de localização de arquivos...")
        
        # Testa código Java de controller
        java_controller_code = """
        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @GetMapping
            public List<User> getAllUsers() {
                return userService.getAllUsers();
            }
        }
        """
        
        location, file_type = manager.determine_file_location(
            java_controller_code, "java", "api", "Implementar REST controller para usuários"
        )
        
        assert "controller" in location, f"Localização incorreta: {location}"
        assert file_type == "controller", f"Tipo incorreto: {file_type}"
        print("✅ Detecção de localização Java funcionando")
        
        # Testa código React
        react_component_code = """
        import React from 'react';
        
        const UserList = () => {
            return (
                <div>
                    <h1>Users</h1>
                </div>
            );
        };
        
        export default UserList;
        """
        
        location, file_type = manager.determine_file_location(
            react_component_code, "javascript", "frontend", "Implementar componente de lista de usuários"
        )
        
        assert "components" in location, f"Localização incorreta: {location}"
        assert file_type == "component", f"Tipo incorreto: {file_type}"
        print("✅ Detecção de localização React funcionando")
        
        # 4. Testa salvamento de arquivos
        print("\n4. Testando salvamento de arquivos...")
        
        saved_path = manager.save_generated_file(
            code_content=java_controller_code,
            code_language="java",
            task_index=1,
            task_description="Implementar REST controller para usuários",
            component_hint="api-controller"
        )
        
        assert os.path.exists(saved_path), f"Arquivo não foi salvo: {saved_path}"
        print(f"✅ Arquivo salvo em: {saved_path}")
        
        # 5. Testa extração de blocos estruturados
        print("\n5. Testando extração de blocos estruturados...")
        
        structured_response = """
        ARQUIVO: UserService.java
        LOCALIZAÇÃO: backend/src/main/java/com/company/app/service
        COMPONENTE: business-service
        DESCRIÇÃO: Serviço de negócio para operações de usuário
        
        ```java
        @Service
        public class UserService {
            private final UserRepository userRepository;
            
            public UserService(UserRepository userRepository) {
                this.userRepository = userRepository;
            }
            
            public List<User> getAllUsers() {
                return userRepository.findAll();
            }
        }
        ```
        
        DEPENDÊNCIAS: UserRepository, User model
        
        ARQUIVO: UserRepository.java
        LOCALIZAÇÃO: backend/src/main/java/com/company/app/repository
        COMPONENTE: data-access
        DESCRIÇÃO: Repositório para acesso aos dados de usuário
        
        ```java
        @Repository
        public interface UserRepository extends JpaRepository<User, Long> {
            List<User> findByActiveTrue();
        }
        ```
        
        DEPENDÊNCIAS: User model, JpaRepository
        """
        
        blocks = extract_structured_code_blocks(structured_response)
        
        assert len(blocks) == 2, f"Deveria extrair 2 blocos, extraiu {len(blocks)}"
        assert blocks[0].filename == "UserService.java", f"Nome incorreto: {blocks[0].filename}"
        assert blocks[0].component == "business-service", f"Componente incorreto: {blocks[0].component}"
        assert len(blocks[0].dependencies) == 2, f"Dependências incorretas: {blocks[0].dependencies}"
        print("✅ Extração de blocos estruturados funcionando")
        
        # 6. Testa geração de resumo
        print("\n6. Testando geração de resumo do projeto...")
        
        summary = manager.generate_project_summary()
        assert "Resumo do Projeto Migrado" in summary, "Resumo não contém título esperado"
        assert "Total de arquivos gerados" in summary, "Resumo não contém contagem de arquivos"
        print("✅ Geração de resumo funcionando")
        
        # 7. Testa visão geral da estrutura
        print("\n7. Testando visão geral da estrutura...")
        
        overview = manager.get_structure_overview()
        assert "📁 Estrutura do Novo Sistema" in overview, "Overview não contém título"
        assert "📂" in overview, "Overview não contém ícones de pasta"
        print("✅ Visão geral da estrutura funcionando")
        
        print("\n🎉 Todos os testes do sistema de estrutura passaram!")
        print(f"📁 Estrutura de teste criada em: {manager.new_system_dir}")
        
        # Mostra a estrutura criada
        print(f"\n📄 Visão geral da estrutura:")
        print("=" * 60)
        print(overview)
        print("=" * 60)
        
        print(f"\n📊 Resumo do projeto:")
        print("=" * 60)
        print(summary)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Mantém arquivos para inspeção (opcional - descomente para limpar)
        # shutil.rmtree(test_dir)
        print(f"\n🗂️ Arquivos de teste mantidos em: {test_dir}")

if __name__ == "__main__":
    test_project_structure_system()
