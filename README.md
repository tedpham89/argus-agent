# Argus Agent

**Financial operations agent** — portfolio analysis, compliance monitoring, and risk assessment powered by LangGraph and Claude.

Argus takes natural language instructions about an investment portfolio, decomposes them into a multi-step plan, orchestrates tool calls against financial data sources, validates results, and surfaces findings with human-in-the-loop confirmation.

## What It Does

Ask Argus a question about your portfolio and watch it plan, execute, and synthesize:

- **"Check my portfolio for concentration risk"** → Queries holdings, retrieves compliance rules via RAG, identifies violations, recommends remediation
- **"Score NVDA and tell me if it fits my portfolio"** → Runs quantitative scoring model, checks regime context, evaluates portfolio fit
- **"What's my sector exposure vs S&P 500?"** → Aggregates holdings by sector, pulls benchmark data, generates comparison
- **"Draft a risk summary for the PM"** → Orchestrates multiple tools, synthesizes into a professional memo

## Architecture

```
User (React Chat UI)
  │
  ▼
FastAPI Backend
  │
  ▼
LangGraph State Graph
  ├── PLAN    → LLM decomposes instruction into structured steps
  ├── EXECUTE → Dispatches tool calls sequentially
  ├── VALIDATE → LLM checks completeness and consistency
  └── RESPOND → LLM synthesizes final answer
        │
        ▼
    Tool Registry
      ├── Portfolio Holdings  (SQLite)
      ├── Market Data         (yfinance)
      ├── Compliance Engine   (ChromaDB RAG)
      ├── Stock Scorer        (quantitative multi-factor model)
      └── Regime Classifier   (macro regime detection)
```

### Design Decisions

- **LangGraph for orchestration** — state machine with checkpointing and human-in-the-loop interrupts, not a simple chain
- **Built tools from scratch** — no LangChain wrappers; each tool has a clean interface compatible with MCP protocol patterns
- **Compliance via RAG** — rules are embedded in ChromaDB and retrieved contextually, mirroring how enterprise policy engines work
- **Mock + Real pattern** — stock scorer and regime tools ship with mock data in the public repo; live demo calls a private quantitative API

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet (Anthropic API) |
| Agent Framework | LangGraph |
| Backend | FastAPI + Python 3.11 |
| Vector DB | ChromaDB |
| Portfolio DB | SQLite |
| Market Data | yfinance |
| Frontend | React + Tailwind |
| Hosting | Railway |

## Local Development

```bash
# Clone and install
git clone https://github.com/tedpham89/argus-agent.git
cd argus-agent
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env with your Anthropic API key

# Run
uvicorn backend.main:app --reload
```

## Production Considerations

Things I'd change at enterprise scale:

1. **Persistent checkpointing** — swap MemorySaver for Postgres-backed checkpoint store so agent state survives restarts
2. **MCP server/client separation** — each tool becomes an independent MCP server, registered and versioned separately
3. **Observability** — structured logging of every tool call, LLM latency, and token usage via OpenTelemetry
4. **Auth + multi-tenancy** — per-user portfolios scoped via JWT auth, org-level tool permissioning
5. **Evaluation** — golden dataset with expected tool call sequences, automated regression testing on agent behavior

## License

MIT
