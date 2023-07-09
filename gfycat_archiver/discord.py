import re
from datetime import datetime, timezone
import time

import httpx

from gfycat_archiver import settings


class DiscordAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bot {self.token}"
        yield request


class DiscordClient(httpx.Client):
    def __init__(self, token: str, *args, **kwargs):
        api_base_url = 'https://discord.com/api/v10'
        super().__init__(
            base_url=api_base_url,
            auth=DiscordAuth(token),
            *args, **kwargs
        )

    def request(self, *args, **kwargs) -> httpx.Response:
        response = super().request(*args, **kwargs)
        if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            data = response.json()
            print("Sleep")
            print(data)
            time.sleep(data["retry_after"])
            response = super().request(*args, **kwargs)
        response.raise_for_status()
        return response


def extract_gfycat_links(text: str) -> set[str]:
    matches = re.findall(r"https://gfycat.com/[a-z]+", text, flags=re.IGNORECASE)
    return set(matches)


def get_gfycat_links(client: DiscordClient, channel_id: int) -> set[str]:
    links = set()
    earliest_message_id = None
    earliest_time = datetime.max.replace(tzinfo=timezone.utc)
    messages = True
    while messages:
        query_params = {
            "limit": 100,
        }
        if earliest_message_id:
            query_params["before"] = earliest_message_id
        response = client.get(f"/channels/{channel_id}/messages", params=query_params)
        messages = response.json()
        for message in messages:
            text = message["content"]
            links.update(extract_gfycat_links(text))
            timestamp = datetime.fromisoformat(message["timestamp"])
            if timestamp < earliest_time:
                earliest_time = timestamp
                earliest_message_id = message["id"]
    return links


def get_channel_ids(client: DiscordClient, guild_id: int) -> set[int]:
    response = client.get(f"/guilds/{guild_id}/channels")
    channels = response.json()
    text_channel_type = 0
    channel_ids = {channel["id"] for channel in channels if channel["type"] == text_channel_type}
    return channel_ids
