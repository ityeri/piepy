import logging

import discord
from PIL import Image
from discord import User
from discord.ext import commands
from io import BytesIO

from .gif_generator import GIFGenerator

class SsudamFlags(commands.FlagConverter):
    target_user: User = \
        commands.Flag(name="쓰다듬을_사용자", description="쓰담쓰담")


class SsudamExtension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.generator: GIFGenerator = GIFGenerator()
        logging.info('load ssudam gif file...')
        self.generator.load()
        logging.info('ssudam gif file loaded')

    @commands.hybrid_command(name='쓰담', description='쓰담쓰담', aliases=['쓰다듬기'])
    async def ssudam(self, ctx: commands.Context, *, flags: SsudamFlags):
        avatar_bytes = await flags.target_user.avatar.read()
        avatar_image = Image.open(BytesIO(avatar_bytes)).convert('RGBA')
        gif_bytes = self.generator.generate_gif(avatar_image)
        await ctx.send(f'쓰담쓰담', file=discord.File(BytesIO(gif_bytes), filename='쑤담쑤담.gif'))

    # TODO 인터넷 링크 받아서 쓰담쓰답하는거


async def setup(bot: commands.Bot):
    await bot.add_cog(SsudamExtension(bot))

__all__ = [
    'setup'
]