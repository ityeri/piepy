import logging
from dataclasses import dataclass
from enum import Enum, auto

from ydpy import Format, StreamingProtocol, Video
from ydpy.exceptions import ExtractionException, InvalidVideoIdentifierException

_logger = logging.getLogger(__name__)


class YouTubeFetchingResult(Enum):
    VIDEO_PRIVATE = auto()
    VIDEO_REMOVED = auto()
    VIDEO_BLOCKED = auto()
    UNAVAILABLE_LIVE = auto()
    BOT_DETECTION = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class YtVideo:
    """ydpy-backed stand-in for the pytubefix YouTube object (feature/ydpy-base)."""

    video_id: str
    title: str
    thumbnail_url: str
    length: float  # seconds
    formats: tuple[Format, ...]


def fetch_youtube(url: str, max_attempts: int = 10) -> YtVideo | YouTubeFetchingResult:
    tries = 0

    while tries < max_attempts:
        try:
            video = Video(url)
            data = video.fetch()
        except ExtractionException as e:
            message = str(e)
            if 'bot' in message.lower():
                tries += 1
                _logger.warning(f'BotDetection on attempt {tries}/{max_attempts}: url={url}')
                continue
            _logger.info(f'YouTube fetch rejected: url={url} reason={message}')
            return _classify_failure(message)
        except InvalidVideoIdentifierException:
            return YouTubeFetchingResult.UNKNOWN

        # Ongoing live streams have no duration and no direct url streams.
        if (data.duration_ms or 0) <= 0 and not _has_direct_streams(data.formats):
            return YouTubeFetchingResult.UNAVAILABLE_LIVE

        _logger.debug(f'YouTube fetch succeeded: url={url}')
        return YtVideo(
            video_id=data.video_id,
            title=data.title or data.video_id,
            thumbnail_url=f'https://i.ytimg.com/vi/{data.video_id}/hqdefault.jpg',
            length=(data.duration_ms or 0) / 1000,
            formats=data.formats,
        )

    _logger.warning(f'BotDetection: exhausted {max_attempts} attempts for url={url}')
    return YouTubeFetchingResult.BOT_DETECTION


def _has_direct_streams(formats: tuple[Format, ...]) -> bool:
    """True when at least one format is a plain url stream (not a manifest)."""
    return any(fmt.protocol is StreamingProtocol.HTTPS for fmt in formats)


def _classify_failure(message: str) -> YouTubeFetchingResult:
    """Coarse mapping from ydpy playability messages onto the old result enum."""
    text = message.lower()

    if any(keyword in text for keyword in ('age', 'sign in', 'private', 'membership', 'member')):
        return YouTubeFetchingResult.VIDEO_PRIVATE
    if any(keyword in text for keyword in ('removed', 'terminated', 'violating')):
        return YouTubeFetchingResult.VIDEO_REMOVED
    if any(keyword in text for keyword in ('blocked', 'region', 'copyright')):
        return YouTubeFetchingResult.VIDEO_BLOCKED
    if 'live' in text:
        return YouTubeFetchingResult.UNAVAILABLE_LIVE
    return YouTubeFetchingResult.UNKNOWN
