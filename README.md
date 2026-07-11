<div align="center">

# PursuitIQ

### Agentic Pursuit Intelligence — know how to win the deal before you bid.

*Eleven coordinated AI agents that read an RFP and hand your bid team a live win strategy: hidden disqualifiers, unstated client needs, competitor intel, and exactly how to beat them.*

</div>

---

## Overview

PursuitIQ is a multi-agent **win-strategy engine** for bid teams. Feed it an RFP and it tells you *how to win the deal* — not by writing the proposal for you, but by handing you the intelligence and strategy the best bid teams spend weeks assembling: the hidden disqualifiers buried in the document, what the client actually wants but didn't say, who else is likely bidding, how they'll price and position, and the specific moves that beat them.

Most "AI proposal" tools are a prompt wrapped around a template that spits out generic text. PursuitIQ is **genuinely agentic and strategy-first**: a planner decides *how* to pursue each deal, agents gather live market intelligence, red-team your competitors, and pressure-test their own conclusions before handing off. Intelligence is **real-time, not hardcoded** — competitor, client, and market data come from live web search and public procurement records, so your strategy is always current.

Built for HCLTech's OpenAI hackathon (Track 2: Sales Operations).

---

## The Pipeline

Eleven coordinated agents, running in parallel wherever possible — a full pursuit completes in roughly **5–8 minutes** and hands your team a complete win strategy.

| Agent | Role |
|-------|------|
| **Planner** | Autonomously decides which agents to run, what to focus on, and which competitors to research. |
| **1 · RFP Decomposer** | Extracts every requirement and surfaces the hidden disqualifiers that quietly kill bids. |
| **2 · Win Intelligence** | Builds the win strategy from your past proposals, public procurement awards, and a deal corpus. |
| **3 · Client Intelligence** | Live web search across earnings calls, exec signals, and job posts to surface what the client *really* wants. |
| **4 · Competitor War Room** | Four-source competitor read — news, real contract prices, hiring signals, and financial filings. |
| **Deal Fingerprint** | Classifies the deal into an archetype and makes a bid / no-bid recommendation. |
| **5 · Solution & Pricing** | A pricing strategy benchmarked against real competitor contracts and live cloud pricing — every number traceable. |
| **Ghost Bid** | Simulates each competitor's likely bid *before they write it* — so you know how to beat them. |
| **6 · Strategy Brief** | Assembles the intelligence into a clear, actionable win-strategy brief for the bid team. |
| **Quality Gate + Reflection** | Agents evaluate their own output and autonomously retry or deepen research. |
| **Verifier** | Anti-hallucination layer — cross-checks every claim against its data source and adjusts confidence. |

---

## Built on OpenAI

- **GPT-5.5** across the pipeline, with per-agent reasoning effort (high for decomposition, pricing, and verification).
- **Responses API + web_search** for real-time client and competitor intelligence.
- **Structured Outputs** everywhere — every agent returns typed, schema-validated data, not free text.
- **Vector Store** for deal-corpus retrieval.

---

## Stack

- **Backend** — Python · FastAPI. Eleven-agent orchestrator with parallel execution, persistent pursuit store, and DOCX export.
- **Frontend** — Next.js 16 · React 19 · Tailwind. Live pursuit dashboard and knowledge-base manager.
- **Data** — Azure Blob + Azure AI Search (proposal knowledge base), public procurement feeds, and live cloud pricing APIs.

---

## What You Can Do

- Upload an RFP PDF, or run the built-in banking-RFP demo.
- Watch the agents build your win strategy in real time, then export the strategy brief as DOCX.
- See exactly who you're up against and how to beat them — competitor moves, pricing, and positioning.
- Manage a searchable knowledge base of your past proposals to sharpen every new strategy.
- Mark pursuits **WON / LOST** — outcomes re-ingest so the system learns from every bid.

---

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env       # add your OpenAI + Azure keys
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start a pursuit.

---

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API access |
| `MODEL` | Model ID (default `gpt-5.5`) |
| `VECTOR_STORE_ID` | Deal-corpus vector store |
| `AZURE_STORAGE_CONNECTION_STRING` | Proposal document storage |
| `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_API_KEY` | Semantic retrieval over past proposals |
