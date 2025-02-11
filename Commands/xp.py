from Helpers.helpers_xp import get_player, get_top_players, get_skin, set_stats, calculate_xp, calculate_level
from Helpers.helpers import is_authorized, send_large_message
from Helpers.helpers_stats import update_global_stats

def xp_commands(bot):
    """
        Muestra el nivel de los jugadores segun sus estadísticas rpg
        oPlayer[0][1] = XP
        oPlayer[1][1] = Nivel
        oPlayer[2][1] = Rol
            
        oPlayer[3][1] = xp_categoria
        oPlayer[4][1] = xp_categoria
        ...
        oPlayer[X][1] = xp_categoria
    """
    @bot.command(name='player')
    async def player(ctx):
        if not is_authorized(ctx):
            return
        if ctx.message.content.strip().startswith('!player @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name

        oPlayer = await get_player(user)
        if oPlayer != False:
            if(int(oPlayer[1][1])>=5):
                response = f"[BOT] - 🧙‍♂️ @{user} {oPlayer[2][1]} 💎Nivel({oPlayer[1][1]}) ->⠀⠀ "
            else:
                response = f"[BOT] - 🧙‍♂️ @{user} Nivel({oPlayer[1][1]}) -> "
            response = response + f" >>> {oPlayer[3][0]}({oPlayer[3][1]}) "
            response = response + f" {oPlayer[4][0]}({oPlayer[4][1]}) "
            response = response + f" {oPlayer[5][0]}({oPlayer[5][1]}) <<< ⠀⠀⠀ 🪙XP({oPlayer[0][1]})"
            await ctx.send(response)
        else:
            await ctx.send("[BOT] - Es un guerrero sin estadísticas...")

    @bot.command(name='xp')
    async def player(ctx):
        if not is_authorized(ctx):
            return
        if ctx.message.content.strip().startswith('!xp @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
        oPlayer = await calculate_xp(user)
        if oPlayer != False or oPlayer!=None:
            response = f"[BOT] - @{user} 🪙 XP({oPlayer})"
            await send_large_message(ctx, response)
        else:
            await ctx.send("[BOT] - Es un guerrero sin estadísticas...")

    @bot.command(name='nivel')
    async def player(ctx):
        if not is_authorized(ctx):
            return
        if ctx.message.content.strip().startswith('!nivel @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name
            
        oPlayer = await calculate_level(user)
        if oPlayer > 0 and oPlayer<=33:
            lcEmojis="🎖️"
        elif oPlayer > 33 and oPlayer<=66:
            lcEmojis="🎖️🎖️"
        elif oPlayer > 67 and oPlayer<=100:
            lcEmojis="🎖️🎖️🎖️"
        elif oPlayer >100:
            lcEmojis="👑"
        
        if oPlayer != False:
            response = f"[BOT] - {lcEmojis} @{user} Es nivel ({oPlayer})"
            await ctx.send(response)
        else:
            await ctx.send("[BOT] - Es un guerrero sin estadísticas...")
    

    @bot.command(name='top')
    async def player(ctx):
        if not is_authorized(ctx):
            return
        user=ctx.author.name
        topPlayer = await get_top_players()
        
        if topPlayer != False:
            await ctx.send(f"[BOT] - | 👑 Top 3 jugadores con mas XP  | >>> ")
            await send_large_message(ctx,topPlayer)
        else:
            await ctx.send("[BOT] - No puedo recopilar aun estadísticas...")

    @bot.command(name='skin')
    async def skin(ctx):
        if not is_authorized(ctx):
            return
        user=ctx.author.name
        skin = await get_skin(user)
        await ctx.send(f"[BOT] - Skin de {skin}")

    @bot.command(name='setskin')
    async def setskin(ctx):
        if not is_authorized(ctx):
            return
        if len(ctx.message.content.strip().split('!setskin'))<2:
            await ctx.send(f"[BOT] - Necesitas especificar tu skin")
            return
        user=ctx.author.name
        nivel = await calculate_level(user)
        if nivel<5:
            await ctx.send(f"[BOT] - Necesitas ser nivel 5 para tener guardar tu skin")
            return
        
        texto = ctx.message.content.strip().split('!setskin')[1].strip()
        newSkin = texto.replace('!setskin', '').strip()

        if nivel>=5: limite = 50
        elif nivel>=10: limite = 70
        elif nivel>=20: limite = 90
        elif nivel>=30: limite = 100
        elif nivel>=40: limite = 150
        elif nivel>=50: limite = 499

        if len(newSkin)>limite:
            await ctx.send(f"[BOT] - Tu skin es muy grande, tu límite es de {limite} caracteres y lo que ingresaste es de {len(newSkin)}")
            return
        
        skin = await set_stats("Skin",user,newSkin)

        if skin is not None:
            await ctx.send(f"[BOT] - Se ha guardado tu skin @{ctx.author.name} correctamente")

    @bot.command(name='recompensas')
    async def recompensas(ctx):
        if not is_authorized(ctx): return

        await ctx.send("[BOT] - Las recompensas de nivel en el canal... 🔥")
        await ctx.send("Nivel [ 5] 🏅 Titulo de jugador  ")
        await ctx.send("Nivel [10] 🥷 Crear Skin (25)  ")
        await ctx.send("Nivel [15] 🧩 Crear clan  ")
        await ctx.send("Nivel [20] 🤖 Tu propio comando ")
        await ctx.send("Nivel [25] 🐕 Adoptar mascota ")
        await ctx.send("Nivel [50] 💎 VIP  ")

    # @bot.command(name='clan')
    # async def clan(ctx):
    #     if not is_authorized(ctx): return
    #     user = ctx.author.name
    #     if ctx.message.content.strip().startswith('!clan '):
    #         uClan = "await get_clan_user(user)"
    #         await ctx.send(f'[BOT] - @{user} {uClan}')

    #     elif ctx.message.content.strip().startswith('!comandos c-'):
    #         nClan = ctx.message.content.strip().split('c-')[1].strip().lower()  # Obtener el filtro y convertirlo a minúsculas
    #         sClan = "await crear_clan(user,nClan)"
    #         if sClan is not None:
    #             await ctx.send(f"[BOT] - @{user} ha creado el clan {nClan}")
    #         else: await ctx.send("No se ha podido crear el clan")
            