"""
Pre-seeded Deterministic Skill: Standard Checking Account CSV Parser.
Parses common checking and savings account tabular statement exports.
"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import List
from src.skills.base import BaseInvoiceParser
from src.models import ParsedTransaction, TransactionType, ScheduleCCategory

class StandardBankCSVParser(BaseInvoiceParser):
    vendor_pattern: str = "account statement"

    def parse(self, content: str) -> List[ParsedTransaction]:
        transactions = []
        reader = csv.DictReader(io.StringIO(content.strip()))

        for row in reader:
            # Normalize keys to lower-case
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            date_str = normalized.get("date") or normalized.get("transaction date") or "2025-01-01"
            try:
                tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    tx_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    tx_date = datetime.now().date()

            desc = normalized.get("description") or normalized.get("memo") or "Bank Transaction"
            amount_str = normalized.get("amount") or "0.00"
            amount_val = Decimal(amount_str.replace("$", "").replace(",", ""))

            tx_type = TransactionType.CREDIT if amount_val > 0 else TransactionType.DEBIT
            abs_amount = abs(amount_val)

            transactions.append(ParsedTransaction(
                transaction_date=tx_date,
                vendor_or_payee=desc.split("-")[0].strip(),
                description=desc,
                amount=abs_amount,
                transaction_type=tx_type,
                category=ScheduleCCategory.OFFICE_EXPENSE if tx_type == TransactionType.DEBIT else ScheduleCCategory.GROSS_RECEIPTS,
                confidence_score=1.0,
                raw_payload=normalized
            ))

        return transactions
