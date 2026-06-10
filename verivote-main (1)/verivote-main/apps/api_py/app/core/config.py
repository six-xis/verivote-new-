from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_mode: Literal["development", "test", "competition", "production"] = "development"
    zk_mock_mode: bool = False
    zk_private_valid_vote_artifacts_dir: str = "artifacts/zk/private_valid_vote"
    zk_snarkjs_command: str = "pnpm exec snarkjs"
    zk_snarkjs_timeout_seconds: int = 30
    allow_demo_credential_issuer: bool = True
    allow_demo_tally_key: bool = True
    allow_mock_verifier: bool = True
    database_url: str = "memory"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VERIVOTE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
