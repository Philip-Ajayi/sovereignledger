"""
Base specification for reusable extraction skills.
Every dynamically synthesized invoice or bank parser inherits from BaseInvoiceParser.
"""
from abc import ABC, abstractmethod
from typing import List
from src.models import ParsedTransaction

class BaseInvoiceParser(ABC):
    """Abstract Interface contract for all dynamically generated parser skills."""

    vendor_pattern: str = "Generic"

    @abstractmethod
    def parse(self, content: str) -> List[ParsedTransaction]:
        """
        Extracts structured transactions from unstructured text or tabular CSV content.
        Must return list of verified ParsedTransaction instances.
        """
        raise NotImplementedError("Parsing method must be implemented by synthesized skill.")
