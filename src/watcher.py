"""
Filesystem Dropzone Watcher Daemon.
Monitors incoming directory via filesystem triggers and parses financial documents.
"""
import time
import hashlib
import logging
import asyncio
import concurrent.futures
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import settings
from src.ledger.database import LedgerDatabase
from src.ledger.reconciliation import ReconciliationEngine
from src.llm.client import LocalInferenceClient
from src.skills.registry import SkillRegistry
from src.skills.synthesizer import AutonomousSkillSynthesizer
from src.sandbox.openshell import OpenShellSupervisor

logger = logging.getLogger("SovereignLedger.Watcher")

class DropzoneHandler(FileSystemEventHandler):
    """Handles file dropped events in the monitored incoming directory."""

    def __init__(
        self,
        db: LedgerDatabase,
        registry: SkillRegistry,
        synthesizer: AutonomousSkillSynthesizer,
        reconciler: ReconciliationEngine
    ):
        self.db = db
        self.registry = registry
        self.synthesizer = synthesizer
        self.reconciler = reconciler
        self._processed_hashes = set()

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        self.process_file(file_path)

    def process_file(self, file_path: Path) -> None:
        """Processes single ingested statement or receipt."""
        if file_path.name.startswith(".") or file_path.suffix not in [".csv", ".txt", ".pdf"]:
            return

        logger.info(f"[DROPZONE INGESTION] Detected new financial record: {file_path.name}")
        time.sleep(0.3)

        try:
            raw_bytes = file_path.read_bytes()
            doc_hash = hashlib.sha256(raw_bytes).hexdigest()

            if doc_hash in self._processed_hashes:
                logger.info(f"Document {file_path.name} already processed. Skipping.")
                return

            content_text = raw_bytes.decode("utf-8", errors="ignore")

            # 1. Check Skill Registry for existing deterministic parser
            matched_parser = self.registry.match_skill(content_text)
            skill_name = "cached_deterministic_parser"

            # 2. If no parser exists, autonomously synthesize one
            if not matched_parser:
                logger.info(f"Synthesizing extraction skill for '{file_path.name}'...")
                vendor_clue = file_path.stem.split("_")[0].capitalize()

                # Check if running inside active event loop (e.g., FastAPI)
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        matched_parser, skill_name = pool.submit(
                            asyncio.run,
                            self.synthesizer.synthesize_parser_skill(content_text, vendor_hint=vendor_clue)
                        ).result()
                else:
                    matched_parser, skill_name = asyncio.run(
                        self.synthesizer.synthesize_parser_skill(content_text, vendor_hint=vendor_clue)
                    )

            if not matched_parser:
                logger.error(f"Skill synthesis could not parse: {file_path.name}")
                return

            # 3. Parse transactions with deterministic code
            parsed_txs = matched_parser.parse(content_text)
            logger.info(f"Extracted {len(parsed_txs)} transactions from {file_path.name}.")

            # 4. Commit to DuckDB double-entry ledger
            self.db.record_document(
                doc_hash=doc_hash,
                filename=file_path.name,
                file_type=file_path.suffix,
                skill_used=skill_name,
                tx_count=len(parsed_txs)
            )

            account_name = "Checking Account" if file_path.suffix == ".csv" else "Cloud Vendor Payable"
            self.reconciler.commit_parsed_transactions(parsed_txs, doc_hash, account_name=account_name)

            # 5. Perform reconciliation pass
            rec_result = self.reconciler.reconcile_unmatched()
            logger.info(f"Ledger Reconciliation: {rec_result}")

            self._processed_hashes.add(doc_hash)

        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}", exc_info=True)

class DropzoneWatcherDaemon:
    """Monitors incoming drop folder."""

    def __init__(self):
        OpenShellSupervisor.install_egress_interceptor()
        self.db = LedgerDatabase()
        self.registry = SkillRegistry()
        self.llm = LocalInferenceClient()
        self.synthesizer = AutonomousSkillSynthesizer(self.llm, self.registry)
        self.reconciler = ReconciliationEngine(self.db)
        self.handler = DropzoneHandler(self.db, self.registry, self.synthesizer, self.reconciler)
        self.observer = Observer()

    def start(self) -> None:
        drop_dir = str(settings.DATA_DIR)
        logger.info(f"Starting Ingest Daemon on dropzone: {drop_dir}")
        for item in settings.DATA_DIR.iterdir():
            if item.is_file():
                self.handler.process_file(item)

        self.observer.schedule(self.handler, drop_dir, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
        self.db.close()
