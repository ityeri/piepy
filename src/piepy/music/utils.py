from yspy.__future__ import VideosSearch

from discord import Guild
from discord.abc import GuildChannel

# 여기서 music.core 참조하면 터짐 core 에서도 music.utils 씀

def get_guild_display_info(guild: Guild) -> str:
    return f'Guild: "{guild.name}" id: {guild.id}'

def get_channel_display_info(channel: GuildChannel) -> str:
    return f'GuildChannel: "{channel.name}" id: {channel.id}'

async def get_urls_by_query(query: str, limit: int) -> list[str]:
    search = VideosSearch(query, limit=limit)
    result = await search.next()

    return [single_result["link"] for single_result in result["result"]]


def parse_time(
        time_sec: float,
        hour_suffix: str = "시간",
        min_suffix: str = "분",
        sec_suffix: str = "초",
        sep: str = " "
) -> str:
    hour = time_sec // 3600
    time_sec %= 3600

    mins = time_sec // 60
    time_sec %= 60

    sec = int(time_sec)

    out = str(sec) + sec_suffix

    if 0 < mins:
        out = str(mins) + min_suffix + sep + out

    if 0 < hour:
        out = str(hour) + hour_suffix + sep + out

    return out