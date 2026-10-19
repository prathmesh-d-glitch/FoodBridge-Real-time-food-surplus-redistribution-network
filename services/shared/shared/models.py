from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    DONOR = "donor"
    NGO = "ngo"
    VOLUNTEER = "volunteer"
    ADMIN = "admin"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class FoodCategory(str, Enum):
    COOKED_MEALS = "cooked_meals"
    BAKERY_BREAD = "bakery_bread"
    RAW_PRODUCE = "raw_produce"
    DAIRY = "dairy"
    PACKAGED_GOODS = "packaged_goods"
    DESSERTS = "desserts"


class StorageCondition(str, Enum):
    HOT_HOLD = "hot_hold"      # Kept hot (>63°C)
    AMBIENT = "ambient"        # Room temp
    CHILLED = "chilled"        # Refrigerated (0-5°C)
    FROZEN = "frozen"          # Freezer (<-18°C)


class DietaryType(str, Enum):
    VEG = "veg"
    NON_VEG = "non_veg"
    VEGAN = "vegan"
    HALAL = "halal"
    JAIN = "jain"
    ANY = "any"


class ListingStatus(str, Enum):
    AVAILABLE = "available"
    OFFERED = "offered"
    CLAIMED = "claimed"
    PICKED_UP = "picked_up"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OfferStatus(str, Enum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RouteStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None


class UserProfile(BaseModel):
    uid: str
    email: str
    name: str
    role: UserRole
    phone: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    reliability_score: float = Field(default=0.95, ge=0.0, le=1.0)
    location: Optional[GeoPoint] = None
    geohash: Optional[str] = None
    capacity_kg: Optional[float] = 100.0   # For NGOs
    dietary_preferences: List[DietaryType] = [DietaryType.ANY]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PhotoAnalysisResult(BaseModel):
    food_type: str
    estimated_portions: int
    shelf_life_hours_hint: float
    safety_flags: List[str] = []
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    source: str = "gemini"  # "gemini" or "heuristic_fallback"


class MatchScoreBreakdown(BaseModel):
    time_feasibility: float = Field(..., ge=0.0, le=1.0)
    proximity: float = Field(..., ge=0.0, le=1.0)
    capacity_fit: float = Field(..., ge=0.0, le=1.0)
    dietary_match: float = Field(..., ge=0.0, le=1.0)
    reliability: float = Field(..., ge=0.0, le=1.0)
    need_urgency: float = Field(..., ge=0.0, le=1.0)
    total_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str


class DonorListing(BaseModel):
    id: str
    donor_id: str
    donor_name: str
    title: str
    description: Optional[str] = ""
    category: FoodCategory
    storage_condition: StorageCondition
    dietary_type: DietaryType
    quantity_kg: float = Field(..., gt=0.0)
    portions: int = Field(..., gt=0)
    prepared_at: datetime
    safe_until: datetime
    location: GeoPoint
    geohash: str
    photo_url: Optional[str] = None
    photo_analysis: Optional[PhotoAnalysisResult] = None
    status: ListingStatus = ListingStatus.AVAILABLE
    current_offer_id: Optional[str] = None
    claimed_by_ngo_id: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Offer(BaseModel):
    id: str
    listing_id: str
    donor_id: str
    ngo_id: str
    ngo_name: str
    rank: int
    score: float
    score_breakdown: MatchScoreBreakdown
    status: OfferStatus = OfferStatus.OFFERED
    response_timeout_seconds: int
    offered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    responded_at: Optional[datetime] = None
    decline_reason: Optional[str] = None


class HandoverLog(BaseModel):
    id: str
    listing_id: str
    offer_id: Optional[str] = None
    volunteer_id: Optional[str] = None
    donor_id: str
    ngo_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    temperature_celsius: Optional[float] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    donor_signature_verified: bool = True
    recipient_signature_verified: bool = True


class RouteStop(BaseModel):
    stop_id: str
    stop_type: str  # "pickup" or "delivery"
    listing_id: str
    target_name: str
    location: GeoPoint
    estimated_arrival: datetime
    deadline: datetime
    completed: bool = False


class VolunteerRoute(BaseModel):
    id: str
    volunteer_id: str
    volunteer_name: str
    stops: List[RouteStop] = []
    total_distance_km: float = 0.0
    estimated_duration_mins: float = 0.0
    status: RouteStatus = RouteStatus.ASSIGNED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImpactRecord(BaseModel):
    id: str
    listing_id: str
    donor_id: str
    ngo_id: str
    quantity_kg: float
    meals_saved: int
    co2e_avoided_kg: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventMessage(BaseModel):
    event_id: str
    event_type: str  # e.g. "listing.created", "match.offered", "offer.accepted", "pickup.completed"
    correlation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]
