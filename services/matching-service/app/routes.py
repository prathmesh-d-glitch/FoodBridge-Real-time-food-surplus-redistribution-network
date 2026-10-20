from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from shared.auth import get_current_user, require_role
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import (
    DonorListing,
    MatchScoreBreakdown,
    Offer,
    OfferStatus,
    UserProfile,
    UserRole,
)
from app.cascade import CascadeManager

logger = setup_logger("matching_routes")
router = APIRouter()
cascade = CascadeManager()
db = get_firestore_client()


class DeclineOfferRequest(BaseModel):
    reason: Optional[str] = "Capacity full or unavailable"


class RankedCandidateResponse(BaseModel):
    ngo_id: str
    ngo_name: str
    score: float
    breakdown: MatchScoreBreakdown


@router.get("/matches/{listing_id}", response_model=List[RankedCandidateResponse])
def get_ranked_matches(listing_id: str) -> List[RankedCandidateResponse]:
    """Calculates and returns ranked candidate NGOs with full score breakdowns for explainability."""
    listing_data = db.get_document("listings", listing_id)
    if not listing_data:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = DonorListing(**listing_data)
    ranked = cascade.rank_candidates(listing)

    results = []
    for ngo, score, breakdown in ranked:
        results.append(
            RankedCandidateResponse(
                ngo_id=ngo.uid,
                ngo_name=ngo.name,
                score=score,
                breakdown=breakdown,
            )
        )
    return results


@router.get("/offers/ngo/{ngo_id}", response_model=List[Offer])
def get_offers_for_ngo(
    ngo_id: str,
    status_filter: Optional[OfferStatus] = Query(None, description="Filter by offer status"),
) -> List[Offer]:
    """Retrieves all active or historical offers sent to an NGO."""
    filters = [("ngo_id", "==", ngo_id)]
    if status_filter:
        filters.append(("status", "==", status_filter.value))

    docs = db.query_collection("offers", filters=filters, order_by="-offered_at")
    offers = []
    for d in docs:
        try:
            offers.append(Offer(**d))
        except Exception as e:
            logger.warning(f"Error parsing offer {d.get('id')}: {e}")
    return offers


@router.get("/offers/{offer_id}", response_model=Offer)
def get_offer(offer_id: str) -> Offer:
    """Fetch single offer details."""
    doc = db.get_document("offers", offer_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Offer not found")
    return Offer(**doc)


@router.post("/offers/{offer_id}/accept", response_model=Offer)
def accept_offer_endpoint(
    offer_id: str,
    current_user: UserProfile = Depends(require_role(UserRole.NGO, UserRole.ADMIN)),
) -> Offer:
    """NGO accepts a surplus offer. Claims listing and triggers logistics."""
    try:
        offer, _ = cascade.accept_offer(offer_id=offer_id, ngo_id=current_user.uid)
        return offer
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/offers/{offer_id}/decline", response_model=Offer)
def decline_offer_endpoint(
    offer_id: str,
    payload: DeclineOfferRequest,
    current_user: UserProfile = Depends(require_role(UserRole.NGO, UserRole.ADMIN)),
) -> Offer:
    """NGO declines an offer. Automatically triggers cascading escalation to next rank."""
    try:
        return cascade.decline_offer(
            offer_id=offer_id,
            ngo_id=current_user.uid,
            reason=payload.reason or "",
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/events/listing-created")
def handle_listing_created_event(payload: Dict[str, Any]):
    """Push endpoint for Pub/Sub subscription on listing.created."""
    listing_id = payload.get("data", {}).get("listing_id") or payload.get("listing_id")
    if not listing_id:
        raise HTTPException(status_code=400, detail="Missing listing_id in event payload")

    offer = cascade.process_new_listing(listing_id)
    return {
        "status": "processed",
        "listing_id": listing_id,
        "offer_created": offer is not None,
        "offer_id": offer.id if offer else None,
    }
