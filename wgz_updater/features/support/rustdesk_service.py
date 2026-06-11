from __future__ import annotations

import ctypes
import logging
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import secrets
import string

from ...core.paths import RUSTDESK_CONFIG_TOML, RUSTDESK_EXE, RUSTDESK_SUPPORT_PW_FILE, ensure_user_dirs

# RustDesk installs itself to Program Files; the system-wide service uses this
# exe, not the portable copy bundled with the app.
INSTALLED_RUSTDESK_EXE = (
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "RustDesk" / "RustDesk.exe"
)

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

log = logging.getLogger(__name__)

_CLI_TIMEOUT_S = 6.0
_LAUNCH_TIMEOUT_S = 8.0
_POLL_INTERVAL_S = 0.4
_OTP_WAIT_S = 12.0
_INSTALL_TIMEOUT_S = 90.0

# ShellExecuteW return codes <= 32 indicate failure. 5 (SE_ERR_ACCESSDENIED) is
# returned when the user cancels the UAC prompt.
_SHELL_EXEC_CANCELLED = 5

_PW_ALPHABET = string.ascii_letters + string.digits
_PW_LEN = 10

# RustDesk persists the current temporary password to RustDesk2.toml under
# `[options].temporary-password` once the service has generated one. This is
# undocumented but stable across 1.2+ releases.
_OTP_TOML_KEYS = ("temporary-password", "temporary_password")


class RustDeskError(RuntimeError):
    """Raised when RustDesk cannot be launched or its ID cannot be retrieved."""


class InstallCancelledError(RustDeskError):
    """Raised when the user dismisses the UAC prompt for the install step."""


@dataclass(frozen=True)
class SessionInfo:
    rustdesk_id: str
    otp: str | None  # None when the service did not yield a password in time


def is_bundled() -> bool:
    return RUSTDESK_EXE.exists()


def is_installed() -> bool:
    """True when RustDesk has been installed system-wide AND its service is registered."""
    return INSTALLED_RUSTDESK_EXE.exists() and _service_registered()


def _service_registered() -> bool:
    """Query the Windows SCM for the RustDesk service."""
    try:
        result = subprocess.run(
            ["sc", "query", "RustDesk"],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=_creationflags(),
        )
    except Exception:
        return False
    return result.returncode == 0


def _active_exe() -> Path:
    """Prefer the installed RustDesk over the portable bundle.

    The installed copy is what registers the Windows service that generates
    the temporary password we want to harvest.
    """
    if is_installed():
        return INSTALLED_RUSTDESK_EXE
    return RUSTDESK_EXE


def _generate_password() -> str:
    return "".join(secrets.choice(_PW_ALPHABET) for _ in range(_PW_LEN))


def read_stored_password() -> str | None:
    if not RUSTDESK_SUPPORT_PW_FILE.exists():
        return None
    try:
        pw = RUSTDESK_SUPPORT_PW_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        log.exception("Failed reading %s", RUSTDESK_SUPPORT_PW_FILE)
        return None
    return pw or None


def _write_stored_password(pw: str) -> None:
    ensure_user_dirs()
    RUSTDESK_SUPPORT_PW_FILE.write_text(pw, encoding="utf-8")


def _build_install_batch(password: str) -> Path:
    """Write a temp batch: `--silent-install` → register service → start → set password.

    Chaining via a .bat file avoids the quoting nightmare of nesting `cmd /c`
    inside ShellExecuteW.
    """
    installed = INSTALLED_RUSTDESK_EXE
    bundled = RUSTDESK_EXE
    script = (
        "@echo off\r\n"
        f'"{bundled}" --silent-install\r\n'
        # Give silent install a moment to finish file copies before sc create.
        "ping 127.0.0.1 -n 4 >nul\r\n"
        f'sc create RustDesk binPath= "\\"{installed}\\" --service" '
        'start= auto DisplayName= "RustDesk"\r\n'
        "sc start RustDesk\r\n"
        "ping 127.0.0.1 -n 3 >nul\r\n"
        # Now elevated, set a known permanent password so later support calls
        # can post it to Discord without another UAC prompt.
        f'"{installed}" --password {password}\r\n'
        "exit /b 0\r\n"
    )
    fd, path = tempfile.mkstemp(prefix="wgz_rustdesk_install_", suffix=".bat")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
    except Exception:
        os.close(fd)
        raise
    return Path(path)


def install_silent_with_uac() -> str:
    """Install RustDesk, register the service, set a permanent support password.

    Workflow:
      1. Generate a random password.
      2. Write a temp .bat chaining `--silent-install`, `sc create`, `sc start`,
         and `RustDesk --password <pw>`.
      3. Invoke `cmd.exe /c "<bat>"` via ShellExecuteW with `runas` for UAC.
      4. Persist the plaintext password to RUSTDESK_SUPPORT_PW_FILE so future
         support calls reuse it without re-elevating.

    Returns the generated password. Cancelling UAC raises InstallCancelledError;
    poll `is_installed()` for actual completion.
    """
    if not RUSTDESK_EXE.exists():
        raise RustDeskError(f"RustDesk executable not found at {RUSTDESK_EXE}")

    password = _generate_password()
    bat = _build_install_batch(password)
    args = f'/c ""{bat}""'

    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            "cmd.exe",
            args,
            None,
            0,  # SW_HIDE
        )
    except Exception as exc:
        raise RustDeskError(f"ShellExecuteW failed: {exc}") from exc

    if ret <= 32:
        if ret == _SHELL_EXEC_CANCELLED:
            raise InstallCancelledError("User cancelled UAC prompt")
        raise RustDeskError(f"ShellExecuteW returned error code {ret}")

    _write_stored_password(password)
    return password


def wait_for_install(deadline_s: float = _INSTALL_TIMEOUT_S) -> bool:
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        if is_installed():
            return True
        time.sleep(_POLL_INTERVAL_S)
    return is_installed()


def _creationflags() -> int:
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def launch() -> subprocess.Popen:
    """Spawn the RustDesk UI (installed copy preferred over portable)."""
    exe = _active_exe()
    if not exe.exists():
        raise RustDeskError(f"RustDesk executable not found at {exe}")
    return subprocess.Popen(
        [str(exe)],
        cwd=str(exe.parent),
        creationflags=_creationflags(),
    )


def _run_cli(args: list[str], *, timeout: float = _CLI_TIMEOUT_S) -> subprocess.CompletedProcess:
    exe = _active_exe()
    return subprocess.run(
        [str(exe), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=_creationflags(),
    )


def _parse_toml(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _get_id_via_cli() -> str | None:
    if not _active_exe().exists():
        return None
    try:
        result = _run_cli(["--get-id"])
    except Exception:
        log.exception("rustdesk --get-id failed")
        return None
    # CLI prints diagnostic lines before the ID; the ID is always the last
    # non-empty token on stdout (a contiguous run of digits).
    text = (result.stdout or "").strip()
    for line in reversed(text.splitlines()):
        token = line.strip()
        if token.isdigit():
            return token
    return None


def _wait_for_config(deadline_s: float) -> bool:
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        if RUSTDESK_CONFIG_TOML.exists():
            return True
        time.sleep(_POLL_INTERVAL_S)
    return RUSTDESK_CONFIG_TOML.exists()


def _enable_service_in_toml(path: Path = RUSTDESK_CONFIG_TOML) -> None:
    """Remove `stop-service = 'Y'` from RustDesk2.toml so the service auto-starts.

    Edits the raw text to preserve formatting (no full TOML rewrite). Idempotent
    — safe to call when the line is absent.
    """
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        log.exception("Failed reading %s", path)
        return

    new_text = re.sub(
        r"^[ \t]*stop-service[ \t]*=[ \t]*['\"]Y['\"][ \t]*\r?\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    if new_text != text:
        try:
            path.write_text(new_text, encoding="utf-8")
            log.info("Cleared stop-service flag in %s", path)
        except Exception:
            log.exception("Failed writing %s", path)


def _read_otp_from_toml(path: Path = RUSTDESK_CONFIG_TOML) -> str | None:
    if not path.exists():
        return None
    try:
        data = _parse_toml(path)
    except Exception:
        log.exception("Failed parsing %s for OTP", path)
        return None
    options = data.get("options") if isinstance(data, dict) else None
    if not isinstance(options, dict):
        return None
    for key in _OTP_TOML_KEYS:
        v = options.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def wait_for_otp(deadline_s: float = _OTP_WAIT_S) -> str | None:
    """Poll RustDesk2.toml for the service-generated temporary password."""
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        otp = _read_otp_from_toml()
        if otp:
            return otp
        time.sleep(_POLL_INTERVAL_S)
    return _read_otp_from_toml()


def prepare_session() -> SessionInfo:
    """Launch RustDesk (installed copy) and resolve (id, password).

    The password is the plaintext written to RUSTDESK_SUPPORT_PW_FILE during
    the one-time install step. If the file is missing, we fall back to the
    service-generated OTP (rarely available without IPC), and then to None;
    the caller can prompt the user to paste manually.
    """
    _enable_service_in_toml()
    launch()
    _wait_for_config(_LAUNCH_TIMEOUT_S)

    rd_id = _resolve_id()

    password: str | None = read_stored_password()
    if not password:
        password = wait_for_otp()

    return SessionInfo(rustdesk_id=rd_id, otp=password)


def _resolve_id() -> str:
    rd_id = _get_id_via_cli()
    if rd_id:
        return rd_id

    if RUSTDESK_CONFIG_TOML.exists():
        try:
            data = _parse_toml(RUSTDESK_CONFIG_TOML)
        except Exception:
            log.exception("Failed parsing %s", RUSTDESK_CONFIG_TOML)
            data = {}
        raw_id = data.get("id")
        if raw_id:
            return str(raw_id)

    raise RustDeskError("Unable to determine RustDesk ID from CLI or config")
