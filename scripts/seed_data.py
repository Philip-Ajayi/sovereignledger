"""
Realistic Test Data Generator for SovereignLedger.
Generates:
1. Bank Checking Account CSV (`bank_statement_2025_q1.csv`)
2. Amazon Web Services Cloud Bill (`aws_invoice_inv98214.txt`)
3. Stripe Merchant Gross Payouts (`stripe_payouts_jan2025.csv`)
4. GitHub Copilot Subscription Bill (`github_copilot_billing.txt`)
"""
from pathlib import Path
from config import settings

def create_sample_files():
    data_dir = settings.DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Bank Checking Statement CSV
    bank_csv_content = """Date,Description,Amount
2025-01-05,STRIPE PAYOUT-AUTO-1002,4250.00
2025-01-12,AWS CLOUD SERVICES - DEBIT,-142.50
2025-01-18,GITHUB COPILOT SUBSCRIPTION,-21.00
2025-01-20,OFFICE DEPOT - PAPER & HARDWARE,-85.40
2025-01-25,CLIENT CONSULTING WIRE-REF488,6500.00
"""
    (data_dir / "bank_statement_2025_q1.csv").write_text(bank_csv_content)

    # 2. AWS Unstructured Invoice
    aws_invoice_content = """
============================================================
              AMAZON WEB SERVICES INVOICE
============================================================
Invoice Number:   INV-AWS-2025-01-88912
Invoice Date:     January 11, 2025
Account ID:       112233445566
Customer:         Sovereign Engineering LLC

SUMMARY OF CHARGES:
------------------------------------------------------------
Amazon Elastic Compute Cloud (EC2) ................... $98.10
Amazon Simple Storage Service (S3) ................... $14.40
Amazon Relational Database Service (RDS) ............. $30.00
------------------------------------------------------------
Total Amount Due:                                     $142.50

Payment Method:   Direct Debit from Checking (..4019)
Status:           PAID
============================================================
"""
    (data_dir / "aws_invoice_inv98214.txt").write_text(aws_invoice_content)

    # 3. Stripe Payouts CSV
    stripe_csv_content = """id,created,amount,currency,status
po_1Nq8234891,2025-01-05,4250.00,usd,paid
po_1Nq9991204,2025-01-25,6500.00,usd,paid
"""
    (data_dir / "stripe_payouts_jan2025.csv").write_text(stripe_csv_content)

    # 4. GitHub Unstructured Billing Receipt
    github_bill_content = """
GitHub Inc. Receipt
Date: 2025-01-17
Invoice ID: GH-BILL-9901
Description: GitHub Team (5 seats) + Copilot Business
Total Paid: $21.00
Payment Status: Completed
"""
    (data_dir / "github_copilot_billing.txt").write_text(github_bill_content)

    print(f"Successfully generated 4 sample financial documents in: {data_dir}")

if __name__ == "__main__":
    create_sample_files()
