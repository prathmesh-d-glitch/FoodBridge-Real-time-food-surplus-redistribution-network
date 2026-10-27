import base64
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from shared.auth import get_current_user, require_role
from shared.events import get_event_bus
from shared.geo import encode_geohash
from shared.logging_setup import get_correlation_id, setup_logger
from shared.models import (
    DonorListing,
    ListingStatus,
    PhotoAnalysisResult,
    UserProfile,
    UserRole,
)
from shared.spoilage import compute_safe_until
from app.repository import ListingRepository
from app.schemas import (
    AnalyzePhotoRequest,
    CreateListingRequest,
    UpdateListingStatusRequest,
)
from app.vision import analyze_food_photo

logger = setup_logger("listing_routes")
router = APIRouter()
repo = ListingRepository()
event_bus = get_event_bus()


@router.post("/listings", response_model=DonorListing, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: CreateListingRequest,
    current_user: UserProfile = Depends(require_role(UserRole.DONOR, UserRole.ADMIN)),
) -> DonorListing:
    """Creates a new surplus food listing, computes spoilage timeline, analyses photo,
    and publishes listing.created event to trigger the matching engine.
    """
    listing_id = f"list_{uuid.uuid4().hex[:12]}"

    # Compute spoilage-aware safe_until deadline
    safe_until = compute_safe_until(
        category=payload.category,
        prepared_at=payload.prepared_at,
        storage=payload.storage_condition,
    )

    # Encode spatial geohash for range indexing
    geohash = encode_geohash(
        lat=payload.location.latitude,
        lon=payload.location.longitude,
        precision=6,
    )

    # Perform Gemini AI photo analysis if photo or base64 provided
    photo_analysis: Optional[PhotoAnalysisResult] = None
    if payload.photo_base64:
        try:
            b64_str = payload.photo_base64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]  # strip "data:image/jpeg;base64," prefix
            raw_bytes = base64.b64decode(b64_str)
            photo_analysis = analyze_food_photo(image_bytes=raw_bytes, photo_hint=payload.title)
        except Exception as e:
            logger.warning(f"Could not decode photo_base64: {e}")
    elif payload.photo_url:
        photo_analysis = analyze_food_photo(photo_url=payload.photo_url, photo_hint=payload.title)

    listing = DonorListing(
        id=listing_id,
        donor_id=current_user.uid,
        donor_name=current_user.name,
        title=payload.title,
        description=payload.description or "",
        category=payload.category,
        storage_condition=payload.storage_condition,
        dietary_type=payload.dietary_type,
        quantity_kg=payload.quantity_kg,
        portions=payload.portions,
        prepared_at=payload.prepared_at,
        safe_until=safe_until,
        location=payload.location,
        geohash=geohash,
        photo_url=payload.photo_url,
        photo_analysis=photo_analysis,
        status=ListingStatus.AVAILABLE,
    )

    # Save to database
    repo.create(listing)

    # Publish listing.created event to trigger matching engine
    event_bus.publish(
        topic="listing.created",
        data={
            "listing_id": listing.id,
            "donor_id": listing.donor_id,
            "category": listing.category.value,
            "dietary_type": listing.dietary_type.value,
            "quantity_kg": listing.quantity_kg,
            "portions": listing.portions,
            "location": listing.location.model_dump(),
            "geohash": listing.geohash,
            "safe_until": listing.safe_until.isoformat(),
            "prepared_at": listing.prepared_at.isoformat(),
        },
    )

    logger.info(f"Listing {listing.id} created successfully and emitted 'listing.created'")
    return listing


@router.get("/listings", response_model=List[DonorListing])
def list_listings(
    status: Optional[ListingStatus] = Query(None, description="Filter by status"),
    donor_id: Optional[str] = Query(None, description="Filter by donor ID"),
    limit: int = Query(50, ge=1, le=200),
) -> List[DonorListing]:
    """Retrieves listings matching the specified filters."""
    return repo.list_all(status=status, donor_id=donor_id, limit=limit)


@router.get("/listings/{listing_id}", response_model=DonorListing)
def get_listing(listing_id: str) -> DonorListing:
    """Fetch details of a single surplus listing."""
    listing = repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.patch("/listings/{listing_id}/status", response_model=DonorListing)
def update_status(
    listing_id: str,
    payload: UpdateListingStatusRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> DonorListing:
    """Updates the status of a listing (e.g. claimed, picked_up, completed)."""
    listing = repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    updates = {"status": payload.status.value, "updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.claimed_by_ngo_id:
        updates["claimed_by_ngo_id"] = payload.claimed_by_ngo_id
    if payload.assigned_volunteer_id:
        updates["assigned_volunteer_id"] = payload.assigned_volunteer_id

    updated = repo.update(listing_id, updates)
    return updated


@router.post("/listings/analyze-photo")
def analyze_photo_endpoint(
    payload: AnalyzePhotoRequest,
):
    """Dedicated endpoint for UI to get Gemini AI photo analysis.
    Returns 503 if Gemini API key is missing or call fails.
    """
    raw_bytes = None
    if payload.photo_base64:
        try:
            b64_str = payload.photo_base64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_str)
        except Exception as e:
            logger.warning(f"Error decoding photo: {e}")

    result = analyze_food_photo(
        image_bytes=raw_bytes,
        photo_url=payload.photo_url,
        photo_hint=payload.food_name_hint,
    )

    if result is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Gemini AI unavailable. Ensure GEMINI_API_KEY is set and valid.",
        )

    return result
