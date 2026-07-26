from __future__ import annotations

from enum import Enum

import discord.ui
from discord import Embed
from discord.interactions import InteractionResponse

from piepy.utils import theme
from ..core.guild_music_manager import GuildMusicManager
from ..core.loop_manager import LoopMode


class LabeledLoopMode(Enum):
    ONCE_IN_ORDER = (
        LoopMode.ONCE_IN_ORDER, "순서대로 한번씩",
        "이제 영상을 순서대로 한번씩만 재생합니다",
        "영상을 끝가지 재생하고 나면 통화방을 나갑니다"
    )
    ONCE_IN_RANDOM = (
        LoopMode.ONCE_IN_RANDOM, "무악위로 한번씩",
        "이제 영상을 랜덤하게 한번씩만 재생합니다",
        "모든 영상을 무작위 순서로 한번씩 재생하고 나면 통화방을 나갑니다"
    )
    LOOP_IN_ORDER = (
        LoopMode.LOOP_IN_ORDER, "순서대로 무한반복",
        "이제 영상을 순서대로 계속 재생합니다",
        "영상 순서에 맞춰 무한반복 합니다"
    )
    LOOP_IN_RANDOM = (
        LoopMode.LOOP_IN_RANDOM, "무작위로 무한반복",
        "이제 영상을 랜덤하게 계속 재생합니다",
        "아무 영상이나 순서에 상관없이 계속 재생합니다"
    )

    def __init__(
            self,
            loop_mode: LoopMode,
            label: str,
            embed_title: str,
            embed_desc: str
    ):
        self.loop_mode: LoopMode = loop_mode
        self.label: str = label
        self.embed_title: str = embed_title
        self.embed_desc: str = embed_desc

    @classmethod
    def get_mode_by_label(cls, label: str) -> 'LabeledLoopMode' | None:
        for mode in LabeledLoopMode:
            if mode.label == label:
                return mode
        return None


class LoopModeSelect(discord.ui.Select):
    def __init__(
            self,
            guild_manager: GuildMusicManager,
            do_response: bool,
            **kwargs
    ):
        self.guild_manager: GuildMusicManager = guild_manager
        self.display_response: bool = do_response

        options = [
            discord.SelectOption(label=LabeledLoopMode.ONCE_IN_ORDER.label),
            discord.SelectOption(label=LabeledLoopMode.ONCE_IN_RANDOM.label),
            discord.SelectOption(label=LabeledLoopMode.LOOP_IN_ORDER.label),
            discord.SelectOption(label=LabeledLoopMode.LOOP_IN_RANDOM.label)
        ]
        super().__init__(
            placeholder="반복 방식을 선택해 주세요",
            min_values=1, max_values=1, options=options,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        mode = LabeledLoopMode.get_mode_by_label(value)
        res: InteractionResponse = interaction.response

        if self.display_response:
            await res.send_message(embed=Embed(
                title=mode.embed_title,
                description=mode.embed_desc,
                color=theme.OK_COLOR
            ))
        else:
            await res.defer(ephemeral=True)


class LoopModeView(discord.ui.View):
    def __init__(self, guild_manager: GuildMusicManager, do_response: bool):
        super().__init__()
        self.add_item(LoopModeSelect(guild_manager, do_response))