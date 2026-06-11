from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from ...core.http import client

log = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))


class DiscordNotifyError(RuntimeError):
    pass


def post_support_request(
    webhook_url: str,
    *,
    rustdesk_id: str,
    rustdesk_password: str,
    user_email: str,
    user_name: str,
    mention: str = "",
) -> None:
    """POST a support-request embed to the Discord webhook.

    Raises DiscordNotifyError on non-2xx response.
    """
    if not webhook_url:
        raise DiscordNotifyError("Empty Discord webhook URL")

    timestamp = datetime.now(_VN_TZ).strftime("%Y-%m-%d %H:%M:%S")

    embed = {
        "title": "🆘 Yêu cầu hỗ trợ từ xa",
        "color": 0xE74C3C,
        "fields": [
            {"name": "Người gọi", "value": f"{user_name}\n`{user_email}`", "inline": False},
            {"name": "RustDesk ID", "value": f"`{rustdesk_id}`", "inline": True},
            {"name": "Mật khẩu", "value": f"`{rustdesk_password}`", "inline": True},
            {"name": "Thời gian", "value": timestamp, "inline": False},
        ],
    }

    payload: dict = {"embeds": [embed]}
    if mention:
        payload["content"] = mention
        payload["allowed_mentions"] = {"parse": ["roles", "users"]}

    try:
        resp = client().post(webhook_url, json=payload)
    except Exception as exc:
        raise DiscordNotifyError(f"Network error: {exc}") from exc

    if resp.status_code >= 300:
        raise DiscordNotifyError(
            f"Discord webhook returned {resp.status_code}: {resp.text[:200]}"
        )
