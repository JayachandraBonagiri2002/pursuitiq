<div align="center">

# PursuitIQ

### Agentic Pursuit Intelligence — turn any RFP into a win-ready proposal in minutes.

*Eleven coordinated AI agents that read an RFP, gather live market intelligence, price a solution, draft the proposal, and verify every claim — autonomously.*

</div>

---

## Overview

PursuitIQ is a multi-agent system that transforms a raw RFP into a win-ready proposal. It reads the document, hunts for hidden disqualifiers, gathers live client and competitor intelligence, designs a priced solution grounded in real market data, and drafts the proposal in the voice of your past winners — then verifies its own claims before handing off.

Most "AI proposal" tools are a prompt wrapped around a template. PursuitIQ is **genuinely agentic**: a planner decides *how* to pursue each deal, agents reflect on and correct their own output, and a final verifier cross-checks every claim against its source. Intelligence is **real-time, not hardcoded** — competitor, client, and market data come from live web search and public procurement records, so the analysis is never stale.

Built for HCLTech's OpenAI hackathon (Track 2: Sales Operations).

---

## The Pipeline

Eleven coordinated agents, running in parallel wherever possible — a full pursuit completes in roughly **5–8 minutes**.

| Agent | Role |
|-------|------|
| **Planner** | Autonomously decides which agents to run, what to focus on, and which competitors to research. |
| **1 · RFP Decomposer** | Extracts every requirement, with a focus on the hidden disqualifiers other tools miss. |
| **2 · Win Intelligence** | Grounds strategy in your past proposals, public procurement awards, and a deal corpus. |
| **3 · Client Intelligence** | Live web search across earnings calls, exec signals, and job posts to surface unstated needs. |
| **4 · Competitor War Room** | Four-source competitor read: news, real contract prices, hiring signals, and financial filings. |
| **Deal Fingerprint** | Classifies the deal into an archetype and makes a bid / no-bid call. |
| **5 · Solution & Pricing** | Prices against real competitor contracts and live cloud pricing — every number traceable to a source. |
| **Ghost Bid** | Simulates each competitor's likely proposal before they write it. |
| **6 · Proposal Generator** | Drafts in the tone and structure of your proven winners. |
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
- Watch the agents work in real time, then export a proposal as DOCX.
- Manage a searchable knowledge base of your past proposals.
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
