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
        email="donor@gmail.com",
        name="Taj Palace Caterers",
        role=UserRole.DONOR,
        phone="+919876543210",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "mock-ngo-token": UserProfile(
        uid="ngo_robin_hood",
        email="ngo@gmail.com",
        name="Robin Hood Army Bangalore",
        role=UserRole.NGO,
        phone="+919876543211",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=250.0,
    ),
    "mock-volunteer-token": UserProfile(
        uid="vol_arun_kumar",
        email="volunteer@gmail.com",
        name="Arun Kumar",
        role=UserRole.VOLUNTEER,
        phone="+919876543212",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "mock-admin-token": UserProfile(
        uid="admin_super",
        email="admin@gmail.com",
        name="FoodBridge System Admin",
        role=UserRole.ADMIN,
        phone="+919876543213",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-admin@gmail.com": UserProfile(
        uid="admin_super",
        email="admin@gmail.com",
        name="FoodBridge System Admin",
        role=UserRole.ADMIN,
        phone="+919876543213",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-donor@gmail.com": UserProfile(
        uid="donor_taj_palace",
        email="donor@gmail.com",
        name="Taj Palace Caterers",
        role=UserRole.DONOR,
        phone="+919876543210",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-ngo@gmail.com": UserProfile(
        uid="ngo_robin_hood",
        email="ngo@gmail.com",
        name="Robin Hood Army Bangalore",
        role=UserRole.NGO,
        phone="+919876543211",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=250.0,
    ),
    "token-volunteer@gmail.com": UserProfile(
        uid="vol_arun_kumar",
        email="volunteer@gmail.com",
        name="Arun Kumar",
        role=UserRole.VOLUNTEER,
        phone="+919876543212",
        verification_status=VerificationStatus.VERIFIED,
    ),
    # ── Gwalior Mock Accounts ──
    "token-gwalior.admin@gmail.com": UserProfile(
        uid="admin_gwalior",
        email="gwalior.admin@gmail.com",
        name="FoodBridge Gwalior Regional Admin",
        role=UserRole.ADMIN,
        phone="+919876577001",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-gwalior.annapurna.ngo@gmail.com": UserProfile(
        uid="ngo_gwalior_annapurna",
        email="gwalior.annapurna.ngo@gmail.com",
        name="Gwalior Annapurna Food Bank",
        role=UserRole.NGO,
        phone="+919876577002",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=300.0,
    ),
    "token-gwalior.ngo1@gmail.com": UserProfile(
        uid="ngo_gwalior_annapurna",
        email="gwalior.ngo1@gmail.com",
        name="Gwalior Annapurna Food Bank",
        role=UserRole.NGO,
        phone="+919876577002",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=300.0,
    ),
    "token-gwalior.relief.ngo@gmail.com": UserProfile(
        uid="ngo_gwalior_relief",
        email="gwalior.relief.ngo@gmail.com",
        name="Gwalior Robin Hood Relief",
        role=UserRole.NGO,
        phone="+919876577003",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=220.0,
    ),
    "token-gwalior.ngo2@gmail.com": UserProfile(
        uid="ngo_gwalior_relief",
        email="gwalior.ngo2@gmail.com",
        name="Gwalior Robin Hood Relief",
        role=UserRole.NGO,
        phone="+919876577003",
        verification_status=VerificationStatus.VERIFIED,
        capacity_kg=220.0,
    ),
    "token-gwalior.palace.donor@gmail.com": UserProfile(
        uid="donor_gwalior_palace",
        email="gwalior.palace.donor@gmail.com",
        name="Gwalior Heritage Palace Catering",
        role=UserRole.DONOR,
        phone="+919876577005",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-gwalior.donor1@gmail.com": UserProfile(
        uid="donor_gwalior_palace",
        email="gwalior.donor1@gmail.com",
        name="Gwalior Heritage Palace Catering",
        role=UserRole.DONOR,
        phone="+919876577005",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-gwalior.banquets.donor@gmail.com": UserProfile(
        uid="donor_gwalior_banquets",
        email="gwalior.banquets.donor@gmail.com",
        name="Gwalior Central Banquets & Sweets",
        role=UserRole.DONOR,
        phone="+919876577006",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-gwalior.donor2@gmail.com": UserProfile(
        uid="donor_gwalior_banquets",
        email="gwalior.donor2@gmail.com",
        name="Gwalior Central Banquets & Sweets",
        role=UserRole.DONOR,
        phone="+919876577006",
        verification_status=VerificationStatus.VERIFIED,
    ),
    "token-gwalior.volunteer@gmail.com": UserProfile(
        uid="vol_gwalior_vikram",
        email="gwalior.volunteer@gmail.com",
        name="Gwalior Rapid Courier Vikram",
        role=UserRole.VOLUNTEER,
        phone="+919876577004",
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

    # Check token-<email> format fallback
    if token.startswith("token-"):
        email = token.replace("token-", "").strip().lower()
        role = UserRole.DONOR
        if "admin" in email:
            role = UserRole.ADMIN
        elif "ngo" in email:
            role = UserRole.NGO
        elif "volunteer" in email or "vol" in email:
            role = UserRole.VOLUNTEER

        clean_name = email.split("@")[0].replace(".", " ").title()
        return UserProfile(
            uid=f"user_{email.replace('@', '_').replace('.', '_')}",
            email=email,
            name=clean_name,
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
