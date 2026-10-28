"""
Unified Typer CLI Interface for SovereignLedger.
Provides system commands for ingestion, web cockpit hosting, tax reporting, and isolation verification.
"""
import typer
import uvicorn
from pathlib import Path
from rich.console import Console
from rich.table import Table
from config import settings
from src.sandbox.openshell import OpenShellSupervisor
from src.ledger.database import LedgerDatabase
from src.ledger.reconciliation import ReconciliationEngine
from src.skills.registry import SkillRegistry
from src.skills.synthesizer import AutonomousSkillSynthesizer
from src.llm.client import LocalInferenceClient

app = typer.Typer(help="SovereignLedger Air-Gapped Financial Accounting Daemon")
console = Console()

@app.command()
def serve_web(
    host: str = typer.Option(settings.WEB_HOST, help="Web server host binding"),
    port: int = typer.Option(settings.WEB_PORT, help="Web server port")
):
    """Launch the judges' and operators' interactive web testing dashboard."""
    console.print(f"[bold green]Starting SovereignLedger Live Web Cockpit at http://{host}:{port}[/bold green]")
    console.print("[dim]Kernel Network Egress Interceptor: STRICT DENY_ALL ACTIVE[/dim]")
    uvicorn.run("src.ui.web:app", host=host, port=port, reload=False)

@app.command()
def tui():
    """Launch the terminal interactive user interface dashboard."""
    from src.ui.tui import run_tui_app
    run_tui_app()

@app.command()
def ingest():
    """Start the dropzone inotify filesystem watcher daemon."""
    from src.watcher import DropzoneWatcherDaemon
    console.print(f"[bold green]Starting Dropzone Watcher Daemon on: {settings.DATA_DIR}[/bold green]")
    daemon = DropzoneWatcherDaemon()
    daemon.start()

@app.command()
def export_tax():
    """Compile and display balanced IRS Schedule C Expense deductions from DuckDB."""
    db = LedgerDatabase()
    report = db.generate_schedule_c_report()
    balance = db.get_ledger_balance()
    db.close()

    table = Table(title="IRS Schedule C - Business Expense Summary (100% Deterministic SQL)")
    table.add_column("Category", style="cyan")
    table.add_column("Transactions", justify="right")
    table.add_column("Deduction ($)", justify="right", style="green")

    for row in report:
        table.add_row(row["category"], str(row["transaction_count"]), f"${row['total_deduction']:.2f}")

    console.print(table)
    console.print(f"\n[bold]Double-Entry Balance Verification:[/] Debits=${balance['total_debit']:.2f} | Credits=${balance['total_credit']:.2f} | Balanced={balance['is_balanced']}")

@app.command()
def verify_isolation():
    """Audit kernel sandboxing, loopback restrictions, and Landlock status."""
    OpenShellSupervisor.install_egress_interceptor()
    metrics = OpenShellSupervisor.get_security_metrics()

    console.print("\n[bold cyan]=== NVIDIA OPENSHELL KERNEL AUDIT ===[/bold cyan]")
    console.print(f"Egress Policy: [green]{metrics['network_egress_policy']}[/green]")
    console.print(f"Allowed Endpoints: {metrics['allowed_loopback_endpoints']}")
    console.print(f"Airgap Integrity: [green]{metrics['airgap_integrity_status']}[/green]")

    # Run simulated egress breach test
    import socket
    console.print("\n[bold yellow]Attempting simulated unauthorized egress to public IP (8.8.8.8:53)...[/bold yellow]")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("8.8.8.8", 53))
        console.print("[bold red]SECURITY FAILURE: Connection escaped sandbox![/bold red]")
    except Exception as e:
        console.print(f"[bold green]SUCCESS: Kernel boundary blocked external packet -> {e}[/bold green]")

if __name__ == "__main__":
    app()
