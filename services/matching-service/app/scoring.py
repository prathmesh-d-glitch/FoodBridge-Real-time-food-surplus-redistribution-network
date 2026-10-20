from datetime import datetime, timezone
from typing import Optional, Tuple
from shared.config import settings
from shared.geo import estimate_travel_time_minutes, haversine_distance
from shared.logging_setup import setup_logger
from shared.models import (
    DietaryType,
    DonorListing,
    MatchScoreBreakdown,
    UserProfile,
)
from shared.spoilage import is_delivery_feasible

logger = setup_logger("scoring_engine")

# Weight coefficients specified in matching-algorithm.md
W_TIME = 0.30
W_PROX = 0.25
W_CAP = 0.15
W_DIET = 0.10
W_REL = 0.15
W_URG = 0.05


def calculate_match_score(
    listing: DonorListing,
    ngo: UserProfile,
    max_radius_km: Optional[float] = None,
    now: Optional[datetime] = None,
) -> Tuple[float, Optional[MatchScoreBreakdown], bool, str]:
    """Computes explainable 6-factor composite match score with spoilage hard-filter.
    
    Returns:
      (total_score, breakdown, is_eligible, rejection_reason)
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if max_radius_km is None:
        max_radius_km = settings.MAX_OFFER_RADIUS_KM

    # 1. Geographic Proximity & Travel Time
    if not ngo.location or not listing.location:
        return 0.0, None, False, "Missing location data for donor or recipient"

    distance_km = haversine_distance(
        listing.location.latitude,
        listing.location.longitude,
        ngo.location.latitude,
        ngo.location.longitude,
    )

    if distance_km > max_radius_km:
        return 0.0, None, False, f"Distance {distance_km:.1f}km exceeds search radius {max_radius_km}km"

    travel_eta_mins = estimate_travel_time_minutes(distance_km)

    # 2. Hard Filter: Spoilage Feasibility
    feasible, slack_mins, feasibility_reason = is_delivery_feasible(
        safe_until=listing.safe_until,
        travel_eta_minutes=travel_eta_mins,
        handover_buffer_minutes=settings.HANDOVER_BUFFER_MINUTES,
        safety_margin_minutes=settings.SAFETY_MARGIN_MINUTES,
        now=now,
    )

    if not feasible:
        return 0.0, None, False, f"Spoilage filter failed: {feasibility_reason}"

    # --- Factor Normalization [0.0 - 1.0] ---

    # Factor 1: Time Feasibility (Scale slack up to 120 minutes)
    time_feasibility = min(1.0, max(0.0, slack_mins / 120.0))

    # Factor 2: Proximity (Linear decay from 1.0 at 0km to 0.0 at max_radius_km)
    proximity = max(0.0, round(1.0 - (distance_km / max_radius_km), 4))

    # Factor 3: Capacity Fit
    ngo_capacity = ngo.capacity_kg or 50.0
    if ngo_capacity >= listing.quantity_kg:
        # Full capacity to take entire surplus
        ratio = listing.quantity_kg / ngo_capacity
        capacity_fit = min(1.0, 0.6 + 0.4 * ratio)
    else:
        # Partial capacity (penalized proportionally)
        capacity_fit = max(0.1, (ngo_capacity / listing.quantity_kg) * 0.5)

    # Factor 4: Dietary Match
    # If NGO accepts ANY or exact match
    if (
        DietaryType.ANY in ngo.dietary_preferences
        or listing.dietary_type in ngo.dietary_preferences
        or (listing.dietary_type == DietaryType.VEG and DietaryType.NON_VEG in ngo.dietary_preferences)
    ):
        dietary_match = 1.0
    else:
        # Strict mismatch (e.g. non-veg offered to strictly veg/jain recipient)
        return 0.0, None, False, f"Dietary incompatibility: Listing is {listing.dietary_type.value}"

    # Factor 5: Reliability Score (Historical handover reliability)
    reliability = min(1.0, max(0.0, ngo.reliability_score))

    # Factor 6: Need Urgency (Baseline 0.50, boosted if shelter has active demand)
    need_urgency = 0.70  # Standard active operational demand

    # Weighted Composite Score
    total_score = (
        (W_TIME * time_feasibility)
        + (W_PROX * proximity)
        + (W_CAP * capacity_fit)
        + (W_DIET * dietary_match)
        + (W_REL * reliability)
        + (W_URG * need_urgency)
    )
    total_score = round(total_score, 4)

    explanation = (
        f"Score {total_score:.3f}: TimeFeas={time_feasibility:.2f} ({slack_mins:.0f}m safe slack), "
        f"Prox={proximity:.2f} ({distance_km:.1f}km, ETA {travel_eta_mins:.0f}m), "
        f"Cap={capacity_fit:.2f} ({listing.quantity_kg}kg / {ngo_capacity}kg cap), "
        f"Diet={dietary_match:.2f}, Rel={reliability:.2f}, Urg={need_urgency:.2f}"
    )

    breakdown = MatchScoreBreakdown(
        time_feasibility=round(time_feasibility, 3),
        proximity=round(proximity, 3),
        capacity_fit=round(capacity_fit, 3),
        dietary_match=round(dietary_match, 3),
        reliability=round(reliability, 3),
        need_urgency=round(need_urgency, 3),
        total_score=total_score,
        explanation=explanation,
    )

    return total_score, breakdown, True, "Eligible"
