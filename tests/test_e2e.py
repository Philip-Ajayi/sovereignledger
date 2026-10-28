"""
End-to-End Test: Full cycle from Dropzone ingestion to balanced Schedule C report.
"""
import pytest
from src.ledger.database import LedgerDatabase
from src.ledger.reconciliation import ReconciliationEngine
from src.llm.client import LocalInferenceClient
from src.skills.registry import SkillRegistry
from src.skills.synthesizer import AutonomousSkillSynthesizer
from src.watcher import DropzoneHandler

def test_end_to_end_dropzone_pipeline(tmp_path):
    db_file = tmp_path / "e2e.duckdb"
    db = LedgerDatabase(str(db_file))
    registry = SkillRegistry(tmp_path / "skills")
    llm = LocalInferenceClient()
    synth = AutonomousSkillSynthesizer(llm, registry)
    rec = ReconciliationEngine(db)
    handler = DropzoneHandler(db, registry, synth, rec)

    # Create dummy AWS receipt
    doc_path = tmp_path / "aws_test.txt"
    doc_path.write_text("Total Amount Due: $142.50\nInvoice Date: January 11, 2025\nAccount: AWS")

    handler.process_file(doc_path)

    entries = db.get_all_entries()
    assert len(entries) >= 2  # Debit and Credit double-entry lines

    balance = db.get_ledger_balance()
    assert balance["is_balanced"] is True

    report = db.generate_schedule_c_report()
    assert len(report) >= 1
    assert float(report[0]["total_deduction"]) == 142.50
    db.close()
