import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from shared.config import settings
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import ImpactRecord

logger = setup_logger("impact_calculator")
IMPACT_COLLECTION = "impact_records"


class ImpactCalculator:
    def __init__(self):
        self.db = get_firestore_client()
        self.co2e_factor = settings.CO2E_FACTOR_KG_PER_KG
        self.avg_meal_weight = settings.AVERAGE_MEAL_WEIGHT_KG

    def record_completed_pickup(
        self,
        listing_id: str,
        donor_id: str,
        ngo_id: str,
        quantity_kg: float,
        portions: Optional[int] = None,
    ) -> ImpactRecord:
        """Computes and persists environmental & hunger relief impact for a fulfilled food redistribution."""
        meals = portions if portions and portions > 0 else int(quantity_kg / self.avg_meal_weight)
        co2e = round(quantity_kg * self.co2e_factor, 2)
        rec_id = f"imp_{uuid.uuid4().hex[:12]}"

        record = ImpactRecord(
            id=rec_id,
            listing_id=listing_id,
            donor_id=donor_id,
            ngo_id=ngo_id,
            quantity_kg=round(quantity_kg, 2),
            meals_saved=meals,
            co2e_avoided_kg=co2e,
            timestamp=datetime.now(timezone.utc),
        )

        self.db.set_document(IMPACT_COLLECTION, record.id, record.model_dump(mode="json"))
        logger.info(
            f"Impact recorded: {quantity_kg}kg ({meals} meals, {co2e}kg CO2e) for listing {listing_id}"
        )
        return record

    def get_global_metrics(self) -> Dict[str, Any]:
        """Calculates platform-wide aggregate impact."""
        docs = self.db.query_collection(IMPACT_COLLECTION)
        total_kg = sum(d.get("quantity_kg", 0.0) for d in docs)
        total_meals = sum(d.get("meals_saved", 0) for d in docs)
        total_co2e = sum(d.get("co2e_avoided_kg", 0.0) for d in docs)

        return {
            "total_kg_diverted": round(total_kg, 2),
            "total_meals_saved": total_meals,
            "total_co2e_avoided_kg": round(total_co2e, 2),
            "completed_deliveries": len(docs),
            "co2e_factor_used": self.co2e_factor,
        }

    def get_donor_metrics(self, donor_id: str) -> Dict[str, Any]:
        """Calculates cumulative impact achieved by a specific donor organization."""
        docs = self.db.query_collection(IMPACT_COLLECTION, filters=[("donor_id", "==", donor_id)])
        total_kg = sum(d.get("quantity_kg", 0.0) for d in docs)
        total_meals = sum(d.get("meals_saved", 0) for d in docs)
        total_co2e = sum(d.get("co2e_avoided_kg", 0.0) for d in docs)

        return {
            "donor_id": donor_id,
            "total_kg_diverted": round(total_kg, 2),
            "total_meals_saved": total_meals,
            "total_co2e_avoided_kg": round(total_co2e, 2),
            "completed_donations": len(docs),
        }
