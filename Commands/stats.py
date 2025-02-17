from datetime import datetime
from twitchio.ext import commands
from Helpers.helpers import  is_channel_online, safe_int
from Helpers.helpers_stats import update_global_stats, get_stats, check_primero, count_user_messages

def stats_commands(bot):
    """
    Registra comandos para leer las estadísticas del bot en el bot.
    """ 

    @bot.command(name='mensajes')
    async def mensajes(ctx):
        if ctx.message.content.strip().startswith('!mensajes @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        messages_hist =await count_user_messages(user,0,0)
        await ctx.send(f"[BOT] - @{user} ha enviado: ({messages_hist}) mensaje(s)")
            
    @bot.command(name='ladrillo')
    async def ladrillo(ctx):
        ladrillos = await update_global_stats("ladrillos","channel",1)
        await update_global_stats("xp_Resistencia",ctx.author.name,0.15)
        await ctx.send(f"[BOT] - @{ctx.author.name} ha agregado un ladrillo, hemos puesto ({ladrillos})🧱 en total ")

    @bot.command(name='primero')
    async def primero(ctx):
        check_online = await is_channel_online()
        if check_online is False:
            await ctx.send("Tramposit@... 👀 este comando solo está disponible si @DannDato está en vivo.")
            return
        handle=await check_primero(ctx.author.name)
        if  handle is None:
            actualiza = await update_global_stats("first_user",ctx.author.name,1)
            await update_global_stats("xp_Resistencia",ctx.author.name,3)
            if actualiza is not None:
                ranking =await get_stats("first_user",ctx.author.name,0)
                await ctx.send(f'[BOT] - Esoo! 🔥 Parece que si has llegado primero! tus puntos actualmente {ranking[1]}: 🏆')
        else:
            if ctx.author.name==handle:
                await ctx.send(f'[BOT] -Que si @{handle}  ya sabemos que tu llegaste primero 😒')
            else:
                await ctx.send(f'[BOT] -Sorry, pero @{handle} llegó primero')
    bot.commands["primero"].category = "Llegar primero"
    
    @bot.command(name='primeroscore')
    async def primeroscore(ctx):
        if ctx.message.content.strip().startswith('!primeroscore @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        ranking =await get_stats("first_user",user,0)
        if ranking is not None:
            await ctx.send(f'[BOT] - 🏎️@{ranking[0]} En Llegar primero: ({ranking[1]}) punto{"s" if ranking[1]!="1" else ""}')
        else:
            await ctx.send(f'[BOT] - Creo que nunca has llegado primero @{user}')
    bot.commands["primeroscore"].category = "Llegar primero"

    @bot.command(name='primerotop')
    async def primerotop(ctx):
        ranking = await get_stats("first_user",None,0)
        await ctx.send(f'[BOT] - Los mas camperos del canal [🔥TOP 5]:')
        await ctx.send(f'{ranking}')
    bot.commands["primerotop"].category = "Llegar primero"



    # Comando para registrar el ganador del Wordle
    @bot.command(name='wordlewin')
    async def wordlewin(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!wordlewin @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlewin @usuario")
                return
            # Obtener el nombre del usuario mencionado
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes otorgarte el punto tu mísmo, pídele ayuda a otro moderador")
                return
            
            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("wordle_wins",mentioned_user,1)
            await update_global_stats("xp_Habilidad",mentioned_user,3)
            # Enviar respuesta al chat
            if actualiza == 0 :
                await ctx.send(f'[BOT] - 🏆 ¡@{mentioned_user} ha alcanzado 5 victorias y ha ganado una suscripción! 🎉')
            else:
                ranking =await get_stats("wordle_wins",mentioned_user,0)
                await ctx.send(f'[BOT] - Felicidades por ganar el Wordle del día! @{ranking[0]} Y tus puntos hasta ahora en 🆆🅾🆁🅳🅻🅴 son ({ranking[1]}) 🏆')
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["wordlewin"].category = "Wordle"


    @bot.command(name='wordlelose')
    async def wordlelose(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!wordlelose @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlelose @usuario")
                return
            # Obtener el nombre del usuario mencionado
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes mover el punto tu mísmo, pídele ayuda a otro moderador")
                return
            
            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("wordle_wins",mentioned_user,-1)
            
            await ctx.send(f'[BOT] - se ha descontado un punto En 🆆🅾🆁🅳🅻🅴 a @{mentioned_user}, ahora tiene ({actualiza})')
            
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["wordlelose"].category = "Wordle"


    # Comando para mostrar estadísticas globales de Wordle
    @bot.command(name='wordlescore')
    async def wordlescore(ctx):
        # Obtener estadísticas de Wordle
        if ctx.message.content.strip().startswith('!wordlescore @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        ranking =await get_stats("wordle_wins",user,0)
        if ranking is not None:
            await ctx.send(f'[BOT] - En 🆆🅾🆁🅳🅻🅴: {ranking[1]}')
        else:
            await ctx.send(f'[BOT] - Creo que @{user} nunca ha ganado el wordle')
    bot.commands["wordlescore"].category = "Wordle"


    @bot.command(name='wordlehist')
    async def wordlehist(ctx):
        # Obtener estadísticas de Wordle
        if ctx.message.content.strip().startswith('!wordlehist @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        ranking =await get_stats("wordle_wins",user,1)
        if ranking is not None:
            await ctx.send(f'[BOT] - En 🆆🅾🆁🅳🅻🅴: {ranking} TOTAL 💎')
        else:
            await ctx.send(f'[BOT] - Creo que @{user} nunca ha ganado el wordle')
    bot.commands["wordlehist"].category = "Wordle"


    @bot.command(name='wordletop')
    async def wordletop(ctx):
        ranking = await get_stats("wordle_wins",None,0)
        await ctx.send(f'[BOT] - Las estadísticas de Wordle [🔥TOP 5]:')
        await ctx.send(f'{ranking}')
    bot.commands["wordletop"].category = "Wordle"

    # Comando para registrar el ganador de un reto random
    @bot.command(name='retowin')
    async def retowin(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!retowin @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retowin @usuario")
                return
            # Obtener el nombre del usuario mencionado
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes otorgarte el punto tu mísmo, pídele ayuda a otro moderador")
                return
            # Actualizar las estadísticas 
            actualiza = await update_global_stats("reto_wins",mentioned_user,1)
            await update_global_stats("xp_Habilidad",mentioned_user,1)
            if actualiza is not None:
                await ctx.send(f'[BOT] - Felicidades! Has ganado el reto @{mentioned_user}🏆')
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["retowin"].category = "Retos"


    @bot.command(name='retolose')
    async def retolose(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!retolose @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retolose @usuario")
                return
            # Obtener el nombre del usuario mencionado
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes quitarte el punto tu mísmo, pídele ayuda a otro moderador")
                return
            
            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("reto_wins",mentioned_user,-1)
            
            await ctx.send(f'[BOT] - se ha descontado un punto a @{mentioned_user}, ahora tiene ({actualiza})')
            
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["retolose"].category = "Retos"

    @bot.command(name='retoscore')
    async def retoscore(ctx):
        # Obtener estadísticas de retos
        if ctx.message.content.strip().startswith('!retoscore @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        ranking =await get_stats("reto_wins",user,0)
        if ranking is not None:
            print(ranking)
            await ctx.send(f"[BOT] - @{user} Ha ganado ({ranking[1]}) reto{'s' if safe_int(ranking[1]) >1 else ''}")
        else:
            await ctx.send(f'[BOT] - Creo que @{user} nunca ha ganado un reto')
    bot.commands["retoscore"].category = "Retos"