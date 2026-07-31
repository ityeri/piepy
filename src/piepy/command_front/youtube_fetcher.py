from enum import Enum, auto

from pytubefix import YouTube
from pytubefix.exceptions import *


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
            return yt
        except BotDetection: pass

        except VideoPrivate: return YouTubeFetchingResult.VIDEO_PRIVATE
        except MembersOnly: return YouTubeFetchingResult.VIDEO_PRIVATE

        except VideoRemovedByUploader: return YouTubeFetchingResult.VIDEO_REMOVED
        except VideoRemovedByYouTubeForViolatingTOS: return YouTubeFetchingResult.VIDEO_REMOVED

        except VideoRegionBlocked: return YouTubeFetchingResult.VIDEO_BLOCKED
        except VideoBlockedByCopyright: return YouTubeFetchingResult.VIDEO_BLOCKED

        except LiveStreamError: return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamEnded: return YouTubeFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamOffline: return YouTubeFetchingResult.UNAVAILABLE_LIVE

        except VideoUnavailable: return YouTubeFetchingResult.UNKNOWN

        tries += 1

    return YouTubeFetchingResult.BOT_DETECTION
