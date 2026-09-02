import asyncio
import os
import uuid
from pathlib import Path

from pytubefix import Stream, YouTube
from yt_dlp import YoutubeDL

from piepy.player_manager import MusicElement, UrlStreamMusicElement
from piepy.player_manager.music_element import LocalFileMusicElement


class YouTubeMusicElementProvider:  # 지금 무료체험 하세요
    def __init__(self, download_dir: str):
        self.download_dir: str = download_dir

    def init(self):
        os.makedirs(self.download_dir, exist_ok=True)

    async def create_music_from_yt(self, yt: YouTube, video_url: str) -> MusicElement:
        stream: Stream = max(yt.streams.filter(only_audio=True), key=lambda s: int(s.abr[:-4]) if s.abr else 0)

        if stream.is_sabr:
            filename = f'{uuid.uuid4()}.bin'
            file_path = str(Path(self.download_dir).joinpath(filename))

            def run():
                config = {
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': file_path,
                    'format': 'bestaudio/best'
                }
                with YoutubeDL(config) as ydl:
                    ydl.extract_info(video_url, download=True)

            await asyncio.to_thread(run)

            return LocalFileMusicElement(
                f'yt_video_{yt.video_id}',
                file_path=file_path,
                title=yt.title,
                url=video_url,
                title_image_url=yt.thumbnail_url,
                length=yt.length,
                auto_file_delete=True
            )
        else:
            return UrlStreamMusicElement(
                f'yt_video_{yt.video_id}',
                title=yt.title,
                url=video_url,
                title_image_url=yt.thumbnail_url,
                length=yt.length,
                stream_url=stream.url
            )
