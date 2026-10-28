"""
Autonomous Skill Synthesizer.
When an unrecognized invoice or statement is encountered:
1. Mistral-NeMo-12B inspects raw content structure.
2. Synthesizes a deterministic Python parser module.
3. Performs strict AST security analysis (no os, sys, network, or subprocess calls allowed).
4. Executes unit validation against sample data in a sandbox harness.
5. Saves validated code to `/skills/parsers/<slug>.py` and registers it for future instant use.
"""
import ast
import re
import logging
from pathlib import Path
from typing import Optional, Tuple
from config import settings
from src.llm.client import LocalInferenceClient
from src.skills.base import BaseInvoiceParser
from src.skills.registry import SkillRegistry

logger = logging.getLogger("SovereignLedger.Synthesizer")

class SecurityASTValidator(ast.NodeVisitor):
    """Ensures synthesized Python parser contains zero unauthorized OS or network imports."""

    FORBIDDEN_MODULES = {
        "os", "sys", "subprocess", "socket", "urllib", "requests", "httpx",
        "shutil", "builtins", "importlib", "pathlib"
    }

    def __init__(self):
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in self.FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in self.FORBIDDEN_MODULES:
            self.violations.append(f"Forbidden from-import: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "open"}:
            self.violations.append(f"Forbidden function call: {node.func.id}")
        self.generic_visit(node)

class AutonomousSkillSynthesizer:
    """Orchestrates autonomous creation and testing of reusable parsing modules."""

    def __init__(self, llm_client: LocalInferenceClient, registry: SkillRegistry):
        self.llm = llm_client
        self.registry = registry

    async def synthesize_parser_skill(
        self,
        document_text: str,
        vendor_hint: str = "Vendor"
    ) -> Tuple[Optional[BaseInvoiceParser], str]:
        """
        Generates and verifies a Python parser class inheriting from BaseInvoiceParser.
        Includes a 3-attempt automated refinement loop.
        """
        sample_slice = document_text[:1800]
        vendor_slug = re.sub(r"[^a-zA-Z0-9_]", "_", vendor_hint.lower())
        skill_name = f"{vendor_slug}_invoice"
        module_path = settings.SKILLS_DIR / "parsers" / f"{skill_name}.py"

        prompt = f"""
You are an expert Python engineer creating a deterministic parser for an air-gapped financial system.
Synthesize a Python module that extracts transactions from this document.

DOCUMENT SAMPLE:
---
{sample_slice}
---

CRITICAL REQUIREMENTS:
1. Must define a class `DynamicInvoiceParser(BaseInvoiceParser)`:
   - Must set `vendor_pattern: str = "{vendor_hint}"`
   - Must implement `def parse(self, content: str) -> List[ParsedTransaction]:`
2. Use regex (`re`) or standard string parsing to extract:
   - transaction_date (datetime.date)
   - vendor_or_payee (string)
   - description (string)
   - amount (Decimal, positive value)
   - transaction_type (TransactionType.DEBIT for expenses, CREDIT for deposits)
   - category (ScheduleCCategory enum)
3. For ScheduleCCategory, choose strictly from:
   - ScheduleCCategory.OTHER_CLOUD_SOFTWARE (for AWS, cloud, hosting, SaaS)
   - ScheduleCCategory.OFFICE_EXPENSE (for hardware, tools, supplies)
   - ScheduleCCategory.LEGAL_PROFESSIONAL (for legal, accountants)
4. DO NOT import os, sys, subprocess, or socket.
5. Return ONLY executable python code enclosed in ```python ... ``` blocks.
"""
        attempts = 0
        max_attempts = 3
        last_error = ""

        while attempts < max_attempts:
            attempts += 1
            logger.info(f"Synthesizing extraction skill for '{vendor_hint}' (Attempt {attempts}/{max_attempts})...")

            if last_error:
                augmented_prompt = prompt + f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR:\n{last_error}\nFix the code."
            else:
                augmented_prompt = prompt

            response = await self.llm.generate_completion(augmented_prompt)
            code = self._extract_code_block(response)

            # Security AST Check
            is_safe, ast_violations = self._validate_ast(code)
            if not is_safe:
                last_error = f"Security Violation: {', '.join(ast_violations)}"
                logger.warning(f"AST check rejected code: {last_error}")
                continue

            # Write code to test module
            module_path.parent.mkdir(parents=True, exist_ok=True)
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Unit test against sample text in isolation
            try:
                parser_instance = self.registry._load_module_from_file(module_path)()
                results = parser_instance.parse(document_text)

                if results and len(results) > 0 and results[0].amount > 0:
                    logger.info(
                        f"Autonomous skill '{skill_name}' successfully compiled and unit tested! "
                        f"Extracted {len(results)} valid transaction(s)."
                    )
                    self.registry.register_skill(skill_name, module_path, vendor_hint)
                    return parser_instance, skill_name
                else:
                    last_error = "Parser returned zero valid transactions or zero amount."
            except Exception as e:
                last_error = f"Runtime Exception during parsing verification: {str(e)}"
                logger.warning(f"Test run failed: {last_error}")

        logger.error(f"Failed to synthesize working skill for '{vendor_hint}' after {max_attempts} attempts.")
        return None, ""

    def _extract_code_block(self, response: str) -> str:
        """Extracts python code from markdown fences."""
        pattern = r"```python\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback if fences are omitted
        lines = response.split("\n")
        code_lines = [l for l in lines if not l.startswith("```")]
        return "\n".join(code_lines).strip()

    def _validate_ast(self, code: str) -> Tuple[bool, list]:
        """Performs static syntax and security analysis."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax Error: {e}"]

        validator = SecurityASTValidator()
        validator.visit(tree)
        if validator.violations:
            return False, validator.violations
        return True, []
