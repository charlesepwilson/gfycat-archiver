import json
import logging

import httpx

from gfycat_archiver.archiver import Archiver

logger = logging.getLogger(__name__)


class GfyCatAuth(httpx.Auth):
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.refresh_token()

    def refresh_token(self) -> str:
        url = "https://api.gfycat.com/v1/oauth/token"
        body = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = httpx.post(url, json=body)
        token = response.json()["access_token"]
        self.token = token
        return self.token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        response = yield request
        if response.status_code == httpx.codes.UNAUTHORIZED:
            self.refresh_token()
            request.headers["Authorization"] = f"Bearer {self.token}"
            yield request


def get_gfy_id(url: str) -> str:
    return url.strip("/").split("/")[-1]


class GfyCatClient(httpx.Client):
    def __init__(
        self, client_id: str, client_secret: str, archiver: Archiver, *args, **kwargs
    ):
        self.archiver = archiver
        super().__init__(*args, auth=GfyCatAuth(client_id, client_secret), **kwargs)

    def request(self, *args, **kwargs) -> httpx.Response:
        response = super().request(*args, **kwargs)
        response.raise_for_status()
        return response

    def save(self, url: str):
        gfy_id = get_gfy_id(url)
        json_file = f"{gfy_id}.json"
        if not self.archiver.file_exists(json_file):
            metadata_url = f"https://api.gfycat.com/v1/gfycats/{gfy_id}"
            metadata_response = self.get(metadata_url)
            with self.archiver.writer(json_file) as f:
                f.write(metadata_response.text)
            metadata = metadata_response.json()
        else:
            with self.archiver.reader(json_file) as f:
                metadata = json.load(f)
        mp4_url = metadata["gfyItem"]["mp4Url"]
        self.save_video(gfy_id, mp4_url, "mp4")
        webm_url = metadata["gfyItem"]["webmUrl"]
        self.save_video(gfy_id, webm_url, "webm")

    def save_video(self, gfy_id: str, url: str, file_format: str):
        file = f"{gfy_id}.{file_format}"
        if not self.archiver.file_exists(f"{gfy_id}.{file_format}"):
            with self.archiver.writer(file, "wb") as f:
                with httpx.stream("GET", url) as r:
                    for chunk in r.iter_bytes():
                        f.write(chunk)

    def save_batch(self, *urls: str):
        for url in urls:
            try:
                self.save(url.replace("\n", ""))
            except httpx.HTTPStatusError:
                logger.info(f"Failed to archive {url}")
