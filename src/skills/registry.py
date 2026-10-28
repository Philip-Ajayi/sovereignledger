"""
Dynamic Skill Registry.
Indexes, caches, and compiles Python parser skills on the filesystem.
Allows immediate execution without invoking LLM tokens for recurring vendors.
"""
import os
import json
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional, Type
from config import settings
from src.skills.base import BaseInvoiceParser

logger = logging.getLogger("SovereignLedger.SkillRegistry")

class SkillRegistry:
    """Manages active extraction skills in the air-gapped runtime."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or (settings.SKILLS_DIR / "parsers")
        self.registry_file = settings.SKILLS_DIR / "registry.json"
        self._skills_cache: Dict[str, Type[BaseInvoiceParser]] = {}
        self._load_builtins()
        self._load_registry()

    def _load_builtins(self) -> None:
        """Register default known parsers."""
        try:
            from src.skills.parsers.standard_bank_csv import StandardBankCSVParser
            from src.skills.parsers.stripe_payout import StripePayoutParser
            self._skills_cache["standard_bank_csv"] = StandardBankCSVParser
            self._skills_cache["stripe_payout"] = StripePayoutParser
        except ImportError as e:
            logger.warning(f"Could not load pre-seeded parser: {e}")

    def _load_registry(self) -> None:
        """Load registered dynamic parser files from disk."""
        if not self.registry_file.exists():
            self._save_registry_manifest({})
            return

        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            for skill_name, info in manifest.items():
                module_path = Path(info["module_path"])
                if module_path.exists():
                    parser_cls = self._load_module_from_file(module_path)
                    if parser_cls:
                        self._skills_cache[skill_name] = parser_cls
        except Exception as e:
            logger.error(f"Error loading skill registry: {e}")

    def _save_registry_manifest(self, manifest: dict) -> None:
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def _load_module_from_file(self, file_path: Path) -> Optional[Type[BaseInvoiceParser]]:
        """Dynamically imports a Python module from an isolated filepath."""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseInvoiceParser)
                    and attr is not BaseInvoiceParser
                ):
                    return attr
        except Exception as e:
            logger.error(f"Failed to load dynamic skill from {file_path}: {e}")
        return None

    def match_skill(self, content_sample: str) -> Optional[BaseInvoiceParser]:
        """Inspects sample content to match an existing deterministic parser."""
        content_sample_lower = content_sample.lower()
        for name, parser_cls in self._skills_cache.items():
            pattern = getattr(parser_cls, "vendor_pattern", "").lower()
            if pattern and pattern in content_sample_lower:
                logger.info(f"Reusing deterministic skill: '{name}' for vendor '{pattern}'. Zero LLM tokens consumed.")
                return parser_cls()
        return None

    def register_skill(self, skill_name: str, module_path: Path, vendor_pattern: str) -> None:
        """Registers a freshly synthesized and validated skill."""
        parser_cls = self._load_module_from_file(module_path)
        if parser_cls:
            self._skills_cache[skill_name] = parser_cls

            manifest = {}
            if self.registry_file.exists():
                try:
                    with open(self.registry_file, "r") as f:
                        manifest = json.load(f)
                except Exception:
                    manifest = {}

            manifest[skill_name] = {
                "module_path": str(module_path),
                "vendor_pattern": vendor_pattern,
                "registered_at": str(Path(module_path).stat().st_mtime)
            }
            self._save_registry_manifest(manifest)
            logger.info(f"Successfully registered autonomous skill: {skill_name}")

    def list_skills(self) -> Dict[str, str]:
        return {name: getattr(cls, "vendor_pattern", "Unknown") for name, cls in self._skills_cache.items()}
