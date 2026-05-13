import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db.init_db import init_database
from backend.agent.graph import run_agent, resume_agent

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and vector store on startup."""
    init_database()
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
