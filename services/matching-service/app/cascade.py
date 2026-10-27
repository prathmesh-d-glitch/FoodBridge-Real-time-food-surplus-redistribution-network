import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from shared.config import settings
from shared.events import get_event_bus
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import (
    DonorListing,
    ListingStatus,
    MatchScoreBreakdown,
    Offer,
    OfferStatus,
    UserProfile,
    UserRole,
    VerificationStatus,
)
from shared.spoilage import get_remaining_shelf_life_minutes
from app.scoring import calculate_match_score

logger = setup_logger("cascade_manager")
OFFERS_COLLECTION = "offers"
LISTINGS_COLLECTION = "listings"
USERS_COLLECTION = "users"


class CascadeManager:
    def __init__(self):
        self.db = get_firestore_client()
        self.event_bus = get_event_bus()

    def get_candidate_ngos(self) -> List[UserProfile]:
        """Fetch all verified active NGOs."""
        users = self.db.query_collection(
            USERS_COLLECTION,
            filters=[("role", "==", UserRole.NGO.value)],
        )
        candidates = []
        for u in users:
            try:
                candidates.append(UserProfile(**u))
            except Exception as e:
                logger.warning(f"Error parsing user {u.get('uid')}: {e}")
        return candidates

    def compute_response_timeout_seconds(self, safe_until: datetime, now: Optional[datetime] = None) -> int:
        """Computes cascading timeout: clamp(remaining_shelf_life * 0.10, 3 min, 15 min)."""
        rem_mins = get_remaining_shelf_life_minutes(safe_until, now=now)
        timeout_mins = rem_mins * 0.10
        # Clamp between 3 and 15 minutes
        clamped_mins = max(3.0, min(15.0, timeout_mins))
        return int(clamped_mins * 60)

    def rank_candidates(
        self,
        listing: DonorListing,
        radius_km: Optional[float] = None,
        now: Optional[datetime] = None,
    ) -> List[Tuple[UserProfile, float, MatchScoreBreakdown]]:
        """Scores and ranks all candidate NGOs for a given listing."""
        if now is None:
            now = datetime.now(timezone.utc)
        if radius_km is None:
            radius_km = settings.MAX_OFFER_RADIUS_KM

        ngos = self.get_candidate_ngos()
        scored: List[Tuple[UserProfile, float, MatchScoreBreakdown]] = []

        for ngo in ngos:
            score, breakdown, eligible, reason = calculate_match_score(
                listing=listing,
                ngo=ngo,
                max_radius_km=radius_km,
                now=now,
            )
            if eligible and breakdown:
                scored.append((ngo, score, breakdown))

        # Sort descending by composite score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def create_offer_for_candidate(
        self,
        listing: DonorListing,
        ngo: UserProfile,
        rank: int,
        score: float,
        breakdown: MatchScoreBreakdown,
        now: Optional[datetime] = None,
    ) -> Offer:
        """Instantiates and registers a cascading offer with delayed timeout task."""
        if now is None:
            now = datetime.now(timezone.utc)

        timeout_sec = self.compute_response_timeout_seconds(listing.safe_until, now=now)
        expires_at = now + timedelta(seconds=timeout_sec)
        offer_id = f"off_{uuid.uuid4().hex[:12]}"

        offer = Offer(
            id=offer_id,
            listing_id=listing.id,
            donor_id=listing.donor_id,
            ngo_id=ngo.uid,
            ngo_name=ngo.name,
            rank=rank,
            score=score,
            score_breakdown=breakdown,
            status=OfferStatus.OFFERED,
            response_timeout_seconds=timeout_sec,
            offered_at=now,
            expires_at=expires_at,
            # Listing snapshot for NGO Feed display
            listing_title=listing.title,
            listing_donor_name=listing.donor_name,
            listing_quantity_kg=listing.quantity_kg,
            listing_portions=listing.portions,
            listing_storage_condition=listing.storage_condition.value if listing.storage_condition else None,
            listing_safe_until=listing.safe_until,
            listing_photo_analysis=listing.photo_analysis,
        )

        # Save offer
        self.db.set_document(OFFERS_COLLECTION, offer.id, offer.model_dump(mode="json"))

        # Update listing status to offered
        self.db.update_document(
            LISTINGS_COLLECTION,
            listing.id,
            {
                "status": ListingStatus.OFFERED.value,
                "current_offer_id": offer.id,
            },
        )

        # Publish match.offered event for notification service
        self.event_bus.publish(
            topic="match.offered",
            data={
                "offer_id": offer.id,
                "listing_id": listing.id,
                "donor_id": listing.donor_id,
                "ngo_id": ngo.uid,
                "ngo_name": ngo.name,
                "rank": rank,
                "score": score,
                "timeout_seconds": timeout_sec,
                "expires_at": expires_at.isoformat(),
            },
        )

        # Schedule Cloud Tasks / delayed escalation timer
        self.event_bus.schedule_delayed(
            delay_seconds=timeout_sec,
            topic="offer.timeout",
            data={
                "offer_id": offer.id,
                "listing_id": listing.id,
                "rank": rank,
            },
            task_id=f"timeout_{offer.id}",
        )

        logger.info(f"Cascading offer {offer.id} (Rank {rank}) sent to {ngo.name} with {timeout_sec}s timeout")
        return offer

    def process_new_listing(self, listing_id: str) -> Optional[Offer]:
        """Triggered on 'listing.created': ranks NGOs and dispatches to rank 1."""
        listing_data = self.db.get_document(LISTINGS_COLLECTION, listing_id)
        if not listing_data:
            logger.error(f"Cannot process matching: listing {listing_id} not found")
            return None

        listing = DonorListing(**listing_data)
        ranked = self.rank_candidates(listing, radius_km=settings.MAX_OFFER_RADIUS_KM)

        if not ranked:
            # Try expanded radius
            logger.warning(f"No candidate NGOs found in {settings.MAX_OFFER_RADIUS_KM}km. Broadening to {settings.EXPANDED_RADIUS_KM}km.")
            ranked = self.rank_candidates(listing, radius_km=settings.EXPANDED_RADIUS_KM)

        if not ranked:
            logger.error(f"Candidates exhausted for listing {listing.id}! Alerting administrators.")
            self.event_bus.publish(
                topic="admin.escalation_alert",
                data={
                    "listing_id": listing.id,
                    "reason": "All candidates exhausted or out of safe radius",
                },
            )
            return None

        # Dispatch offer to Rank 1 candidate
        top_ngo, score, breakdown = ranked[0]
        return self.create_offer_for_candidate(listing, top_ngo, rank=1, score=score, breakdown=breakdown)

    def escalate_next_rank(self, listing_id: str, last_rank: int, reason: str = "timeout") -> Optional[Offer]:
        """Auto-escalates offer to rank last_rank + 1."""
        listing_data = self.db.get_document(LISTINGS_COLLECTION, listing_id)
        if not listing_data:
            return None

        listing = DonorListing(**listing_data)
        if listing.status == ListingStatus.CLAIMED or listing.status == ListingStatus.COMPLETED:
            logger.info(f"Listing {listing_id} already claimed/completed. Skipping cascade escalation.")
            return None

        ranked = self.rank_candidates(listing, radius_km=settings.MAX_OFFER_RADIUS_KM)
        next_index = last_rank  # 0-indexed: rank 1 is index 0, so next is index 1 (rank 2)

        if next_index >= len(ranked):
            # Broaden search radius
            logger.info(f"Exhausted candidates within base radius for {listing_id}. Broadening radius.")
            ranked_expanded = self.rank_candidates(listing, radius_km=settings.EXPANDED_RADIUS_KM)
            # Find candidate with highest score not yet offered
            existing_offers = self.db.query_collection(OFFERS_COLLECTION, filters=[("listing_id", "==", listing_id)])
            offered_ngo_ids = {o.get("ngo_id") for o in existing_offers}
            remaining = [c for c in ranked_expanded if c[0].uid not in offered_ngo_ids]

            if not remaining:
                logger.error(f"All candidates exhausted even with expanded radius for {listing_id}!")
                self.event_bus.publish(
                    topic="admin.escalation_alert",
                    data={
                        "listing_id": listing_id,
                        "reason": f"Candidates exhausted at rank {last_rank}. Manual admin intervention needed.",
                    },
                )
                return None

            next_ngo, score, breakdown = remaining[0]
            return self.create_offer_for_candidate(
                listing, next_ngo, rank=last_rank + 1, score=score, breakdown=breakdown
            )

        next_ngo, score, breakdown = ranked[next_index]
        return self.create_offer_for_candidate(
            listing, next_ngo, rank=last_rank + 1, score=score, breakdown=breakdown
        )

    def accept_offer(self, offer_id: str, ngo_id: str) -> Tuple[Offer, DonorListing]:
        """Handles recipient acceptance of an offer."""
        offer_data = self.db.get_document(OFFERS_COLLECTION, offer_id)
        if not offer_data:
            raise ValueError("Offer not found")

        offer = Offer(**offer_data)
        if offer.ngo_id != ngo_id:
            raise PermissionError("Offer is addressed to a different recipient")

        if offer.status != OfferStatus.OFFERED:
            raise ValueError(f"Offer is not open (status: {offer.status.value})")

        now = datetime.now(timezone.utc)
        if now > offer.expires_at:
            self.db.update_document(OFFERS_COLLECTION, offer_id, {"status": OfferStatus.TIMEOUT.value})
            raise ValueError("Offer has expired")

        # Mark offer accepted
        self.db.update_document(
            OFFERS_COLLECTION,
            offer_id,
            {"status": OfferStatus.ACCEPTED.value, "responded_at": now.isoformat()},
        )
        offer.status = OfferStatus.ACCEPTED

        # Mark listing claimed
        listing_data = self.db.get_document(LISTINGS_COLLECTION, offer.listing_id)
        listing = DonorListing(**listing_data)
        self.db.update_document(
            LISTINGS_COLLECTION,
            offer.listing_id,
            {
                "status": ListingStatus.CLAIMED.value,
                "claimed_by_ngo_id": ngo_id,
            },
        )
        listing.status = ListingStatus.CLAIMED
        listing.claimed_by_ngo_id = ngo_id

        # Cancel any other pending offers for this listing
        competing = self.db.query_collection(
            OFFERS_COLLECTION,
            filters=[("listing_id", "==", offer.listing_id), ("status", "==", OfferStatus.OFFERED.value)],
        )
        for comp in competing:
            if comp.get("id") != offer_id:
                self.db.update_document(OFFERS_COLLECTION, comp["id"], {"status": OfferStatus.CANCELLED.value})

        # Emit offer.accepted event to trigger logistics and notifications
        self.event_bus.publish(
            topic="offer.accepted",
            data={
                "offer_id": offer.id,
                "listing_id": listing.id,
                "donor_id": listing.donor_id,
                "ngo_id": ngo_id,
                "quantity_kg": listing.quantity_kg,
                "portions": listing.portions,
                "location": listing.location.model_dump(),
                "accepted_at": now.isoformat(),
            },
        )

        logger.info(f"Offer {offer_id} ACCEPTED by {ngo_id}. Emitted 'offer.accepted'")
        return offer, listing

    def decline_offer(self, offer_id: str, ngo_id: str, reason: str = "") -> Offer:
        """Handles recipient decline of an offer, escalating immediately to rank N+1."""
        offer_data = self.db.get_document(OFFERS_COLLECTION, offer_id)
        if not offer_data:
            raise ValueError("Offer not found")

        offer = Offer(**offer_data)
        if offer.ngo_id != ngo_id:
            raise PermissionError("Offer is addressed to a different recipient")

        now = datetime.now(timezone.utc)
        self.db.update_document(
            OFFERS_COLLECTION,
            offer_id,
            {
                "status": OfferStatus.DECLINED.value,
                "responded_at": now.isoformat(),
                "decline_reason": reason,
            },
        )
        offer.status = OfferStatus.DECLINED

        # Emit offer.declined
        self.event_bus.publish(
            topic="offer.declined",
            data={
                "offer_id": offer.id,
                "listing_id": offer.listing_id,
                "rank": offer.rank,
                "decline_reason": reason,
            },
        )

        # Trigger immediate cascade escalation to next rank
        self.escalate_next_rank(listing_id=offer.listing_id, last_rank=offer.rank, reason="declined")
        return offer
