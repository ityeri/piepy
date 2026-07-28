from discord.ext import commands
from pytubefix import YouTube

from piepy.player_manager import PlayerManager, UrlStreamMusicElement


class MusicCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot, player_manager: PlayerManager):
        self.bot: commands.Bot = bot
        self.player_manager: PlayerManager = player_manager

    class PlayFlags(commands.FlagConverter):
        url_or_query: str = \
            commands.Flag(name='주소나_검색어', description='유튜브 영상의 주소나 검색어를 입력하세요')

    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, flags: PlayFlags):
        yt = YouTube(flags.url_or_query)

        stream = max(yt.streams.filter(only_audio=True), key=lambda s: int(s.abr[:-4]) if s.abr else 0)
        audio_stream_url = stream.url

        music_add_result = await self.player_manager.play_or_add(
            ctx.guild.id,
            voice_channel=ctx.author.voice.channel,
            music_element=UrlStreamMusicElement(
                f'yt_video_{yt.video_id}',
                title='언더테일 아시는구나! 혹시 모르시는분들에 대해[1] 설명해드립니다 샌즈랑[2] 언더테일의 세가지 엔딩루트중 몰살엔딩의 최종보스로 진.짜.겁.나.어.렵.습.니.다 공격은 전부다 회피하고 만피가 92인데 샌즈의 공격은 1초당 60이 다는데다가[3] 독뎀까지 추가로 붙어있습니다.. 하지만 이러면 절대로 게임을 깰 수 가없으니 제작진[4]이 치명적인 약점을 만들었죠. 샌즈의 치명적인 약점이 바로 지친다는것입니다. 패턴들을 다 견디고나면 지쳐서 자신의 턴을 유지한채로 잠에듭니다. 하지만 잠이들었을때 창을옮겨서 공격을 시도하고 샌즈는 1차공격은 피하지만 그 후에 바로날아오는 2차 공격을 맞고 죽습니다.',
                url=flags.url_or_query,
                title_image_url=yt.thumbnail_url,
                length=1000000000000000000000.0,
                stream_url=audio_stream_url
            ),
        )

        await ctx.reply(content=music_add_result.name)
