import asyncio
import os
from concurrent.futures.thread import ThreadPoolExecutor

from pytubefix import YouTube


def download_audio_sync(url: str, output_path: str):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    audio_stream.download(
        output_path=os.path.split(output_path)[0],
        filename=os.path.split(output_path)[1]
    )


async def download_audio(url: str, output_path: str, executor: ThreadPoolExecutor | None = None):
    loop = asyncio.get_running_loop()

    await loop.run_in_executor(
        executor, download_audio_sync, url, output_path
    )