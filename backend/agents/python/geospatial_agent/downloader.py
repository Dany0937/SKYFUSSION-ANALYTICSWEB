import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DownloadManifest:
    scene_id: str
    collection: str
    date: str
    url: str
    bands: list[str]
    scale: int
    bounds: dict
    checksum: str = ''
    status: str = 'pending'
    local_path: str = ''
    blob_url: str = ''
    retry_count: int = 0
    error: str | None = None


class Downloader:
    def __init__(self, config: dict):
        self.download_dir = config.get('download_dir', '/tmp/skyfusion/downloads')
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 300)
        self.concurrency = config.get('concurrency', 4)
        self._semaphore = asyncio.Semaphore(self.concurrency)
        os.makedirs(self.download_dir, exist_ok=True)

    async def download_scene(self, manifest: DownloadManifest) -> DownloadManifest:
        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    manifest.status = 'downloading'
                    local_path = os.path.join(
                        self.download_dir,
                        manifest.collection,
                        manifest.date[:10].replace('-', '/'),
                        f'{manifest.scene_id}.tif',
                    )
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    if manifest.url.startswith('http'):
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.get(manifest.url, timeout=self.timeout) as resp:
                                resp.raise_for_status()
                                with open(local_path, 'wb') as f:
                                    while chunk := await resp.content.read(8192):
                                        f.write(chunk)
                    else:
                        import shutil
                        shutil.copy2(manifest.url, local_path)

                    with open(local_path, 'rb') as f:
                        manifest.checksum = hashlib.sha256(f.read()).hexdigest()

                    manifest.local_path = local_path
                    manifest.status = 'completed'
                    manifest.blob_url = f'file://{local_path}'
                    break

                except Exception as e:
                    manifest.retry_count = attempt + 1
                    manifest.error = str(e)
                    manifest.status = 'retrying' if attempt + 1 < self.max_retries else 'failed'
                    if attempt + 1 < self.max_retries:
                        await asyncio.sleep(2 ** attempt)

            return manifest

    async def download_many(self, manifests: list[DownloadManifest]) -> list[DownloadManifest]:
        tasks = [self.download_scene(m) for m in manifests]
        return await asyncio.gather(*tasks)

    def save_manifest(self, manifests: list[DownloadManifest], request_id: str):
        path = os.path.join(self.download_dir, f'manifest_{request_id}.json')
        data = []
        for m in manifests:
            data.append({
                'scene_id': m.scene_id,
                'collection': m.collection,
                'date': m.date,
                'url': m.url,
                'bands': m.bands,
                'scale': m.scale,
                'checksum': m.checksum,
                'status': m.status,
                'local_path': m.local_path,
                'blob_url': m.blob_url,
                'error': m.error,
            })
        with open(path, 'w') as f:
            json.dump({'request_id': request_id, 'scenes': data, 'timestamp': datetime.utcnow().isoformat()}, f, indent=2)
        return path
