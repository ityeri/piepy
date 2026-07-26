import logging
import uuid

from discord import Embed, VoiceChannel
from discord.ext import commands
from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable

from piepy.utils import theme
from piepy.utils.template import send_error_embed
from .ui import PanelManager, LoopModeView
from .core import GuildManagerPool, GuildMusicManager, GuildManagerEvent, StopReason, Music
from .utils import get_guild_display_info, get_urls_by_query, parse_time
from .youtube import download_audio


# TODO  테스트, 페널, 검색기능?, 재생목록 지원, 그거그거 재생모드
# TODO 믹서 만들어서, 10초 건너뛰기, 배속 기타 등등... 플래그 전부 익스텐션 클래스 안으로 넣기


class PlayFlags(commands.FlagConverter):
    url_or_query: str = \
        commands.Flag(name="주소나_검색어", description="유튜브 영상의 주소나 검색어를 입력하세요")

class NextFlags(commands.FlagConverter):
    title_or_index: str | None = \
        commands.Flag(name="번호나_제목", description="영상의 번호나 제목 또는 제목의 일부를 입력하세요")

class RmFlags(commands.FlagConverter):
    title_or_index: str = \
        commands.Flag(name="번호나_제목", description="영상의 번호나 제목 또는 제목의 일부를 입력하세요")

def query_music_naturally(musics: list[Music], title_or_index: str) -> Music | None:
    try:
        index: int = int(title_or_index) - 1

        if 0 <= index:  # 맞다 파이썬 음수 인덱스도 있었지
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


class MusicExtension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.guild_pool = GuildManagerPool(self.bot)
        self.guild_pool.listeners.add_listener(GuildManagerEvent.END, self.on_play_end)

        self.panel_manager = PanelManager(self.bot)

        self.logger = logging.getLogger("MusicExtension")


    async def music_command_preprocessing(self, ctx: commands.Context, is_starting: bool = False) -> GuildMusicManager | None:
        guild_manager = self.guild_pool.get_guild(ctx.guild)

        user_voice_channel: VoiceChannel | None = None

        if ctx.author.voice:
            if ctx.author.voice.channel.guild == guild_manager.guild:
                user_voice_channel = ctx.author.voice.channel

        # 정상! -> 봇 접속 X 사용자 접속 O, 봇이랑 사용자 같은곳 접속
        # 암때나 접속 ㄱ -> 봇 접속 X 사용자 접속 X
        # 여기에 접속 ㄱ -> 봇 접속 O 사용자 접속 X

        if not guild_manager.is_running and user_voice_channel is None:
            if is_starting:
                await send_error_embed(
                    ctx, "UserNotConnectedError",
                    "먼저 이 서버의 아무 음성 채팅방에 접속해 주세요"
                )
            else:
                await send_error_embed(
                    ctx, "UserNotConnectedError & NotRunningError",
                    "먼저 이 서버의 아무 음성 채팅방에 접속한 후, 영상 기능을 시작해 주세요"
                )

            return None

        elif not guild_manager.is_running and user_voice_channel is not None:
            if not is_starting:
                await send_error_embed(
                    ctx, "NotRunningError",
                    "영상 기능을 사용중이지 않습니다",
                    footer="/재생 <영상 링크 또는 검색어>"
                )
                return None
            else:
                return guild_manager

        elif guild_manager.is_running and guild_manager.current_channel != user_voice_channel:
            await send_error_embed(
                ctx, "UserNotConnectedError",
                f"먼저 <#{guild_manager.current_channel.id}> 이곳에 접속해 주세요"
            )
            return None

        else:
            return guild_manager


    @commands.hybrid_command(name="재생", description="영상을 재생하거나 플레이리스트에 영상을 추가합니다")
    async def play(self, ctx: commands.Context, *, flags: PlayFlags):

        guild_manager = await self.music_command_preprocessing(ctx, is_starting=True)
        if guild_manager is None:
            return

        yt: YouTube = None # type: ignore
        url: str = None # type: ignore
        query: str = None # type: ignore
        searched = False


        try:
            yt = YouTube(flags.url_or_query) # 이거 통과되면 유튭 url 인거인
            url = flags.url_or_query

        except RegexMatchError:
            query = flags.url_or_query
            searched = True

        except VideoUnavailable:
            query = flags.url_or_query
            searched = True

        if searched:
            try:
                url = (await get_urls_by_query(query, limit=1))[0]
                yt = YouTube(url)
            except IndexError:
                await send_error_embed(
                    ctx, "QueryError",
                    f"검색어 **{query}**\n 에 대한 검색 결과를 찾을수 없습니다",
                    footer="유튜브 영상 링크를 넣었는데, 이 메세지가 보인다면, 영상 링크 또는 영상 자체가 잘못되었을수 있습니다"
                )
                return


        await ctx.defer()

        file_path = f"temp/{uuid.uuid4()}.thismustaudiofile"
        await download_audio(url, file_path, None)

        music = Music("yt_" + yt.video_id, yt.title, yt.watch_url, yt.thumbnail_url, yt.length, file_path)

        if music.music_id in [m.music_id for m in guild_manager.get_all_musics()]:
            await send_error_embed(
                ctx, "DuplicateError",
                "해당 영상은 중복됩니다",
                footer="/목록 명령으로 재생목록에 올라가 있는 영상들을 확인할수 있습니다"
            )
            return

        guild_manager.add_music(music)

        is_immediately_play = False

        if not guild_manager.is_running:
            await guild_manager.start(ctx.author.voice.channel, 0)
            is_immediately_play = True

        embed = Embed(
            url=url,
            title=music.title,
            color=theme.OK_COLOR
        )
        embed.set_image(url=music.title_image_url)

        if is_immediately_play:
            embed.description = f"영상을 바로 재생합니다\n`{parse_time(yt.length)}`"
        else:
            embed.description = f"영상을 재생 목록에 추가합니다\n`{parse_time(yt.length)}`"

        if searched:
            embed.set_footer(text=f'검색어: \"{query}\" | 관리자용 새기능 생김: "/검열 ..."')


        await ctx.send(embed=embed)


    @commands.hybrid_command(name="나가", description="재생을 멈추고 통화방을 나갑니다")
    async def stop(self, ctx: commands.Context):
        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        try:
            await guild_manager.stop(StopReason.USER_CONTROL)
        except RuntimeError:
            await ctx.send(embed=Embed(
                description="이미 통화방을 나갔습니다 ~~이거 아마 버그일꺼인~~",
                color=theme.WARN_COLOR
            ))
        else:
            await ctx.send(embed=Embed(
                description="ㅂㅇㅂㅇ", color=theme.OK_COLOR
            ))


    @commands.hybrid_command(name="빼기", description="재생목록에서 영상을 하나 제거합니다")
    async def rm(self, ctx: commands.Context, *, flags: RmFlags):

        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        music = query_music_naturally(
            guild_manager.get_all_musics(),
            flags.title_or_index
        )

        if music is not None:
            if music == guild_manager.current_music:
                await send_error_embed(
                    ctx, "ElementError",
                    "현재 재생중인 영상은 제거할수 없습니다"
                )
                return

            guild_manager.rm_music(music)
            await ctx.send(embed=Embed(
                title=f"\"**{music.title}**\" 영상을 제거했습니다", color=theme.OK_COLOR
            ))
        else:
            await send_error_embed(
                ctx, "KeyError",
                "잘못된 번호나 제목입니다",
                footer="/목록 명령어를 통해 재생목록에 있는 영상, 번호를 확인할수 있습니다"
            )


    @commands.hybrid_command(name="다음", description="다음 영상을 바로 재생하거나 지정한 영상으로 건너뜁니다")
    async def next(self, ctx: commands.Context, *, flags: NextFlags):
        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        previous_music = guild_manager.current_music
        target_music: Music | None = None

        if flags.title_or_index is not None:
            target_music = query_music_naturally(
                guild_manager.get_all_musics(),
                flags.title_or_index
            )

            if target_music is not None:
                guild_manager.skip_to(
                    target_music
                )
            else:
                await send_error_embed(
                    ctx, "KeyError",
                    "잘못된 번호나 제목입니다",
                    footer="/목록 명령어를 통해 재생목록에 있는 영상과 번호를 확인할수 있습니다"
                )
                return


        played_music = guild_manager.skip_to(target_music) # TODO 이거 이전, 다음 버튼에 복붙

        if played_music is not None:
            if played_music == previous_music:
                await ctx.send(embed=Embed(
                    title=f"\"**{played_music.title}**\" 영상을 다시 재생합니다", color=theme.OK_COLOR
                ))
            else:
                await ctx.send(embed=Embed(
                    title=f"\"**{played_music.title}**\" 영상으로 건너 뛰었습니다", color=theme.OK_COLOR
                ))

        else:
            await ctx.send(embed=Embed(
                title="현재 영상의 재생을 끝냅니다",
                description="다음으로 재생할 영상이 없습니다", color=theme.OK_COLOR
            ))


    @commands.hybrid_command(name="목록", description="현재 재생목록을 확인합니다")
    async def list(self, ctx: commands.Context):

        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        musics = guild_manager.get_all_musics()
        embed = Embed(
            title="현재 재생목록",
            description=f"현재 총 {len(musics)}개의 영상이 있습니다",
            color=theme.OK_COLOR
        )

        for i, music in enumerate(guild_manager.get_all_musics()):
            embed.add_field(name=f"{i + 1}. {music.title}", value=parse_time(music.length))
            if guild_manager.current_music == music:
                embed.add_field(name="-", value="🛐 Now Playing!")
            else:
                embed.add_field(name="", value="")

            embed.add_field(name="", value="", inline=False)

        embed.set_footer(text="/다음 <제목이나 번호> 명령어를 통해 영상으로 건너뛸수 있습니다")

        await ctx.send(embed=embed)


    @commands.hybrid_command(name="반복", description="반복할지, 말지, 셔플할지, 순서대로 재생할지 설정합니다")
    async def loop_mode(self, ctx: commands.Context):
        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        await ctx.send(
            embed=Embed(title="재생 방식을 선택해 주세요", color=theme.OK_COLOR),
            view = LoopModeView(guild_manager, True)
        )


    @commands.hybrid_command(name="패널", description="뮤직봇 기능을 편하게 사용할수 있는 UI 를 표시합니다")
    async def panel(self, ctx: commands.Context):
        guild_manager = await self.music_command_preprocessing(ctx)
        if guild_manager is None:
            return

        message = await ctx.send("패널을 만듭니다...")
        await self.panel_manager.new_panel(guild_manager, message)


    async def on_play_end(self, guild_manager: GuildMusicManager, stopped_reason: StopReason):
        if stopped_reason == StopReason.LOOP_END:
            await guild_manager.current_channel.send(
                embed=Embed(
                    title="영상을 모두 재생했습니다",
                    description="전 가봅니당",
                    color=theme.OK_COLOR
                )
            )


    @commands.Cog.listener()
    async def on_close(self):
        print("hㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗㅗ")
        for guild_manager in self.guild_pool.all_guilds():
            self.logger.info(
                f"{get_guild_display_info(guild_manager.guild)} 의 GuildMusicManager 정리중"
            )
            await guild_manager.stop(StopReason.UNKNOWN)
            await guild_manager.cleanup()


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicExtension(bot))

__all__ = [
    'setup'
]