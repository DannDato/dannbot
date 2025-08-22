import os
import sys
from Helpers.helpers import is_authorized
from Helpers.helpers_admin import end_stream, start_stream
from twitchio.ext import commands
from Helpers.printlog import printlog

class admin_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot

    @commands.command(name='ini')
    async def ini(self, ctx):
        print(ctx.chatter.name)
        print(ctx.chatter.id)
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            streamEnded = await start_stream()
            if streamEnded==True:
                await ctx.send(f' [BOT] - 🤖 Excelente! Se ha Iniciado el directo correctamente en la base de datos... ¿Estan listos? 🟢')
            else:
                await ctx.send(f' [BOT] - 🟡 Ya existe un stream en proceso...')

    @commands.command(name='end')
    async def end(self, ctx):
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            streamEnded = await end_stream()
            if streamEnded==True:
                await ctx.send(f' [BOT] - 🤖 Listo, Se ha terminado el stream, Gracias por todo! nos vemos en el siguiente directo... Chao ❤️')
            else:
                await ctx.send(f' [BOT] - 🔴 No se puede finalizar un stream que no se ha iniciado...')


    @commands.command(name='restart')
    async def restart(self, ctx):
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            printlog("[Monitor] - Reiniciando bot por comando autorizado...")
            await ctx.send("[BOT] - OK... un momento que me estoy reiniciando 😰")
            await self.bot.close()
            os.execv(sys.executable, [sys.executable] + sys.argv)

    @commands.command(name='botstatus', aliases=["estas", "estas?", "hey"])
    async def botstatus(self, ctx):
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            printlog("Chequeando estado del bot...")
            try:
                if not self.bot.connected:
                    printlog("[Monitor] - WebSocket desconectado. Reiniciando bot...","ERROR")
                    printlog("Reiniciando bot...")
                    await ctx.send("[BOT] - Algo anda raro... me voy a reiniciar, pérate")
                    await self.bot.close()
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    await ctx.send("[BOT] - Todo joya 😎")
                    printlog("DannDato en linea","\033[38;5;51m")
            except Exception as e:
                printlog("Algo ha ocurrido, reiniciando bot...")
                await ctx.send("[BOT] - Ni supe que hacer, imaginate...")
                printlog(f"[Monitor] - Error en chequeo de salud: {e}. Reiniciando...","ERROR")
                await self.bot.close()
                script = os.path.abspath(sys.argv[0])
                os.execv(sys.executable, [sys.executable, script] + sys.argv[1:])
    
    

    
