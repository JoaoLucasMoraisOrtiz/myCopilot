import json
import os
import time
import uuid
import sys
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP

from codingos.runtime.models import (
    SystemMode, 
    Requirement, 
    Specification, 
    ImplementationPlan,
    RequirementCategory
)

# --- Dynamic Prompts (Tuned & English) ---

PROMPT_ANALYST = """
# ROLE: SENIOR SYSTEMS ANALYST (Requirements Gathering)

## OBJECTIVE
Your goal is to extract a comprehensive **Requirements Specification** from the user. 
You must **NOT** write code or propose technical implementation details yet. Focus strictly on the "WHAT" and "WHY".

## OPERATIONAL GUIDELINES
1.  **Be Socratic & Critical:** Do not accept vague requests like "build a blog". Ask about auth, database preferences, admin panels, SEO requirements, etc.
2.  **Structured Thinking:** Classify information into Business Rules, User Stories, or Technical Constraints.
3.  **Iterative Discovery:** Use `get_specification` to see what you have gathered. If gaps exist, ask the user.
4.  **Final Gate:** Only call `request_architecture_approval` when you have a crystal-clear picture of the software.

## TOOLS
- `add_requirement(category, description, priority)`: Call this IMMEDIATELY when the user confirms a detail. Don't wait.
- `update_project_overview(name, overview)`: Keep the high-level summary up to date.
- `get_specification()`: Review your current knowledge base.
- `request_architecture_approval()`: Call this ONLY when the spec is complete and approved by the user.

## INTERACTION STYLE
User: "I want a login."
You (Internal Thought): "Too vague. Need scope."
You (Response): "Sure. Should this be email/password, social login (Google/GitHub), or Magic Links? Do we need password recovery flows?"
"""

PROMPT_ARCHITECT = """
# ROLE: CHIEF SOFTWARE ARCHITECT (Planning Phase)

## OBJECTIVE
The requirements are locked. Your goal is to translate the **Specification** into a concrete **Implementation Plan**.
You must define the "HOW".

## OPERATIONAL GUIDELINES
1.  **Analyze the Spec:** Read the requirements using `get_specification`.
2.  **Granular Tasking:** Break down features into ATOMIC technical tasks.
    *   BAD: "Implement Authentication" (Too big)
    *   GOOD: ["Install auth libraries", "Create User model", "Implement login route", "Create login UI component"]
3.  **Quality Assurance (QA) Integration:**
    *   **CRITICAL:** You MUST include verification steps.
    *   For every logical block of code (e.g., a new API endpoint), add a subsequent task: "Create and run unit tests for [feature]".
    *   The Builder is obedient but needs to be TOLD to test.
4.  **File-Centric:** Every task should ideally target specific files or modules.
5.  **Logical Order:** Dependencies first (e.g., Database setup before API routes).

## TOOLS
- `create_implementation_plan(phases, tasks)`: Submit the definitive list of steps the Builder will execute.
    *   `tasks` must be a list of objects: `{"description": "...", "file_context": "src/auth.py"}`.
- `start_building()`: Call this AFTER the user confirms the plan is perfect.

## INTERACTION STYLE
You: "Based on the requirements, here is the technical roadmap. I've divided it into 3 phases: Setup, API, and Frontend. Shall I proceed?"
"""

PROMPT_BUILDER = """
# ROLE: SENIOR SOFTWARE ENGINEER (Execution Phase)

## OBJECTIVE
You are a pure execution engine. The thinking has been done. The plan is set.
Your goal is to clear the Task Queue by executing strictly what is requested.

## OPERATIONAL GUIDELINES
1.  **Obedience:** Do not question the plan. Do not ask the user for "ideas".
2.  **Context Aware:** Use `get_next_task` to know exactly what to do.
3.  **Autonomy:**
    *   If a file is missing, create it.
    *   If a library is missing, install it (check `package.json`/`requirements.txt` first).
    *   If a bug appears, fix it within the scope of the current task.
4.  **Definition of Done:** A task is done when the code is written AND verified (if possible).

## TOOLS
- `get_next_task()`: Your primary trigger. CALL THIS AT THE START OF EVERY TURN.
- `report_task_completion(summary)`: Call this when the task is done.
- `read_file` / `write_file` / `run_shell_command`: Your hands.

## INTERACTION LOOP
1. `get_next_task()` -> Returns: "Create src/app.py with Flask setup"
2. Action: `write_file("src/app.py", ...)`
3. Action: `report_task_completion("Created app.py with basic Flask scaffold")`
4. Repeat.
"""

class SupervisorBrain:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.state_path = os.path.join(self.repo_root, ".gemini", "project_state.json")
        self.gemini_md_path = os.path.join(self.repo_root, "GEMINI.md")
        
        # State
        self.mode = SystemMode.ANALYST
        self.spec = Specification(project_name="Project", overview="")
        self.plan: Optional[ImplementationPlan] = None
        
        self._load_state()

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        data = {
            "mode": self.mode.value,
            "spec": self.spec.to_dict(),
            "plan": {
                "phases": self.plan.phases,
                "tasks": self.plan.tasks,
                "current_task_index": self.plan.current_task_index
            } if self.plan else None
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_state(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.mode = SystemMode(data.get("mode", "analyst"))
            
            s_data = data.get("spec", {})
            self.spec = Specification(
                project_name=s_data.get("project_name", "Project"),
                overview=s_data.get("overview", "")
            )
            for r in s_data.get("requirements", []):
                self.spec.requirements.append(Requirement(**r))
            
            p_data = data.get("plan")
            if p_data:
                self.plan = ImplementationPlan(
                    phases=p_data.get("phases", []),
                    tasks=p_data.get("tasks", []),
                    current_task_index=p_data.get("current_task_index", 0)
                )
        except Exception as e:
            print(f"Error loading state: {e}")

    def _update_gemini_prompt(self, prompt_content: str):
        """Atualiza o GEMINI.md para trocar a persona do modelo."""
        with open(self.gemini_md_path, "w", encoding="utf-8") as f:
            f.write(prompt_content)

    # --- Analyst Tools ---

    def add_requirement(self, category: str, description: str, priority: str = "medium") -> str:
        if self.mode != SystemMode.ANALYST:
            return f"ERROR: Current mode is {self.mode.value}. Cannot add requirements now."
        
        req_id = str(uuid.uuid4())[:8]
        req = Requirement(id=req_id, category=category, description=description, priority=priority)
        self.spec.requirements.append(req)
        self._save_state()
        return f"Requirement Added [{category.upper()}]: {description} (ID: {req_id})"

    def update_project_overview(self, name: str, overview: str) -> str:
        self.spec.project_name = name
        self.spec.overview = overview
        self._save_state()
        return "Project overview updated."

    def get_specification(self) -> str:
        txt = f"# Specification: {self.spec.project_name}\n\n## Overview\n{self.spec.overview}\n\n## Requirements\n"
        if not self.spec.requirements:
            txt += "(No requirements recorded yet)"
        
        for req in self.spec.requirements:
            txt += f"- [{req.id}] [{req.category.upper()}] {req.description} (Prio: {req.priority})\n"
        return txt

    def request_architecture_approval(self) -> str:
        """Transição FASE 1 -> FASE 2"""
        if not self.spec.requirements:
            return "ERROR: Specification is empty. Gather requirements first."
        
        self.mode = SystemMode.ARCHITECT
        self._save_state()
        self._update_gemini_prompt(PROMPT_ARCHITECT)
        
        return (
            "SPECIFICATION LOCKED.\n"
            "SYSTEM MODE CHANGED TO: ARCHITECT.\n"
            "SYSTEM: GEMINI.md has been updated. Please present a summary of the Spec to the user and ask for confirmation to proceed to Implementation Planning."
        )

    # --- Architect Tools ---

    def create_implementation_plan(self, phases: List[str], tasks: List[Dict[str, str]]) -> str:
        """
        Tasks format: [{"description": "Setup React", "file_context": "package.json"}]
        """
        if self.mode != SystemMode.ARCHITECT:
            return f"ERROR: Current mode is {self.mode.value}."
        
        clean_tasks = []
        for t in tasks:
            clean_tasks.append({
                "id": str(uuid.uuid4())[:6],
                "description": t.get("description", "Task"),
                "status": "pending",
                "file_context": t.get("file_context", "")
            })
            
        self.plan = ImplementationPlan(phases=phases, tasks=clean_tasks)
        self._save_state()
        return f"Plan created with {len(clean_tasks)} tasks. Waiting for user approval to start building."

    def start_building(self) -> str:
        """Transição FASE 2 -> FASE 3"""
        if not self.plan or not self.plan.tasks:
            return "ERROR: No implementation plan defined."
        
        self.mode = SystemMode.BUILDER
        self._save_state()
        self._update_gemini_prompt(PROMPT_BUILDER)
        
        return (
            "PLAN APPROVED.\n"
            "SYSTEM MODE CHANGED TO: BUILDER.\n"
            "SYSTEM: GEMINI.md has been updated.\n"
            "FROM NOW ON: Do not ask questions. Call `get_next_task` and execute."
        )

    # --- Builder Tools ---

    def get_next_task(self) -> str:
        if self.mode != SystemMode.BUILDER:
            return f"ERROR: Current mode is {self.mode.value}."
        
        if not self.plan: return "ERROR: No plan."
        
        if self.plan.current_task_index >= len(self.plan.tasks):
            return "ALL TASKS COMPLETED. Congratulations."
        
        task = self.plan.tasks[self.plan.current_task_index]
        spec_summary = self.get_specification()
        
        return (
            f"CURRENT TASK ({self.plan.current_task_index + 1}/{len(self.plan.tasks)})\n"
            f"DESCRIPTION: {task['description']}\n"
            f"TARGET CONTEXT: {task.get('file_context', 'None')}\n\n"
            f"--- Project Context ---\n{spec_summary}"
        )

    def report_task_completion(self, summary: str) -> str:
        if self.mode != SystemMode.BUILDER: return "ERROR: Current mode is not Builder."
        
        idx = self.plan.current_task_index
        if idx < len(self.plan.tasks):
            self.plan.tasks[idx]["status"] = "done"
            self.plan.tasks[idx]["result"] = summary
            self.plan.current_task_index += 1
            self._save_state()
            return "Task marked as DONE. Call `get_next_task` to proceed."
        return "All tasks already done."


# --- Instanciação do Server ---

def create_mcp_server(repo_root: str = ".") -> FastMCP:
    brain = SupervisorBrain(repo_root)
    mcp = FastMCP("codingOS-Consultant")

    # Common Tools
    @mcp.tool()
    def get_project_status() -> str:
        return f"CURRENT MODE: {brain.mode.value.upper()}\nRequirements: {len(brain.spec.requirements)}\nTasks: {len(brain.plan.tasks) if brain.plan else 0}"

    # Analyst Tools
    @mcp.tool()
    def add_requirement(category: str, description: str, priority: str = "medium") -> str:
        return brain.add_requirement(category, description, priority)
    
    @mcp.tool()
    def update_project_overview(name: str, overview: str) -> str:
        return brain.update_project_overview(name, overview)

    @mcp.tool()
    def get_specification() -> str:
        return brain.get_specification()
    
    @mcp.tool()
    def request_architecture_approval() -> str:
        return brain.request_architecture_approval()

    # Architect Tools
    @mcp.tool()
    def create_implementation_plan(phases: List[str], tasks: List[Dict[str, str]]) -> str:
        """Define the technical plan. 'tasks' list of dicts with 'description' and optional 'file_context'."""
        return brain.create_implementation_plan(phases, tasks)

    @mcp.tool()
    def start_building() -> str:
        return brain.start_building()

    # Builder Tools
    @mcp.tool()
    def get_next_task() -> str:
        return brain.get_next_task()

    @mcp.tool()
    def report_task_completion(summary: str) -> str:
        return brain.report_task_completion(summary)

    # File System Tools (Wrappers simples para facilitar)
    @mcp.tool()
    def read_file(path: str) -> str:
        try:
            with open(os.path.abspath(path), 'r', encoding='utf-8') as f: return f.read()
        except Exception as e: return str(e)

    @mcp.tool()
    def write_file(path: str, content: str) -> str:
        try:
            p = os.path.abspath(path)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f: f.write(content)
            return "OK"
        except Exception as e: return str(e)
    
    @mcp.tool()
    def list_dir(path: str) -> List[str]:
        try: return os.listdir(os.path.abspath(path))
        except: return []

    return mcp

if __name__ == "__main__":
    # Fallback para rodar direto (ex: testes manuais)
    repo = os.getcwd()
    server = create_mcp_server(repo)
    server.run(transport="stdio")
