import logging
from enum import Enum, auto

from pytubefix import YouTube
from pytubefix.exceptions import *

_logger = logging.getLogger(__name__)


class YouTubeFetchingResult(Enum):
    VIDEO_PRIVATE = auto()
    VIDEO_REMOVED = auto()
    VIDEO_BLOCKED = auto()
    UNAVAILABLE_LIVE = auto()
    BOT_DETECTION = auto()
    UNKNOWN = auto()

def fetch_youtube(url: str, max_attempts: int = 10) -> YouTube | YouTubeFetchingResult:
    tries = 0

    while tries < max_attempts:
        try:
            yt = YouTube(url)
            yt.check_availability()
            _logger.debug(f'YouTube fetch succeeded: url={url}')
            return yt
        except BotDetection:
            tries += 1
            _logger.warning(f'BotDetection on attempt {tries}/{max_attempts}: url={url}')

        # TODO this giant exception logic does not working
        # pytubefix lib raises errors by checking a UI message and this message is depends on the locale
        # pytubefix's message comparing logic is made based on english locale UI messages
        # that means it doesn't works in korea locale.
        # This is pytubefix's problem it self. This might more good to implement on the yspy lib
        except VideoPrivate: return YouTubeFetchingResult.VIDEO_PRIVATE
        except MembersOnly: return YouTubeFetchingResult.VIDEO_PRIVATE
        except LoginRequired: return YouTubeFetchingResult.VIDEO_PRIVATE
        except AgeRestrictedError: return YouTubeFetchingResult.VIDEO_PRIVATE
        except AgeCheckRequiredError: return YouTubeFetchingResult.VIDEO_PRIVATE

        except VideoRemovedByUploader: return YouTubeFetchingResult.VIDEO_REMOVED
        except VideoRemovedByYouTubeForViolatingTOS: return YouTubeFetchingResult.VIDEO_REMOVED
        except AccountTerminated: return YouTubeFetchingResult.VIDEO_REMOVED

        except VideoRegionBlocked: return YouTubeFetchingResult.VIDEO_BLOCKED
        except VideoBlockedByCopyright: return YouTubeFetchingResult.VIDEO_BLOCKED

        except LiveStreamError: return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamEnded: return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamOffline: return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except RecordingUnavailable: return YouTubeFetchingResult.UNAVAILABLE_LIVE

        except VideoUnavailable: return YouTubeFetchingResult.UNKNOWN

    _logger.warning(f'BotDetection: exhausted {max_attempts} attempts for url={url}')
    return YouTubeFetchingResult.BOT_DETECTION
