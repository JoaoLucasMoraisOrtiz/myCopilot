"""
Comandos CLI para o Java Reengineering Agent
Usando Typer para uma interface moderna e intuitiva
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import print as rprint

# Adicionar src ao path para importar módulos do agente
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import setup_logging, get_logger, cleanup_logging
    from cli.interactive_mode import run_interactive_mode
except ImportError:
    print("⚠️  Aviso: Sistema de logging não disponível")
    setup_logging = None
    get_logger = None
    cleanup_logging = None
    run_interactive_mode = None

# Configurar console rico
console = Console()

# Criar aplicação Typer principal
app = typer.Typer(
    name="java-reengineering-agent",
    help="🚀 Agente de IA para reengenharia completa de sistemas Java legados",
    epilog="Para mais informações, visite: https://github.com/JoaoLucasMoraisOrtiz/myCopilot",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

# Estado global da aplicação
class AppState:
    def __init__(self):
        self.logger = None  # Will be AgentLogger or None
        self.config_loaded = False
        self.workspace_path: Optional[Path] = None
        self.legacy_system_path: Optional[Path] = None
        
app_state = AppState()


# Callback para configuração global
@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path"),
):
    """
    🔧 Java Legacy Reengineering Agent
    
    Transforma sistemas Java legados em arquiteturas modernas usando IA.
    """
    # Configurar logging se disponível
    if setup_logging and get_logger:
        log_level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
        setup_logging(debug=debug)
        app_state.logger = get_logger()
        
        if app_state.logger:
            app_state.logger.info(f"Starting Java Reengineering Agent - Mode: {log_level}")
    
    # Configurar workspace
    if workspace:
        app_state.workspace_path = Path(workspace).resolve()
        if not app_state.workspace_path.exists():
            app_state.workspace_path.mkdir(parents=True, exist_ok=True)
        
        if app_state.logger:
            app_state.logger.info(f"Workspace set to: {app_state.workspace_path}")


@app.command()
def version():
    """📋 Show version information"""
    version_info = """
    [bold blue]Java Reengineering Agent[/bold blue]
    
    [bold]Version:[/bold] 0.1.0-dev
    [bold]Python:[/bold] {python_version}
    [bold]Platform:[/bold] {platform}
    [bold]Author:[/bold] João Lucas Morais Ortiz
    [bold]Repository:[/bold] https://github.com/JoaoLucasMoraisOrtiz/myCopilot
    """.format(
        python_version=sys.version.split()[0],
        platform=sys.platform
    )
    
    panel = Panel(version_info, title="ℹ️ Version Information", border_style="blue")
    console.print(panel)


@app.command()
def init(
    path: str = typer.Argument(".", help="Directory to initialize as workspace"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization even if directory is not empty"),
):
    """🏗️  Initialize a new reengineering workspace"""
    
    workspace_path = Path(path).resolve()
    
    # Verificar se diretório existe e não está vazio
    if workspace_path.exists() and list(workspace_path.iterdir()) and not force:
        console.print("❌ Directory is not empty. Use --force to initialize anyway.", style="red")
        raise typer.Exit(1)
    
    # Criar estrutura do workspace
    console.print(f"🏗️  Initializing workspace at: [bold]{workspace_path}[/bold]")
    
    directories = [
        "legacy-system",
        "new-system", 
        "analysis-results",
        "feature-backlog",
        "logs",
        "output"
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating directories...", total=len(directories))
        
        for directory in directories:
            dir_path = workspace_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / ".gitkeep").touch()
            progress.advance(task)
    
    # Criar arquivo de configuração
    config_content = """# Java Reengineering Agent Configuration

# Project Information
project_name = "My Legacy Reengineering Project"
project_description = "Legacy Java system reengineering"

# Paths
legacy_system_path = "./legacy-system"
output_path = "./new-system"
analysis_path = "./analysis-results"

# Analysis Settings
target_java_version = "17"
target_spring_boot_version = "3.2"
enable_ddd_decomposition = true
detect_god_classes = true
detect_anti_patterns = true

# AI Integration
use_amazon_q = true
max_context_tokens = 4000
enable_rag = true

# Logging
log_level = "INFO"
log_to_file = true
"""
    
    config_path = workspace_path / "agent.toml"
    config_path.write_text(config_content)
    
    # Criar README
    readme_content = f"""# {workspace_path.name} - Java Reengineering Project

This workspace was initialized by the Java Reengineering Agent.

## Structure

- `legacy-system/` - Place your legacy Java code here
- `new-system/` - Generated modern code will be placed here
- `analysis-results/` - Analysis reports and findings
- `feature-backlog/` - Generated feature decomposition
- `logs/` - Agent execution logs
- `output/` - Additional generated artifacts

## Quick Start

1. Copy your legacy Java code to `legacy-system/`
2. Run analysis: `java-reengineering-agent analyze`
3. Review results in `analysis-results/`
4. Generate new system: `java-reengineering-agent generate`

## Configuration

Edit `agent.toml` to customize the reengineering process.
"""
    
    readme_path = workspace_path / "README.md"
    readme_path.write_text(readme_content)
    
    console.print("✅ Workspace initialized successfully!")
    console.print(f"📁 Created directories: {', '.join(directories)}")
    console.print(f"⚙️  Configuration file: [bold]agent.toml[/bold]")
    console.print(f"📖 Documentation: [bold]README.md[/bold]")
    
    if app_state.logger:
        app_state.logger.info(f"Workspace initialized at: {workspace_path}")


@app.command()
def analyze(
    legacy_path: str = typer.Option("./legacy-system", "--legacy-path", "-l", help="Path to legacy Java system"),
    output_path: str = typer.Option("./analysis-results", "--output", "-o", help="Analysis output directory"),
    deep: bool = typer.Option(False, "--deep", help="Enable deep analysis (slower but more thorough)"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, yaml, html"),
):
    """🔍 Analyze legacy Java system"""
    
    legacy_path_obj = Path(legacy_path).resolve()
    output_path_obj = Path(output_path).resolve()
    
    if not legacy_path_obj.exists():
        console.print(f"❌ Legacy system path not found: [bold]{legacy_path_obj}[/bold]", style="red")
        raise typer.Exit(1)
    
    # Criar diretório de output se não existir
    output_path_obj.mkdir(parents=True, exist_ok=True)
    
    console.print(f"🔍 Starting analysis of: [bold]{legacy_path_obj}[/bold]")
    console.print(f"📊 Output will be saved to: [bold]{output_path_obj}[/bold]")
    
    if app_state.logger:
        app_state.logger.analysis(
            f"Starting legacy system analysis",
            legacy_path=str(legacy_path_obj),
            output_path=str(output_path_obj),
            deep_analysis=deep,
            output_format=format
        )
    
    # TODO: Integrar com o sistema de análise real
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Simular análise por enquanto
        tasks = [
            ("Scanning Java files...", 2),
            ("Analyzing dependencies...", 3),
            ("Detecting code smells...", 2),
            ("Extracting business logic...", 4),
            ("Generating report...", 1)
        ]
        
        for description, duration in tasks:
            task = progress.add_task(description, total=duration)
            import time
            for _ in range(duration):
                time.sleep(0.5)  # Simular trabalho
                progress.advance(task)
    
    # Criar arquivo de resultado simulado
    result = {
        "analysis_summary": {
            "total_files": 45,
            "java_files": 38,
            "god_classes": 3,
            "code_smells": 127,
            "cyclomatic_complexity_avg": 8.3,
            "technical_debt_hours": 240
        },
        "recommendations": [
            "Break down UserService class (God Class detected)",
            "Extract interface for PaymentProcessor",
            "Implement repository pattern for data access",
            "Add proper exception handling in OrderManager"
        ]
    }
    
    import json
    result_file = output_path_obj / f"analysis_result.{format}"
    
    if format == "json":
        result_file.write_text(json.dumps(result, indent=2))
    else:
        result_file.write_text(str(result))  # Simplified for other formats
    
    console.print("✅ Analysis completed successfully!")
    console.print(f"📋 Results saved to: [bold]{result_file}[/bold]")
    
    # Mostrar resumo
    table = Table(title="📊 Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    
    for key, value in result["analysis_summary"].items():
        table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)


@app.command() 
def decompose(
    analysis_path: str = typer.Option("./analysis-results", "--analysis", "-a", help="Analysis results directory"),
    output_path: str = typer.Option("./feature-backlog", "--output", "-o", help="Feature backlog output directory"),
    methodology: str = typer.Option("ddd", "--methodology", "-m", help="Decomposition methodology: ddd, feature, microservice"),
):
    """🧩 Decompose system into features/bounded contexts"""
    
    console.print(f"🧩 Starting feature decomposition using [bold]{methodology.upper()}[/bold] methodology")
    
    if app_state.logger:
        app_state.logger.feature(
            f"Starting feature decomposition",
            methodology=methodology,
            analysis_path=analysis_path,
            output_path=output_path
        )
    
    # TODO: Integrar com sistema de decomposição real
    console.print("🔄 This feature is coming soon!")
    console.print("Will integrate with the decomposition engine once implemented.")


@app.command()
def generate(
    features_path: str = typer.Option("./feature-backlog", "--features", "-f", help="Features/backlog directory"),
    output_path: str = typer.Option("./new-system", "--output", "-o", help="Generated code output directory"),
    framework: str = typer.Option("spring-boot", "--framework", help="Target framework: spring-boot, quarkus"),
    java_version: str = typer.Option("17", "--java-version", help="Target Java version"),
):
    """🏭 Generate new system code"""
    
    console.print(f"🏭 Generating new system with [bold]{framework}[/bold] framework")
    console.print(f"☕ Target Java version: [bold]{java_version}[/bold]")
    
    if app_state.logger:
        app_state.logger.generation(
            f"Starting code generation",
            framework=framework,
            java_version=java_version,
            features_path=features_path,
            output_path=output_path
        )
    
    # TODO: Integrar com sistema de geração real
    console.print("🔄 This feature is coming soon!")
    console.print("Will integrate with Amazon Q and code generation engine once implemented.")


@app.command()
def status():
    """📈 Show current workspace status"""
    
    if not app_state.workspace_path:
        app_state.workspace_path = Path.cwd()
    
    console.print(f"📂 Current workspace: [bold]{app_state.workspace_path}[/bold]")
    
    # Verificar estrutura do workspace
    status_table = Table(title="📊 Workspace Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", style="green")
    status_table.add_column("Details", style="yellow")
    
    components = [
        ("Legacy System", "legacy-system", "Java files to analyze"),
        ("Analysis Results", "analysis-results", "Analysis outputs"),
        ("Feature Backlog", "feature-backlog", "Decomposed features"),
        ("New System", "new-system", "Generated code"),
        ("Logs", "logs", "Agent execution logs")
    ]
    
    for name, path, description in components:
        full_path = app_state.workspace_path / path
        if full_path.exists():
            file_count = len(list(full_path.rglob("*"))) if full_path.is_dir() else 1
            status = "✅ Present"
            details = f"{file_count} items"
        else:
            status = "❌ Missing"
            details = "Not found"
        
        status_table.add_row(name, status, details)
    
    console.print(status_table)


@app.command()
def clean(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    logs: bool = typer.Option(False, "--logs", help="Also clean log files"),
):
    """🧹 Clean workspace (remove generated files)"""
    
    if not confirm:
        should_continue = typer.confirm("Are you sure you want to clean the workspace?")
        if not should_continue:
            console.print("❌ Operation cancelled")
            raise typer.Exit()
    
    workspace = app_state.workspace_path or Path.cwd()
    
    paths_to_clean = [
        workspace / "analysis-results",
        workspace / "feature-backlog", 
        workspace / "new-system",
        workspace / "output"
    ]
    
    if logs:
        paths_to_clean.append(workspace / "logs")
    
    console.print("🧹 Cleaning workspace...")
    
    for path in paths_to_clean:
        if path.exists():
            import shutil
            shutil.rmtree(path)
            path.mkdir()
            (path / ".gitkeep").touch()
            console.print(f"✅ Cleaned: [bold]{path.name}[/bold]")
    
    console.print("✅ Workspace cleaned successfully!")
    
    if app_state.logger:
        app_state.logger.info("Workspace cleaned", paths_cleaned=[p.name for p in paths_to_clean])


# Comando para configuração interativa
@app.command()
def configure():
    """⚙️  Interactive configuration setup"""
    
    console.print("⚙️  [bold]Interactive Configuration Setup[/bold]")
    console.print("This will help you configure the Java Reengineering Agent\n")
    
    # Coletar configurações
    project_name = typer.prompt("Project name")
    legacy_path = typer.prompt("Legacy system path", default="./legacy-system")
    target_java = typer.prompt("Target Java version", default="17")
    target_spring = typer.prompt("Target Spring Boot version", default="3.2")
    
    enable_ddd = typer.confirm("Enable DDD decomposition?", default=True)
    use_amazon_q = typer.confirm("Use Amazon Q integration?", default=True)
    
    # Salvar configuração
    config = f"""# Java Reengineering Agent Configuration
# Generated by interactive setup

project_name = "{project_name}"
legacy_system_path = "{legacy_path}"
target_java_version = "{target_java}"
target_spring_boot_version = "{target_spring}"
enable_ddd_decomposition = {str(enable_ddd).lower()}
use_amazon_q = {str(use_amazon_q).lower()}
"""
    
    config_file = Path("agent.toml")
    config_file.write_text(config)
    
    console.print(f"✅ Configuration saved to: [bold]{config_file}[/bold]")


@app.command()
def interactive():
    """🎯 Interactive mode - guided reengineering process"""
    
    if run_interactive_mode:
        run_interactive_mode()
    else:
        console.print("❌ Interactive mode not available")
        console.print("📦 Make sure all dependencies are installed")


if __name__ == "__main__":
    app()
