"""
Tests DuckDB relational ledger schema, double-entry equality, and Schedule C compilation.
"""
from datetime import date
from decimal import Decimal
from src.ledger.database import LedgerDatabase
from src.models import LedgerEntry, ScheduleCCategory

def test_double_entry_balance_calculation(tmp_path):
    test_db = tmp_path / "test_ledger.duckdb"
    db = LedgerDatabase(str(test_db))

    doc_hash = "fake_sha256_hash_1"
    db.record_document(doc_hash, "test.csv", ".csv", "manual", 1)

    # Balanced expense transaction
    db.insert_transaction(LedgerEntry(
        transaction_date=date(2025, 1, 10),
        account_name="Business Expenses",
        vendor_or_payee="AWS",
        description="Hosting",
        debit=Decimal("150.00"),
        credit=Decimal("0.00"),
        category=ScheduleCCategory.OTHER_CLOUD_SOFTWARE,
        document_hash=doc_hash
    ))

    db.insert_transaction(LedgerEntry(
        transaction_date=date(2025, 1, 10),
        account_name="Checking Account",
        vendor_or_payee="AWS",
        description="Debit Payment",
        debit=Decimal("0.00"),
        credit=Decimal("150.00"),
        category=ScheduleCCategory.OTHER_CLOUD_SOFTWARE,
        document_hash=doc_hash
    ))

    balance = db.get_ledger_balance()
    assert balance["is_balanced"] is True
    assert balance["total_debit"] == Decimal("150.00")
    assert balance["total_credit"] == Decimal("150.00")

    # Schedule C report check
    report = db.generate_schedule_c_report()
    assert len(report) == 1
    assert report[0]["total_deduction"] == 150.00
    db.close()
