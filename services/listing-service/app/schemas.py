from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from shared.models import (
    DietaryType,
    FoodCategory,
    GeoPoint,
    ListingStatus,
    PhotoAnalysisResult,
    StorageCondition,
)


class CreateListingRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = Field(default="", max_length=1000)
    category: FoodCategory
    storage_condition: StorageCondition
    dietary_type: DietaryType
    quantity_kg: float = Field(..., gt=0.0)
    portions: int = Field(..., gt=0)
    prepared_at: datetime
    location: GeoPoint
    photo_url: Optional[str] = None
    photo_base64: Optional[str] = None


class UpdateListingStatusRequest(BaseModel):
    status: ListingStatus
    claimed_by_ngo_id: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None


class AnalyzePhotoRequest(BaseModel):
    photo_url: Optional[str] = None
    photo_base64: Optional[str] = None
    food_name_hint: Optional[str] = None
