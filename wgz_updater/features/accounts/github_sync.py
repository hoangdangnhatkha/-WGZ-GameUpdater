from __future__ import annotations

import base64
import json
import logging
from dataclasses import asdict
from pathlib import Path

import httpx

from ...core.http import client
from ...core.paths import GITHUB_TOKEN_FILE
from .models import AccountRecord

log = logging.getLogger(__name__)

API_ROOT = "https://api.github.com"


class GitHubSync:
    """Read/write a JSON blob (account list) in a GitHub repo via the contents API."""

    def __init__(self, owner: str, repo: str, file_path: str, branch: str = "main") -> None:
        self._owner = owner
        self._repo = repo
        self._path = file_path
        self._branch = branch

    def _token(self) -> str:
        if not GITHUB_TOKEN_FILE.exists():
            raise FileNotFoundError("GitHub token not configured")
        return GITHUB_TOKEN_FILE.read_text(encoding="utf-8").strip()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _content_url(self) -> str:
        return f"{API_ROOT}/repos/{self._owner}/{self._repo}/contents/{self._path}"

    def fetch(self) -> tuple[list[AccountRecord], str | None]:
        try:
            r = client().get(
                self._content_url(),
                headers=self._headers(),
                params={"ref": self._branch},
            )
            if r.status_code == 404:
                return [], None
            r.raise_for_status()
            payload = r.json()
            sha = payload.get("sha")
            content_b64 = payload.get("content", "")
            decoded = base64.b64decode(content_b64).decode("utf-8")
            data = json.loads(decoded)
            accounts = [AccountRecord(**a) for a in data.get("accounts", [])]
            return accounts, sha
        except httpx.HTTPError as exc:
            log.exception("GitHub fetch failed")
            raise RuntimeError(str(exc)) from exc

    def push(self, records: list[AccountRecord], sha: str | None, commit_message: str = "Update accounts") -> str:
        body = {
            "message": commit_message,
            "branch": self._branch,
            "content": base64.b64encode(
                json.dumps(
                    {"accounts": [asdict(r) for r in records]},
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8")
            ).decode("ascii"),
        }
        if sha:
            body["sha"] = sha
        r = client().put(self._content_url(), headers=self._headers(), json=body)
        r.raise_for_status()
        return r.json().get("content", {}).get("sha", "")
