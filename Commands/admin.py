from twitchio.ext import commands

from Helpers.helpers import is_authorized
from Helpers.helpers_admin import end_stream, start_stream
from Helpers.printlog import printlog


class admin_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot

    @commands.command(name='ini')
    async def ini(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_started = await start_stream()
        if stream_started:
            await ctx.send(' [BOT] - 🤖 Excelente! Se ha iniciado el directo correctamente en la base de datos... ¿Estan listos? 🟢')
        else:
            await ctx.send(' [BOT] - 🟡 Ya existe un stream en proceso...')

    @commands.command(name='end')
    async def end(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_ended = await end_stream()
        if stream_ended:
            await ctx.send(' [BOT] - 🤖 Listo, se ha terminado el stream. Gracias por todo! nos vemos en el siguiente directo... Chao ❤️')
        else:
            await ctx.send(' [BOT] - 🔴 No se puede finalizar un stream que no se ha iniciado...')

    @commands.command(name='restart')
    async def restart(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        await ctx.send("[BOT] - OK... un momento que me estoy reiniciando 😰")
        await self.bot.restart_process("[Monitor] - Reiniciando bot por comando autorizado...")

    @commands.command(name='status', aliases=["estas", "estas?", "hey"])
    async def botstatus(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        printlog("Chequeando estado del bot...")
        try:
            if not self.bot.connected:
                await ctx.send("[BOT] - Algo anda raro... me voy a reiniciar, pérate")
                await self.bot.restart_process("[Monitor] - WebSocket desconectado. Reiniciando bot...")
            else:
                await ctx.send("[BOT] - Todo joya 😎")
                printlog("DannDato en linea", "\033[38;5;51m")
        except Exception as e:
            printlog("Algo ha ocurrido, reiniciando bot...")
            await ctx.send("[BOT] - Ni supe que hacer, imaginate...")
            await self.bot.restart_process(f"[ Monitor ] - Error en chequeo de salud: {e}. Reiniciando...")
