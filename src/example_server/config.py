"""Server configuration loaded from environment variables or a .env file.

Every field can be overridden by an environment variable of the same name
(upper- or lower-case). Copy `.env.example` to `.env` for local development.
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP server settings. Override any field via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Transport ─────────────────────────────────────────────────────────────
    # "stdio"           — local subprocess (Claude Desktop / Claude Code / Zed)
    # "streamable-http" — remote HTTP server (containers, cloud deploys)
    #
    # NOTE: app.py also auto-selects HTTP when a platform injects DATABRICKS_APP_PORT
    # or PORT, so you usually do NOT need to set this on a cloud host.
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    # ── Dataset API keys ──────────────────────────────────────────────────────
    # Add a typed field for each API key your tools need, then read it from
    # `settings.<field>` in your tool. Document the matching env var in
    # `.env.example`. Example:
    #
    #   example_api_key: str = ""   # ← set EXAMPLE_API_KEY in the environment


    # Cleaned project inventory
    govcode_project_lookup_enabled: bool = False
    govcode_project_search_enabled: bool = False
    govcode_project_catalog: str = ""
    govcode_project_schema: str = ""
    govcode_project_table: str = ""

    @model_validator(mode="after")
    def validate_project_lookup_settings(self) -> Self:
        """Require a complete table location when lookup is enabled."""
        if (
            self.govcode_project_lookup_enabled
            or self.govcode_project_search_enabled
        ):
            required = {
                "GOVCODE_PROJECT_CATALOG": self.govcode_project_catalog,
                "GOVCODE_PROJECT_SCHEMA": self.govcode_project_schema,
                "GOVCODE_PROJECT_TABLE": self.govcode_project_table,
            }
            missing = [
                name for name, value in required.items() if not value.strip()
            ]
            if missing:
                raise ValueError(
                    "Project tools require: " + ", ".join(missing)
                )

        return self

settings = Settings()
