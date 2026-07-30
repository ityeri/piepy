from abc import ABC

import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView

from piepy.player_manager import PlayerController, PlayerStatus, MusicElement
from piepy.utils import theme


class PlayerContextView(ABC, LayoutView):
    def __init__(self, player_controller: PlayerController, *, timeout: float | None):
        super().__init__(timeout=timeout)
        self.controller: PlayerController = player_controller

    async def validate_player_context(self, interaction: discord.Interaction, command_name: str) -> bool:
        response: InteractionResponse = interaction.response

        if self.controller.status == PlayerStatus.ACTIVE:
            return True
        else:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇을 사용중이지 않거나 사용하신 임베드가 너무 오래전에 생겼습니다',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'/재생 명령어를 쓰거나 {command_name} 명령어로 새 임베드를 띄워보세요')
            )
            return False

    async def get_music_by_id(
            self,
            interaction: discord.Interaction,
            music_id: str,
            command_name: str
    ) -> MusicElement | None:
        response: InteractionResponse = interaction.response

        try:
            return next(filter(lambda m: m.id == music_id, self.controller.musics))
        except StopIteration:
            await response.send_message(
                embed=Embed(
                    title='MUSIC_NOT_FOUND',
                    description=f'해당 영상은 현재 재생목록에 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text=f'{command_name} 명령어로 이 UI를 다시 띄워보세요')
            )
            return None
