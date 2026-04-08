from twitchio.ext import commands

from Helpers.helpers import is_authorized, is_mod
from Helpers.helpers_moderator import (
    set_stream_title,
    set_stream_category,
    create_stream_marker,
    save_basic_command,
    edit_basic_command,
    delete_basic_command,
    custom_command_exists,
)


class moderator_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot

    def _can_manage_stream(self, ctx) -> bool:
        # Permitir si es moderador o está en la lista autorizada.
        return is_authorized(ctx) or is_mod(ctx)

    @commands.command(name='titulo', aliases=['title'])
    async def titulo(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send('[BOT] - Usa: !titulo <nuevo titulo>')
            return

        ok, result = await set_stream_title(parts[1].strip())
        await ctx.send(f'[BOT] - {"Titulo actualizado: " + result if ok else result}')

    @commands.command(name='categoria', aliases=['cat', 'game', 'category','categoría'])
    async def categoria(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send('[BOT] - Usa: !categoria <nombre aproximado de categoria>')
            return

        ok, result = await set_stream_category(parts[1].strip())
        await ctx.send(f'[BOT] - {"Categoria actualizada a: " + result if ok else result}')

    @commands.command(name='mark', aliases=['marker'])
    async def mark(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        description = parts[1].strip() if len(parts) > 1 else ""

        ok, result = await create_stream_marker(description)
        await ctx.send(f'[BOT] - {result}')

    @commands.command(name='newcmd', aliases=['ncmd'])
    async def newcmd(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 2)
        if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
            await ctx.send('[BOT] - Usa: !newcmd <!comando> <respuesta>')
            return

        command_name = parts[1].strip().lower()
        command_lookup = command_name[1:] if command_name.startswith('!') else command_name
        if self.bot.get_command(command_lookup):
            await ctx.send('[BOT] - Ese comando ya existe en el bot. Usa otro nombre.')
            return

        ok, result = await save_basic_command(parts[1].strip(), parts[2].strip())
        if ok:
            await ctx.send(f'[BOT] - Comando guardado: {result}')
        else:
            await ctx.send(f'[BOT] - {result}')

    @commands.command(name='delcmd', aliases=['dcmd', 'rmcmd'])
    async def delcmd(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send('[BOT] - Usa: !delcmd <!comando>')
            return

        command_name = parts[1].strip().split()[0]
        command_lookup = command_name[1:] if command_name.startswith('!') else command_name
        if self.bot.get_command(command_lookup):
            await ctx.send('[BOT] - Ese comando pertenece al bot y no se puede eliminar con !delcmd.')
            return
        if not custom_command_exists(command_name):
            await ctx.send('[BOT] - Ese comando personalizado no existe en la base de datos.')
            return

        ok, result = await delete_basic_command(command_name)
        if ok:
            await ctx.send(f'[BOT] - Comando eliminado: {result}')
        else:
            await ctx.send(f'[BOT] - {result}')

    @commands.command(name='editcmd', aliases=['ecmd'])
    async def editcmd(self, ctx):
        if not self._can_manage_stream(ctx):
            await ctx.send("[BOT] - Hey, este comando es solo para usuarios autorizados y moderadores 😑")
            return

        parts = ctx.message.text.strip().split(' ', 2)
        if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
            await ctx.send('[BOT] - Usa: !editcmd <!comando> <nueva respuesta>')
            return

        command_name = parts[1].strip().split()[0]
        command_lookup = command_name[1:] if command_name.startswith('!') else command_name
        if self.bot.get_command(command_lookup):
            await ctx.send('[BOT] - Ese comando pertenece al bot y no se puede editar con !editcmd.')
            return
        if not custom_command_exists(command_name):
            await ctx.send('[BOT] - Ese comando personalizado no existe en la base de datos.')
            return

        ok, result = await edit_basic_command(command_name, parts[2].strip())
        if ok:
            await ctx.send(f'[BOT] - Comando editado: {result}')
        else:
            await ctx.send(f'[BOT] - {result}')
