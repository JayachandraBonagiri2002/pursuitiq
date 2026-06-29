"""
main.py — PursuitIQ FastAPI Server

This is the entry point. Run it with:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health                    → Check server is running
    POST /api/pursuit/demo          → Run demo with built-in banking RFP
    POST /api/rfp/upload            → Upload your own RFP PDF
    GET  /api/pursuit/{rfp_id}      → Check progress + get results
    GET  /api/pursuits              → List all pursuits
"""

import logging
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── In-memory state (holds all pursuit results while server is running) ────────
pursuit_store: dict[str, dict[str, Any]] = {}
vector_store_id: str = ""


# ── App startup: initialise the vector store ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts."""
    global vector_store_id
    logger.info("PursuitIQ starting up...")
    from corpus.vector_store import get_or_create
    vector_store_id = get_or_create()
    logger.info(f"Ready. Vector Store: {vector_store_id}")
    yield
    logger.info("PursuitIQ shutting down.")


# ── Create the FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(
    title="PursuitIQ",
    description="Agentic Pursuit Intelligence Platform — HCLTech × OpenAI Hackathon",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (Next.js on port 3000) to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 1. Health check ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Open this in your browser to confirm the server is running."""
    return {
        "status":          "running ✅",
        "vector_store":    vector_store_id or "not ready",
        "active_pursuits": len(pursuit_store),
    }


# ── 2. Start demo pursuit (no PDF needed) ────────────────────────────────────
@app.post("/api/pursuit/demo")
async def start_demo(background_tasks: BackgroundTasks):
    """
    Kick off a full pursuit using the built-in Nordbank AG banking RFP.
    Use this for the demo video — no file upload needed.
    """
    rfp_id = "RFP-DEMO-001"

    pursuit_store[rfp_id] = _empty_pursuit(rfp_id, "Nordbank_AG_RFP.pdf")
    background_tasks.add_task(_run_demo_pipeline, rfp_id)

    return {
        "rfp_id":  rfp_id,
        "status":  "started",
        "message": "Poll GET /api/pursuit/RFP-DEMO-001 to see live progress.",
    }


# ── 3. Upload your own RFP (PDF or DOCX) ─────────────────────────────────────
@app.post("/api/rfp/upload")
async def upload_rfp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload an RFP as PDF or DOCX. Triggers the full 6-agent pipeline."""
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith(".pdf") or filename_lower.endswith(".docx")):
        raise HTTPException(400, "Only PDF and DOCX files are accepted.")

    rfp_id    = "RFP-" + str(uuid.uuid4())[:6].upper()
    file_bytes = await file.read()

    pursuit_store[rfp_id] = _empty_pursuit(rfp_id, file.filename)
    background_tasks.add_task(_run_upload_pipeline, rfp_id, file_bytes, file.filename)

    return {
        "rfp_id":  rfp_id,
        "status":  "started",
        "message": f"Poll GET /api/pursuit/{rfp_id} to see live progress.",
    }


# ── 4. Get pursuit status and results ─────────────────────────────────────────
@app.get("/api/pursuit/{rfp_id}")
async def get_pursuit(rfp_id: str):
    """
    Poll this to check progress.
    Status values: started → running → agent1_complete → ... → complete → error
    """
    if rfp_id not in pursuit_store:
        raise HTTPException(404, f"No pursuit found with ID: {rfp_id}")
    return pursuit_store[rfp_id]


# ── 5. List all pursuits ──────────────────────────────────────────────────────
@app.get("/api/pursuits")
async def list_pursuits():
    return [
        {"rfp_id": p["rfp_id"], "filename": p["filename"], "status": p["status"]}
        for p in pursuit_store.values()
    ]


# ── 6. Export proposal as DOCX ────────────────────────────────────────────────
@app.get("/api/pursuit/{rfp_id}/export")
async def export_proposal(rfp_id: str):
    """
    Download the generated proposal as a professional Word document (.docx).
    Only available after the pipeline is complete.
    """
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


# ── Background tasks ──────────────────────────────────────────────────────────

async def _run_demo_pipeline(rfp_id: str):
    """Runs the full pipeline using the built-in demo RFP."""
    try:
        from agents.agent1_decomposer import DEMO_RFP
        await _run_pipeline(rfp_id, DEMO_RFP)
    except Exception as e:
        logger.exception(f"[{rfp_id}] Demo pipeline failed")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"]  = str(e)


async def _run_upload_pipeline(rfp_id: str, file_bytes: bytes, filename: str):
    """Extracts text from uploaded PDF or DOCX then runs the full pipeline."""
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
        pursuit_store[rfp_id]["error"]  = str(e)


async def _run_pipeline(rfp_id: str, rfp_text: str):
    """Runs all 6 agents. Updates pursuit_store at each step so frontend can show live progress."""
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empty_pursuit(rfp_id: str, filename: str) -> dict:
    return {
        "rfp_id":         rfp_id,
        "filename":       filename,
        "status":         "started",
        "current_agent":  None,
        "decomposition":  None,
        "win_intel":      None,
        "client_intel":   None,
        "competitor":     None,
        "solution_pricing": None,
        "draft":          None,
        "win_probability": None,
        "recommended_price": None,
        "error":          None,
    }