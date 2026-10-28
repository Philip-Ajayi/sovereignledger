"""
Textual Terminal Dashboard (TUI).
Enables local operators to monitor ingest queues, ledger health,
and kernel security metrics directly within a terminal console.
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Button
from src.sandbox.openshell import OpenShellSupervisor
from src.ledger.database import LedgerDatabase

class SovereignTUI(App):
    """Textual interactive dashboard."""

    CSS = """
    Screen {
        background: #0d1117;
    }
    #sidebar {
        width: 35%;
        border-right: solid #30363d;
        padding: 1;
    }
    #main-content {
        width: 65%;
        padding: 1;
    }
    .metric-card {
        background: #161b22;
        border: solid #21262d;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Vertical(
                Static("## SovereignLedger Security Boundary", classes="metric-card"),
                Static(id="security-info", classes="metric-card"),
                Static("## Dropzone / Ingest Status", classes="metric-card"),
                Static("Drop directory: /data/incoming\nKernel Egress: DENIED", id="ingest-info", classes="metric-card"),
                Button("Run Test Reconciliation", id="btn-reconcile", variant="primary"),
                id="sidebar"
            ),
            Vertical(
                Static("## Reconciled Double-Entry Ledger"),
                DataTable(id="ledger-table"),
                id="main-content"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#ledger-table", DataTable)
        table.add_columns("Date", "Account", "Payee", "Debit", "Credit", "Reconciled")
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        # Load security metrics
        sec = OpenShellSupervisor.get_security_metrics()
        sec_widget = self.query_one("#security-info", Static)
        sec_widget.update(
            f"Egress Policy: [green]{sec['network_egress_policy']}[/]\n"
            f"Blocked Violations: [green]{sec['violations_blocked']}[/]\n"
            f"Landlock LSM: [yellow]{'Active' if sec['landlock_active'] else 'Emulated'}[/]\n"
            f"Loopback Model: Mistral-NeMo-12B"
        )

        # Query DuckDB
        db = LedgerDatabase()
        entries = db.get_all_entries()
        db.close()

        table = self.query_one("#ledger-table", DataTable)
        table.clear()
        for e in entries[:25]:
            table.add_row(
                str(e["transaction_date"]),
                e["account_name"],
                e["vendor_or_payee"],
                f"${float(e['debit']):.2f}",
                f"${float(e['credit']):.2f}",
                "YES" if e["reconciled"] else "NO"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-reconcile":
            self.refresh_dashboard()

def run_tui_app():
    app = SovereignTUI()
    app.run()
