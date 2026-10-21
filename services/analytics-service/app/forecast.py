from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger

logger = setup_logger("forecasting_engine")


def get_default_seasonal_multiplier(weekday: int, hour: int) -> float:
    """Prior baseline distribution for Indian commercial food surplus (catering, hostels, weddings).
    Weekday: 0=Mon ... 6=Sun
    """
    # Weekend surge (Fri=4, Sat=5, Sun=6) due to weddings & banquets
    weekend_factor = 1.45 if weekday in [4, 5, 6] else 1.0

    # Meal cycle diurnal peaks:
    # Lunch surplus window: 14:00 - 16:00 (hours 14, 15, 16)
    # Dinner / Wedding banquet surplus window: 22:00 - 01:00 (hours 22, 23, 0)
    if hour in [14, 15, 16]:
        diurnal_factor = 1.8
    elif hour in [22, 23, 0]:
        diurnal_factor = 2.4
    elif hour in [9, 10]:
        diurnal_factor = 0.8  # Breakfast
    else:
        diurnal_factor = 0.3  # Off-peak

    return round(weekend_factor * diurnal_factor, 2)


class SurplusForecaster:
    """Predicts surplus food volume (kg) per donor/weekday/hour using seasonal-average baseline + simple trend."""

    def __init__(self):
        self.db = get_firestore_client()

    def forecast_surplus(
        self,
        donor_id: Optional[str] = None,
        target_weekday: int = 4,  # Friday by default
        target_hour: int = 22,     # 10 PM banquet peak
    ) -> Dict[str, Any]:
        """Calculates expected surplus forecast with confidence bounds.
        
        Method:
          1. Historical samples matching donor and time bucket (weekday, hour +/- 1hr).
          2. Baseline seasonal mean computation.
          3. Linear trend regression slope.
          4. Category prior fusion for cold-start donors.
        """
        filters = []
        if donor_id:
            filters.append(("donor_id", "==", donor_id))

        listings = self.db.query_collection("listings", filters=filters, limit=200)

        quantities = []
        timestamps = []
        for l in listings:
            q = l.get("quantity_kg")
            created_str = l.get("created_at")
            if q is not None and created_str:
                try:
                    dt = datetime.fromisoformat(created_str)
                    # Check if matching weekday
                    if dt.weekday() == target_weekday and abs(dt.hour - target_hour) <= 1:
                        quantities.append(float(q))
                        timestamps.append(dt.timestamp())
                except Exception:
                    pass

        # Cold-start handling
        base_prior_kg = 25.0
        seasonal_multiplier = get_default_seasonal_multiplier(target_weekday, target_hour)

        if len(quantities) >= 3:
            # Baseline mean
            mean_kg = sum(quantities) / len(quantities)

            # Simple linear trend slope over time
            n = len(quantities)
            mean_t = sum(timestamps) / n
            denom = sum((t - mean_t) ** 2 for t in timestamps)
            if denom > 0:
                slope = sum((timestamps[i] - mean_t) * (quantities[i] - mean_kg) for i in range(n)) / denom
                # Project 1 week forward (604800 seconds)
                trend_adjustment = slope * 604800.0
            else:
                trend_adjustment = 0.0

            predicted_kg = max(5.0, round(mean_kg + trend_adjustment, 1))
            confidence = min(0.92, 0.60 + 0.05 * len(quantities))
            method = "empirical_seasonal_trend"
        else:
            # Bayesian shrinkage towards domain prior
            predicted_kg = round(base_prior_kg * seasonal_multiplier, 1)
            confidence = 0.65
            method = "heuristic_seasonal_prior"

        return {
            "donor_id": donor_id or "all_aggregate",
            "weekday": target_weekday,
            "hour": target_hour,
            "predicted_surplus_kg": predicted_kg,
            "expected_portions": int(predicted_kg / 0.35),
            "confidence_score": round(confidence, 2),
            "method": method,
            "seasonal_multiplier": seasonal_multiplier,
            "forecast_generated_at": datetime.now(timezone.utc).isoformat(),
        }
