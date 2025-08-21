from datetime import datetime
from twitchio.ext import commands
from Helpers.helpers import  is_channel_online, safe_int, normalize_username
from Helpers.helpers_stats import update_global_stats, get_stats, check_primero, count_user_messages, get_twitch_id
from twitchio.ext import commands
from Helpers.printlog import printlog

class stats_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot
    """
                Registra comandos para leer las estadísticas del bot en el bot.
        -mensajes
        -ladrillo
        -primero
        -primeroscore
        -primerotop
        -wordlewin
        -wordlelose
        -wordlescore
        -wordletop
        -retowin
        -retolose
        -retoscore
    """ 
    @commands.command(name='mensajes')
    async def mensajes(self, ctx):
        if ctx.message.text.strip().startswith('!mensajes @'):
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        messages_hist =await get_stats("messages",user)
        await ctx.send(f"[BOT] - @{mentioned_user} ha enviado: ({messages_hist[1]}) mensaje(s)")
 
    @commands.command(name='ladrillo')
    async def ladrillo(self, ctx):
        ladrillos = await update_global_stats("ladrillos","channel",1)
        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)
        await update_global_stats("xp_voluntad",ctx.chatter.id,0.15)
        await ctx.send(f"[BOT] - @{ctx.chatter.name} ha agregado un ladrillo, hemos puesto ({ladrillos})🧱 en total ")

    @commands.command(name='primero')
    async def primero(self, ctx):
        check_online = await is_channel_online()
        if check_online is False:
            await ctx.send("Tramposit@... 👀 este comando solo está disponible si @DannDato está en vivo.")
            return
        handle=await check_primero(ctx.chatter)
        if  handle is None:
            actualiza = await update_global_stats("first_user",ctx.chatter.id,1)
            await update_global_stats("xp_Resistencia",ctx.chatter.id,3)
            await update_global_stats("xp_voluntad",ctx.chatter.id,0.15)
            if actualiza is not None:
                ranking =await get_stats("first_user",ctx.chatter.id)
                await ctx.send(f'[BOT] - Esoo! 🔥 Parece que si has llegado primero! tus puntos actualmente {ranking[1]}: 🏆')
        else:
            if ctx.chatter.id==handle:
                await ctx.send(f'[BOT] -Que si @{handle}  ya sabemos que tu llegaste primero 😒')
            else:
                await ctx.send(f'[BOT] -Sorry, pero @{handle} llegó primero')

    
    @commands.command(name='primeropuntos',aliases=["ps","pscore","primeroscore"])
    async def primeropuntos(self, ctx):
        # Obtener estadísticas de Wordle
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        ranking = None
        ranking =await get_stats("first_user",user)
        if ranking is not None:
            await ctx.send(f'[BOT] - 🏎️@{mentioned_user} En Llegar primero: ({ranking[1]}) punto{"s" if ranking[1]!="1" else ""}')
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha llegado primero ')


    @commands.command(name='primerotop',aliases=["pt","ptop"])
    async def primerotop(self, ctx):
        ranking = await get_stats("first_user",None)
        await ctx.send(f'[BOT] - Los mas camperos del canal [🔥TOP 5]:')
        await ctx.send(f'{ranking}')


    # Comando para registrar el ganador del Wordle
    @commands.command(name='wordlewin', aliases=["ww", "wwin"])
    async def wordlewin(self, ctx):
        # Verificar si el autor es moderador
        if ctx.chatter.moderator:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.text):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlewin @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.text.strip().split('@')[1].strip())
            if mentioned_user == ctx.chatter.name:
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
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')



    @commands.command(name='wordlelose',aliases=["wl","wlose"])
    async def wordlelose(self, ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.chatter.moderator:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.text):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !wordlelose @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.text.strip().split('@')[1].strip())
            if mentioned_user == ctx.chatter.name:
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
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')



    # Comando para mostrar estadísticas globales de Wordle
    @commands.command(name='wordlepuntos',aliases=["ws","wscore","wordlescore"])
    async def wordlepuntos(self, ctx):
        # Obtener estadísticas 
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        ranking =await get_stats("wordle_wins",user)
        if ranking is not None:
            await ctx.send(f'[BOT] - @{mentioned_user} En 🆆🅾🆁🅳🅻🅴 tiene {ranking[1]} punto{"s" if ranking[1]>1 else ""}')
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha ganado el wordle')



    @commands.command(name='wordletop',aliases=["wt","wtop"])
    async def wordletop(self, ctx):
        ranking = await get_stats("wordle_wins",None)
        await ctx.send(f'[BOT] - Las estadísticas de Wordle [🔥TOP 5]:')
        await ctx.send(f'{ranking}')


    # Comando para registrar el ganador de un reto random
    @commands.command(name='retowin',aliases=["rw","rwin"])
    async def retowin(self, ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.chatter.moderator:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.text):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retowin @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.text.strip().split('@')[1].strip())
            if mentioned_user == ctx.chatter.name:
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
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')



    @commands.command(name='retolose',aliases=["rl","rlose"])
    async def retolose(self, ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.chatter.moderator:
            # Verificar si el mensaje contiene un formato válido
            if not ('@' in ctx.message.text):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !retolose @usuario")
                return
            
            # Validar que no se otorgue el punto al propio usuario
            mentioned_user = normalize_username(ctx.message.text.strip().split('@')[1].strip())
            if mentioned_user == ctx.chatter.name:
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
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')


    @commands.command(name='retospuntos',aliases=["rs","rscore","retoscore"])
    async def retospuntos(self, ctx):
        # Obtener estadísticas 
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            # Buscar el ID en la base de datos
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        ranking =await get_stats("reto_wins",user)
        if ranking is not None and ranking[1]!=0:
            print(ranking)
            await ctx.send(f"[BOT] - @{mentioned_user} Ha ganado ({ranking[1]}) reto{'s' if safe_int(ranking[1]) >1 else ''}")
        else:
            await ctx.send(f'[BOT] - Creo que @{mentioned_user} nunca ha ganado un reto')