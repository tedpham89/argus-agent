import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.db.init_db import init_database
from backend.db.aerondight_db import init_aerondight_db, get_connection as get_aero_conn

load_dotenv()

from backend.agent.graph import run_agent, resume_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and vector store on startup."""
    init_database()
    init_aerondight_db()
    yield


app = FastAPI(
    title="Argus Agent",
    description="Financial operations agent — portfolio analysis, compliance, and risk monitoring",
    version="0.1.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------

class AgentRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


class SyncPayload(BaseModel):
    scores: list[dict] | None = None
    regime: list[dict] | None = None


# ---------- Routes ----------

@app.get("/health")
def health():
    return {"status": "ok", "service": "argus-agent"}


@app.post("/agent/run")
async def agent_run(req: AgentRequest):
    """Run the agent on a user message. Returns plan, results, and status."""
    result = await run_agent(req.message, req.thread_id)
    return result


@app.post("/agent/approve")
async def agent_approve(req: ApprovalRequest):
    """Resume agent after human approval/rejection."""
    result = await resume_agent(req.thread_id, req.approved)
    return result


# ---------- Data sync ----------

@app.post("/data/sync")
async def data_sync(payload: SyncPayload, x_api_key: Optional[str] = Header(None)):
    """Receive synced scores and regime data from Aerondight research system."""
    sync_key = os.getenv("SYNC_API_KEY")
    if not sync_key:
        raise HTTPException(status_code=503, detail="Sync not configured")
    if x_api_key != sync_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    conn = get_aero_conn()
    counts = {"scores": 0, "regime": 0}

    if payload.scores:
        conn.executemany(
            """INSERT OR REPLACE INTO analysis_scores
               (symbol, date, model_type, fundamental_score, valuation_score,
                quality_score, growth_score, balance_sheet_score, technical_score,
                sector_score, combined_score, signal, trend_score, updated_at)
               VALUES (:symbol, :date, :model_type, :fundamental_score, :valuation_score,
                       :quality_score, :growth_score, :balance_sheet_score, :technical_score,
                       :sector_score, :combined_score, :signal, :trend_score, :updated_at)""",
            payload.scores,
        )
        counts["scores"] = len(payload.scores)

    if payload.regime:
        conn.executemany(
            """INSERT OR REPLACE INTO regime_states
               (date, hmm_regime, hmm_regime_label, hmm_confidence,
                xgb_regime, xgb_confidence, regime_agreement, updated_at)
               VALUES (:date, :hmm_regime, :hmm_regime_label, :hmm_confidence,
                       :xgb_regime, :xgb_confidence, :regime_agreement, :updated_at)""",
            payload.regime,
        )
        counts["regime"] = len(payload.regime)

    conn.commit()
    conn.close()
    return {"status": "ok", "synced": counts}


# ---------- Static frontend ----------

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA — all non-API routes fall through to index.html."""
        file = DIST_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(DIST_DIR / "index.html")
