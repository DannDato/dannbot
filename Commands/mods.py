from twitchio.ext import commands

from Helpers.helpers import is_authorized, is_mod
from Helpers.helpers_admin import set_stream_title, set_stream_category, create_stream_marker


class mods_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot

    def _can_manage_stream(self, ctx) -> bool:
        return is_authorized(ctx) and is_mod(ctx)

    @commands.command(name='titulo')
    async def titulo(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send('[BOT] - Usa: !titulo <nuevo titulo>')
            return

        ok, result = await set_stream_title(parts[1].strip())
        if ok:
            await ctx.send(f'[BOT] - Titulo actualizado: {result}')
        else:
            await ctx.send(f'[BOT] - {result}')

    @commands.command(name='categoria', aliases=['cat'])
    async def categoria(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send('[BOT] - Usa: !categoria <nombre aproximado de categoria>')
            return

        ok, result = await set_stream_category(parts[1].strip())
        if ok:
            await ctx.send(f'[BOT] - Categoria actualizada a: {result}')
        else:
            await ctx.send(f'[BOT] - {result}')

    @commands.command(name='mark', aliases=['marker'])
    async def mark(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        description = parts[1].strip() if len(parts) > 1 else ""

        ok, result = await create_stream_marker(description)
        if ok:
            await ctx.send(f'[BOT] - {result}')
        else:
            await ctx.send(f'[BOT] - {result}')
