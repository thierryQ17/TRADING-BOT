"""FastAPI server — connects the dashboard to the trading bots."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.bot_manager import BotManager

app = FastAPI(title="Polymarket RBI Bot API", version="1.0.0")

# CORS — allow dashboard to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton bot manager
manager = BotManager()

# Serve dashboard static files
dashboard_dir = Path(__file__).parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")


# ========== Routes ==========

@app.get("/")
async def root():
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
async def start_bot(key: str):
    return manager.start_bot(key)


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


# --- Settings ---

class SettingsUpdate(BaseModel):
    position_size: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    dry_run: bool | None = None
    account: str | None = None


@app.get("/api/settings")
async def get_settings():
    return manager.get_settings()


@app.put("/api/settings")
async def update_settings(body: SettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return manager.update_settings(updates)


# ========== Entry point ==========

if __name__ == "__main__":
    import uvicorn
    print("\n  Polymarket RBI Bot — API Server")
    print("  Dashboard: http://localhost:1818")
    print("  API docs:  http://localhost:1818/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=1818)
