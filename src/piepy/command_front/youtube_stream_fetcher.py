from enum import Enum, auto

from pytubefix import Stream, YouTube
from pytubefix.exceptions import *


class StreamFetchingResult(Enum):
    VIDEO_PRIVATE = auto()
    VIDEO_REMOVED = auto()
    VIDEO_BLOCKED = auto()
    UNAVAILABLE_LIVE = auto()
    BOT_DETECTION = auto()
    UNKNOWN = auto()

def get_highest_resolution_audio_stream(url: str, max_attempts: int = 10) -> Stream | StreamFetchingResult:
    tries = 0

    while (tries < max_attempts):
        yt = YouTube(url)

        try:
            stream = max(yt.streams.filter(only_audio=True), key=lambda s: int(s.abr[:-4]) if s.abr else 0)
            return stream
        except BotDetection: pass

        except VideoPrivate: return StreamFetchingResult.VIDEO_PRIVATE
        except MembersOnly: return StreamFetchingResult.VIDEO_PRIVATE

        except VideoRemovedByUploader: return StreamFetchingResult.VIDEO_REMOVED
        except VideoRemovedByYouTubeForViolatingTOS: return StreamFetchingResult.VIDEO_REMOVED

        except VideoRegionBlocked: return StreamFetchingResult.VIDEO_BLOCKED
        except VideoBlockedByCopyright: return StreamFetchingResult.VIDEO_BLOCKED

        except LiveStreamError: return StreamFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamEnded: return StreamFetchingResult.UNAVAILABLE_LIVE
        except LiveStreamOffline: return StreamFetchingResult.UNAVAILABLE_LIVE

        except VideoUnavailable: return StreamFetchingResult.UNKNOWN

        tries += 1

    return StreamFetchingResult.BOT_DETECTION
