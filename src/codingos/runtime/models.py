from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class SystemMode(Enum):
    ANALYST = "analyst"          # Fase de extração de requisitos (Socrático)
    ARCHITECT = "architect"      # Fase de transformar requisitos em plano técnico
    BUILDER = "builder"          # Fase de execução cega (Single Instance)
    COMPLETED = "completed"

class RequirementCategory(Enum):
    BUSINESS_RULE = "business_rule"    # Regras de negócio (O que o software DEVE fazer)
    USER_STORY = "user_story"          # Funcionalidades do ponto de vista do usuário
    TECHNICAL_CONSTRAINT = "constraint" # Limitações (Stack, OS, Performance)
    UI_UX = "ui_ux"                    # Design e comportamento visual
    DATA_MODEL = "data_model"          # Estruturas de dados essenciais

@dataclass
class Requirement:
    id: str
    category: str  # String based on RequirementCategory values
    description: str
    priority: str = "medium"  # high, medium, low
    status: str = "draft"     # draft, approved

@dataclass
class Specification:
    """O Documento Mestre de Requisitos."""
    project_name: str
    overview: str
    requirements: List[Requirement] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "overview": self.overview,
            "requirements": [
                {"id": r.id, "category": r.category, "description": r.description, "priority": r.priority}
                for r in self.requirements
            ]
        }

@dataclass
class ImplementationPlan:
    """O plano técnico derivado da especificação."""
    phases: List[str]
    tasks: List[Dict[str, str]]  # id, description, status, file_paths
    current_task_index: int = 0