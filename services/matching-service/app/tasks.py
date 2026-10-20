from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import Offer, OfferStatus
from app.cascade import CascadeManager

logger = setup_logger("matching_tasks")
OFFERS_COLLECTION = "offers"


def handle_offer_timeout(offer_id: str, listing_id: str, rank: int) -> None:
    """Invoked when Cloud Tasks or local timer expires for a pending offer.
    If recipient did not respond in time, marks timeout and escalates to rank N+1.
    """
    db = get_firestore_client()
    offer_data = db.get_document(OFFERS_COLLECTION, offer_id)
    if not offer_data:
        logger.warning(f"Timeout handler: offer {offer_id} does not exist")
        return

    offer = Offer(**offer_data)
    if offer.status == OfferStatus.OFFERED:
        logger.info(f"Offer {offer_id} (Rank {rank}) TIMED OUT without response. Escalating.")
        db.update_document(OFFERS_COLLECTION, offer_id, {"status": OfferStatus.TIMEOUT.value})

        # Escalate to next rank
        manager = CascadeManager()
        manager.escalate_next_rank(listing_id=listing_id, last_rank=rank, reason="timeout")
    else:
        logger.info(f"Offer {offer_id} status is already '{offer.status.value}'. No timeout escalation required.")
