from enum import Enum, auto

from discord import Embed
from discord.ext import commands
from pytubefix import YouTube, extract
from pytubefix.exceptions import RegexMatchError
from yarl import URL
from yspy.__future__ import VideosSearch

from piepy.player_manager import PlayerManager, UrlStreamMusicElement, MusicAddingResult, MusicElement, \
    PlayerController, PlayerStatus, PlayerStopReason, StateValidationFailedReason
from piepy.utils import theme
from .next_music_select_view import NextMusicSelectView
from .order_mode_select_view import OrderModeSelectView
from .playlist_view import PlaylistView
from .removing_music_select_view import RemovingMusicSelectView
from .youtube_fetcher import YouTubeFetchingResult, fetch_youtube


async def get_urls_by_query(query: str, limit: int) -> list[str]:
    search = VideosSearch(query, limit=limit)
    result = await search.next()

    return [single_result['link'] for single_result in result['result']]

def query_music_naturally(musics: list[MusicElement], title_or_index: str) -> MusicElement | None:
    try:
        index: int = int(title_or_index) - 1
        if 0 <= index: # 맞다 파이썬 음수 인덱스도 있었지
            try:
                return musics[index]
            except IndexError:
                pass

    except ValueError:
        title: str = title_or_index

        for checking_music in musics:
            if title in checking_music.title:
                return checking_music

    return None

def ensure_scheme(url_str: str, scheme: str = 'https') -> URL:
    url = URL(url_str)
    if not url.scheme:
        url = URL(f"{scheme}://{url_str}")
    return url

class UserVoiceAvailability(Enum):
    UNAVAILABLE = auto()
    CREATABLE = auto()
    MOVABLE = auto()


class MusicCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot, player_manager: PlayerManager):
        self.bot: commands.Bot = bot
        self.player_manager: PlayerManager = player_manager

    async def on_player_stop(self, player_controller: PlayerController, reason: PlayerStopReason):
        if reason == PlayerStopReason.END_OF_PLAY:
            await player_controller.current_channel.send(
                embed=Embed(
                    title='BYE_BYE',
                    description='모든 영상을 재생했습니다! ㅃ',
                    color=theme.OK_COLOR
                )
            )
        elif reason == PlayerStopReason.DISCONNECTED:
            await player_controller.current_channel.send(
                embed=Embed(
                    title='DISCONNECTED',
                    description='통화방과의 연결이 끊겼습니다',
                    color=theme.OK_COLOR
                )
            )
        elif reason == PlayerStopReason.SOURCE_CREATION_FAILED:
            await player_controller.current_channel.send(
                embed=Embed(
                    title='SOURCE_CREATION_FAILED',
                    description='다음으로 재생할 음악을 준비하던 중, 알 수 없는 문제가 발생했습니다!',
                    color=theme.ERROR_COLOR
                )
            )

    async def check_user_voice_state(
            self, ctx: commands.Context, is_first: bool = False
    ) -> PlayerController | UserVoiceAvailability:
        user_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
        player_controller = self.player_manager.get_player_controller(ctx.guild.id)

        if user_channel is None:
            await ctx.reply(
                embed=Embed(
                    title='NOT_CONNECTED',
                    description='이 기능을 사용하기 위해선 먼저 이 서버의 아무 통화방에 접속해 주세요!',
                    color=theme.ERROR_COLOR
                )
            )
            return UserVoiceAvailability.UNAVAILABLE

        if player_controller is None:
            if not is_first:
                await ctx.reply(
                    embed=Embed(
                        title='BOT_DISCONNECTED',
                        description='뮤직봇 기능을 사용중이지 않습니다! /재생 명령어를 써보세요',
                        color=theme.ERROR_COLOR
                    )
                )
                return UserVoiceAvailability.UNAVAILABLE
            return UserVoiceAvailability.CREATABLE

        player_channel = player_controller.current_channel

        if user_channel == player_channel:
            return player_controller

        if is_first and not any(not m.bot for m in player_channel.members):
            return UserVoiceAvailability.MOVABLE

        await ctx.reply(
            embed=Embed(
                title='CHANNEL_MISMATCH',
                description=f'이 명령어를 사용하기 위해선 먼저 {player_channel.mention} 통화방에 접속해 주세요!',
                color=theme.ERROR_COLOR
            )
        )
        return UserVoiceAvailability.UNAVAILABLE


    class PlayFlags(commands.FlagConverter):
        url_or_query: str = \
            commands.Flag(name='주소나_검색어', description='유튜브 영상의 주소나 검색어를 입력하세요')

    @commands.hybrid_command(name='재생', description='영상을 재생하거나 재생목록에 영상을 추가합니다')
    async def play(self, ctx: commands.Context, *, flags: PlayFlags):
        availability = await self.check_user_voice_state(ctx, is_first=True)
        if availability == UserVoiceAvailability.UNAVAILABLE:
            return

        await ctx.defer()

        # step1. is the url_or_query url?
        try:
            extract.video_id(flags.url_or_query)
            is_youtube_url = True
        except RegexMatchError:
            is_youtube_url = False

        # step2. get query, url from url_or_query
        if is_youtube_url:
            query = None
            url = flags.url_or_query
        else:
            query = flags.url_or_query
            results = await get_urls_by_query(query, limit=1)

            if not results:
                await ctx.reply(
                    embed=Embed(
                        title='RESULT_NOT_FOUND',
                        description=f'주어진 검색어 "{query}" 에 대한 유튜브 검색 결과가 없습니다!',
                        color=theme.ERROR_COLOR
                    ).set_footer(
                        text='혹시 URL을 넣었는데 이게 표시됐나요? URL을 다시 한번 확인해 주세요'
                    )
                )
                return

            url = results[0]

        # step3. get the YouTube object and validate
        yt = await self.fetch_youtube(ctx, url, query)
        if yt is None:
            return

        # step4. get the final stream url and create a MusicElement
        stream = max(yt.streams.filter(only_audio=True), key=lambda s: int(s.abr[:-4]) if s.abr else 0)
        audio_stream_url = stream.url

        music = UrlStreamMusicElement(
            f'yt_video_{yt.video_id}',
            title=yt.title,
            url=str(ensure_scheme(url)),
            title_image_url=yt.thumbnail_url,
            length=yt.length,
            stream_url=audio_stream_url
        )

        # step5. if necessary, ready or move a player
        if availability == UserVoiceAvailability.CREATABLE:
            player_controller = await self.player_manager.ready_player(
                ctx.guild.id, ctx.author.voice.channel, stop_callback=self.on_player_stop
            )
        elif availability == UserVoiceAvailability.MOVABLE:
            player_controller = self.player_manager.get_player_controller(ctx.guild.id)
            await player_controller.move_to(ctx.author.voice.channel)
        else:
            player_controller = availability

        # final adding and response
        music_add_result = player_controller.add_music(music)

        if music_add_result == MusicAddingResult.ADDED:
            if player_controller.status != PlayerStatus.ACTIVE:
                await ctx.reply(
                    embed=Embed(
                        title='CONNECTED_AND_PLAYED',
                        description=f'**{music.title}** 영상을 연결 및 재생합니다!',
                        color=theme.OK_COLOR,
                        url=music.url
                    ).set_thumbnail(url=music.title_image_url)
                    .set_footer(text=f'검색어: {query}' if query is not None else None)
                )
                player_controller.start()

            else:
                footer_text = f'검색어: {query}' if query is not None else None

                if availability == UserVoiceAvailability.MOVABLE:
                    footer_text += '\n  **·**  원래 봇이 있던곳이 비어 있어 자동으로 이동했습니다!'

                await ctx.reply(
                    embed=Embed(
                        title='ADDED_TO_PLAYLIST',
                        description=f'**{music.title}** 영상을 재생목록에 추가했습니다',
                        color=theme.OK_COLOR,
                        url=music.url
                    ).set_thumbnail(url=music.title_image_url)
                    .set_footer(text=footer_text)
                )

        elif music_add_result == MusicAddingResult.DUPLICATED:
            await ctx.reply(
                embed=Embed(
                    title='DUPLICATED',
                    description=f'**{music.title}** 영상은 중복됩니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )

    async def fetch_youtube(self, ctx: commands.Context, url: str, query: str | None) -> YouTube | None:
        result = fetch_youtube(url)

        # TODO most of this if statements are never be reached. read the youtube_fetcher.py
        if result == YouTubeFetchingResult.VIDEO_PRIVATE:
            await ctx.reply(
                embed=Embed(
                    title='VIDEO_PRIVATE',
                    description='비공개 영상이거나, 멤버십 전용 영상이거나, 연령 제한이 존재하는 영상입니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )
        elif result == YouTubeFetchingResult.VIDEO_REMOVED:
            await ctx.reply(
                embed=Embed(
                    title='VIDEO_REMOVED',
                    description='삭제된 영상입니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )
        elif result == YouTubeFetchingResult.VIDEO_BLOCKED:
            await ctx.reply(
                embed=Embed(
                    title='VIDEO_BLOCKED',
                    description='저작권 또는 지역 제한으로 재생할 수 없는 영상입니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )
        elif result == YouTubeFetchingResult.UNAVAILABLE_LIVE:
            await ctx.reply(
                embed=Embed(
                    title='UNAVAILABLE_LIVE',
                    description='라이브 방송은 다시보기가 아니라면 재생할 수 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )
        elif result == YouTubeFetchingResult.BOT_DETECTION:
            await ctx.reply(
                embed=Embed(
                    title='BOT_DETECTION',
                    description='영상을 가져오던중 YouTube에 의해 봇으로 감지되었습니다. 잠시 후 다시 시도해 주세요!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )
        elif result == YouTubeFetchingResult.UNKNOWN:
            await ctx.reply(
                embed=Embed(
                    title='VIDEO_UNAVAILABLE',
                    description='알 수 없는 이유로 영상에 접근할 수 없습니다!'
                                '영상 비공개, 맴버십 전용이나 연령 제한 등등이 원인일수 있습니다',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )

        if isinstance(result, YouTube):
            return result
        else:
            return None


    @commands.hybrid_command(name='나가', description='재생을 멈추고 통화방을 나갑니다')
    async def stop(self, ctx: commands.Context):
        result = await self.check_user_voice_state(ctx)
        if not isinstance(result, PlayerController):
            return
        player_controller = result

        result = await player_controller.stop()

        if result == StateValidationFailedReason.NOT_YET_ACTIVE:
            await ctx.reply(
                embed=Embed(
                    title='NOT_YET_ACTIVE',
                    description='아직 뮤직봇 기능이 시작되지 않았습니다!',
                    color=theme.ERROR_COLOR
                )
            )
        elif result == StateValidationFailedReason.ALREADY_STOPPED:
            await ctx.reply(
                embed=Embed(
                    title='ALREADY_STOPPED',
                    description='이미 뮤직봇 기능이 종료됬습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text='이 희귀한 메세지를 보시다니.. 도대체 뮤직봇을 어떻게 쓰신거죠')
            )
        else:
            await ctx.reply(
                embed=Embed(
                    title='BYE_BYE',
                    description='재생을 멈추고 통화방을 나갑니다',
                    color=theme.OK_COLOR
                )
            )

    @commands.hybrid_command(name='제거', description='재생목록에서 영상을 하나 제거합니다')
    async def rm(self, ctx: commands.Context):
        result = await self.check_user_voice_state(ctx)
        if not isinstance(result, PlayerController):
            return
        player_controller = result

        await ctx.reply(
            view=RemovingMusicSelectView('재생목록에서 뺄 영상을 골라 주세요', player_controller)
        )

    @commands.hybrid_command(name='다음', description='다음 영상을 바로 재생하거나 지정한 영상으로 건너뜁니다')
    async def next(self, ctx: commands.Context):
        result = await self.check_user_voice_state(ctx)
        if not isinstance(result, PlayerController):
            return
        player_controller = result

        await ctx.reply(
            view=NextMusicSelectView('다음 영상으로 건너 뛰거나, 재생할 영상을 골라 주세요', player_controller)
        )

    @commands.hybrid_command(name='목록', description='현재 재생목록을 확인합니다')
    async def list(self, ctx: commands.Context):
        result = await self.check_user_voice_state(ctx)
        if not isinstance(result, PlayerController):
            return
        player_controller = result

        await ctx.reply(
            view=PlaylistView('현재 재생목록', player_controller)
        )

    @commands.hybrid_command(name='순서', description='반복할지, 한번만 재생할지, 무작위로 재생할지 등을 설정합니다')
    async def order(self, ctx: commands.Context):
        result = await self.check_user_voice_state(ctx)
        if not isinstance(result, PlayerController):
            return
        player_controller = result

        await ctx.reply(
            view=OrderModeSelectView('어떤 순서로 영상을 재생할까요?', player_controller)
        )
