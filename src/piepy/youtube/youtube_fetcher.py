import logging
from dataclasses import dataclass
from enum import Enum, auto

from pytubefix import YouTube
from pytubefix.exceptions import VideoPrivate, MembersOnly, LoginRequired, AgeRestrictedError, AgeCheckRequiredError, \
    VideoRemovedByUploader, VideoRemovedByYouTubeForViolatingTOS, AccountTerminated, VideoRegionBlocked, \
    VideoBlockedByCopyright, LiveStreamError, LiveStreamEnded, LiveStreamOffline, RecordingUnavailable, \
    VideoUnavailable, BotDetection
from ydpy import Format, Video
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
    """Stream formats (ydpy) plus metadata, fetched via a two-stage check."""

    video_id: str
    title: str
    thumbnail_url: str
    length: float  # seconds
    formats: tuple[Format, ...]


def fetch_youtube(url: str, max_attempts: int = 10) -> YtVideo | YouTubeFetchingResult:
    tries = 0

    while tries < max_attempts:
        # stage 1: pytubefix WEB availability/metadata (typed failure classification)
        try:
            yt = YouTube(url, client='WEB')
            yt.check_availability()
        except BotDetection:
            tries += 1
            _logger.warning(f'BotDetection on attempt {tries}/{max_attempts}: url={url}')
            continue

        # TODO this giant exception logic does not working
        # pytubefix lib raises errors by checking a UI message and this message is depends on the locale
        # pytubefix's message comparing logic is made based on english locale UI messages
        # that means it doesn't works in korea locale.
        # This is pytubefix's problem it self. This might more good to implement on the yspy lib
        except VideoPrivate:
            return YouTubeFetchingResult.VIDEO_PRIVATE
        except MembersOnly:
            return YouTubeFetchingResult.VIDEO_PRIVATE
        except LoginRequired:
            return YouTubeFetchingResult.VIDEO_PRIVATE
        except AgeRestrictedError:
            return YouTubeFetchingResult.VIDEO_PRIVATE
        except AgeCheckRequiredError:
            return YouTubeFetchingResult.VIDEO_PRIVATE
        except VideoRemovedByUploader:
            return YouTubeFetchingResult.VIDEO_REMOVED
        except VideoRemovedByYouTubeForViolatingTOS:
            return YouTubeFetchingResult.VIDEO_REMOVED
        except AccountTerminated:
            return YouTubeFetchingResult.VIDEO_REMOVED
        except VideoRegionBlocked:
            return YouTubeFetchingResult.VIDEO_BLOCKED
        except VideoBlockedByCopyright:
            return YouTubeFetchingResult.VIDEO_BLOCKED
        except LiveStreamError:
            return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamEnded:
            return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamOffline:
            return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except RecordingUnavailable:
            return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except VideoUnavailable:
            return YouTubeFetchingResult.UNKNOWN

        # stage 2: ydpy stream formats (fetch again; pytubefix streams would be SABR)
        try:
            data = Video(url).fetch()
        except ExtractionException as e:
            message = str(e)
            if 'bot' in message.lower():
                tries += 1
                _logger.warning(f'BotDetection on attempt {tries}/{max_attempts}: url={url}')
                continue
            _logger.info(f'ydpy fetch rejected after pytubefix ok: url={url} reason={message}')
            return _classify_failure(message)
        except InvalidVideoIdentifierException:
            return YouTubeFetchingResult.UNKNOWN

        _logger.debug(f'YouTube fetch succeeded: url={url}')
        return YtVideo(
            video_id=yt.video_id,
            title=yt.title,
            thumbnail_url=yt.thumbnail_url,
            length=float(yt.length),
            formats=data.formats,
        )

    _logger.warning(f'BotDetection: exhausted {max_attempts} attempts for url={url}')
    return YouTubeFetchingResult.BOT_DETECTION


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
