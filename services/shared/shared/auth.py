import os
from typing import Callable, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.config import settings
from shared.logging_setup import setup_logger
from shared.models import UserProfile, UserRole, VerificationStatus

logger = setup_logger("auth")
security = HTTPBearer(auto_error=False)

# Mock tokens for local dev and simulation tests
MOCK_TOKENS = {
    "mock-donor-token": UserProfile(
        uid="donor_taj_palace",
        email="chef@tajpalace.example",
        name="Taj Palace Caterers",
        role=UserRole.DONOR,
        phone="+919876543210",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "mock-ngo-token": UserProfile(
        uid="ngo_robin_hood",
        email="ops@robinhoodarmy.example",
        name="Robin Hood Army Bangalore",
        role=UserRole.NGO,
        phone="+919876543211",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=250.0,
    ),
    "mock-volunteer-token": UserProfile(
        uid="vol_arun_kumar",
        email="arun.k@volunteer.example",
        name="Arun Kumar",
        role=UserRole.VOLUNTEER,
        phone="+919876543212",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "mock-admin-token": UserProfile(
        uid="admin_super",
        email="admin@foodbridge.org",
        name="FoodBridge System Admin",
        role=UserRole.ADMIN,
        phone="+919876543213",
        verification_status=VerificationStatus.VERIFIED,
    ),
}


def verify_firebase_token(token: str) -> UserProfile:
    """Decodes a Firebase Auth JWT token and extracts user profile and custom claims."""
    # Check mock tokens first (for zero-cloud-credentials local development)
    if token in MOCK_TOKENS:
        return MOCK_TOKENS[token]

    # Check development prefix mock format: e.g. "mock:<role>:<uid>:<name>"
    if token.startswith("mock:"):
        parts = token.split(":")
        role = UserRole(parts[1]) if len(parts) > 1 else UserRole.DONOR
        uid = parts[2] if len(parts) > 2 else "mock_user_1"
        name = parts[3] if len(parts) > 3 else "Mock User"
        return UserProfile(
            uid=uid,
            email=f"{uid}@example.com",
            name=name,
            role=role,
            verification_status=VerificationStatus.VERIFIED,
        )

    # In production, verify using firebase-admin SDK
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        role = decoded.get("role", "donor")
        return UserProfile(
            uid=decoded["uid"],
            email=decoded.get("email", ""),
            name=decoded.get("name", "User"),
            role=UserRole(role),
            verification_status=VerificationStatus(decoded.get("verification_status", "verified")),
        )
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> UserProfile:
    """FastAPI dependency to extract and verify the current authenticated user."""
    # If no token passed in dev mode, provide default mock donor for convenience
    if credentials is None:
        if settings.ENVIRONMENT == "development":
            return MOCK_TOKENS["mock-donor-token"]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return verify_firebase_token(credentials.credentials)


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory enforcing custom claim role constraints."""
    def _role_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if user.role not in allowed_roles and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{user.role}'. Required: {[r.value for r in allowed_roles]}",
            )
        return user

    return _role_checker
