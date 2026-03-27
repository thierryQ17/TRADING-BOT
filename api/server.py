"""FastAPI server — connects the dashboard to the trading bots."""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from api.bot_manager import BotManager
from data.storage import close_db

# Auth config
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")
AUTH_SECRET = os.getenv("AUTH_SECRET", "default-secret-change-me")
TOKEN_EXPIRY = 864000  # 10 jours

# Singleton bot manager
manager = BotManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    yield
    # Graceful shutdown — stop all bots, join threads, close DB
    manager.kill_all()
    close_db()


app = FastAPI(title="Polymarket RBI Bot API", version="1.0.0", lifespan=lifespan)

# CORS — restricted to localhost by default, configurable via CORS_ORIGINS env var
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:1818,http://127.0.0.1:1818"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)

# Serve dashboard static files
dashboard_dir = Path(__file__).parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")


# ========== Auth ==========

def _make_token(username: str) -> str:
    """Create a signed token: base64url(payload)-signature (cookie-safe, no special chars)."""
    payload = json.dumps({"user": username, "exp": int(time.time()) + TOKEN_EXPIRY})
    b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(AUTH_SECRET.encode(), b64.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{b64}-{sig}"


def _verify_token(token: str) -> bool:
    """Verify token signature and expiry."""
    try:
        token = token.strip('"')
        b64, sig = token.rsplit("-", 1)
        expected = hmac.new(AUTH_SECRET.encode(), b64.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return False
        # Re-add base64 padding
        padded = b64 + "=" * (4 - len(b64) % 4) if len(b64) % 4 else b64
        payload = base64.urlsafe_b64decode(padded).decode()
        data = json.loads(payload)
        return data.get("exp", 0) > time.time()
    except Exception:
        return False


# Public paths that don't require auth
PUBLIC_PATHS = {"/api/auth/login", "/api/auth/check", "/login.html", "/docs"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    # Only protect /api/ endpoints (except auth routes)
    if not path.startswith("/api/") or path in PUBLIC_PATHS:
        return await call_next(request)

    # Check token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""

    if token and _verify_token(token):
        return await call_next(request)

    return JSONResponse({"detail": "Non authentifie"}, status_code=401)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def auth_login(body: LoginRequest):
    if body.username == AUTH_USERNAME and body.password == AUTH_PASSWORD:
        return {"token": _make_token(body.username)}
    return JSONResponse({"detail": "Identifiants incorrects"}, status_code=401)


@app.get("/api/auth/check")
async def auth_check(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if _verify_token(token):
        return {"status": "ok"}
    return JSONResponse({"detail": "Token invalide"}, status_code=401)


# ========== Routes ==========

@app.get("/")
async def root(request: Request):
    """Serve the dashboard."""
    index = dashboard_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Dashboard not found — place index.html in dashboard/"}


@app.get("/docs.html")
async def docs_page():
    """Serve the documentation page."""
    docs = dashboard_dir / "docs.html"
    if docs.exists():
        return FileResponse(str(docs))
    return {"message": "Documentation not found"}


# --- Bots ---

@app.get("/api/bots")
async def get_bots():
    return manager.get_all_bots()


@app.post("/api/bots/{key}/start")
async def start_bot(key: str, token_id: str = ""):
    return manager.start_bot(key, token_id=token_id)


@app.post("/api/bots/{key}/stop")
async def stop_bot(key: str):
    return manager.stop_bot(key)


@app.post("/api/bots/kill-all")
async def kill_all():
    return manager.kill_all()


# --- Metrics ---

@app.get("/api/metrics")
async def get_metrics():
    return manager.get_metrics()


# --- Trades ---

@app.get("/api/trades")
async def get_trades(limit: int = 50):
    return manager.get_trades(limit=limit)


# --- Risk ---

@app.get("/api/risk")
async def get_risk():
    return manager.get_risk()


# --- Logs ---

@app.get("/api/logs")
async def get_logs(limit: int = 100, level: str = ""):
    return manager.get_logs(limit=limit, level=level)


# --- Alerts ---

@app.get("/api/alerts/status")
async def alerts_status():
    return {"enabled": manager.alerter.enabled}


@app.post("/api/alerts/test")
async def alerts_test():
    ok = manager.alerter.send_test()
    return {"status": "sent" if ok else "failed", "enabled": manager.alerter.enabled}


# --- Settings ---

class SettingsUpdate(BaseModel):
    position_size: float | None = Field(None, gt=0, le=1000, description="Position size in USD")
    stop_loss_pct: float | None = Field(None, gt=0, le=100, description="Stop loss percentage (1-100)")
    take_profit_pct: float | None = Field(None, gt=0, le=100, description="Take profit percentage (1-100)")
    risk_per_trade_pct: float | None = Field(None, gt=0, le=10, description="Risk per trade percentage (0.5-10)")
    trailing_tp_enabled: bool | None = None
    trailing_tp_activation: float | None = Field(None, gt=0, le=100, description="Trailing TP activation percentage")
    trailing_tp_distance: float | None = Field(None, gt=0, le=100, description="Trailing TP distance percentage")
    dry_run: bool | None = None
    account: str | None = Field(None, min_length=1, max_length=50)


@app.get("/api/settings")
async def get_settings():
    return manager.get_settings()


@app.put("/api/settings")
async def update_settings(body: SettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return manager.update_settings(updates)


# --- Config (.env) ---

# Keys that are masked when reading (sensitive)
_SENSITIVE_KEYS = {"POLYMARKET_PRIVATE_KEY", "AUTH_PASSWORD", "AUTH_SECRET", "SMTP_PASSWORD"}

# All configurable keys grouped by section
_CONFIG_KEYS = [
    "POLYMARKET_PRIVATE_KEY", "POLYMARKET_FUNDER_ADDRESS", "POLYMARKET_TOKEN_ID",
    "MAX_POSITION_SIZE", "MAX_DAILY_LOSS", "MAX_OPEN_POSITIONS",
    "DRY_RUN", "LOG_LEVEL", "CORS_ORIGINS",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "ALERT_EMAIL_TO",
    "ALERT_LOSS_THRESHOLD", "ALERT_GAIN_THRESHOLD",
    "ALERT_DAILY_LOSS_THRESHOLD", "ALERT_DAILY_GAIN_THRESHOLD",
    "COPYTRADE_MIN_TRADES", "COPYTRADE_MIN_WIN_RATE", "COPYTRADE_TOP_N",
    "COPYTRADE_SCAN_INTERVAL", "COPYTRADE_RESCORE_INTERVAL",
    "AUTH_USERNAME", "AUTH_PASSWORD",
]


def _read_env() -> dict[str, str]:
    """Read .env file into a dict."""
    env_path = Path(__file__).parent.parent / ".env"
    values = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


def _write_env(updates: dict[str, str]) -> None:
    """Update specific keys in the .env file, preserving structure."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)
    # Add any new keys not already in the file
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@app.get("/api/config")
async def get_config():
    """Read all configurable .env values (sensitive keys masked)."""
    values = _read_env()
    result = {}
    for key in _CONFIG_KEYS:
        val = values.get(key, "")
        if key in _SENSITIVE_KEYS and val:
            result[key] = val[:3] + "*" * (len(val) - 3)
        else:
            result[key] = val
    return result


@app.put("/api/config")
async def update_config(request: Request):
    """Update .env values. Empty strings and masked values (***) are ignored."""
    body = await request.json()
    updates = {}
    current = _read_env()
    for key, val in body.items():
        if key not in _CONFIG_KEYS:
            continue
        val = str(val).strip()
        # Skip masked values (unchanged sensitive fields)
        if "*" in val:
            continue
        # Allow clearing non-sensitive fields
        if val != current.get(key, ""):
            updates[key] = val
    if updates:
        _write_env(updates)
    return {"updated": list(updates.keys()), "restart_required": bool(updates)}


# ========== Entry point ==========

if __name__ == "__main__":
    import uvicorn
    print("\n  Polymarket RBI Bot — API Server")
    print("  Dashboard: http://localhost:1818")
    print("  API docs:  http://localhost:1818/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=1818)
