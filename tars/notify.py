"""Outbound notifications (Discord webhook): the robot's way of reaching
your phone when something happens while you're away. Zero dependencies
beyond requests; failures are logged, never raised."""
import logging

log = logging.getLogger("tars.notify")


def notify(text: str, s) -> bool:
    """Post to the configured Discord webhook. Returns True if delivered."""
    if not s.discord_webhook or not text:
        return False
    try:
        import requests
        response = requests.post(s.discord_webhook,
                                 json={"content": text[:1900]}, timeout=8)
        return response.status_code in (200, 204)
    except Exception as e:
        log.warning("discord notify failed: %s", e)
        return False
