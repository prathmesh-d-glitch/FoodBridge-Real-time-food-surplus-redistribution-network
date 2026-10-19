from typing import Any, Dict, List, Optional
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import DonorListing, ListingStatus

logger = setup_logger("listing_repository")
COLLECTION = "listings"


class ListingRepository:
    def __init__(self):
        self.db = get_firestore_client()

    def create(self, listing: DonorListing) -> DonorListing:
        data = listing.model_dump(mode="json")
        self.db.set_document(COLLECTION, listing.id, data)
        logger.info(f"Persisted listing {listing.id} in collection '{COLLECTION}'")
        return listing

    def get_by_id(self, listing_id: str) -> Optional[DonorListing]:
        data = self.db.get_document(COLLECTION, listing_id)
        if not data:
            return None
        return DonorListing(**data)

    def list_all(
        self,
        status: Optional[ListingStatus] = None,
        donor_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[DonorListing]:
        filters = []
        if status:
            filters.append(("status", "==", status.value))
        if donor_id:
            filters.append(("donor_id", "==", donor_id))

        docs = self.db.query_collection(COLLECTION, filters=filters, limit=limit)
        listings = []
        for d in docs:
            try:
                listings.append(DonorListing(**d))
            except Exception as e:
                logger.warning(f"Error parsing listing doc {d.get('id')}: {e}")
        return listings

    def update(self, listing_id: str, updates: Dict[str, Any]) -> Optional[DonorListing]:
        self.db.update_document(COLLECTION, listing_id, updates)
        return self.get_by_id(listing_id)
