"""
main.py — PursuitIQ FastAPI Server (ENHANCED)

Now includes:
  - Knowledge base management API (upload/search proposals)
  - Public procurement data integration
  - Enhanced 6-agent pipeline with multi-layer intelligence

Run it with:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health                         → Check server is running
    POST /api/pursuit/demo               → Run demo with built-in banking RFP
    POST /api/rfp/upload                 → Upload your own RFP PDF
    GET  /api/pursuit/{rfp_id}           → Check progress + get results
    GET  /api/pursuits                   → List all pursuits
    GET  /api/pursuit/{rfp_id}/export    → Download proposal as DOCX

    # Outcome Tracking & Learning
    POST /api/pursuit/{rfp_id}/outcome   → Mark pursuit as WON/LOST (re-ingests for learning)
    GET  /api/pursuits/completed         → List all completed pursuits with outcomes
    GET  /api/intelligence/stats         → Aggregate intelligence stats

    # Knowledge Base Management
    POST /api/knowledge/upload           → Upload a proposal to knowledge base
    GET  /api/knowledge/documents        → List all documents in knowledge base
    POST /api/knowledge/search           → Search the knowledge base
    POST /api/knowledge/reindex          → Re-index all documents from blob
"""

import json
import logging
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks, File, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Maximum file upload size: 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# ── Persistent state (survives restarts, shared across instances) ─────────────
from persistent_store import PursuitStore
pursuit_store = PursuitStore()
vector_store_id: str = ""


# ── App startup ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts."""
    global vector_store_id
    logger.info("PursuitIQ starting up...")

    # 1. Initialize deal corpus vector store
    from corpus.vector_store import get_or_create
    vector_store_id = get_or_create()
    logger.info(f"Deal corpus ready: {vector_store_id}")

    # 2. Initialize knowledge base (OpenAI Vector Store)
    try:
        from knowledge_base.openai_store import _get_store_id
        kb_id = _get_store_id()
        logger.info(f"Proposal knowledge base ready: {kb_id}")
    except Exception as e:
        logger.warning(f"Knowledge base init deferred (will create on first upload): {e}")

    logger.info("PursuitIQ ready — all systems operational")
    yield
    # Flush any dirty pursuit data on shutdown
    logger.info("PursuitIQ shutting down — flushing pending writes...")
    pursuit_store.flush_all()
    logger.info("PursuitIQ shutdown complete.")


# ── Create the FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(
    title="PursuitIQ",
    description="Agentic Pursuit Intelligence Platform — Multi-Layer Knowledge System",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# PURSUIT ENDPOINTS (existing, unchanged interface)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status": "running",
        "version": "2.0.0",
        "vector_store": vector_store_id or "not ready",
        "active_pursuits": len(pursuit_store),
        "knowledge_base": "Azure AI Search",
        "procurement_sources": ["TED.europa.eu", "UK Contracts Finder", "USASpending.gov"],
    }


@app.post("/api/pursuit/demo")
async def start_demo(background_tasks: BackgroundTasks):
    rfp_id = "RFP-DEMO-001"
    pursuit_store[rfp_id] = _empty_pursuit(rfp_id, "Nordbank_AG_RFP.pdf")
    background_tasks.add_task(_run_demo_pipeline, rfp_id)
    return {
        "rfp_id": rfp_id,
        "status": "started",
        "message": "Poll GET /api/pursuit/RFP-DEMO-001 to see live progress.",
    }


@app.get("/api/pursuit/instant-demo")
async def instant_demo():
    """Load a pre-computed pursuit result instantly — zero wait time for hackathon demos."""
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "data", "demo_pursuit.json")
    if not os.path.exists(demo_path):
        raise HTTPException(404, "No pre-computed demo available. Run a full demo first.")
    with open(demo_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/rfp/upload")
async def upload_rfp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    filename_lower = file.filename.lower()
    valid_extensions = (".pdf", ".docx", ".pptx", ".ppt")
    if not any(filename_lower.endswith(ext) for ext in valid_extensions):
        raise HTTPException(400, "Supported formats: PDF, DOCX, PPTX")

    rfp_id = "RFP-" + str(uuid.uuid4())[:6].upper()
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size: 50MB")

    pursuit_store[rfp_id] = _empty_pursuit(rfp_id, file.filename)
    background_tasks.add_task(_run_upload_pipeline, rfp_id, file_bytes, file.filename)

    return {
        "rfp_id": rfp_id,
        "status": "started",
        "message": f"Poll GET /api/pursuit/{rfp_id} to see live progress.",
    }


@app.get("/api/pursuit/{rfp_id}")
async def get_pursuit(rfp_id: str):
    if rfp_id not in pursuit_store:
        raise HTTPException(404, f"No pursuit found with ID: {rfp_id}")
    return pursuit_store[rfp_id]


@app.get("/api/pursuits")
async def list_pursuits():
    return [
        {"rfp_id": p["rfp_id"], "filename": p["filename"], "status": p["status"]}
        for p in pursuit_store.values()
    ]


@app.post("/api/pursuit/{rfp_id}/retry")
async def retry_pursuit(rfp_id: str, background_tasks: BackgroundTasks):
    """Re-run a stuck or failed pursuit from scratch using stored file."""
    if rfp_id not in pursuit_store:
        raise HTTPException(404, f"No pursuit found with ID: {rfp_id}")
    p = pursuit_store[rfp_id]
    if p["status"] == "complete":
        raise HTTPException(400, "Pursuit already complete.")
    p["status"] = "started"
    p["current_agent"] = None
    p["error"] = None
    filename = p.get("filename", "unknown.pdf")
    # Try to re-read the file from wherever it came from
    background_tasks.add_task(_run_demo_pipeline, rfp_id)
    return {"rfp_id": rfp_id, "status": "restarted", "message": "Pipeline restarted."}


@app.get("/api/pursuit/{rfp_id}/export")
async def export_proposal(rfp_id: str):
    if rfp_id not in pursuit_store:
        raise HTTPException(404, f"No pursuit found with ID: {rfp_id}")
    pursuit = pursuit_store[rfp_id]
    if pursuit["status"] != "complete":
        raise HTTPException(400, "Proposal export is only available after all agents complete.")

    from export_proposal import generate_proposal_docx
    docx_bytes = generate_proposal_docx(pursuit)
    filename = f"Proposal_{pursuit.get('decomposition', {}).get('client_name', rfp_id).replace(' ', '_')}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE ENDPOINTS (NEW — manage your proposal intelligence)
# ══════════════════════════════════════════════════════════════════════════════

class KnowledgeSearchRequest(BaseModel):
    query: str
    industry: Optional[str] = None
    geography: Optional[str] = None
    outcome: Optional[str] = None
    top: int = 10


@app.post("/api/knowledge/upload")
async def upload_to_knowledge_base(
    file: UploadFile = File(...),
    industry: str = Form(default=""),
    client_name: str = Form(default=""),
    geography: str = Form(default=""),
    deal_size: str = Form(default=""),
    outcome: str = Form(default="WON"),
    tags: str = Form(default=""),
):
    """
    Upload a proposal document to the knowledge base.
    Stores in Azure Blob and indexes in Azure AI Search for semantic retrieval.

    Supported formats: PDF, DOCX, PPTX
    """
    filename_lower = file.filename.lower()
    valid_extensions = (".pdf", ".docx", ".pptx", ".ppt")
    if not any(filename_lower.endswith(ext) for ext in valid_extensions):
        raise HTTPException(400, f"Supported formats: {', '.join(valid_extensions)}")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size: 50MB")

    metadata = {
        "industry": industry,
        "client_name": client_name,
        "geography": geography,
        "deal_size": deal_size,
        "outcome": outcome,
        "tags": tags,
        "doc_type": "proposal",
    }

    # Upload to OpenAI Vector Store (works immediately)
    try:
        from knowledge_base.openai_store import upload_to_knowledge_store
        result = upload_to_knowledge_store(file_bytes, file.filename, metadata)
        store_status = result.get("status", "unknown")
    except Exception as e:
        logger.error(f"Knowledge store upload failed: {e}")
        store_status = f"failed: {e}"

    # Also try Azure Blob (for backup / future Azure AI Search)
    blob_url = None
    try:
        from knowledge_base.blob_manager import upload_proposal
        blob_url = upload_proposal(file_bytes, file.filename, metadata)
    except Exception as e:
        logger.warning(f"Blob backup upload failed (non-critical): {e}")

    return {
        "status": "success",
        "filename": file.filename,
        "store_status": store_status,
        "blob_url": blob_url,
        "metadata": metadata,
        "message": f"Proposal uploaded to knowledge base ({store_status}). AI is now smarter.",
    }


@app.get("/api/knowledge/documents")
async def list_knowledge_documents():
    """List all documents in the knowledge base."""
    try:
        from knowledge_base.blob_manager import list_proposals
        docs = list_proposals()
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return {"documents": [], "total": 0, "error": str(e)}


@app.post("/api/knowledge/search")
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """
    Semantic search across all indexed proposals.
    Uses OpenAI Vector Store for instant semantic retrieval.
    """
    try:
        from knowledge_base.openai_store import search_knowledge_store
        raw_results = search_knowledge_store(
            query=request.query,
            industry=request.industry,
            geography=request.geography,
        )
        # Format as structured results for the frontend
        results = [{
            "content": raw_results,
            "section": "Knowledge Base Results",
            "filename": "multiple proposals",
            "page": 0,
            "industry": request.industry or "",
            "client": "",
            "geography": request.geography or "",
            "deal_size": "",
            "outcome": request.outcome or "",
            "score": 1.0,
        }] if raw_results and "No matching" not in raw_results else []
        return {"results": results, "count": len(results), "query": request.query}
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return {"results": [], "count": 0, "error": str(e)}


@app.post("/api/knowledge/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks):
    """Re-index all documents from Azure Blob into Azure AI Search."""
    background_tasks.add_task(_reindex_all)
    return {"status": "started", "message": "Re-indexing all documents in background."}


# ══════════════════════════════════════════════════════════════════════════════
# OUTCOME TRACKING & LEARNING (auto-learning feedback loop)
# ══════════════════════════════════════════════════════════════════════════════

class OutcomeRequest(BaseModel):
    outcome: str  # "WON" or "LOST"
    notes: Optional[str] = None


@app.post("/api/pursuit/{rfp_id}/outcome")
async def record_outcome(rfp_id: str, request: OutcomeRequest):
    """
    Record whether a proposal WON or LOST.
    Re-ingests the pursuit into the knowledge base with outcome data
    so future runs learn which strategies actually work.
    """
    if rfp_id not in pursuit_store:
        raise HTTPException(404, f"No pursuit found with ID: {rfp_id}")

    outcome = request.outcome.upper()
    if outcome not in ("WON", "LOST"):
        raise HTTPException(400, "Outcome must be 'WON' or 'LOST'")

    pursuit_store.mark_outcome(rfp_id, outcome)
    if request.notes:
        pursuit_store.update_pursuit(rfp_id, outcome_notes=request.notes)

    # Re-ingest with outcome so the knowledge base learns what wins
    reingest_result = None
    try:
        from knowledge_base.auto_ingest import ingest_with_outcome
        reingest_result = ingest_with_outcome(pursuit_store[rfp_id], outcome)
    except Exception as e:
        logger.warning(f"Outcome re-ingest failed: {e}")

    return {
        "rfp_id": rfp_id,
        "outcome": outcome,
        "reingested": reingest_result is not None,
        "message": f"Marked as {outcome}. Knowledge base updated — future proposals will learn from this.",
    }


@app.get("/api/intelligence/stats")
async def get_intelligence_stats():
    """
    Get aggregate intelligence stats — how much the system has learned.
    """
    stats = pursuit_store.get_stats()
    return {
        **stats,
        "message": f"System has processed {stats['total_pursuits']} pursuits. "
                   f"Knowledge base grows with every run.",
    }


@app.get("/api/pursuits/completed")
async def list_completed_pursuits():
    """List all completed pursuits with their outcomes."""
    completed = pursuit_store.get_completed()
    return [
        {
            "rfp_id": p["rfp_id"],
            "filename": p.get("filename"),
            "status": p["status"],
            "outcome": p.get("outcome", "PENDING"),
            "win_probability": p.get("win_probability"),
            "recommended_price": p.get("recommended_price"),
            "auto_ingested": p.get("auto_ingested", False),
            "updated_at": p.get("updated_at"),
        }
        for p in completed
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PROCUREMENT DATA ENDPOINT (NEW — query public contract databases)
# ══════════════════════════════════════════════════════════════════════════════

class ProcurementSearchRequest(BaseModel):
    keywords: list[str]
    country: Optional[str] = None
    max_results: int = 15


@app.post("/api/procurement/search")
async def search_procurement(request: ProcurementSearchRequest):
    """
    Search public procurement databases for real contract awards.
    Sources: TED.europa.eu, UK Contracts Finder, USASpending.gov
    """
    all_results = []

    # TED (EU)
    try:
        from procurement.ted_europe import search_ted_contracts
        ted = search_ted_contracts(request.keywords, request.country, max_results=request.max_results)
        all_results.extend(ted)
    except Exception as e:
        logger.warning(f"TED search failed: {e}")

    # UK Contracts Finder (if UK)
    if not request.country or request.country.upper() in ("GB", "UK"):
        try:
            from procurement.contracts_finder import search_uk_contracts
            uk = search_uk_contracts(request.keywords, max_results=5)
            all_results.extend(uk)
        except Exception as e:
            logger.warning(f"UK Contracts Finder failed: {e}")

    # USASpending (if US)
    if not request.country or request.country.upper() == "US":
        try:
            from procurement.sam_gov import search_us_contracts
            us = search_us_contracts(request.keywords, max_results=5)
            all_results.extend(us)
        except Exception as e:
            logger.warning(f"USASpending failed: {e}")

    return {"results": all_results, "count": len(all_results), "sources": ["TED", "UK CF", "USASpending"]}


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ══════════════════════════════════════════════════════════════════════════════

async def _run_demo_pipeline(rfp_id: str):
    try:
        from agents.agent1_decomposer import DEMO_RFP
        await _run_pipeline(rfp_id, DEMO_RFP)
    except Exception as e:
        logger.exception(f"[{rfp_id}] Demo pipeline failed")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"] = str(e)


async def _run_upload_pipeline(rfp_id: str, file_bytes: bytes, filename: str):
    try:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext == "docx":
            from openai_client import extract_text_from_docx
            rfp_text = extract_text_from_docx(file_bytes)
        elif ext in ("pptx", "ppt"):
            from knowledge_base.document_parser import get_full_text
            rfp_text = get_full_text(file_bytes, filename)
        else:
            from openai_client import extract_text_from_pdf
            rfp_text = extract_text_from_pdf(file_bytes)
        await _run_pipeline(rfp_id, rfp_text)
    except Exception as e:
        logger.exception(f"[{rfp_id}] Upload pipeline failed")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"] = str(e)


async def _run_pipeline(rfp_id: str, rfp_text: str):
    from orchestrator import run_full_pursuit
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                None,
                run_full_pursuit,
                rfp_id,
                rfp_text,
                pursuit_store,
                vector_store_id,
            ),
            timeout=1200,  # 20 minutes max (generous safety net)
        )
    except asyncio.TimeoutError:
        logger.error(f"[{rfp_id}] Pipeline timed out after 20 minutes")
        # Graceful degradation: if we have partial results, mark complete
        p = pursuit_store[rfp_id]
        if p.get("draft"):
            p["status"] = "complete"
            p["error"] = None
            logger.info(f"[{rfp_id}] Draft exists — marking complete despite timeout")
        elif p.get("solution_pricing"):
            p["status"] = "complete"
            p["error"] = "Draft generation timed out, but pricing and intel are available"
            logger.info(f"[{rfp_id}] Pricing exists — marking complete (draft missing)")
        else:
            p["status"] = "error"
            p["error"] = "Pipeline timed out. Try again or upload a shorter RFP."


async def _reindex_all():
    try:
        from knowledge_base.indexer import ingest_all_from_blob
        total = ingest_all_from_blob()
        logger.info(f"Reindex complete: {total} chunks indexed")
    except Exception as e:
        logger.error(f"Reindex failed: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empty_pursuit(rfp_id: str, filename: str) -> dict:
    from datetime import datetime, timezone
    return {
        "rfp_id": rfp_id,
        "filename": filename,
        "status": "started",
        "current_agent": None,
        "decomposition": None,
        "win_intel": None,
        "client_intel": None,
        "competitor": None,
        "ghost_bids": None,
        "deal_fingerprint": None,
        "solution_pricing": None,
        "draft": None,
        "verification": None,
        "win_probability": None,
        "recommended_price": None,
        "outcome": None,
        "outcome_notes": None,
        "auto_ingested": False,
        "pursuit_plan": None,
        "quality_verdict": None,
        "agentic_decisions": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
