"""
Gerenciador de Configuração de Migração (Fase 0)
Coleta e gerencia as preferências e requisitos do usuário para migração
"""

import os
import json
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class MigrationRequirements:
    """Requisitos de migração especificados pelo usuário"""
    
    # Tecnologias atuais
    current_technology_stack: Dict[str, str]
    
    # Tecnologias alvo
    target_technology_stack: Dict[str, str]
    
    # Arquitetura
    current_architecture: str
    target_architecture: str
    
    # Preferências específicas
    preferences: Dict[str, str]
    
    # Restrições e considerações
    constraints: List[str]
    
    # Prioridades (performance, security, maintainability, etc.)
    priorities: List[str]
    
    # Timeline e recursos
    timeline: str
    team_size: int
    team_skills: List[str]
    
    # Considerações de negócio
    business_requirements: List[str]
    
    # Observações especiais
    special_notes: str

class MigrationConfigManager:
    """Gerencia configuração de migração baseada nos requisitos do usuário"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.config_file = self.output_dir / "migration_config.json"
        self.requirements_file = self.output_dir / "user_requirements.json"
        self.requirements: Optional[MigrationRequirements] = None
        
        self.output_dir.mkdir(exist_ok=True)
    
    def collect_user_requirements_interactive(self) -> MigrationRequirements:
        """Coleta requisitos do usuário de forma interativa"""
        
        print("🚀 FASE 0: CONFIGURAÇÃO DA MIGRAÇÃO")
        print("=" * 50)
        print("Vamos coletar suas preferências para personalizar todo o processo de migração.\n")
        
        # Tecnologias atuais
        print("📋 1. TECNOLOGIAS ATUAIS")
        current_stack = {}
        current_stack['language'] = input("Linguagem principal atual (ex: Java 6, Python 2.7): ").strip()
        current_stack['framework'] = input("Framework principal atual (ex: Struts, Spring 3.x): ").strip()
        current_stack['database'] = input("Banco de dados atual (ex: Oracle 11g, MySQL 5.7): ").strip()
        current_stack['server'] = input("Servidor de aplicação atual (ex: Tomcat 7, JBoss): ").strip()
        current_stack['other'] = input("Outras tecnologias relevantes: ").strip()
        
        # Tecnologias alvo
        print("\n🎯 2. TECNOLOGIAS ALVO")
        target_stack = {}
        target_stack['language'] = input("Linguagem alvo (ex: Java 17, Python 3.11): ").strip()
        target_stack['framework'] = input("Framework alvo (ex: Spring Boot 3.x, FastAPI): ").strip()
        target_stack['database'] = input("Banco de dados alvo (ex: PostgreSQL 15, MongoDB): ").strip()
        target_stack['server'] = input("Servidor alvo (ex: WildFly, Docker): ").strip()
        target_stack['api_style'] = input("Estilo de API (ex: REST, GraphQL, SOAP): ").strip()
        target_stack['other'] = input("Outras tecnologias alvo: ").strip()
        
        # Arquitetura
        print("\n🏗️ 3. ARQUITETURA")
        current_arch = input("Arquitetura atual (ex: Monolítica, SOA): ").strip()
        target_arch = input("Arquitetura alvo (ex: Microserviços, Monolito Modular): ").strip()
        
        # Preferências específicas
        print("\n⚙️ 4. PREFERÊNCIAS ESPECÍFICAS")
        preferences = {}
        preferences['deployment'] = input("Preferência de deploy (ex: Docker, Kubernetes, VM): ").strip()
        preferences['cloud'] = input("Provedor de nuvem (ex: AWS, Azure, GCP, On-premise): ").strip()
        preferences['testing'] = input("Estratégia de testes (ex: TDD, BDD, E2E): ").strip()
        preferences['ci_cd'] = input("Pipeline CI/CD (ex: Jenkins, GitLab, GitHub Actions): ").strip()
        preferences['monitoring'] = input("Monitoramento (ex: Prometheus, Datadog, ELK): ").strip()
        
        # Restrições
        print("\n⚠️ 5. RESTRIÇÕES E LIMITAÇÕES")
        constraints_input = input("Restrições importantes (separadas por vírgula): ").strip()
        constraints = [c.strip() for c in constraints_input.split(',') if c.strip()]
        
        # Prioridades
        print("\n📊 6. PRIORIDADES")
        print("Prioridades disponíveis: performance, security, maintainability, scalability, cost, time-to-market")
        priorities_input = input("Suas prioridades em ordem (separadas por vírgula): ").strip()
        priorities = [p.strip() for p in priorities_input.split(',') if p.strip()]
        
        # Timeline e recursos
        print("\n⏱️ 7. TIMELINE E RECURSOS")
        timeline = input("Timeline desejado (ex: 6 meses, 1 ano): ").strip()
        team_size = int(input("Tamanho da equipe: ") or "3")
        team_skills_input = input("Habilidades da equipe (separadas por vírgula): ").strip()
        team_skills = [s.strip() for s in team_skills_input.split(',') if s.strip()]
        
        # Requisitos de negócio
        print("\n💼 8. REQUISITOS DE NEGÓCIO")
        business_input = input("Requisitos específicos de negócio (separados por vírgula): ").strip()
        business_requirements = [b.strip() for b in business_input.split(',') if b.strip()]
        
        # Observações especiais
        print("\n📝 9. OBSERVAÇÕES ESPECIAIS")
        special_notes = input("Observações ou considerações especiais: ").strip()
        
        # Cria objeto de requisitos
        requirements = MigrationRequirements(
            current_technology_stack=current_stack,
            target_technology_stack=target_stack,
            current_architecture=current_arch,
            target_architecture=target_arch,
            preferences=preferences,
            constraints=constraints,
            priorities=priorities,
            timeline=timeline,
            team_size=team_size,
            team_skills=team_skills,
            business_requirements=business_requirements,
            special_notes=special_notes
        )
        
        self.requirements = requirements
        self.save_requirements()
        
        print("\n✅ Configuração salva com sucesso!")
        return requirements
    
    def load_requirements_from_file(self, file_path: str) -> MigrationRequirements:
        """Carrega requisitos de um arquivo JSON/YAML"""
        file_path_obj = Path(file_path)
        
        if file_path_obj.suffix.lower() in ['.yaml', '.yml']:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Se existe chave 'migration_config', usa ela
        if 'migration_config' in data:
            config_data = data['migration_config']
        else:
            config_data = data
        
        # Converte a estrutura do arquivo para a estrutura esperada
        requirements_data = self._convert_config_to_requirements(config_data)
        
        requirements = MigrationRequirements(**requirements_data)
        self.requirements = requirements
        self.save_requirements()
        
        return requirements
    
    def _convert_config_to_requirements(self, config_data: Dict) -> Dict:
        """Converte dados do arquivo de configuração para formato MigrationRequirements"""
        
        # Extrai tecnologias atuais
        current_stack = config_data.get('current_stack', {})
        current_tech_stack = {
            'language': current_stack.get('language', ''),
            'framework': current_stack.get('framework', ''),
            'database': current_stack.get('database', {}).get('type', '') if isinstance(current_stack.get('database'), dict) else current_stack.get('database', ''),
            'server': current_stack.get('server', ''),
            'other': current_stack.get('build_tool', '')
        }
        
        # Extrai tecnologias alvo
        target_stack = config_data.get('target_stack', {})
        target_tech_stack = {
            'language': target_stack.get('language', ''),
            'framework': target_stack.get('framework', ''),
            'database': target_stack.get('database', {}).get('type', '') if isinstance(target_stack.get('database'), dict) else target_stack.get('database', ''),
            'server': target_stack.get('server', ''),
            'api_style': config_data.get('target_architecture', {}).get('api_style', ''),
            'other': target_stack.get('build_tool', '')
        }
        
        # Extrai arquitetura
        target_arch = config_data.get('target_architecture', {})
        current_architecture = "Legado"  # Valor padrão
        target_architecture = target_arch.get('type', 'modernized')
        
        # Extrai preferências
        infra = config_data.get('infrastructure', {})
        migration_prefs = config_data.get('migration_preferences', {})
        preferences = {
            'deployment': infra.get('deployment', ''),
            'cloud': infra.get('cloud_provider', ''),
            'testing': migration_prefs.get('testing_approach', ''),
            'ci_cd': 'GitHub Actions',  # Valor padrão
            'monitoring': 'Basic'  # Valor padrão
        }
        
        # Extrai restrições
        constraints_data = config_data.get('constraints', {})
        constraints = []
        if constraints_data.get('max_downtime'):
            constraints.append(f"Downtime máximo: {constraints_data['max_downtime']}")
        if constraints_data.get('budget_limit'):
            constraints.append(f"Orçamento: {constraints_data['budget_limit']}")
        if constraints_data.get('timeline'):
            constraints.append(f"Timeline: {constraints_data['timeline']}")
        if constraints_data.get('compliance_requirements'):
            constraints.extend([f"Compliance: {req}" for req in constraints_data['compliance_requirements']])
        
        # Extrai prioridades
        priorities = config_data.get('business_priorities', [])
        
        # Extrai timeline e equipe
        timeline = constraints_data.get('timeline', '6 meses')
        team_size = constraints_data.get('team_size', 3)
        
        # Skills padrão baseados na tecnologia alvo
        team_skills = [target_tech_stack['language'], target_tech_stack['framework']]
        team_skills = [skill for skill in team_skills if skill]  # Remove vazios
        
        # Requisitos de negócio
        business_requirements = []
        if config_data.get('migration_objective'):
            business_requirements.append(config_data['migration_objective'])
        
        # Componentes críticos como notas especiais
        critical_components = config_data.get('critical_components', [])
        special_notes = config_data.get('migration_objective', '')
        if critical_components:
            special_notes += f"\n\nComponentes Críticos:\n"
            for comp in critical_components:
                if isinstance(comp, dict):
                    special_notes += f"- {comp.get('name', 'N/A')}: {comp.get('description', comp.get('notes', ''))}\n"
                else:
                    special_notes += f"- {comp}\n"
        
        return {
            'current_technology_stack': current_tech_stack,
            'target_technology_stack': target_tech_stack,
            'current_architecture': current_architecture,
            'target_architecture': target_architecture,
            'preferences': preferences,
            'constraints': constraints,
            'priorities': priorities,
            'timeline': timeline,
            'team_size': team_size,
            'team_skills': team_skills,
            'business_requirements': business_requirements,
            'special_notes': special_notes
        }
    
    def save_requirements(self):
        """Salva requisitos no arquivo"""
        if self.requirements:
            with open(self.requirements_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.requirements), f, indent=4, ensure_ascii=False)
    
    def load_requirements(self) -> Optional[MigrationRequirements]:
        """Carrega requisitos salvos"""
        if self.requirements_file.exists():
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.requirements = MigrationRequirements(**data)
            return self.requirements
        return None
    
    def generate_migration_context(self) -> str:
        """Gera contexto formatado para uso nos prompts"""
        if not self.requirements:
            return ""
        
        context = f"""
## 🎯 CONFIGURAÇÃO DE MIGRAÇÃO (FASE 0)

### TECNOLOGIAS ATUAIS
- **Linguagem:** {self.requirements.current_technology_stack.get('language', 'N/A')}
- **Framework:** {self.requirements.current_technology_stack.get('framework', 'N/A')}
- **Banco de Dados:** {self.requirements.current_technology_stack.get('database', 'N/A')}
- **Servidor:** {self.requirements.current_technology_stack.get('server', 'N/A')}
- **Outras:** {self.requirements.current_technology_stack.get('other', 'N/A')}

### TECNOLOGIAS ALVO
- **Linguagem:** {self.requirements.target_technology_stack.get('language', 'N/A')}
- **Framework:** {self.requirements.target_technology_stack.get('framework', 'N/A')}
- **Banco de Dados:** {self.requirements.target_technology_stack.get('database', 'N/A')}
- **Servidor:** {self.requirements.target_technology_stack.get('server', 'N/A')}
- **Estilo de API:** {self.requirements.target_technology_stack.get('api_style', 'N/A')}
- **Outras:** {self.requirements.target_technology_stack.get('other', 'N/A')}

### ARQUITETURA
- **Atual:** {self.requirements.current_architecture}
- **Alvo:** {self.requirements.target_architecture}

### PREFERÊNCIAS
- **Deploy:** {self.requirements.preferences.get('deployment', 'N/A')}
- **Cloud:** {self.requirements.preferences.get('cloud', 'N/A')}
- **Testes:** {self.requirements.preferences.get('testing', 'N/A')}
- **CI/CD:** {self.requirements.preferences.get('ci_cd', 'N/A')}
- **Monitoramento:** {self.requirements.preferences.get('monitoring', 'N/A')}

### PRIORIDADES
{chr(10).join(f"- {priority}" for priority in self.requirements.priorities)}

### RESTRIÇÕES
{chr(10).join(f"- {constraint}" for constraint in self.requirements.constraints)}

### RECURSOS
- **Timeline:** {self.requirements.timeline}
- **Equipe:** {self.requirements.team_size} pessoas
- **Habilidades:** {', '.join(self.requirements.team_skills)}

### REQUISITOS DE NEGÓCIO
{chr(10).join(f"- {req}" for req in self.requirements.business_requirements)}

### OBSERVAÇÕES ESPECIAIS
{self.requirements.special_notes}

---
**IMPORTANTE:** Todas as recomendações e implementações devem seguir rigorosamente essas especificações do usuário.
"""
        return context
    
    def update_project_structure_config(self, project_manager):
        """Atualiza configuração da estrutura do projeto baseada nos requisitos"""
        if not self.requirements:
            return
        
        # Atualiza stack tecnológico
        target_stack = self.requirements.target_technology_stack
        
        # Detecta tipo de projeto baseado nas especificações
        if 'java' in target_stack.get('language', '').lower():
            project_manager.structure_config['technology_stack']['backend'] = 'java_spring'
            if 'spring boot' in target_stack.get('framework', '').lower():
                project_manager.structure_config['technology_stack']['backend'] = 'java_spring_boot'
        elif 'python' in target_stack.get('language', '').lower():
            project_manager.structure_config['technology_stack']['backend'] = 'python_fastapi'
        elif 'node' in target_stack.get('language', '').lower():
            project_manager.structure_config['technology_stack']['backend'] = 'nodejs'
        
        # Configura arquitetura
        project_manager.structure_config['architecture_type'] = self.requirements.target_architecture.lower()
        
        # Configura estilo de API
        api_style = target_stack.get('api_style', '').lower()
        if 'soap' in api_style:
            project_manager.structure_config['api_style'] = 'soap'
            self._add_soap_structure(project_manager)
        elif 'graphql' in api_style:
            project_manager.structure_config['api_style'] = 'graphql'
        else:
            project_manager.structure_config['api_style'] = 'rest'
        
        # Adiciona configurações específicas baseadas nas preferências
        if 'docker' in self.requirements.preferences.get('deployment', '').lower():
            self._add_docker_structure(project_manager)
        
        if 'kubernetes' in self.requirements.preferences.get('deployment', '').lower():
            self._add_kubernetes_structure(project_manager)
        
        project_manager._save_structure_config()
    
    def _add_soap_structure(self, project_manager):
        """Adiciona estrutura específica para SOAP"""
        soap_dirs = {
            "soap": {
                "path": "backend/src/main/java/com/company/app/soap",
                "subdirs": {
                    "endpoint": "SOAP endpoints",
                    "model": "SOAP models/schemas",
                    "config": "SOAP configuration",
                    "wsdl": "WSDL files"
                }
            }
        }
        project_manager.structure_config["directory_structure"].update(soap_dirs)
    
    def _add_docker_structure(self, project_manager):
        """Adiciona estrutura Docker mais detalhada"""
        docker_dirs = {
            "docker-compose.yml": "Docker Compose configuration",
            "Dockerfile": "Main application Dockerfile",
            "docker/": "Docker configurations"
        }
        
        if "infrastructure" in project_manager.structure_config["directory_structure"]:
            project_manager.structure_config["directory_structure"]["infrastructure"]["subdirs"].update({
                "docker/development": "Development Docker configs",
                "docker/production": "Production Docker configs",
                "docker/scripts": "Docker utility scripts"
            })
    
    def _add_kubernetes_structure(self, project_manager):
        """Adiciona estrutura Kubernetes detalhada"""
        k8s_dirs = {
            "manifests": "Kubernetes manifests",
            "helm": "Helm charts",
            "ingress": "Ingress configurations",
            "secrets": "Secret templates"
        }
        
        if "infrastructure" in project_manager.structure_config["directory_structure"]:
            project_manager.structure_config["directory_structure"]["infrastructure"]["subdirs"]["kubernetes"].update(k8s_dirs)
    
    def generate_summary_report(self) -> str:
        """Gera relatório resumido da configuração"""
        if not self.requirements:
            return "Nenhuma configuração definida."
        
        return f"""# Resumo da Configuração de Migração

## Migração Definida
**De:** {self.requirements.current_technology_stack.get('language', 'N/A')} + {self.requirements.current_technology_stack.get('framework', 'N/A')}
**Para:** {self.requirements.target_technology_stack.get('language', 'N/A')} + {self.requirements.target_technology_stack.get('framework', 'N/A')}

## Arquitetura
**De:** {self.requirements.current_architecture}
**Para:** {self.requirements.target_architecture}

## Principais Prioridades
{', '.join(self.requirements.priorities[:3])}

## Timeline
{self.requirements.timeline}

## Configuração Salva
- ✅ Requisitos do usuário salvos
- ✅ Contexto global configurado  
- ✅ Estrutura de projeto personalizada
"""
