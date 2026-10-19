from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from shared.models import FoodCategory, StorageCondition

# Base shelf life in hours according to food safety guidelines (FSSAI / Codex Alimentarius / FDA)
SHELF_LIFE_HOURS: dict[Tuple[FoodCategory, StorageCondition], float] = {
    # Cooked meals
    (FoodCategory.COOKED_MEALS, StorageCondition.HOT_HOLD): 4.0,     # Max 4 hours hot holding >63°C
    (FoodCategory.COOKED_MEALS, StorageCondition.AMBIENT): 3.0,      # Danger zone (ambient): max 3 hours
    (FoodCategory.COOKED_MEALS, StorageCondition.CHILLED): 24.0,     # Refrigerated 0-4°C
    (FoodCategory.COOKED_MEALS, StorageCondition.FROZEN): 72.0,      # Frozen

    # Bakery & Bread
    (FoodCategory.BAKERY_BREAD, StorageCondition.AMBIENT): 36.0,
    (FoodCategory.BAKERY_BREAD, StorageCondition.CHILLED): 48.0,
    (FoodCategory.BAKERY_BREAD, StorageCondition.HOT_HOLD): 6.0,
    (FoodCategory.BAKERY_BREAD, StorageCondition.FROZEN): 168.0,

    # Raw produce (vegetables, fruits)
    (FoodCategory.RAW_PRODUCE, StorageCondition.AMBIENT): 24.0,
    (FoodCategory.RAW_PRODUCE, StorageCondition.CHILLED): 72.0,
    (FoodCategory.RAW_PRODUCE, StorageCondition.HOT_HOLD): 4.0,
    (FoodCategory.RAW_PRODUCE, StorageCondition.FROZEN): 168.0,

    # Dairy (milk, paneer, yogurt)
    (FoodCategory.DAIRY, StorageCondition.CHILLED): 12.0,
    (FoodCategory.DAIRY, StorageCondition.AMBIENT): 3.0,
    (FoodCategory.DAIRY, StorageCondition.HOT_HOLD): 2.0,
    (FoodCategory.DAIRY, StorageCondition.FROZEN): 48.0,

    # Packaged goods
    (FoodCategory.PACKAGED_GOODS, StorageCondition.AMBIENT): 72.0,
    (FoodCategory.PACKAGED_GOODS, StorageCondition.CHILLED): 120.0,
    (FoodCategory.PACKAGED_GOODS, StorageCondition.HOT_HOLD): 6.0,
    (FoodCategory.PACKAGED_GOODS, StorageCondition.FROZEN): 240.0,

    # Desserts / Sweets
    (FoodCategory.DESSERTS, StorageCondition.CHILLED): 16.0,
    (FoodCategory.DESSERTS, StorageCondition.AMBIENT): 6.0,
    (FoodCategory.DESSERTS, StorageCondition.HOT_HOLD): 2.0,
    (FoodCategory.DESSERTS, StorageCondition.FROZEN): 72.0,
}


def get_shelf_life_hours(category: FoodCategory, storage: StorageCondition) -> float:
    """Retrieve standard shelf-life hours for a category and storage mode."""
    return SHELF_LIFE_HOURS.get((category, storage), 4.0)


def compute_safe_until(
    category: FoodCategory,
    prepared_at: datetime,
    storage: StorageCondition,
) -> datetime:
    """Compute the safe expiration timestamp from preparation time and storage conditions."""
    hours = get_shelf_life_hours(category, storage)
    return prepared_at + timedelta(hours=hours)


def get_remaining_shelf_life_minutes(
    safe_until: datetime,
    now: Optional[datetime] = None,
) -> float:
    """Calculate minutes remaining until food reaches safe_until threshold."""
    if now is None:
        now = datetime.now(timezone.utc)
    if safe_until.tzinfo is None:
        safe_until = safe_until.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delta = (safe_until - now).total_seconds() / 60.0
    return max(0.0, round(delta, 1))


def is_delivery_feasible(
    safe_until: datetime,
    travel_eta_minutes: float,
    handover_buffer_minutes: int = 15,
    safety_margin_minutes: int = 30,
    now: Optional[datetime] = None,
) -> Tuple[bool, float, str]:
    """Hard filter: recipient ETA + handover buffer must be < safe_until minus a safety margin.
    
    Formula:
      required_time = travel_eta_minutes + handover_buffer_minutes
      available_time = remaining_shelf_life_minutes - safety_margin_minutes
      feasible = (required_time < available_time)

    Returns:
      (feasible, slack_minutes, explanation)
    """
    remaining_shelf_life = get_remaining_shelf_life_minutes(safe_until, now=now)
    required_time = travel_eta_minutes + handover_buffer_minutes
    available_time = remaining_shelf_life - safety_margin_minutes
    slack_minutes = available_time - required_time

    if remaining_shelf_life <= 0:
        return False, 0.0, "Food has already reached safety limit (expired)"

    if available_time <= 0:
        return (
            False,
            slack_minutes,
            f"Remaining shelf life ({remaining_shelf_life:.1f}m) does not satisfy mandatory safety margin ({safety_margin_minutes}m)",
        )

    if required_time >= available_time:
        return (
            False,
            slack_minutes,
            f"Trip ETA ({travel_eta_minutes:.1f}m) + handover ({handover_buffer_minutes}m) exceeds available safe window ({available_time:.1f}m)",
        )

    return (
        True,
        round(slack_minutes, 1),
        f"Feasible with {slack_minutes:.1f}m safe slack margin remaining upon delivery",
    )
