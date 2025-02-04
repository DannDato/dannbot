
from Helpers.helpers import normalize_username, is_authorized
from Helpers.helpers_admin import end_stream, start_stream, end_mail
from Helpers.mailer import enviar_correo

def admin_commands(bot):

    @bot.command(name='ini')
    async def iniciar(ctx):
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            streamEnded = await start_stream()
            if streamEnded==True:
                await ctx.send(f' [BOT] - 🤖 Se ha Iniciado el directo correctamente en la base de datos 🟢')
            else:
                await ctx.send(f' [BOT] - 🟡 Ya existe un stream en proceso...')
    bot.commands["ini"].category = "Administrador"

    @bot.command(name='end')
    async def finalizar(ctx):
        if not is_authorized(ctx):  # Comprobamos si el usuario está autorizado
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return
        else:
            streamEnded = await end_stream()
            if streamEnded==True:
                await ctx.send(f' [BOT] - 🤖 Se ha terminado el stream, nos vemos en el siguiente directo ❤️')
            else:
                await ctx.send(f' [BOT] - 🔴 No se puede finalizar un stream que no se ha iniciado...')
    bot.commands["end"].category = "Administrador"

    # @bot.command(name='mail')
    # async def mail(ctx):
    #     if not is_authorized(ctx): return
    #     html = await end_mail()        # Ejemplo de uso
    #     await enviar_correo("danieltova97@gmail.com", "Prueba de correo", html)

    

    
