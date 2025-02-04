from Helpers.helpers_xp import get_player, get_top_players, get_skin, calculate_xp, calculate_level
from Helpers.helpers import is_authorized

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
            await ctx.send(response)
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
            response = f"[BOT] - {lcEmojis} @{user} Nivel ({oPlayer})"
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
            await ctx.send(f"[BOT] - | 👑 Top 3 jugadores con mas XP  | >>> {topPlayer}")
        else:
            await ctx.send("[BOT] - No puedo recopilar aun estadísticas...")

    @bot.command(name='skin')
    async def skin(ctx):
        if not is_authorized(ctx):
            return
        user=ctx.author.name
        skin = await get_skin(user)
        await ctx.send(f"[BOT] - | Skin de {skin}")

    @bot.command(name='recompensas')
    async def recompensas(ctx):
        if not is_authorized(ctx): return

        await ctx.send("[BOT] - Las recompensas de nivel en el canal... 🔥")
        await ctx.send("Nivel [ 5] 🏅 Titulo de jugador  ")
        await ctx.send("Nivel [10] 🥷 Crear Skin (25)  ")
        await ctx.send("Nivel [15] 🧩 Crear clan  ")
        await ctx.send("Nivel [20] 🤖 Tu propio comando  ")
        await ctx.send("Nivel [30] 💎 VIP  ")
