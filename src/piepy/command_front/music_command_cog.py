from yspy.__future__ import VideosSearch

from discord import Embed
from discord.ext import commands
from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable
from yarl import URL

from piepy.player_manager import PlayerManager, UrlStreamMusicElement, MusicAddingResult, MusicElement, PlayerController
from piepy.utils import theme
from .next_music_select_view import NextMusicSelectView
from .order_mode_select_view import OrderModeSelectView
from .playlist_view import PlaylistView
from .removing_music_select_view import RemovingMusicSelectView


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


class MusicCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot, player_manager: PlayerManager):
        self.bot: commands.Bot = bot
        self.player_manager: PlayerManager = player_manager

    async def check_user_voice_state(self, ctx: commands.Context, auto_ready: bool = False) -> PlayerController | None:
        player_controller = self.player_manager.get_player_controller(ctx.guild.id)

        if ctx.author.voice is None:
            await ctx.reply(
                embed=Embed(
                    title='NOT_CONNECTED',
                    description=f'이 명령어를 사용하기 위해선 먼저 이 서버의 아무 통화방에 접속해 주세요!',
                    color=theme.ERROR_COLOR
                )
            )
            return None
        elif player_controller is not None:
            player_voice_channel = player_controller.current_channel

            if ctx.author.voice.channel != player_voice_channel:
                await ctx.reply(
                    embed=Embed(
                        title='CHANNEL_MISMATCH',
                        description=f'이 명령어를 사용하기 위해선 먼저 {player_voice_channel.mention} 통화방에 접속해 주세요!',
                        color=theme.ERROR_COLOR
                    )
                )
                return None
        elif player_controller is None and not auto_ready:
            await ctx.reply(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇 기능을 사용중이지 않습니다! /재생 명령어를 써보세요',
                    color=theme.ERROR_COLOR
                )
            )
            return None

        player_controller = await self.player_manager.ready_player(ctx.guild.id, ctx.author.voice.channel)

        return player_controller


    class PlayFlags(commands.FlagConverter):
        url_or_query: str = \
            commands.Flag(name='주소나_검색어', description='유튜브 영상의 주소나 검색어를 입력하세요')

    @commands.hybrid_command(name='재생', description='영상을 재생하거나 재생목록에 영상을 추가합니다')
    async def play(self, ctx: commands.Context, *, flags: PlayFlags):
        is_valid_context = await self.check_user_voice_state(ctx, auto_ready=True)
        if not is_valid_context:
            return

        is_youtube_url = True

        try:
            YouTube(flags.url_or_query)
        except RegexMatchError:
            is_youtube_url = False
        except VideoUnavailable:
            is_youtube_url = False

        if is_youtube_url:
            yt = YouTube(flags.url_or_query)
            url = flags.url_or_query
            query = None

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
                        text='혹시 URL 을 넣었는데 이게 표시됐나요? 비공개 동영상이나 기타 이유로 볼 수 없는 동영상일 수도 있습니다'
                    )
                )

            yt = YouTube(results[0])
            url = results[0]

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

        music_add_result = await self.player_manager.play_or_add(
            ctx.guild.id,
            voice_channel=ctx.author.voice.channel,
            music_element=music,
        )

        if music_add_result == MusicAddingResult.CREATED_AND_ADDED:
            await ctx.reply(
                embed=Embed(
                    title='CONNECTED_AND_PLAYED',
                    description=f'**{music.title}** 영상을 연결 및 재생합니다!',
                    color=theme.OK_COLOR,
                    url=music.url
                ).set_thumbnail(url=music.title_image_url)
                .set_footer(text=f'검색어: {query}' if query is not None else None)
            )

        elif music_add_result == MusicAddingResult.ADDED:
            await ctx.reply(
                embed=Embed(
                    title='ADDED_TO_PLAYLIST',
                    description=f'**{music.title}** 영상을 재생목록에 추가했습니다',
                    color=theme.OK_COLOR,
                    url=music.url
            ).set_thumbnail(url=music.title_image_url)
                .set_footer(text=f'검색어: {query}' if query is not None else None)
            )

        elif music_add_result == MusicAddingResult.DUPLICATED:
            await ctx.reply(
                embed=Embed(
                    title='DUPLICATED',
                    description=f'**{music.title}** 영상은 중복됩니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'검색어: {query}' if query is not None else None)
            )

    @commands.hybrid_command(name='나가', description='재생을 멈추고 통화방을 나갑니다')
    async def stop(self, ctx: commands.Context):
        is_valid_context = await self.check_user_voice_state(ctx, is_first=True)
        if not is_valid_context:
            return

        await self.player_manager.stop(ctx.guild.id)

        await ctx.reply(
            embed=Embed(
                title='BYE_BYE',
                description='재생을 멈추고 통화방을 나갑니다',
                color=theme.OK_COLOR
            )
        )

    @commands.hybrid_command(name='제거', description='재생목록에서 영상을 하나 제거합니다')
    async def rm(self, ctx: commands.Context):
        is_valid_context = await self.check_user_voice_state(ctx, is_first=True)
        if not is_valid_context:
            return

        player_state = self.player_manager.get_player_state(ctx.guild.id)

        await ctx.reply(
            view=RemovingMusicSelectView(
                '재생목록에서 뺄 영상을 골라 주세요',
                self.player_manager,
                player_state.guild_id,
                player_state.musics
            )
        )

    @commands.hybrid_command(name='다음', description='다음 영상을 바로 재생하거나 지정한 영상으로 건너뜁니다')
    async def next(self, ctx: commands.Context):
        is_valid_context = await self.check_user_voice_state(ctx)
        if not is_valid_context:
            return

        player_state = self.player_manager.get_player_state(ctx.guild.id)
        musics = player_state.musics

        await ctx.reply(
            view=NextMusicSelectView(
                '다음 영상으로 건너 뛰거나, 재생할 영상을 골라 주세요',
                self.player_manager,
                player_state.guild_id,
                musics,
            )
        )

    @commands.hybrid_command(name='목록', description='현재 재생목록을 확인합니다')
    async def list(self, ctx: commands.Context):
        is_valid_context = await self.check_user_voice_state(ctx)
        if not is_valid_context:
            return

        player_state = self.player_manager.get_player_state(ctx.guild.id)
        musics = player_state.musics

        await ctx.reply(
            view=PlaylistView(
                '현재 재생목록',
                self.player_manager,
                player_state.guild_id,
                musics,
                player_state.current_music
            )
        )

    @commands.hybrid_command(name='순서', description='반복할지, 한번만 재생할지, 무작위로 재생할지 등을 설정합니다')
    async def order(self, ctx: commands.Context):
        is_valid_context = await self.check_user_voice_state(ctx)
        if not is_valid_context:
            return

        await ctx.reply(
            view=OrderModeSelectView(
                '어떤 순서로 영상을 재생할까요?',
                self.player_manager,
                ctx.guild.id
            )
        )
