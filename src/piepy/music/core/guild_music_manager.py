from __future__ import annotations

import logging
import traceback
from enum import Enum, auto
from logging import Logger
from typing import Callable, Awaitable

from discord import Guild, VoiceClient, VoiceChannel, VoiceState, Member
from discord.ext import commands

from piepy.async_listener import AsyncListenerManager, AsyncEventEnum
from .loop_manager import MusicLoopManager, LoopMode
from .music import Music
from ..utils import get_guild_display_info, get_channel_display_info


class StopReason(Enum):
    USER_CONTROL = auto() # 사용자가 명령어로 정지함
    LOOP_END = auto() # 플리 재생 다함 (루프에 다음이 ㅇ벖음)
    UNKNOWN = auto() # 괄자가 끊었거나 그외 겁나 신비로운 상황들 (대부분은 통방 추방 먹은거인)

class GuildManagerEvent(AsyncEventEnum):
    END = (Callable[['GuildMusicManager', StopReason], Awaitable[None]],)
    LOOP_SWITCH = (Callable[['GuildMusicManager'], Awaitable[None]],)
    LOOP_MODE_CHANGE = (Callable[['GuildMusicManager'], Awaitable[None]])
    PLAYLIST_MODIFY = (Callable[['GuildMusicManager'], Awaitable[None]])

# TODO 장기적으로 loop_manager 는 private 으로 바꾸는게 좋을듯
class GuildMusicManager:
    # 재생이 정지될수 있는 케이스 + 과정
    # 재생 목록에 있는거 다 틀었을 경우: loop 에서 END 로 stop 호출 -> vc.disconn -> on_voice_state_update -> on_disconne
    # 명령어로 중지되면: 외부에서 COMMAND 로 stop 호출 -> vc.disconn -> on_voice_state_update -> on_disconne
    # 괄자가 연결 끊기로 끊는거나 그외 신비로운 이유: on_voice_state_update -> on_disconne

    # 괄자가 연결 끊기로 끊는거나 그외 신비로운 이유에 경우에는
    # on_voice_state_update 쪽에서 UNKNOWN 으로 전처리 함으로서 stop 함수를 대신함


    def __init__(self, bot: commands.Bot, guild: Guild):
        self.bot: commands.Bot = bot
        self.guild: Guild = guild

        # is_running == voice_client.is_connected 대부분에 상황에선 이럼
        self.is_running: bool = False
        self.voice_client: VoiceClient | None = None

        self._loop_manager: MusicLoopManager = MusicLoopManager(LoopMode.ONCE_IN_ORDER)

        self.logger: Logger = logging.getLogger("GuildMusicManager " + get_guild_display_info(self.guild))

        # 재생이 왜 중단됬는가?
        # 괄자가 연결 끊기 하는것마냥 끊으면 얘는 UNKNOWN 임 (제발 그래야함)
        # 얘 값에 따라 on_disconnect 의 행동이 바뀜
        # on_disconnect 호출 시점엔 self.stopped_reason 가 None 이 아니여야 함 (엄청 특수한 경우 아니면)
        self.stop_reason: StopReason | None = None
        # 굳이 None 이랑 StoppedReason 랑 바꿔갈 필요는 없는데 걍 변?수 통?제용
        self.listeners: AsyncEventEnum[GuildManagerEvent] = AsyncListenerManager()

        self.bot.add_listener(self.on_voice_state_update)

    @property
    def current_channel(self) -> VoiceChannel | None:
        if self.voice_client:
            return self.voice_client.channel
        else: return None

    @property
    def current_music(self) -> Music | None:
        return self._loop_manager.current_music

    @property
    def current_music_index(self) -> int | None:
        return self._loop_manager.current_index

    @property
    def loop_mode(self) -> LoopMode:
        return self._loop_manager.loop_mode

    def get_all_musics(self) -> list[Music]:
        return self._loop_manager.get_all_musics()

    def get_music_by_id(self, music_id: str) -> Music | None:
        return self._loop_manager.get_music_by_id(music_id)


    async def start(self, channel: VoiceChannel, start_index: int):

        if self.guild != channel.guild:
            raise ValueError("채널이 딴 길드에 있음;;")

        if self.is_running:
            raise RuntimeError("이미 돌아가는중")


        self._loop_manager.reset_loop()
        self._loop_manager.current_index = None
        self._loop_manager.next_index = start_index

        self.voice_client: VoiceClient = await channel.connect()
        self.loop()
        self.is_running = True
        self.logger.info(f"{get_channel_display_info(channel)} 에서 시작됨")

    async def stop(self, stopped_reason: StopReason):

        if not self.is_running:
            raise RuntimeError("이미 중지됨")

        self.stop_reason = stopped_reason
        await self.voice_client.disconnect() # -> on_disconnect


    def skip_to(self, next_music: Music | None = None) -> Music:
        if next_music is not None:
            self._loop_manager.next_music = next_music

            if next_music in self._loop_manager.tried_musics:
                self._loop_manager.tried_musics.remove(next_music)

        actual_next_music = self._loop_manager.next_music
        self.voice_client.stop() # vc.stop() 은 콜백에 e 로 None 넣어줌 (에러 없)

        return actual_next_music

    def set_loop_mode(self, loop_mode: LoopMode):
        if not self.is_running:
            raise RuntimeError("is_running 중이 아닙니다")

        self._loop_manager.loop_mode = loop_mode
        self._loop_manager.reset_loop()
        self._loop_manager.update_next_index()
        self.bot.loop.create_task(
            self.listeners.dispatch_event(GuildManagerEvent.LOOP_MODE_CHANGE, self)
        )

    async def cleanup(self):
        if self.voice_client:
            await self.voice_client.disconnect()

        for music in self._loop_manager.get_all_musics():
            music.cleanup()


    def add_music(self, music: Music):
        self._loop_manager.add(music)
        self.bot.loop.create_task(
            self.listeners.dispatch_event(GuildManagerEvent.PLAYLIST_MODIFY)
        )

    def rm_music(self, music: Music):
        if music == self._loop_manager.current_music:
            raise ValueError("현재 재생에 사용중인 음악은 제거할수 없습니다")
        self._loop_manager.rm(music)
        self.bot.loop.create_task(
            self.listeners.dispatch_event(GuildManagerEvent.PLAYLIST_MODIFY)
        )


    async def on_disconnect(self):
        # 얜 항상 disconnect 이후에 호출됨

        if self.stop_reason is None:
            self.logger.warning("stopped_reason 이 None 임. 무시. (원래 이게 None 이면 안ㄷ댐;;)")
        else:
            self.logger.info(f"중단 사유: {self.stop_reason}")

        await self.listeners.dispatch_event(GuildManagerEvent.END, self, self.stop_reason)

        self.voice_client.cleanup()
        self._loop_manager.clear_all()

        disconnected_channel = self.current_channel

        self.voice_client = None
        self.is_running = False
        self.stop_reason = None

        self.logger.info(f"{get_channel_display_info(disconnected_channel)} 에서 종료됨")

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):

        if member != self.bot.user or member.guild != self.guild:
            return

        if self.is_running and after.channel is None:
            if self.stop_reason is None:
                # self.stopped_reason 이 None 이면 stop 에 의한 정상적인 전처리를 거치치 못했음을 의미
                # 자세한건 __init__ 함수 주석참조ㅗ
                self.stop_reason = StopReason.UNKNOWN

            await self.on_disconnect()


    def loop(self, e: Exception | None = None):

        if e is not None:
            tb = traceback.TracebackException.from_exception(e)
            tb_str = ''.join(tb.format())
            self.logger.error(f"알수 없는 에러로 재생이 중단됨. 무시함 : {e}\n{tb_str}")

        if self.voice_client is None: # vc 가 연결이 끊기면서 다음 콜백이 호출된거 감지용
            return

        elif not self.voice_client.is_connected(): # vc 가 연결이 끊기면서 다음 콜백이 호출된거 감지용
            return

        elif not self._loop_manager.has_next():
            self.logger.info("Playing will stopping by GuildMusicManager.loop method!")
            self.bot.loop.create_task(self.stop(StopReason.LOOP_END))
            # asyncio.run_coroutine_threadsafe( # 쓰레드 ㅏㅇㄴ전이 뭐임?
            #     self.stop(StoppedReason.END),
            #     asyncio.get_event_loop()
            # )
            return

        current_music = self._loop_manager.next()
        current_music.ready()
        self.bot.loop.create_task(self.listeners.dispatch_event(GuildManagerEvent.LOOP_SWITCH, self))
        self.voice_client.play(current_music.source, after=self.loop)