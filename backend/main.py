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

    # Knowledge Base Management
    POST /api/knowledge/upload           → Upload a proposal to knowledge base
    GET  /api/knowledge/documents        → List all documents in knowledge base
    POST /api/knowledge/search           → Search the knowledge base
    POST /api/knowledge/reindex          → Re-index all documents from blob
"""

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

# ── In-memory state ──────────────────────────────────────────────────────────
pursuit_store: dict[str, dict[str, Any]] = {}
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
    logger.info("PursuitIQ shutting down.")


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


@app.post("/api/rfp/upload")
async def upload_rfp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith(".pdf") or filename_lower.endswith(".docx")):
        raise HTTPException(400, "Only PDF and DOCX files are accepted.")

    rfp_id = "RFP-" + str(uuid.uuid4())[:6].upper()
    file_bytes = await file.read()

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
        if filename.lower().endswith(".docx"):
            from openai_client import extract_text_from_docx
            rfp_text = extract_text_from_docx(file_bytes)
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
    await loop.run_in_executor(
        None,
        run_full_pursuit,
        rfp_id,
        rfp_text,
        pursuit_store,
        vector_store_id,
    )


async def _reindex_all():
    try:
        from knowledge_base.indexer import ingest_all_from_blob
        total = ingest_all_from_blob()
        logger.info(f"Reindex complete: {total} chunks indexed")
    except Exception as e:
        logger.error(f"Reindex failed: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empty_pursuit(rfp_id: str, filename: str) -> dict:
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
        "error": None,
    }
