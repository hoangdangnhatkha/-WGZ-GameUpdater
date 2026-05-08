from __future__ import annotations

from functools import lru_cache

import httpx


@lru_cache(maxsize=1)
def client() -> httpx.Client:
    return httpx.Client(
        http2=True,
        timeout=httpx.Timeout(15.0, connect=10.0),
        follow_redirects=True,
        headers={"User-Agent": "WGZ-GameUpdater/2.0"},
    )


def get_json(url: str, *, cachebust: bool = True) -> dict:
    if cachebust:
        sep = "&" if "?" in url else "?"
        import time
        url = f"{url}{sep}t={int(time.time())}"
    resp = client().get(url)
    resp.raise_for_status()
    return resp.json()
