"""Accounts service — now backed by the wgz-api REST endpoint.

Keeps the original `DriveAccountsService` class name and method signatures
(`fetch()` / `push()`) so the view layer needs no changes. The underlying
storage moved from Google Drive JSON to PostgreSQL via wgz-api.
"""
from __future__ import annotations

import logging

from ...core import api_client

log = logging.getLogger(__name__)


class DriveAccountsService:
    """Reads/writes shared accounts via wgz-api.

    Data shape (unchanged from the legacy Drive JSON):
        {
          "<game_name>": [
            {"nickname": "...", "username": "...", "password": "...",
             "type": "steam|riot|...", "game": "<game_name>"},
            ...
          ]
        }
    """

    def __init__(self, folder_id: str | None = None) -> None:
        # folder_id kept for signature compat with old callers; unused now.
        self._folder_id = folder_id

    def fetch(self) -> dict[str, list[dict]]:
        try:
            return api_client.get_accounts()
        except Exception as exc:
            log.warning("Failed fetching accounts from wgz-api: %s", exc)
            return {}

    def push(self, data: dict[str, list[dict]]) -> None:
        # Strip any per-row "id" fields the API doesn't accept on bulk PUT.
        cleaned: dict[str, list[dict]] = {}
        for game, rows in data.items():
            cleaned[game] = [
                {k: v for k, v in row.items() if k != "id"} for row in rows
            ]
        api_client.put_accounts_bulk(cleaned)
