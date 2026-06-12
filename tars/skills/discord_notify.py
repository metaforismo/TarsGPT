"""Discord skill: TARS messages your server.

Uses an incoming webhook (Server settings -> Integrations -> Webhooks),
so there is no bot token, no gateway connection and no heavy dependency.
The fall and battery watchdogs use the same channel automatically.
"""
from . import skill
from ..notify import notify


@skill("discord_send",
       "Send a message to the owner's Discord channel. Use when asked to "
       "notify, message or report something to Discord.",
       {"type": "object", "properties": {"message": {"type": "string"}},
        "required": ["message"]})
def discord_send(ctx, message):
    if not ctx.settings.discord_webhook:
        return "error: Discord not configured (set DISCORD_WEBHOOK in .env)"
    if notify(message, ctx.settings):
        return "ok: sent to Discord"
    return "error: Discord webhook refused the message"
