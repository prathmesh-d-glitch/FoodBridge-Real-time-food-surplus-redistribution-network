import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import urllib.request
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger

logger = setup_logger("admin_routes")
router = APIRouter(prefix="/admin", tags=["admin"])
db = get_firestore_client()

VERIFICATIONS_COLLECTION = "verifications"
ESCALATIONS_COLLECTION = "escalations"

# Default pre-seeded verification requests if database collection is empty
INITIAL_VERIFICATIONS = [
    {
        "id": "req_01",
        "name": "ITC Gardenia Banquets",
        "type": "donor",
        "fssai_license": "11223344556677",
        "address": "Residency Road, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_02",
        "name": "Hasiru Dala Feeding Centre",
        "type": "ngo",
        "fssai_license": "NGO-8829-KA",
        "address": "KR Market, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_03",
        "name": "Marriott Convention Center",
        "type": "donor",
        "fssai_license": "11899223344551",
        "address": "Whitefield, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
]

INITIAL_ESCALATIONS = [
    {
        "id": "esc_101",
        "listing_id": "list_wedding_rush_3",
        "donor": "Royal Orchid Hotel",
        "reason": "No responses within 15km. Search radius broadened to 30km.",
        "timestamp": "12m ago",
        "resolved": False,
    },
    {
        "id": "esc_100",
        "listing_id": "list_lunch_rush_1",
        "donor": "Taj Caterers",
        "reason": "Rank 1 NGO response timeout. Escalated to Koramangala Kitchen.",
        "timestamp": "34m ago",
        "resolved": True,
    },
]


def _ensure_initial_admin_data():
    existing_ver = db.query_collection(VERIFICATIONS_COLLECTION)
    if not existing_ver:
        for v in INITIAL_VERIFICATIONS:
            db.set_document(VERIFICATIONS_COLLECTION, v["id"], v)

    existing_esc = db.query_collection(ESCALATIONS_COLLECTION)
    if not existing_esc:
        for e in INITIAL_ESCALATIONS:
            db.set_document(ESCALATIONS_COLLECTION, e["id"], e)


@router.get("/verifications")
def get_verification_queue() -> List[Dict[str, Any]]:
    """Retrieves all partner organization verification requests."""
    _ensure_initial_admin_data()
    return db.query_collection(VERIFICATIONS_COLLECTION, order_by="-submitted_at")


@router.post("/verifications/{req_id}/approve")
def approve_verification(req_id: str) -> Dict[str, Any]:
    """Approves a partner and updates verification status in database."""
    doc = db.get_document(VERIFICATIONS_COLLECTION, req_id)
    if not doc:
        doc = {"id": req_id, "status": "pending"}

    doc["status"] = "verified"
    doc["verified_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)
    logger.info(f"Admin approved verification request {req_id}")
    return doc


@router.post("/verifications/{req_id}/reject")
def reject_verification(req_id: str) -> Dict[str, Any]:
    """Rejects a partner verification request in database."""
    doc = db.get_document(VERIFICATIONS_COLLECTION, req_id)
    if not doc:
        doc = {"id": req_id, "status": "pending"}

    doc["status"] = "rejected"
    doc["rejected_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)
    logger.info(f"Admin rejected verification request {req_id}")
    return doc


@router.get("/escalations")
def get_escalations() -> List[Dict[str, Any]]:
    """Retrieves all matching escalation alerts."""
    _ensure_initial_admin_data()
    return db.query_collection(ESCALATIONS_COLLECTION)


@router.post("/escalations/{esc_id}/resolve")
def resolve_escalation(esc_id: str) -> Dict[str, Any]:
    """Resolves an escalation alert in the database."""
    doc = db.get_document(ESCALATIONS_COLLECTION, esc_id)
    if not doc:
        doc = {"id": esc_id, "resolved": False}

    doc["resolved"] = True
    doc["resolved_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(ESCALATIONS_COLLECTION, esc_id, doc)
    logger.info(f"Admin resolved escalation {esc_id}")
    return doc


@router.get("/health-telemetry")
def get_health_telemetry() -> Dict[str, Any]:
    """Actively probes the status and latency of all FoodBridge serverless microservices."""
    endpoints = {
        "listing-service": ("http://127.0.0.1:8001/health", 8001),
        "matching-service": ("http://127.0.0.1:8002/health", 8002),
        "notification-service": ("http://127.0.0.1:8003/health", 8003),
        "logistics-service": ("http://127.0.0.1:8004/health", 8004),
        "analytics-service": ("http://127.0.0.1:8005/health", 8005),
        "expiry-job": ("http://127.0.0.1:8006/health", 8006),
    }

    results = {}
    for name, (url, port) in endpoints.items():
        t0 = time.time()
        is_healthy = False
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FoodBridgeAdminProbe"})
            with urllib.request.urlopen(req, timeout=0.6) as response:
                if response.status == 200:
                    is_healthy = True
        except Exception:
            # Fallback if listing-service is self
            is_healthy = (name == "listing-service")

        latency_ms = round((time.time() - t0) * 1000, 1)
        results[name] = {
            "healthy": is_healthy,
            "port": port,
            "latency_ms": latency_ms if is_healthy else None,
        }

    return results
