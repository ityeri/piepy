import asyncio
import os
import uuid
from pathlib import Path

from pytubefix import Stream, YouTube
from yt_dlp import YoutubeDL

from piepy.player_manager import LocalFileMusicElement, MusicElement, UrlStreamMusicElement

_YTDLP_CONFIG: dict[str, object] = {
    'quiet': True,
    'no_warnings': True,
    'noprogress': True,
    'format': 'bestaudio/best',
    'js_runtimes': {'node': {}},
    'remote_components': ['ejs:github'],
}


class YouTubeMusicElementProvider:  # 지금 무료체험 하세요
    def __init__(self, download_dir: str):
        self.download_dir: str = download_dir

    def init(self):
        os.makedirs(self.download_dir, exist_ok=True)

        # remove leftover files from crashed previous sessions
        for leftover in Path(self.download_dir).glob('*.bin'):
            leftover.unlink()

    async def create_music_from_yt(self, yt: YouTube, video_url: str) -> MusicElement:
        stream: Stream = max(yt.streams.filter(only_audio=True), key=lambda s: int(s.abr[:-4]) if s.abr else 0)

        if stream.is_sabr:
            return LocalFileMusicElement(
                f'yt_video_{yt.video_id}',
                title=yt.title,
                url=video_url,
                title_image_url=yt.thumbnail_url,
                length=yt.length,
                file_path=await self._download_audio(video_url),
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

    async def _download_audio(self, video_url: str) -> str:
        filename = f'{uuid.uuid4()}.bin'
        file_path = str(Path(self.download_dir).joinpath(filename))

        def run():
            with YoutubeDL({**_YTDLP_CONFIG, 'outtmpl': file_path}) as ydl:
                ydl.extract_info(video_url, download=True)

        await asyncio.to_thread(run)
        return file_path
