"""Home Assistant skill: control smart-home devices via the HA REST API.

Configure HA_URL (e.g. http://homeassistant.local:8123) and a long-lived
access token HA_TOKEN in .env.
"""
from . import skill


def _request(ctx, method, path, payload=None):
    import requests
    s = ctx.settings
    if not (s.ha_url and s.ha_token):
        return None, "error: Home Assistant not configured (set HA_URL and HA_TOKEN in .env)"
    try:
        r = requests.request(method, f"{s.ha_url.rstrip('/')}{path}",
                             headers={"Authorization": f"Bearer {s.ha_token}"},
                             json=payload, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, f"error: Home Assistant request failed: {e}"


@skill("home_assistant",
       "Control or query smart-home devices via Home Assistant. "
       "entity_id examples: light.living_room, switch.fan, climate.bedroom.",
       {"type": "object", "properties": {
           "action": {"type": "string",
                      "enum": ["turn_on", "turn_off", "toggle", "status"]},
           "entity_id": {"type": "string"}},
        "required": ["action", "entity_id"]})
def home_assistant(ctx, action, entity_id):
    if action == "status":
        data, err = _request(ctx, "GET", f"/api/states/{entity_id}")
        if err:
            return err
        return f"{entity_id} is {data.get('state')} ({data.get('attributes', {})})"
    data, err = _request(ctx, "POST", f"/api/services/homeassistant/{action}",
                         {"entity_id": entity_id})
    return err or f"ok: {action} sent to {entity_id}"
