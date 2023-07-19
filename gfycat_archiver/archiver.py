import os
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from os import PathLike
from pathlib import Path
from typing import IO, Any

from discord import File


class Archiver(ABC):
    @abstractmethod
    def writer(self, file_name: str, *args, **kwargs) -> AbstractContextManager:
        pass

    @abstractmethod
    def file_exists(self, file_name: str) -> bool:
        pass

    @abstractmethod
    def reader(self, file_name: str, *args, **kwargs) -> AbstractContextManager:
        pass

    @abstractmethod
    def attach_files(self, gfy_id: str) -> dict[str, Any]:
        pass


class LocalArchiver(Archiver):
    def __init__(self, save_directory: PathLike):
        self.save_directory = Path(save_directory)

    def file_exists(self, file_name: str) -> bool:
        return os.path.isfile(self.save_directory / file_name)

    def writer(self, file_name, *args, **kwargs) -> IO:
        return open(self.save_directory / file_name, "w")

    def reader(self, file_name: str, *args, **kwargs) -> IO:
        return open(self.save_directory / file_name)

    def attach_files(self, gfy_id: str) -> dict[str, Any]:
        json_file = f"{gfy_id}.json"
        webm_file = f"{gfy_id}.webm"
        metadata = File(self.save_directory / json_file)
        video = File(self.save_directory / webm_file)
        return dict(files=[metadata, video])


try:
    from google.cloud import storage  # type: ignore
    from google.cloud.storage.blob import BlobReader, BlobWriter  # type: ignore

    class GoogleCloudArchiver(Archiver):
        def __init__(self, project_id: str, bucket: str):
            self.client = storage.Client(project=project_id)
            self.bucket: storage.Bucket = self.client.bucket(bucket)

        def file_exists(self, file_name: str) -> bool:
            return self.bucket.blob(file_name).exists()

        def writer(self, file_name: str, *args, **kwargs) -> BlobWriter:
            blob = self.bucket.blob(file_name)
            return BlobWriter(blob)

        def reader(self, file_name: str, *args, **kwargs) -> BlobReader:
            blob = self.bucket.blob(file_name)
            return BlobReader(blob)

        def attach_files(self, gfy_id: str) -> dict[str, Any]:
            json_file = f"{gfy_id}.json"
            webm_file = f"{gfy_id}.webm"
            json_url = self.bucket.blob(json_file).public_url
            webm_url = self.bucket.blob(webm_file).public_url
            return dict(content=f"{json_url}\n{webm_url}")

except ImportError:
    pass
