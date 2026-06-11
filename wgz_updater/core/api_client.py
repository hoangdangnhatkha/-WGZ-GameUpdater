"""HTTP client for the wgz-api backend.

Auth: pulls the OAuth2 access_token from `AuthSession` and sends it as
`Authorization: Bearer ...`. The API verifies the token against Google.
"""
from __future__ import annotations

import logging
import socket
import threading
import uuid
from typing import Any

import httpx

from .http import client as http_client
from .paths import APP_DIR, get_api_base_url, ensure_user_dirs

log = logging.getLogger(__name__)
_refresh_lock = threading.Lock()


class ApiError(RuntimeError):
    """Raised for non-2xx responses or network failures."""


def _machine_id() -> str:
    """Stable per-install machine id, persisted under APP_DIR."""
    f = APP_DIR / "machine_id.txt"
    if f.exists():
        try:
            v = f.read_text(encoding="utf-8").strip()
            if v:
                return v
        except Exception:
            log.exception("Reading machine_id.txt")
    ensure_user_dirs()
    mid = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    try:
        f.write_text(mid, encoding="utf-8")
    except Exception:
        log.exception("Writing machine_id.txt")
    return mid


def _bearer_token() -> str | None:
    """Return a fresh access_token. Auto-refreshes via refresh_token when expired.

    Thread-safe: uses a module-level lock around the refresh + persist sequence
    so two concurrent QThread workers don't both hit Google's refresh endpoint.
    """
    try:
        from ..features.auth.session import AuthSession
        creds = AuthSession.credentials()
        if creds is None:
            return None

        needs_refresh = bool(getattr(creds, "expired", False)) and bool(
            getattr(creds, "refresh_token", None)
        )
        if needs_refresh:
            with _refresh_lock:
                # Re-check inside the lock — another thread may have just refreshed.
                if creds.expired and creds.refresh_token:
                    try:
                        from google.auth.transport.requests import Request
                        from ..features.auth.google_auth import save_credentials
                        creds.refresh(Request())
                        save_credentials(creds)
                        log.info("Access token refreshed")
                    except Exception:
                        log.exception("Token refresh failed")
                        return None
        return getattr(creds, "token", None)
    except Exception:
        log.exception("Reading auth session token")
        return None


def _force_refresh() -> bool:
    """Force-refresh credentials regardless of `expired` flag. Returns True on success."""
    try:
        from ..features.auth.session import AuthSession
        from ..features.auth.google_auth import save_credentials
        from google.auth.transport.requests import Request
        creds = AuthSession.credentials()
        if not creds or not getattr(creds, "refresh_token", None):
            return False
        with _refresh_lock:
            creds.refresh(Request())
            save_credentials(creds)
        log.info("Access token force-refreshed after 401")
        return True
    except Exception:
        log.exception("Force refresh failed")
        return False


def _request(method: str, path: str, *, json: Any = None, params: dict | None = None) -> Any:
    base = get_api_base_url()
    url = f"{base}{path}"
    last_detail: Any = None
    for attempt in range(2):
        token = _bearer_token()
        if not token:
            raise ApiError("Not authenticated — no Google access token available")
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = http_client().request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=httpx.Timeout(30.0, connect=5.0),
            )
        except httpx.RequestError as exc:
            raise ApiError(f"{method} {path} → network unreachable: {exc.__class__.__name__}") from None
        if resp.status_code == 401 and attempt == 0:
            # Server rejected token (revoked / stale). Force refresh + retry once.
            if _force_refresh():
                continue
        if resp.status_code >= 400:
            try:
                last_detail = resp.json()
            except Exception:
                last_detail = {"error": resp.text}
            raise ApiError(f"{method} {path} → {resp.status_code}: {last_detail}")
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()
    raise ApiError(f"{method} {path} → 401 (refresh failed)")


# ---- Config ----
def get_config() -> dict:
    """Return raw config dict (matches CapNhatNightReignMod.json + game_themes.json fold-in)."""
    return _request("GET", "/api/config")


def put_config_bulk(raw: dict) -> None:
    """Admin: replace the whole catalog (mods + themes + updater) wholesale."""
    _request("PUT", "/api/mods/bulk", json=raw)


# ---- Accounts ----
def get_accounts() -> dict[str, list[dict]]:
    return _request("GET", "/api/accounts") or {}


def put_accounts_bulk(data: dict[str, list[dict]]) -> None:
    _request("PUT", "/api/accounts/bulk", json=data)


# ---- Installs ----
def get_installs() -> dict[str, dict]:
    return _request("GET", "/api/installs", params={"machine_id": _machine_id()}) or {}


def put_install(mod_position: int, install_path: str, installed_version: str) -> None:
    _request(
        "PUT",
        "/api/installs",
        json={
            "mod_position": mod_position,
            "install_path": install_path,
            "installed_version": installed_version,
            "machine_id": _machine_id(),
        },
    )


def delete_install(mod_position: int) -> None:
    _request(
        "DELETE",
        "/api/installs",
        json={"mod_position": mod_position, "machine_id": _machine_id()},
    )
