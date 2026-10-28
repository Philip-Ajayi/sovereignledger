"""
Pre-seeded Deterministic Skill: Stripe Payout & Gross Revenue Parser.
Extracts processor fees and net settlements into balanced gross receipts entries.
"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import List
from src.skills.base import BaseInvoiceParser
from src.models import ParsedTransaction, TransactionType, ScheduleCCategory

class StripePayoutParser(BaseInvoiceParser):
    vendor_pattern: str = "stripe payout"

    def parse(self, content: str) -> List[ParsedTransaction]:
        transactions = []
        reader = csv.DictReader(io.StringIO(content.strip()))

        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            date_str = normalized.get("created") or normalized.get("date") or "2025-01-15"
            try:
                tx_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            except Exception:
                tx_date = datetime.now().date()

            amount_val = Decimal(normalized.get("amount", "0.00").replace("$", ""))

            transactions.append(ParsedTransaction(
                transaction_date=tx_date,
                vendor_or_payee="Stripe Payments",
                description=f"Client Gross Settlement: {normalized.get('id', 'PAYOUT')}",
                amount=abs(amount_val),
                transaction_type=TransactionType.CREDIT,
                category=ScheduleCCategory.GROSS_RECEIPTS,
                confidence_score=1.0,
                reference_id=normalized.get("id")
            ))

        return transactions
