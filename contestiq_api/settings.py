from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(path: Path) -> None:
    """Minimal .env loader — sets env vars that are not already set."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# Load .env from the project root (Trace_X_project/.env) unless env vars already set.
# Also try python-dotenv for richer .env support if available.
_ENV_FILE = Path(__file__).parent.parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(_ENV_FILE, override=False)
except ImportError:
    _load_env_file(_ENV_FILE)


DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3006",
    "http://localhost:3007",
    "http://localhost:3008",
    "http://localhost:3009",
    "http://localhost:3010",
    "http://localhost:3011",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3006",
    "http://127.0.0.1:3008",
    "http://127.0.0.1:3010",
    "http://127.0.0.1:3011",
    "http://127.0.0.1:5173",
]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return max(0, int(value))
    except ValueError:
        return default


def _parse_origins(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    enable_debug_endpoint: bool
    cors_origins: list[str]
    rate_limit_analyze_seconds: int
    judge0_base_url: str = ""
    judge0_api_key: str = ""
    judge0_api_host: str = ""
    port: int | None = None
    # DeepSeek Copilot
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    # Supabase (optional — copilot works without it, messages just won't persist)
    supabase_url: str = ""
    supabase_service_key: str = ""
    # Coach Memory: set to True to use DeepSeek for AI-generated profile summaries
    # (costs tokens — disabled by default; deterministic summaries are used instead)
    enable_ai_profile_summary: bool = False


def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development").strip().lower() or "development"
    default_debug = app_env != "production"
    default_rate_limit = 30 if app_env == "production" else 0
    port_value = os.getenv("PORT")
    return Settings(
        app_env=app_env,
        enable_debug_endpoint=_parse_bool(os.getenv("ENABLE_DEBUG_ENDPOINT"), default_debug),
        cors_origins=_parse_origins(os.getenv("CORS_ORIGINS")),
        rate_limit_analyze_seconds=_parse_int(os.getenv("RATE_LIMIT_ANALYZE_SECONDS"), default_rate_limit),
        judge0_base_url=(os.getenv("JUDGE0_BASE_URL") or "").rstrip("/"),
        judge0_api_key=os.getenv("JUDGE0_API_KEY") or "",
        judge0_api_host=os.getenv("JUDGE0_API_HOST") or "",
        port=_parse_int(port_value, 0) or None,
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or "",
        deepseek_model=os.getenv("DEEPSEEK_MODEL") or "deepseek-chat",
        deepseek_base_url=(os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/"),
        supabase_url=(os.getenv("SUPABASE_URL") or "").rstrip("/"),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY") or "",
        enable_ai_profile_summary=_parse_bool(os.getenv("ENABLE_AI_PROFILE_SUMMARY"), False),
    )
