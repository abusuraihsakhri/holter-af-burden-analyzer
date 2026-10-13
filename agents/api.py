"""
FastAPI REST API Server for Holter Af Burden Analyzer.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from holter_af import comprehensive_holter_analysis
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Holter Af Burden Analyzer API",
    description="Research-oriented RR analytics with an optional legacy audit API",
    version="3.0.0",
)


class ChatRequest(BaseModel):
    query: str


class HolterAnalysisRequest(BaseModel):
    rr_intervals_ms: List[float]
    af_annotations: Optional[List[bool]] = None


@app.post("/api/analyze")
def api_analyze(payload: HolterAnalysisRequest):
    if len(payload.rr_intervals_ms) > 100000:
        raise HTTPException(status_code=413, detail="Maximum 100,000 RR intervals per request")
    try:
        return comprehensive_holter_analysis(payload.rr_intervals_ms, payload.af_annotations)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "holter-af-burden-analyzer", "domain": "RR interval analysis", "version": "3.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        PHIGuard.assert_no_phi(payload.model_dump_json())
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except (SecurityException, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Input rejected by validation or identifier screening") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Input rejected by identifier screening") from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Mount after API routes so local FastAPI use shares the same browser-only UI.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "web"), html=True), name="web")
