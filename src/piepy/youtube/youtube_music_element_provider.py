import os
import uuid
from collections.abc import Iterable
from pathlib import Path

from ydpy import Format, StreamingProtocol

from piepy.player_manager import LocalFileMusicElement, MusicElement
from piepy.youtube.youtube_fetcher import YtVideo

_MAX_AUDIO_BPS = 50_000


def _pick_audio_format(formats: Iterable[Format]) -> Format:
    # limit the audio bitrate to 50kbps: pick the best stream under the cap
    audio = [
        f for f in formats
        if f.is_audio and f.protocol is StreamingProtocol.HTTPS and not f.has_drm
    ]
    if not audio:
        raise RuntimeError('no playable audio stream found')

    capped = [f for f in audio if f.bitrate and f.bitrate <= _MAX_AUDIO_BPS]
    if capped:
        return max(capped, key=lambda f: f.bitrate or 0)

    # no stream under the cap: pick the lowest bitrate one so playback never breaks
    if known_bitrate := [f for f in audio if f.bitrate]:
        return min(known_bitrate, key=lambda f: f.bitrate or 0)
    return max(audio, key=lambda f: f.bitrate or 0)


class YouTubeMusicElementProvider:  # 지금 무료체험 하세요
    def __init__(self, download_dir: str):
        self.download_dir: str = download_dir

    def init(self):
        os.makedirs(self.download_dir, exist_ok=True)

        # remove leftover files from crashed previous sessions
        for leftover in Path(self.download_dir).glob('*.bin*'):
            leftover.unlink()

    async def create_music_from_yt(self, yt: YtVideo, video_url: str) -> MusicElement:
        fmt = _pick_audio_format(yt.formats)

        # ydpy streams are plain (non-SABR) urls; keep the file-based element so
        # playback never breaks on stream url expiry mid-queue
        return LocalFileMusicElement(
            f'yt_video_{yt.video_id}',
            title=yt.title,
            url=video_url,
            title_image_url=yt.thumbnail_url,
            length=yt.length,
            file_path=await self._download_audio(fmt),
            auto_file_delete=True
        )

    async def _download_audio(self, fmt: Format) -> str:
        filename = f'{uuid.uuid4()}.bin'
        file_path = str(Path(self.download_dir).joinpath(filename))

        # ydpy downloads are pure httpx IO that cooperates with the event loop,
        # so the yt-dlp subprocess isolation is no longer needed
        await fmt.adownload(file_path)
        return file_path
