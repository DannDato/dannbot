from datetime import datetime
from twitchio.ext import commands
from Helpers.helpers import  is_channel_online, safe_int, normalize_username
from Helpers.helpers_stats import update_global_stats, get_stats, check_primero, count_user_messages, get_twitch_id

def stats_commands(bot):
    """
    Registra comandos para leer las estadísticas del bot en el bot.
    """ 
    @bot.command(name='mensajes')
    async def mensajes(ctx):
        if ctx.message.content.strip().startswith('!mensajes @'):
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.author.name
            user=ctx.author.id
        messages_hist =await get_stats("messages",user)
        await update_global_stats("xp_Voluntad",ctx.author.id,0.25)
        await ctx.send(f"[BOT] - @{mentioned_user} ha enviado: ({messages_hist[1]}) mensaje(s)")
 
    @bot.command(name='ladrillo')
    async def ladrillo(ctx):
        ladrillos = await update_global_stats("ladrillos","channel",1)
        await update_global_stats("xp_Resistencia",ctx.author.id,0.15)
        await update_global_stats("xp_Astucia",ctx.author.id,0.15)
        await update_global_stats("xp_voluntad",ctx.author.id,0.15)
        await ctx.send(f"[BOT] - @{ctx.author.name} ha agregado un ladrillo, hemos puesto ({ladrillos})🧱 en total ")

    @bot.command(name='primero')
    async def primero(ctx):
        check_online = await is_channel_online()
        if check_online is False:
            await ctx.send("Tramposit@... 👀 este comando solo está disponible si @DannDato está en vivo.")
            return
        handle=await check_primero(ctx.author.id)
        if  handle is None:
            actualiza = await update_global_stats("first_user",ctx.author.id,1)
            await update_global_stats("xp_Resistencia",ctx.author.id,3)
            await update_global_stats("xp_voluntad",ctx.author.id,0.15)
            if actualiza is not None:
                ranking =await get_stats("first_user",ctx.author.id)
                await ctx.send(f'[BOT] - Esoo! 🔥 Parece que si has llegado primero! tus puntos actualmente {ranking[1]}: 🏆')
        else:
            if ctx.author.name==handle:
                await ctx.send(f'[BOT] -Que si @{handle}  ya sabemos que tu llegaste primero 😒')
            else:
                await ctx.send(f'[BOT] -Sorry, pero @{handle} llegó primero')
    bot.commands["primero"].category = "Llegar primero"
    
    @bot.command(name='primeroscore',aliases=["ps","pscore"])
    async def primeroscore(ctx):
        # Obtener estadísticas de Wordle
        if '@' in ctx.message.content:
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.author.name
            user=ctx.author.id
        ranking = None
        ranking =await get_stats("first_user",user)
        if ranking is not None:
            await ctx.send(f'[BOT] - 🏎️@{mentioned_user} En Llegar primero: ({ranking[1]}) punto{"s" if ranking[1]!="1" else ""}')
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha llegado primero ')
    bot.commands["primeroscore"].category = "Llegar primero"

    @bot.command(name='primerotop',aliases=["pt","ptop"])
    async def primerotop(ctx):
        ranking = await get_stats("first_user",None)
        await ctx.send(f'[BOT] - Los mas camperos del canal [🔥TOP 5]:')
        await ctx.send(f'{ranking}')
    bot.commands["primerotop"].category = "Llegar primero"

    # Comando para registrar el ganador del Wordle
    @bot.command(name='wordlewin', aliases=["ww", "wwin"])
    async def wordlewin(ctx):
        # Verificar si el autor es moderador
        if ctx.author.is_mod:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.content):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlewin @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.content.strip().split('@')[1].strip())
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes otorgarte el punto a ti mismo, pídele ayuda a otro moderador")
                return

            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return

            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("wordle_wins", user, 1)
            await update_global_stats("xp_Habilidad", user, 3)
            # Responder con el mensaje apropiado
            if actualiza == 0:
                await ctx.send(f'[BOT] - 🏆 ¡@{mentioned_user} ha alcanzado 5 victorias y ha ganado una suscripción! 🎉')
            else:
                ranking = await get_stats("wordle_wins", user)
                await ctx.send(f'[BOT] - Felicidades por ganar el Wordle del día! @{mentioned_user} Y tus puntos hasta ahora en 🆆🅾🆁🅳🅻🅴 son ({ranking[1]}) 🏆')

        else:
            # Si el autor no es moderador, enviar un mensaje de error
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
        bot.commands["wordlewin"].category = "Wordle"


    @bot.command(name='wordlelose',aliases=["wl","wlose"])
    async def wordlelose(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.content):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlelose @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.content.strip().split('@')[1].strip())
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes quitarte el punto a ti mismo, pídele ayuda a otro moderador")
                return

            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
            
            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("wordle_wins",user,-1)
            
            await ctx.send(f'[BOT] - se ha descontado un punto En 🆆🅾🆁🅳🅻🅴 a @{mentioned_user}, ahora tiene ({actualiza})')
            
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["wordlelose"].category = "Wordle"


    # Comando para mostrar estadísticas globales de Wordle
    @bot.command(name='wordlescore',aliases=["ws","wscore"])
    async def wordlescore(ctx):
        # Obtener estadísticas 
        if '@' in ctx.message.content:
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.author.name
            user=ctx.author.id
        ranking =await get_stats("wordle_wins",user)
        if ranking is not None:
            await ctx.send(f'[BOT] - {mentioned_user} En 🆆🅾🆁🅳🅻🅴 tiene {ranking[1]} punto{'s' if ranking[1]>1 else ''}')
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha ganado el wordle')
    bot.commands["wordlescore"].category = "Wordle"


    @bot.command(name='wordletop',aliases=["wt","wtop"])
    async def wordletop(ctx):
        ranking = await get_stats("wordle_wins",None)
        await ctx.send(f'[BOT] - Las estadísticas de Wordle [🔥TOP 5]:')
        await ctx.send(f'{ranking}')
    bot.commands["wordletop"].category = "Wordle"

    # Comando para registrar el ganador de un reto random
    @bot.command(name='retowin',aliases=["rw","rwin"])
    async def retowin(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.content):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retowin @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.content.strip().split('@')[1].strip())
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes otorgarte el punto a ti mismo, pídele ayuda a otro moderador")
                return

            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
            # Actualizar las estadísticas 
            actualiza = await update_global_stats("reto_wins",user,1)
            await update_global_stats("xp_Habilidad",user,1)
            if actualiza is not None:
                await ctx.send(f'[BOT] - Felicidades! Has ganado el reto @{mentioned_user}🏆')
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["retowin"].category = "Retos"


    @bot.command(name='retolose',aliases=["rl","rlose"])
    async def retolose(ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.content):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retolose @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.content.strip().split('@')[1].strip())
            if mentioned_user == ctx.author.name:
                await ctx.send("[BOT] - No puedes otorgarte el punto a ti mismo, pídele ayuda a otro moderador")
                return

            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
            # Actualizar las estadísticas de Wordle
            actualiza = await update_global_stats("reto_wins",user,-1)
            
            await ctx.send(f'[BOT] - se ha descontado un punto a @{mentioned_user}, ahora tiene ({actualiza})')
            
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    bot.commands["retolose"].category = "Retos"

    @bot.command(name='retoscore',aliases=["rs","rscore"])
    async def retoscore(ctx):
         # Obtener estadísticas 
        if '@' in ctx.message.content:
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.author.name
            user=ctx.author.id
        ranking =await get_stats("reto_wins",user)
        if ranking is not None:
            print(ranking)
            await ctx.send(f"[BOT] - @{mentioned_user} Ha ganado ({ranking[1]}) reto{'s' if safe_int(ranking[1]) >1 else ''}")
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha ganado un reto')
    bot.commands["retoscore"].category = "Retos"