import json
import os.path
from pathlib import Path

import httpx

from gfycat_archiver import settings


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


class GfyCatClient(httpx.Client):
    def __init__(self, client_id: str, client_secret: str, save_directory: Path, *args, **kwargs):
        self.save_directory = save_directory
        super().__init__(
            auth=GfyCatAuth(client_id, client_secret),
            *args, **kwargs
        )

    def save(self, url: str):
        gfy_id = url.split("/")[-1]
        json_file = f"{gfy_id}.json"
        if not os.path.isfile(self.save_directory / json_file):
            print(f"getting metadata {json_file}")
            metadata_url = f"https://api.gfycat.com/v1/gfycats/{gfy_id}"
            metadata_response = self.get(metadata_url)
            with open(self.save_directory / json_file, "w") as f:
                f.write(metadata_response.text)
            metadata = metadata_response.json()
        else:
            with open(self.save_directory / json_file, "r") as f:
                metadata = json.load(f)
        mp4_url = metadata["gfyItem"]["mp4Url"]
        self.save_video(gfy_id, mp4_url, "mp4")
        webm_url = metadata["gfyItem"]["webmUrl"]
        self.save_video(gfy_id, webm_url, "webm")

    def save_video(self, gfy_id: str,  url: str, file_format: str):
        file = f"{gfy_id}.{file_format}"
        if not os.path.isfile(self.save_directory / file):
            print(f"getting video {file}")
            with open(self.save_directory / file, "wb") as f:
                with httpx.stream('GET', url) as r:
                    for chunk in r.iter_bytes():
                        f.write(chunk)

    def save_batch(self, *urls: str):
        for url in urls:
            self.save(url.replace("\n", ""))


if __name__ == "__main__":
    s = settings.Settings()
    client = GfyCatClient(s.gfycat_client_id, s.gfycat_secret, s.save_directory)
    with open("links.txt") as f:
        links = f.readlines()
        client.save_batch(
            *links,
        )
