import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def _require(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        print(f"\nERRO: Variável '{key}' não encontrada no .env\n", file=sys.stderr)
        sys.exit(1)
    return value


# ── IA ────────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-haiku-4-5")

# ── HubSpot ───────────────────────────────────────────────────────────────────
HUBSPOT_API_KEY: str = _require("HUBSPOT_API_KEY")
HUBSPOT_PIPELINE_ID: str = os.getenv("HUBSPOT_PIPELINE_ID", "default")
HUBSPOT_DEAL_STAGE_HOT: str = os.getenv("HUBSPOT_DEAL_STAGE_HOT", "appointmentscheduled")
HUBSPOT_DEAL_STAGE_WARM: str = os.getenv("HUBSPOT_DEAL_STAGE_WARM", "qualifiedtobuy")
HUBSPOT_DEAL_STAGE_COLD: str = os.getenv("HUBSPOT_DEAL_STAGE_COLD", "presentationscheduled")

# ── Hunter.io ─────────────────────────────────────────────────────────────────
HUNTER_API_KEY: str = os.getenv("HUNTER_API_KEY", "")

# ── Agente ────────────────────────────────────────────────────────────────────
MAX_CONCURRENT_LEADS: int = int(os.getenv("MAX_CONCURRENT_LEADS", "3"))
RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
HOT_LEAD_THRESHOLD: int = int(os.getenv("HOT_LEAD_THRESHOLD", "70"))
WARM_LEAD_THRESHOLD: int = int(os.getenv("WARM_LEAD_THRESHOLD", "40"))