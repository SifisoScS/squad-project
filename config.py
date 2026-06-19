"""
Central configuration — all magic numbers and environment variables in one place.
Import `cfg` anywhere; never read os.environ directly in application code.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class _Config:
    # ── Model / Agent ──────────────────────────────────────────────────────────
    MODEL               = os.environ.get("SQUAD_MODEL", "claude-sonnet-4-6")
    MAX_ITERATIONS      = int(os.environ.get("MAX_ITERATIONS", "15"))
    MAX_RETRIES         = int(os.environ.get("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY    = float(os.environ.get("RETRY_BASE_DELAY", "2.0"))
    MAX_HISTORY_TURNS   = int(os.environ.get("MAX_HISTORY_TURNS", "20"))

    # ── Build Pipeline ─────────────────────────────────────────────────────────
    MAX_BUILD_SPRINTS   = int(os.environ.get("MAX_BUILD_SPRINTS", "10"))
    MAX_REJECTIONS      = int(os.environ.get("MAX_REJECTIONS", "2"))
    BUILD_TIMEOUT_SECS  = int(os.environ.get("BUILD_TIMEOUT_SECONDS", "1800"))
    WORKSPACE_ROOT      = os.environ.get("WORKSPACE_ROOT", "workspace")

    # ── API Security ───────────────────────────────────────────────────────────
    API_SECRET_KEY      = os.environ.get("API_SECRET_KEY", "")
    ALLOWED_ORIGINS     = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_LEVEL           = os.environ.get("LOG_LEVEL", "INFO")

    # ── Memory ─────────────────────────────────────────────────────────────────
    DECISION_LOG_MAX    = int(os.environ.get("DECISION_LOG_MAX_ENTRIES", "5000"))

    # ── Cost Tracking (Sonnet 4.6 pricing, USD per million tokens) ─────────────
    COST_PER_MTK_IN     = float(os.environ.get("COST_PER_MTK_IN", "3.0"))
    COST_PER_MTK_OUT    = float(os.environ.get("COST_PER_MTK_OUT", "15.0"))


cfg = _Config()
