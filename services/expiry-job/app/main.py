import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Request
from shared.config import settings
from shared.events import get_event_bus
from shared.firestore_client import get_firestore_client
from shared.logging_setup import set_correlation_id, setup_logger
from shared.models import DonorListing, ListingStatus, OfferStatus

logger = setup_logger("expiry_job")
db = get_firestore_client()
event_bus = get_event_bus()


def scan_and_expire_listings(now: Optional[datetime] = None) -> List[str]:
    """Scans all active listings, identifies expired safe_until deadlines,
    updates statuses, cancels pending offers, and publishes listing.expired.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Query listings that are still open
    available_docs = db.query_collection("listings", filters=[("status", "==", ListingStatus.AVAILABLE.value)])
    offered_docs = db.query_collection("listings", filters=[("status", "==", ListingStatus.OFFERED.value)])

    expired_ids = []
    for doc in available_docs + offered_docs:
        try:
            listing = DonorListing(**doc)
            safe_until = listing.safe_until
            if safe_until.tzinfo is None:
                safe_until = safe_until.replace(tzinfo=timezone.utc)

            if now >= safe_until:
                logger.info(f"Listing {listing.id} has expired (safe_until: {safe_until.isoformat()})")
                # 1. Update listing status
                db.update_document(
                    "listings",
                    listing.id,
                    {"status": ListingStatus.EXPIRED.value, "updated_at": now.isoformat()},
                )

                # 2. Cancel any pending offers
                open_offers = db.query_collection(
                    "offers",
                    filters=[("listing_id", "==", listing.id), ("status", "==", OfferStatus.OFFERED.value)],
                )
                for off in open_offers:
                    db.update_document("offers", off["id"], {"status": OfferStatus.CANCELLED.value})

                # 3. Emit listing.expired event
                event_bus.publish(
                    topic="listing.expired",
                    data={
                        "listing_id": listing.id,
                        "donor_id": listing.donor_id,
                        "portions": listing.portions,
                        "quantity_kg": listing.quantity_kg,
                        "safe_until": safe_until.isoformat(),
                    },
                )
                expired_ids.append(listing.id)

        except Exception as e:
            logger.error(f"Error processing listing in expiry scanner: {e}", exc_info=True)

    return expired_ids


app = FastAPI(
    title="FoodBridge Expiry Job Service",
    description="Automated expiration scanner and escalation triggers (Cloud Scheduler)",
    version="1.0.0",
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "expiry-job"}


@app.post("/run")
def run_expiry_scan():
    """Triggered by Cloud Scheduler (e.g. every 5 minutes)."""
    expired_ids = scan_and_expire_listings()
    return {
        "status": "completed",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "expired_count": len(expired_ids),
        "expired_listing_ids": expired_ids,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.EXPIRY_JOB_PORT, reload=True)
