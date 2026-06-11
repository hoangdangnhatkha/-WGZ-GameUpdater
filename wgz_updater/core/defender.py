"""Windows Defender exclusion-path helper.

Excluding an install folder from Microsoft Defender's real-time scan cuts
extraction + first-run scan time dramatically on large game archives. This
module is the thin shim the Library uses to:

  * read the current `ExclusionPath` list via PowerShell
  * detect whether a destination is already covered by an ancestor entry
  * add a new entry via UAC (Defender preference changes require admin)

Everything here is Windows-only and best-effort: if PowerShell fails or
Defender is disabled the helpers degrade to "not covered / cannot add" so
the caller can decide whether to surface an error.
"""
from __future__ import annotations

import ctypes
import logging
import subprocess
from pathlib import Path

from .paths import APP_DIR, ensure_user_dirs

log = logging.getLogger(__name__)

_PS_TIMEOUT_S = 8.0
_SHELL_EXEC_CANCELLED = 5  # SE_ERR_ACCESSDENIED when user dismisses UAC

# Local mirror of exclusion paths we have asked Defender to add. `Get-
# MpPreference` requires admin to read the live list, so for non-elevated
# sessions we treat this file as the source of truth for "covered". The cache
# is additive only — entries are never expired, since removing an exclusion
# also requires admin and isn't something this app does.
_LOCAL_EXCLUSIONS_FILE = APP_DIR / "defender_exclusions.txt"

# Sentinel substrings PowerShell emits when the query is blocked by Defender's
# admin-only ACL on `Get-MpPreference`. We filter these so they don't poison
# the exclusion list with junk paths.
_PS_ERROR_MARKERS = (
    "must be an administrator",
    "access is denied",
    "n\\a:",
)


def _creationflags() -> int:
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def _load_local_cache() -> list[Path]:
    if not _LOCAL_EXCLUSIONS_FILE.exists():
        return []
    try:
        lines = _LOCAL_EXCLUSIONS_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        log.warning("Reading %s failed", _LOCAL_EXCLUSIONS_FILE, exc_info=True)
        return []
    return [Path(line.strip()) for line in lines if line.strip()]


def _append_local_cache(path: Path) -> None:
    ensure_user_dirs()
    try:
        with _LOCAL_EXCLUSIONS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(str(path) + "\n")
    except Exception:
        log.warning("Writing %s failed", _LOCAL_EXCLUSIONS_FILE, exc_info=True)


def _query_live_exclusions() -> list[Path]:
    """Best-effort `Get-MpPreference` query. Returns [] when blocked by ACL.

    Reading Defender's exclusion list requires admin on most Windows builds;
    when the call is rejected PowerShell still prints `N\\A: Must be an
    administrator…` to stdout, which we filter out so it can't masquerade
    as a real exclusion path.
    """
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-Command", "(Get-MpPreference).ExclusionPath -join '|'",
            ],
            capture_output=True,
            text=True,
            timeout=_PS_TIMEOUT_S,
            creationflags=_creationflags(),
        )
    except Exception:
        log.warning("Get-MpPreference failed", exc_info=True)
        return []

    raw = (result.stdout or "").strip()
    if not raw:
        return []

    paths: list[Path] = []
    for token in raw.split("|"):
        s = token.strip()
        if not s:
            continue
        low = s.lower()
        if any(marker in low for marker in _PS_ERROR_MARKERS):
            continue
        paths.append(Path(s))
    return paths


def list_exclusions() -> list[Path]:
    """Union of the locally cached + live Defender exclusion paths.

    Live query is best-effort (admin gate); the local cache is the durable
    record of what *this app* has asked Defender to exclude. Deduped by
    case-folded resolved string.
    """
    seen: set[str] = set()
    merged: list[Path] = []
    for src in (_query_live_exclusions(), _load_local_cache()):
        for p in src:
            key = _normalize(p)
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(p)
    return merged


def _normalize(path: Path) -> str:
    """Case-fold + trailing-separator-strip for Windows path comparison."""
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    s = str(resolved).rstrip("\\/").lower()
    return s


def is_covered(dest: Path, exclusions: list[Path] | None = None) -> bool:
    """True when `dest` equals or sits under an existing exclusion entry."""
    excl = list_exclusions() if exclusions is None else exclusions
    if not excl:
        return False
    d = _normalize(dest)
    for ex in excl:
        e = _normalize(ex)
        if not e:
            continue
        if d == e or d.startswith(e + "\\"):
            return True
    return False


def add_exclusion_with_uac(dest: Path) -> tuple[bool, str]:
    """Run `Add-MpPreference -ExclusionPath <dest>` elevated. Returns (ok, error).

    `(False, '')` means the user dismissed the UAC prompt — the caller can
    distinguish that from a real failure if it cares (we treat both the same
    in the UI). Note: the elevated call returns asynchronously; the function
    only reports whether the spawn itself succeeded, not whether the
    PowerShell command exit code was 0. In practice `Add-MpPreference` is
    idempotent so the worst case is a duplicate entry, which Defender
    silently dedupes.
    """
    # Single-quote the path inside the PowerShell command so spaces, parens
    # and other path quirks don't trip the parser. ' is escaped as ''.
    safe_path = str(dest).replace("'", "''")
    ps_cmd = f"Add-MpPreference -ExclusionPath '{safe_path}'"
    args = f'-NoProfile -NonInteractive -Command "{ps_cmd}"'

    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "powershell.exe", args, None, 0,  # SW_HIDE
        )
    except Exception as exc:
        log.exception("ShellExecuteW failed for Defender exclusion")
        return False, str(exc)

    if ret <= 32:
        if ret == _SHELL_EXEC_CANCELLED:
            return False, "Người dùng hủy UAC"
        return False, f"ShellExecuteW lỗi (mã {ret})"

    # Record the path locally so subsequent `is_covered` calls can answer
    # without needing admin to read the live Defender list. We can't tell
    # from ShellExecuteW alone whether Add-MpPreference actually succeeded,
    # but the spawn-only success path is the best signal we have here and
    # over-recording costs nothing (duplicate adds are silently deduped).
    try:
        _append_local_cache(dest)
    except Exception:
        log.exception("Could not record local Defender cache for %s", dest)

    return True, ""
