"""Configuration constants and environment settings for Exitwise."""

import os
from pathlib import Path

# Auto-load .env from the current working directory or parent directories.
# This means `exitwise` CLI picks up GEMINI_API_KEY from a .env file
# without needing the user to export it manually each session.
try:
    from dotenv import load_dotenv as _load_dotenv
    # Walk up from CWD looking for .env
    _cwd = Path.cwd()
    for _parent in [_cwd, *_cwd.parents]:
        _env_file = _parent / ".env"
        if _env_file.is_file():
            _load_dotenv(_env_file, override=False)  # override=False: env vars already set win
            break
except ImportError:
    pass  # python-dotenv not installed — user must export env vars manually

# Model configurations
# Hosted Gemini API Gemma 4 models
DEFAULT_GEMMA_MODEL: str = os.getenv("EXITWISE_MODEL", "gemma-4-26b-a4b-it")
FALLBACK_GEMMA_MODELS: list[str] = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemma-4-12b-it",
]

# API & Access details
GEMMA_ACCESS_METHOD: str = "Hosted Gemini API via official google-genai Python SDK"
GEMMA_LICENSE: str = "Apache-2.0 (Gemma Open Weights & Code)"
GEMMA_TERMS_URL: str = "https://ai.google.dev/gemma/terms"
GEMINI_API_TERMS_URL: str = "https://ai.google.dev/gemini-api/terms"

# Timeouts & Limits (in seconds)
SUBPROCESS_TIMEOUT_DEFAULT: int = 60
TEST_SUITE_TIMEOUT: int = 120
SMOKE_TEST_TIMEOUT: int = 35
API_REQUEST_TIMEOUT: float = 30.0
MAX_RETRY_ATTEMPTS: int = 2
PER_RUN_REQUEST_BUDGET: int = 50

# Output paths
DEFAULT_OUTPUT_DIR: Path = Path("exitwise-output")

# Environment Keys
ENV_KEY_NAMES: list[str] = ["GEMINI_API_KEY", "GOOGLE_API_KEY"]


def get_api_key() -> str | None:
    """Retrieve Gemini API key from environment without logging or exposing it."""
    for key_name in ENV_KEY_NAMES:
        val = os.getenv(key_name, "").strip()
        if val:
            return val
    return None


def is_offline() -> bool:
    """Check if offline signals flag is set."""
    return os.getenv("EXITWISE_OFFLINE", "0") in ("1", "true", "True")
