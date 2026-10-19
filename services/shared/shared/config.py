import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    GCP_PROJECT_ID: str = Field(default="foodbridge-dev")
    GCP_REGION: str = Field(default="asia-south1")

    # Local ports
    PORT: int = Field(default=8000)
    LISTING_SERVICE_PORT: int = Field(default=8001)
    MATCHING_SERVICE_PORT: int = Field(default=8002)
    NOTIFICATION_SERVICE_PORT: int = Field(default=8003)
    LOGISTICS_SERVICE_PORT: int = Field(default=8004)
    ANALYTICS_SERVICE_PORT: int = Field(default=8005)
    EXPIRY_JOB_PORT: int = Field(default=8006)
    WEB_PORT: int = Field(default=5173)

    # Event bus configuration
    EVENT_BUS_TYPE: str = Field(default="in-memory")  # "in-memory" or "pubsub"
    PUBSUB_EMULATOR_HOST: str | None = Field(default=None)
    PUBSUB_PROJECT_ID: str = Field(default="foodbridge-dev")

    # Cloud Tasks
    TASK_DISPATCHER_TYPE: str = Field(default="in-memory")  # "in-memory" or "cloud-tasks"

    # Databases
    FIRESTORE_EMULATOR_HOST: str | None = Field(default=None)
    FIRESTORE_DATABASE: str = Field(default="(default)")
    GCS_BUCKET_NAME: str = Field(default="foodbridge-photos")
    STORAGE_EMULATOR_HOST: str | None = Field(default=None)

    # External APIs
    GEMINI_API_KEY: str | None = Field(default=None)
    FCM_SERVER_KEY: str | None = Field(default=None)
    SMS_PROVIDER: str = Field(default="mock")

    # Algorithm constants
    SAFETY_MARGIN_MINUTES: int = Field(default=30)
    HANDOVER_BUFFER_MINUTES: int = Field(default=15)
    CO2E_FACTOR_KG_PER_KG: float = Field(default=2.5)
    AVERAGE_MEAL_WEIGHT_KG: float = Field(default=0.35)
    MAX_OFFER_RADIUS_KM: float = Field(default=25.0)
    EXPANDED_RADIUS_KM: float = Field(default=40.0)

    # Inter-service URLs
    LISTING_SERVICE_URL: str = Field(default="http://localhost:8001")
    MATCHING_SERVICE_URL: str = Field(default="http://localhost:8002")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://localhost:8003")
    LOGISTICS_SERVICE_URL: str = Field(default="http://localhost:8004")
    ANALYTICS_SERVICE_URL: str = Field(default="http://localhost:8005")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
