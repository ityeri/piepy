import asyncio
import os
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path

from pytubefix import Stream, YouTube

from piepy.player_manager import LocalFileMusicElement, MusicElement, UrlStreamMusicElement

_MAX_AUDIO_KBPS = 50

_YTDLP_ARGS: list[str] = [
    '--no-playlist',
    '--format', 'bestaudio[abr<=50]/worstaudio/best',
    '--js-runtimes', 'node',
    '--remote-components', 'ejs:github',
]


def _pick_audio_stream(streams: Iterable[Stream]) -> Stream:
    # limit the audio bitrate to 50kbps: pick the best stream under the cap
    capped = [s for s in streams if s.abr and int(s.abr[:-4]) <= _MAX_AUDIO_KBPS]
    if capped:
        return max(capped, key=lambda s: int(s.abr[:-4]))

    # no stream under the cap: pick the lowest bitrate one so playback never breaks
    if known_abr := [s for s in streams if s.abr]:
        return min(known_abr, key=lambda s: int(s.abr[:-4]))
    return next(iter(streams))


class YouTubeMusicElementProvider:  # 지금 무료체험 하세요
    def __init__(self, download_dir: str):
        self.download_dir: str = download_dir

    def init(self):
        os.makedirs(self.download_dir, exist_ok=True)

        # remove leftover files from crashed previous sessions
        for leftover in Path(self.download_dir).glob('*.bin*'):
            leftover.unlink()

    async def create_music_from_yt(self, yt: YouTube, video_url: str) -> MusicElement:
        stream = _pick_audio_stream(yt.streams.filter(only_audio=True))

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

        # yt-dlp runs as a separate process so that its CPU work and memory do not
        # contend with the bot's event loop and voice playback for the GIL
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'yt_dlp',
            *_YTDLP_ARGS,
            '--output', file_path,
            video_url,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            _, stderr = await proc.communicate()
        except asyncio.CancelledError:
            proc.terminate()
            await proc.wait()
            raise

        if proc.returncode != 0:
            raise RuntimeError(
                f'yt-dlp download failed with exit code {proc.returncode}: '
                f'{stderr.decode(errors="replace")[-300:]}'
            )
        return file_path
