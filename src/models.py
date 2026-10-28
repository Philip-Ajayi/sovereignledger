"""
Domain models and Schemas for SovereignLedger.
Defines immutable data objects for accounting entries, skills, and Schedule C tax categories.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ScheduleCCategory(str, Enum):
    ADVERTISING = "Line 8 - Advertising"
    VEHICLE = "Line 9 - Car and truck expenses"
    COMMISSIONS = "Line 10 - Commissions and fees"
    CONTRACT_LABOR = "Line 11 - Contract labor"
    LEGAL_PROFESSIONAL = "Line 17 - Legal and professional services"
    OFFICE_EXPENSE = "Line 18 - Office expense"
    RENT_LEASE_EQUIPMENT = "Line 20a - Rent/lease vehicles/machinery"
    RENT_LEASE_PROPERTY = "Line 20b - Rent/lease other business property"
    SUPPLIES = "Line 22 - Supplies"
    TAXES_LICENSES = "Line 23 - Taxes and licenses"
    TRAVEL_MEALS = "Line 24b - Travel and meals"
    UTILITIES = "Line 25 - Utilities"
    OTHER_CLOUD_SOFTWARE = "Line 27a - Other expenses (Cloud/SaaS/Compute)"
    GROSS_RECEIPTS = "Part I - Gross receipts or sales"
    NON_DEDUCTIBLE = "Non-Deductible / Personal Transfer"

class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class ParsedTransaction(BaseModel):
    transaction_date: date
    vendor_or_payee: str
    description: str
    amount: Decimal = Field(gt=0, description="Absolute transaction value")
    transaction_type: TransactionType
    category: ScheduleCCategory = ScheduleCCategory.OTHER_CLOUD_SOFTWARE
    reference_id: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_payload: Optional[Dict[str, Any]] = None

class ExtractionSkillManifest(BaseModel):
    skill_name: str
    vendor_pattern: str
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    module_path: str
    is_autonomous: bool = True
    test_passed: bool = False
    source_code: str

class DocumentIngestionRecord(BaseModel):
    document_hash: str
    filename: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    file_type: str
    skill_used: Optional[str] = None
    transaction_count: int = 0
    reconciled_count: int = 0

class LedgerEntry(BaseModel):
    id: Optional[int] = None
    transaction_date: date
    account_name: str
    vendor_or_payee: str
    description: str
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    category: ScheduleCCategory
    document_hash: str
    reconciled: bool = False
    reconciliation_match_id: Optional[int] = None
