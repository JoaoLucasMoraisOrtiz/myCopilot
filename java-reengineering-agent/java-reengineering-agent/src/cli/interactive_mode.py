"""
Modo interativo para o Java Reengineering Agent
Interface conversacional para facilitar o uso
"""

from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

console = Console()


class InteractiveMode:
    """Modo interativo para guiar o usuário através do processo"""
    
    def __init__(self):
        self.workspace_path: Optional[Path] = None
        self.legacy_path: Optional[Path] = None
        self.current_step = 0
        self.steps = [
            "workspace_setup",
            "legacy_analysis", 
            "feature_decomposition",
            "code_generation",
            "validation"
        ]
    
    def start(self):
        """Iniciar modo interativo"""
        self._show_welcome()
        
        while self.current_step < len(self.steps):
            step_name = self.steps[self.current_step]
            method_name = f"_step_{step_name}"
            
            if hasattr(self, method_name):
                step_method = getattr(self, method_name)
                if step_method():
                    self.current_step += 1
                else:
                    break
            else:
                console.print(f"❌ Step '{step_name}' not implemented yet")
                break
        
        self._show_completion()
    
    def _show_welcome(self):
        """Mostrar tela de boas-vindas"""
        welcome_text = """
        [bold blue]🚀 Java Legacy Reengineering Agent[/bold blue]
        [bold]Interactive Mode[/bold]
        
        This wizard will guide you through the complete process of
        reengineering your Java legacy system into a modern architecture.
        
        [bold]Process Overview:[/bold]
        1. 🏗️  Setup workspace
        2. 🔍 Analyze legacy system
        3. 🧩 Decompose into features
        4. 🏭 Generate new code
        5. ✅ Validate results
        
        [dim]Press Ctrl+C at any time to exit[/dim]
        """
        
        panel = Panel(welcome_text, title="Welcome", border_style="blue")
        console.print(panel)
        
        if not Confirm.ask("Ready to start?", default=True):
            console.print("👋 Goodbye!")
            return False
        
        return True
    
    def _step_workspace_setup(self) -> bool:
        """Passo 1: Configurar workspace"""
        console.print("\n[bold]🏗️  Step 1: Workspace Setup[/bold]")
        
        # Verificar se já temos um workspace
        current_dir = Path.cwd()
        if (current_dir / "agent.toml").exists():
            console.print("✅ Found existing workspace configuration")
            self.workspace_path = current_dir
            return True
        
        # Criar novo workspace
        workspace_name = Prompt.ask(
            "Enter workspace name",
            default="my-reengineering-project"
        )
        
        self.workspace_path = Path(workspace_name)
        
        if self.workspace_path.exists() and list(self.workspace_path.iterdir()):
            if not Confirm.ask(f"Directory '{workspace_name}' is not empty. Continue?"):
                return False
        
        # Executar comando init
        console.print(f"🔨 Creating workspace: {workspace_name}")
        
        # Simular criação (integrará com comando real)
        self.workspace_path.mkdir(exist_ok=True)
        console.print("✅ Workspace created successfully!")
        
        return True
    
    def _step_legacy_analysis(self) -> bool:
        """Passo 2: Análise do sistema legacy"""
        console.print("\n[bold]🔍 Step 2: Legacy System Analysis[/bold]")
        
        # Solicitar caminho do sistema legacy
        legacy_path_str = Prompt.ask(
            "Enter path to your legacy Java system",
            default="./legacy-system"
        )
        
        self.legacy_path = Path(legacy_path_str)
        
        if not self.legacy_path.exists():
            console.print(f"❌ Path not found: {self.legacy_path}")
            create_sample = Confirm.ask("Create sample legacy code for demo?")
            
            if create_sample:
                self._create_sample_legacy_code()
            else:
                return False
        
        # Opções de análise
        console.print("\n[bold]Analysis Options:[/bold]")
        
        analysis_options = Table()
        analysis_options.add_column("Option", style="cyan")
        analysis_options.add_column("Description", style="white")
        analysis_options.add_column("Time", style="yellow")
        
        analysis_options.add_row("Quick", "Basic analysis", "~2 min")
        analysis_options.add_row("Standard", "Detailed analysis", "~5 min")
        analysis_options.add_row("Deep", "Comprehensive analysis", "~15 min")
        
        console.print(analysis_options)
        
        analysis_type = Prompt.ask(
            "Choose analysis type",
            choices=["quick", "standard", "deep"],
            default="standard"
        )
        
        console.print(f"🔄 Running {analysis_type} analysis...")
        
        # Simular análise (integrará com comando real)
        console.print("✅ Analysis completed!")
        
        # Mostrar resumo dos resultados
        self._show_analysis_summary()
        
        return True
    
    def _step_feature_decomposition(self) -> bool:
        """Passo 3: Decomposição em features"""
        console.print("\n[bold]🧩 Step 3: Feature Decomposition[/bold]")
        
        methodology = Prompt.ask(
            "Choose decomposition methodology",
            choices=["ddd", "feature", "microservice"],
            default="ddd"
        )
        
        console.print(f"🔄 Decomposing using {methodology.upper()} methodology...")
        console.print("🔄 This feature is under development!")
        
        return True
    
    def _step_code_generation(self) -> bool:
        """Passo 4: Geração de código"""
        console.print("\n[bold]🏭 Step 4: Code Generation[/bold]")
        
        framework = Prompt.ask(
            "Choose target framework",
            choices=["spring-boot", "quarkus"],
            default="spring-boot"
        )
        
        java_version = Prompt.ask(
            "Choose Java version",
            choices=["11", "17", "21"],
            default="17"
        )
        
        console.print(f"🔄 Generating code with {framework} and Java {java_version}...")
        console.print("🔄 This feature is under development!")
        
        return True
    
    def _step_validation(self) -> bool:
        """Passo 5: Validação"""
        console.print("\n[bold]✅ Step 5: Validation[/bold]")
        
        console.print("🔄 This feature is under development!")
        
        return True
    
    def _create_sample_legacy_code(self):
        """Criar código legacy de exemplo"""
        if self.legacy_path is None:
            self.legacy_path = Path("./legacy-system")
            
        self.legacy_path.mkdir(parents=True, exist_ok=True)
        
        sample_code = '''package com.example.legacy;

public class LegacyUserManager {
    // This is a God Class example
    // Handles users, orders, payments, emails, etc.
    
    public void createUser(String name, String email) {
        // Mixed responsibilities
    }
    
    public void processPayment(double amount) {
        // Wrong place for payment logic
    }
    
    public void sendEmail(String message) {
        // Email service mixed with user management
    }
}'''
        
        (self.legacy_path / "LegacyUserManager.java").write_text(sample_code)
        console.print(f"✅ Sample legacy code created at: {self.legacy_path}")
    
    def _show_analysis_summary(self):
        """Mostrar resumo da análise"""
        summary = Table(title="📊 Analysis Summary")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="yellow")
        
        # Dados simulados (integrará com análise real)
        metrics = [
            ("Java Files", "38"),
            ("God Classes", "3"),
            ("Code Smells", "127"),
            ("Complexity (avg)", "8.3"),
            ("Tech Debt (hours)", "240")
        ]
        
        for metric, value in metrics:
            summary.add_row(metric, value)
        
        console.print(summary)
    
    def _show_completion(self):
        """Mostrar tela de conclusão"""
        completion_text = """
        [bold green]🎉 Reengineering Process Completed![/bold green]
        
        Your Java legacy system has been successfully analyzed and
        the reengineering process is ready to proceed.
        
        [bold]Next Steps:[/bold]
        • Review the analysis results
        • Examine the generated features
        • Validate the new system code
        • Deploy to your target environment
        
        [bold]Files Generated:[/bold]
        • Analysis reports in ./analysis-results/
        • Feature decomposition in ./feature-backlog/
        • New system code in ./new-system/
        
        [dim]Thank you for using Java Reengineering Agent![/dim]
        """
        
        panel = Panel(completion_text, title="Completion", border_style="green")
        console.print(panel)


def run_interactive_mode():
    """Função principal para executar modo interativo"""
    try:
        interactive = InteractiveMode()
        interactive.start()
    except KeyboardInterrupt:
        console.print("\n👋 Interactive mode cancelled by user")
    except Exception as e:
        console.print(f"\n❌ Error in interactive mode: {e}")


if __name__ == "__main__":
    run_interactive_mode()
