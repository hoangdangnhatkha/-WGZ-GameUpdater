from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import UserProfile


class AuthSession:
    """Global singleton holding the authenticated user's profile and credentials."""

    _profile: "UserProfile | None" = None
    _credentials = None          # google.oauth2.credentials.Credentials

    @classmethod
    def set(cls, profile: "UserProfile", credentials) -> None:
        cls._profile = profile
        cls._credentials = credentials

    @classmethod
    def profile(cls) -> "UserProfile | None":
        return cls._profile

    @classmethod
    def credentials(cls):
        return cls._credentials

    @classmethod
    def is_authenticated(cls) -> bool:
        c = cls._credentials
        if c is None:
            return False
        try:
            return c.valid
        except Exception:
            return False

    @classmethod
    def clear(cls) -> None:
        cls._profile = None
        cls._credentials = None
