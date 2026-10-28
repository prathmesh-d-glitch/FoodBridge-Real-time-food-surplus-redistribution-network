import time
import uuid
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


class PartnerApplicationRequest(BaseModel):
    name: str
    email: str
    type: str  # "donor" or "ngo"
    fssai_license: str
    address: str
    phone: Optional[str] = "+91 98765 00000"
    password: Optional[str] = "1234"

# Default pre-seeded verification requests if database collection is empty
INITIAL_VERIFICATIONS = [
    {
        "id": "req_gwl_01",
        "name": "Gwalior Heritage Palace Catering",
        "email": "gwalior.palace.donor@gmail.com",
        "type": "donor",
        "fssai_license": "10423001000542",
        "address": "Jayaji Chowk, Lashkar, Gwalior, MP",
        "phone": "+91 98765 77005",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_02",
        "name": "Gwalior Annapurna Food Bank",
        "email": "gwalior.annapurna.ngo@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474011",
        "address": "Patel Nagar, City Center, Gwalior, MP",
        "phone": "+91 98765 77002",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_03",
        "name": "Gwalior Robin Hood Relief",
        "email": "gwalior.relief.ngo@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474006",
        "address": "Mall Road, Morar Cantt, Gwalior, MP",
        "phone": "+91 98765 77003",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_04",
        "name": "Gwalior Central Banquets & Sweets",
        "email": "gwalior.banquets.donor@gmail.com",
        "type": "donor",
        "fssai_license": "10423001000889",
        "address": "Station Road, Padav, Gwalior, MP",
        "phone": "+91 98765 77006",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_05",
        "name": "Gwalior Chambal Rasoi Seva Trust",
        "email": "chambal.rasoi.gwalior@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474015",
        "address": "Mayur Nagar, Thatipur, Gwalior, MP",
        "phone": "+91 98765 77010",
        "password": "1234",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_01",
        "name": "ITC Gardenia Banquets",
        "email": "itc@gardenia.com",
        "type": "donor",
        "fssai_license": "11223344556677",
        "address": "Residency Road, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_02",
        "name": "Hasiru Dala Feeding Centre",
        "email": "hasiru@feeding.org",
        "type": "ngo",
        "fssai_license": "NGO-8829-KA",
        "address": "KR Market, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_03",
        "name": "Marriott Convention Center",
        "email": "marriott@whitefield.com",
        "type": "donor",
        "fssai_license": "11899223344551",
        "address": "Whitefield, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
]

INITIAL_ESCALATIONS = [
    {
        "id": "esc_gwl_1",
        "listing_id": "list_gwalior_wedding_feast",
        "donor": "Gwalior Heritage Palace Catering",
        "reason": "Gwalior surplus volume alert: 45kg wedding banquet matched with high priority.",
        "timestamp": "4m ago",
        "resolved": False,
    },
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
    existing_ids = {v["id"] for v in existing_ver}
    for v in INITIAL_VERIFICATIONS:
        if v["id"] not in existing_ids:
            db.set_document(VERIFICATIONS_COLLECTION, v["id"], v)

    existing_esc = db.query_collection(ESCALATIONS_COLLECTION)
    existing_esc_ids = {e["id"] for e in existing_esc}
    for e in INITIAL_ESCALATIONS:
        if e["id"] not in existing_esc_ids:
            db.set_document(ESCALATIONS_COLLECTION, e["id"], e)


@router.post("/verifications/apply")
def apply_for_verification(payload: PartnerApplicationRequest) -> Dict[str, Any]:
    """Allows a new donor or NGO to apply for verified partnership."""
    req_id = f"req_{uuid.uuid4().hex[:8]}"
    pwd = payload.password if payload.password else "1234"
    doc = {
        "id": req_id,
        "name": payload.name,
        "email": payload.email.strip().lower(),
        "type": payload.type.strip().lower(),
        "fssai_license": payload.fssai_license,
        "address": payload.address,
        "phone": payload.phone,
        "password": pwd,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)

    # Also register in user profiles as pending
    user_uid = f"{payload.type.strip().lower()}_{uuid.uuid4().hex[:6]}"
    user_doc = {
        "uid": user_uid,
        "email": payload.email.strip().lower(),
        "name": payload.name,
        "role": payload.type.strip().lower(),
        "phone": payload.phone,
        "password": pwd,
        "verification_status": "pending",
        "fssai_license": payload.fssai_license,
    }
    db.set_document("users", user_uid, user_doc)
    logger.info(f"Registered partner application {req_id} for {payload.name} ({payload.email})")
    return doc


@router.get("/verifications")
def get_verification_queue() -> List[Dict[str, Any]]:
    """Retrieves all partner organization verification requests."""
    _ensure_initial_admin_data()
    return db.query_collection(VERIFICATIONS_COLLECTION, order_by="-submitted_at")


@router.get("/verifications/status/{email}")
def get_partner_verification_status(email: str) -> Dict[str, Any]:
    """Retrieves current verification and account status for a given email."""
    norm_email = email.strip().lower()
    vers = db.query_collection(VERIFICATIONS_COLLECTION, filters=[("email", "==", norm_email)])
    if vers:
        # Return the latest one
        v = sorted(vers, key=lambda x: str(x.get("submitted_at", "")), reverse=True)[0]
        return {
            "found": True,
            "status": v.get("status", "pending"),
            "id": v.get("id"),
            "name": v.get("name"),
            "email": v.get("email"),
            "type": v.get("type"),
            "password": v.get("password", "1234"),
            "phone": v.get("phone"),
            "address": v.get("address"),
            "fssai_license": v.get("fssai_license"),
            "verified_at": v.get("verified_at"),
        }

    # Fallback to users collection
    users = db.query_collection("users", filters=[("email", "==", norm_email)])
    if users:
        u = users[0]
        return {
            "found": True,
            "status": u.get("verification_status", "verified"),
            "name": u.get("name"),
            "email": u.get("email"),
            "type": u.get("role"),
            "password": u.get("password", "1234"),
            "phone": u.get("phone"),
            "fssai_license": u.get("fssai_license"),
        }

    return {"found": False}


@router.post("/verifications/{req_id}/approve")
def approve_verification(req_id: str) -> Dict[str, Any]:
    """Approves a partner and updates verification status in database."""
    doc = db.get_document(VERIFICATIONS_COLLECTION, req_id)
    if not doc:
        doc = {"id": req_id, "status": "pending"}

    doc["status"] = "verified"
    doc["verified_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)

    # Sync verification_status across users collection
    if doc.get("email"):
        users = db.query_collection("users", filters=[("email", "==", doc["email"])])
        for u in users:
            u["verification_status"] = "verified"
            db.set_document("users", u["uid"], u)

    logger.info(f"Admin approved verification request {req_id} ({doc.get('email')})")
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

    if doc.get("email"):
        users = db.query_collection("users", filters=[("email", "==", doc["email"])])
        for u in users:
            u["verification_status"] = "rejected"
            db.set_document("users", u["uid"], u)

    logger.info(f"Admin rejected verification request {req_id} ({doc.get('email')})")
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
