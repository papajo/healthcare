"""Auth service — in-memory SMART on FHIR authorization.

Provides JWT-based authentication with refresh tokens, role-based access
control, and SMART on FHIR scope verification. Dev-mode in-memory store.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from src.config.settings import settings
from src.models.auth import (
    ROLE_SCOPES,
    Scope,
    TokenResponse,
    UserCreate,
    UserRecord,
    UserResponse,
)

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """In-memory auth service for development."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}
        self._blacklisted_refresh: set[str] = set()

    def register(self, user: UserCreate) -> UserRecord:
        """Register a new user. Raises ValueError on duplicate username/email."""
        # Check duplicates
        for existing in self._users.values():
            if existing.username == user.username:
                raise ValueError("Username already exists")
            if existing.email == user.email:
                raise ValueError("Email already exists")

        now = datetime.now(UTC)
        record = UserRecord(
            user_id=uuid4(),
            username=user.username,
            email=user.email,
            hashed_password=pwd_context.hash(user.password),
            full_name=user.full_name,
            role=user.role,
            created_at=now,
            is_active=True,
        )
        self._users[str(record.user_id)] = record
        logger.info("User registered: %s (%s)", record.username, record.role.value)
        return record

    def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate and return token pair. Raises ValueError on failure."""
        user = self._find_user_by_username(username)
        if user is None:
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is deactivated")
        if not pwd_context.verify(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        return self.generate_tokens(user)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Validate refresh token and issue new pair. Raises ValueError on failure."""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")

        jti = payload.get("jti")
        if jti in self._blacklisted_refresh:
            raise ValueError("Refresh token revoked")

        user_id = payload.get("sub")
        user = self._users.get(user_id)
        if user is None or not user.is_active:
            raise ValueError("User not found or deactivated")

        return self.generate_tokens(user)

    def logout(self, user_id: str) -> None:
        """Invalidate all refresh tokens for a user by blacklisting current jti."""
        user = self._users.get(user_id)
        if user is None:
            return
        if user.refresh_token_jti:
            self._blacklisted_refresh.add(user.refresh_token_jti)
        logger.info("User logged out: %s", user.username)

    def get_current_user(self, token: str) -> UserResponse:
        """Decode access JWT and return user profile. Raises ValueError on failure."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

        if payload.get("type") != "access":
            raise ValueError("Not an access token")

        user = self._users.get(payload["sub"])
        if user is None or not user.is_active:
            raise ValueError("User not found or deactivated")

        return self._to_response(user)

    def verify_scope(self, token: str, required_scope: Scope) -> bool:
        """Check that the token grants the required scope."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError:
            return False

        token_scopes = payload.get("scope", "").split()
        return required_scope.value in token_scopes

    def generate_tokens(self, user: UserRecord) -> TokenResponse:
        """Create access + refresh JWT pair."""
        now = datetime.now(UTC)
        scopes = ROLE_SCOPES.get(user.role, [])
        scope_str = " ".join(s.value for s in scopes)

        # Access token
        access_jti = str(uuid4())
        access_exp = now + timedelta(minutes=settings.access_token_expire_minutes)
        access_payload = {
            "sub": str(user.user_id),
            "role": user.role.value,
            "scope": scope_str,
            "exp": access_exp,
            "iat": now,
            "iss": "crisiscost-orchestrator",
            "jti": access_jti,
            "type": "access",
        }
        access_token = jwt.encode(
            access_payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        # Refresh token
        refresh_jti = str(uuid4())
        refresh_exp = now + timedelta(days=settings.refresh_token_expire_days)
        refresh_payload = {
            "sub": str(user.user_id),
            "role": user.role.value,
            "scope": scope_str,
            "exp": refresh_exp,
            "iat": now,
            "iss": "crisiscost-orchestrator",
            "jti": refresh_jti,
            "type": "refresh",
        }
        refresh_token = jwt.encode(
            refresh_payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        # Track current refresh jti so logout can blacklist it
        user.refresh_token_jti = refresh_jti

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            scope=scope_str,
        )

    def get_user(self, user_id: str) -> UserResponse | None:
        """Get user by ID."""
        user = self._users.get(user_id)
        if user is None:
            return None
        return self._to_response(user)

    def list_users(self) -> list[UserResponse]:
        """List all active users."""
        return [self._to_response(u) for u in self._users.values() if u.is_active]

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user. Returns True if found."""
        user = self._users.get(user_id)
        if user is None:
            return False
        user.is_active = False
        if user.refresh_token_jti:
            self._blacklisted_refresh.add(user.refresh_token_jti)
        logger.info("User deactivated: %s", user.username)
        return True

    def _find_user_by_username(self, username: str) -> UserRecord | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    @staticmethod
    def _to_response(user: UserRecord) -> UserResponse:
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            created_at=user.created_at,
            is_active=user.is_active,
        )


# Singleton
auth_service = AuthService()
