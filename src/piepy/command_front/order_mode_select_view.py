from enum import Enum, auto

import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView, Select, Container, TextDisplay, ActionRow

from piepy.player_manager import PlayerManager
from piepy.utils import theme


class OrderMode(Enum):
    def __new__(cls, value, is_loop: bool, is_random_order: bool, label: str):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, is_loop: bool, is_random_order: bool, label: str):
        self.is_loop: bool = is_loop
        self.is_random_order: bool = is_random_order
        self.label: str = label

    ONCE_IN_ORDER = (
        auto(), False, False,
        '순서대로 한번씩'
    )
    ONCE_IN_RANDOM = (
        auto(), False, True,
        '무작위 순서로 한번씩'
    )
    LOOP_IN_ORDER = (
        auto(), True, False,
        '순서대로 무한반복'
    )
    LOOP_IN_RANDOM = (
        auto(), True, True,
        '무작위 순서로 무한반복'
    )


class OrderModeSelectView(LayoutView):
    def __init__(
            self,
            title: str,
            player_manager: PlayerManager,
            guild_id: int,
    ):
        super().__init__(timeout=60)

        self.player_manager: PlayerManager = player_manager
        self.guild_id: int = guild_id

        select = Select(
            placeholder='순서 방식을 선택해 주세요',
            options=[
                *[
                    discord.SelectOption(label=mode.label, value=mode.name)
                    for mode in OrderMode
                ],
            ],
        )
        select.callback = self.on_select

        self.add_item(
            Container(
                TextDisplay(f'### {title}'),
                ActionRow(select),
                accent_color=theme.OK_COLOR
            )
        )

    async def on_select(self, interaction: discord.Interaction):
        value = interaction.data['values'][0]
        mode: OrderMode = next(filter(lambda m: m.name == value, OrderMode))
        is_success = self.player_manager.change_order_mode(self.guild_id, mode.is_loop, mode.is_random_order)
        response: InteractionResponse = interaction.response

        if is_success:
            await response.send_message(
                embed=Embed(
                    title='ORDER_MODE_CHANGED',
                    description='순서 방식이 변경되었습니다',
                    color=theme.OK_COLOR
                )
            )
        else:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇 기능을 사용중이지 않습니다! `/재생` 명령어를 써보세요',
                    color=theme.ERROR_COLOR
                )
            )
