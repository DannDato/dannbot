from Helpers.helpers_xp import get_player, get_top_players, get_skin, set_stats, calculate_xp, calculate_level, get_clanes, left_clan, join_to_clan, admin_clan, get_clan_user, get_clan_members
from Helpers.helpers import is_authorized, send_large_message, normalize_username
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
        
        
        if ctx.message.content.strip().startswith('!player @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        else:
            user=ctx.author.name

        await update_global_stats("xp_Astucia",ctx.author.name,0.25)

        user = normalize_username(user)
        oPlayer = await get_player(user)
        
        if oPlayer != False:
            response=f"[BOT] -  🇯  🇺  🇬  🇦  🇩  🇴  🇷 ⠀⠀⠀⠀ @{user} ⠀ "
            if(int(oPlayer[1][1])>=5):
                response = response + f"{oPlayer[2][1]} Nivel({oPlayer[1][1]})⠀ "
            else:
                response = response + f"Nivel({oPlayer[1][1]})⠀ "
            response = response + f" >>> ⠀|{oPlayer[3][0]}({oPlayer[3][1]})|⠀"
            response = response + f" |{oPlayer[4][0]}({oPlayer[4][1]})|⠀"
            response = response + f" |{oPlayer[5][0]}({oPlayer[5][1]})|⠀|💰XP({oPlayer[0][1]})|⠀"

            skin = await get_skin(user)
            if skin is not None:
                response = response +f"👕Skin: [{skin[1]}]⠀"
                
            await ctx.send(response)
        else:
            await ctx.send("[BOT] - Es un guerrero sin estadísticas...")

    @bot.command(name='xp')
    async def player(ctx):
        
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

        await update_global_stats("xp_Astucia",ctx.author.name,0.25)
    @bot.command(name='nivel')
    async def player(ctx):
        
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
        
        user=ctx.author.name
        topPlayer = await get_top_players()
        await update_global_stats("xp_Voluntad",ctx.author.name,0.25)
        message = f"[BOT] -👑 Top 3 jugadores con mas XP >>> ⠀ {topPlayer}"
        if topPlayer != False:
            await send_large_message(ctx,message)
        else:
            await ctx.send("[BOT] - No puedo recopilar aun estadísticas...")

    @bot.command(name='skin')
    async def skin(ctx):
        
        user=ctx.author.name
        skin = await get_skin(user)
        
        await ctx.send(f"[BOT] - Skin de {skin[1]}")

    @bot.command(name='setskin')
    async def setskin(ctx):
        
        if len(ctx.message.content.strip().split('!setskin'))<2:
            await ctx.send(f"[BOT] - Necesitas especificar tu skin")
            return
        user=ctx.author.name
        await update_global_stats("xp_Astucia",ctx.author.name,0.25)
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

    #comando para leer los clanes de los usuarios
    @bot.command(name='clan')
    async def clan(ctx):
        
         #Obtener el clan actual del usuario
        if ctx.message.content.strip().startswith('!clan @'):
            user = ctx.message.content.strip().split('@')[1].strip()
        elif ctx.message.content.strip().startswith('!clan -'):
            nClan = ctx.message.content.strip().split('-')[1].strip()
        else:
            user=ctx.author.name

        if nClan is None:
            uClan = await get_clan_user(user)
            await ctx.send(f'[BOT] - @{user} {uClan}')
        else:
            uClan = await get_clan_members(nClan)
            await ctx.send(f'[BOT] - {uClan}')


    #Comando para administrar clanes
    @bot.command(name='liderclan')
    async def liderclan(ctx):
        
        user = ctx.author.name
        uNivel= await calculate_level(user)

        await update_global_stats("xp_Fuerza",ctx.author.name,0.25)
        #variante del comando para crear un nuevo clan
        if ctx.message.content.strip().startswith('!liderclan -c'):
            if uNivel>=15:
                nClan = ctx.message.content.strip().split('-c')[1].strip()  # Obtener el nombre del clan
                #si el usuario no ha creado ningun clan devuelve TRUE, si no, FALSE
                sClan = await admin_clan(user,nClan,1)
                if sClan == True:
                    await ctx.send(f"[BOT] - @{user} ha creado el clan {nClan}")
                elif sClan == False:
                    await ctx.send(f"[BOT] - @{user} Ya eres líder de un clan actualmente")
                elif sClan is None: 
                    await ctx.send("[BOT] - No se ha podido crear el clan")

            else: await ctx.send(f"[BOT] - No tienes el nivel necesario para administrar un clan @{user}")
        #variante del comando para borrar un clan
        elif ctx.message.content.strip().startswith('!liderclan -b'):
            if uNivel>=15:
                nClan = ctx.message.content.strip().split('-b')[1].strip()  # Obtener el nombre del clan
                #si encuentra el clan lo borra y devuelve TRUE, si no, FALSE
                sClan = await admin_clan(user,nClan,2)
                if sClan == True:
                    await ctx.send(f"[BOT] - @{user} ha borrado el clan {nClan}")
                elif sClan == False:
                    await ctx.send(f"[BOT] - @{user} no se ha encontrado el clan o no eres líder")
                elif sClan is None: 
                    await ctx.send("[BOT] - No se ha podido borrar el clan")

            else: await ctx.send(f"[BOT] - No tienes el nivel necesario para administrar un clan @{user}")
        
        # variante del comando para unir un usuario a un clan
        elif ctx.message.content.strip().startswith('!liderclan -u @'):
            if uNivel>=15:
                nUser = ctx.message.content.strip().split('@')[1].strip()  # Obtener el usuario a unir
                #si añade al jugador devuelve TRUE, si no, FALSE
                sClan = await join_to_clan(user,nUser)
                if sClan == True:
                    await ctx.send(f"[BOT] - @{user} Ha añadido a @{nUser} a su clan!")
                elif sClan == False:
                    await ctx.send(f"[BOT] - @{user} no se ha encontrado el clan o no eres líder")
                elif sClan is None: 
                    await ctx.send("[BOT] - No se ha podido añadir al clan")

            else: await ctx.send(f"[BOT] - No tienes el nivel necesario para administrar un clan @{user}")

    #Comando para abandonar un clan
    @bot.command(name='dejarclan')
    async def dejarclan(ctx):
        
        user = ctx.author.name
        sClan = await left_clan(user)
        await update_global_stats("xp_Voluntad",ctx.author.name,0.25)
        if sClan == True:
            await ctx.send(f"[BOT] - @{user} Ha abandonado a su clan!")
        elif sClan == False:
            await ctx.send(f"[BOT] - @{user} no se ha encontrado el clan")
        elif sClan is None: 
            await ctx.send("[BOT] - ocurrió un error al abandonar el clan")


            
        
    @bot.command(name='clanes')
    async def clanes(ctx):
        
        lcClanes = await get_clanes()
        await update_global_stats("xp_Voluntad",ctx.author.name,0.25)
        await ctx.send(f"[BOT] - Clanes actuales: {lcClanes}")

    @bot.command(name='recompensas')
    async def recompensas(ctx):
        
        await update_global_stats("xp_Voluntad",ctx.author.name,0.25)
        await ctx.send("[BOT] - Las recompensas de nivel en el canal... 🔥")
        await ctx.send("Nivel [ 5] 🏅 Titulo de jugador  ")
        await ctx.send("Nivel [10] 🥷 Crear Skin (25)  ")
        await ctx.send("Nivel [15] 🧩 Crear clan  ")
        await ctx.send("Nivel [20] 🤖 Tu propio comando ")
        await ctx.send("Nivel [25] 🐕 Adoptar mascota ")
        await ctx.send("Nivel [50] 💎 VIP  ")