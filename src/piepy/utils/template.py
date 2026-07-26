from . import theme
from discord import Embed
from discord.ext import commands


# TODO 이름 get_error_embed 로 바꾸고, 기능고 그렇게 하도록 바꾸기 (Context 가 아닌 상황에서 못씀;;) 아니다 걍 폐기하자 조만간
async def send_error_embed(
        ctx: commands.Context,
        title: str,
        description: str,
        footer: str | None=None,
        **kwargs
):
    embed = Embed(
        title=title,
        description=description,
        color=theme.ERROR_COLOR,
        **kwargs
    )
    if footer:
        embed.set_footer(text=footer)

    await ctx.send(embed=embed)