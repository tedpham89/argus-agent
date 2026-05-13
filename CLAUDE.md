# Argus Agent

## What This Is
A financial operations agent that takes natural language instructions about an investment portfolio, decomposes them into a multi-step plan using LangGraph, orchestrates tool calls, validates results, and responds. This is a portfolio project targeting BlackRock Aladdin AI Engineering roles.

## Live URL
- Production: https://argus-agent.dev
- Railway auto-deploys on every push to `main`

## Current State
- Phase 1 COMPLETE: FastAPI skeleton deployed, /health endpoint working
- Phase 2 TODO: Get the LangGraph agent loop working end-to-end
- Phase 3 COMPLETE: React frontend (ChatPanel, PlanViewer, ConfirmModal)

## Tech Stack
- Python 3.11, FastAPI, LangGraph, langchain-anthropic
- SQLite for portfolio holdings (seeded with 40 positions on startup)
- ChromaDB for compliance rules RAG
- yfinance for market data
- Claude Sonnet via Anthropic API
- Deployed on Railway

## Architecture
```
POST /agent/run { "message": "..." }
  → Planner (LLM decomposes into steps)
  → Executor (calls tools sequentially)
  → Validator (LLM checks completeness)
  → Responder (LLM synthesizes final answer)
  → Returns { thread_id, plan, final_response }
```

## Tools (5 total, all in backend/tools/)
1. portfolio.py — query_holdings, get_sector_breakdown, get_top_positions (SQLite)
2. market_data.py — get_market_data (yfinance)
3. compliance.py — check_compliance (ChromaDB RAG + rule checks)
4. stock_scorer.py — score_stock (mock data, will connect to private API later)
5. regime.py — get_market_regime (mock data, will connect to private API later)

## Key Files
- backend/main.py — FastAPI app with /health, /agent/run, /agent/approve
- backend/agent/graph.py — LangGraph StateGraph definition + run_agent()
- backend/agent/nodes.py — planner, executor, validator, response nodes
- backend/agent/state.py — AgentState TypedDict
- backend/agent/prompts.py — system prompts for each node
- backend/tools/__init__.py — tool registry with get_tool_descriptions()
- backend/db/init_db.py — SQLite init + seed from data/seed_holdings.json

## Commands
```bash
# Run locally
uvicorn backend.main:app --reload

# Test agent endpoint
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "show my top 5 holdings"}'

# Deploy (auto on push)
git add . && git commit -m "description" && git push
```

## Environment Variables
- ANTHROPIC_API_KEY (required)
- AERONDIGHT_API_URL (optional, for real stock scores)
- AERONDIGHT_API_KEY (optional, for real stock scores)

## Important Rules
- Do NOT put any real API keys or Aerondight model logic in the codebase — this repo is PUBLIC
- stock_scorer.py and regime.py contain mock data only; real API integration is via env vars
- Push frequently — Railway auto-deploys and we test on the live URL
- Keep the agent loop max 5 steps per plan
- All tool functions use @tool decorator from langchain_core.tools

## Immediate Next Step
Get the /agent/run endpoint working end-to-end:
1. Run locally with `uvicorn backend.main:app --reload`
2. Test with: POST /agent/run {"message": "show my top 5 holdings"}
3. Debug any import errors or LangGraph wiring issues
4. Once working locally, push to deploy
