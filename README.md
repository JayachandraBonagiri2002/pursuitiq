# PursuitIQ

**AI-Powered Pursuit Intelligence Platform for Enterprise Sales**

PursuitIQ transforms RFP (Request for Proposal) documents into winning proposals through a 6-agent AI pipeline. It ingests RFP documents, decomposes requirements, gathers real-time market intelligence, performs competitive analysis, designs pricing strategies, and generates complete proposal drafts — all within minutes.

> Built for **HCLTech Sales Operations** (Track 2: Sales Operations)

---

## Key Features

- **6-Agent AI Pipeline** — Specialized agents for RFP decomposition, win intelligence, client intelligence, competitor analysis, pricing optimization, and proposal drafting
- **Real-Time Market Intelligence** — Live web search for competitor moves, client news, job postings, and procurement signals
- **Smart Pricing Engine** — Real-time cloud pricing from Azure and AWS APIs with margin-optimized solution options
- **Knowledge Base** — Upload past proposals (PDF/DOCX/PPTX) to build institutional memory via Azure AI Search
- **Competitive Shadow Analysis** — Predicts competitor positioning and surfaces killer differentiators
- **Quality Gate + Reflection Loop** — AI-driven verification that catches hallucinations and weak claims before output
- **Live Pipeline Tracker** — Real-time UI showing agent progress as they work
- **Proposal Export** — One-click DOCX export of the completed proposal

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 / React 19 / Tailwind CSS)   │
└──────────────────────┬─────────────────────────────┘
                       │ REST API (3s polling)
┌──────────────────────▼─────────────────────────────┐
│  Backend (FastAPI / Uvicorn ASGI)                   │
│                                                     │
│  Orchestrator ──► Agent Pipeline                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │           │
│  │   RFP   │─►│   Win   │  │ Client  │           │
│  │Decompose│  │  Intel  │  │  Intel  │           │
│  └─────────┘  └─────────┘  └─────────┘           │
│       │            │             │                 │
│       ▼       (parallel)         ▼                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Agent 4 │  │ Agent 5 │  │ Agent 6 │           │
│  │Competitor│─►│ Pricing │─►│  Draft  │           │
│  │ Shadow  │  │+Solution│  │Generator│           │
│  └─────────┘  └─────────┘  └─────────┘           │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│  External Services                                  │
│  • OpenAI GPT-4.1 (Structured Outputs + Web Search)│
│  • Azure Blob Storage (Document Store)              │
│  • Azure AI Search (Semantic Retrieval)             │
│  • Azure/AWS Pricing APIs (Live Cloud Costs)        │
└────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| AI/ML | OpenAI GPT-4.1, Structured Outputs, Web Search, File Search |
| Storage | Azure Blob Storage, Azure AI Search |
| Pricing | Azure Retail Prices API, AWS Published Rates |
| Document Parsing | pypdf, python-docx, python-pptx |

---

## Project Structure

```
pursuitiq/
├── backend/
│   ├── agents/                 # 6 specialized AI agents + planner + quality gate
│   │   ├── agent1_decomposer.py
│   │   ├── agent2_win_intel.py
│   │   ├── agent3_client_intel.py
│   │   ├── agent4_competitor.py
│   │   ├── agent5_pricing.py
│   │   ├── agent6_draft.py
│   │   ├── planner_agent.py
│   │   ├── quality_gate.py
│   │   └── reflection_loop.py
│   ├── corpus/                 # Historical deal vector store
│   ├── knowledge_base/         # Document ingestion + semantic search
│   ├── procurement/            # Live procurement source scrapers
│   │   ├── sam_gov.py          # USA (SAM.gov)
│   │   ├── ted_europe.py       # Europe (TED)
│   │   ├── contracts_finder.py # UK
│   │   ├── austender.py        # Australia
│   │   └── gebiz.py            # Singapore
│   ├── data/pursuits/          # Stored pursuit analysis results
│   ├── main.py                 # FastAPI application entry point
│   ├── orchestrator.py         # Agent pipeline orchestration
│   ├── config.py               # Environment configuration
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx            # Landing page + RFP upload
│   │   ├── pursuit/[rfp_id]/   # Pursuit dashboard (5-tab view)
│   │   └── knowledge/          # Knowledge base management
│   ├── package.json
│   └── tsconfig.json
├── Architecture.md             # Detailed system architecture
└── .env.example                # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key
- Azure Storage + AI Search (optional, for knowledge base)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## How It Works

1. **Upload RFP** — Drag and drop a PDF/DOCX/PPTX document or run the demo
2. **Agent 1: RFP Decomposer** — Extracts requirements, disqualifiers, evaluation criteria, and key dates
3. **Agents 2-4 (Parallel)** — Win intelligence searches past deals, client intelligence scrapes live web data, competitor analysis predicts rival positioning
4. **Agent 5: Solution + Pricing** — Designs 3 solution options with real-time cloud pricing from Azure/AWS APIs
5. **Agent 6: Draft Generator** — Synthesizes all intelligence into a complete proposal with architecture diagrams
6. **Quality Gate** — Verifies claims, checks for hallucinations, and scores output quality
7. **Export** — Download the final proposal as a formatted DOCX document

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rfp/upload` | Upload RFP document and start pipeline |
| POST | `/api/pursuit/demo` | Run demo with sample RFP |
| GET | `/api/pursuit/{id}` | Get pursuit status and results |
| GET | `/api/pursuit/{id}/export` | Export proposal as DOCX |
| POST | `/api/knowledge/upload` | Upload documents to knowledge base |
| GET | `/api/knowledge/documents` | List knowledge base documents |

---

## Team

Built by the HCLTech innovation team for the OpenAI Hackathon 2025.

---

## License

Proprietary - HCLTech Internal Use
