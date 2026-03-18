import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def post_follow_up(application_id: str, interaction_token: str, data: dict) -> None:
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original"
    patch_data = {k: v for k, v in data.items() if k != "flags"}
    body = json.dumps(patch_data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="PATCH",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://discord.com/developers/docs, 1.0)",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        logger.error(f"Discord follow-up failed: {e.code} {e.read().decode()}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"Discord follow-up network error: {e.reason}")
        raise
