"""
SovereignLedger Core Runtime Configuration.
Governs isolation parameters, database destinations, and loopback LLM communication.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SOVEREIGN_ENV: str = "production"

    # Path configuration
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data" / "incoming"
    DB_PATH: Path = BASE_DIR / "db" / "sovereignledger.duckdb"
    SQLITE_PATH: Path = BASE_DIR / "db" / "episodic_memory.sqlite3"
    SKILLS_DIR: Path = BASE_DIR / "skills"

    # Cryptographic store
    SOVEREIGN_ENCRYPTION_KEY: str = "sovereign_dev_key_32_bytes_super_secret_ledger!"

    # Local Inference settings (NVIDIA Mistral-NeMo-12B on loopback)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "nvidia/Mistral-NeMo-12B-Instruct"
    LLM_TIMEOUT_SECONDS: float = 4.0

    # Sandboxing & Kernel Security
    ENFORCE_KERNEL_LANDLOCK: bool = True
    STRICT_ZERO_EGRESS: bool = True

    # Web & UI parameters: dynamically falls back to Render's $PORT
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = int(os.environ.get("PORT", "8080"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def initialize_filesystem(self) -> None:
        """Create necessary system directories if they do not exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        (self.SKILLS_DIR / "parsers").mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.initialize_filesystem()