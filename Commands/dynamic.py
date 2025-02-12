import logging
import random
import time 
import locale
from datetime import datetime, date


from Helpers.helpers import send_large_message, is_authorized, normalize_username, wordslist
from Helpers.chatgpt import chatgpt
from Helpers.helpers_dynamic import gen_response, get_steam_library, get_vips
from Helpers.helpers_stats import update_global_stats

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para sistemas basados en Unix

def dynamic_commands(bot):
    """
                    COMANDOS DINAMICOS

        Los comandos dinamicos son los que requieren programacion
        para arrojar un resultado, se define la funcion dentro
        del mismo comando

                INDICE
        -comandos
        -so
        -memide
        -ruleta
        -bola8
        -insultar
        -halago
        -meporte
        -nalgada
        -abrazo
        -duelo
        -amor
        -midinero
        -donar
        -juegos

    """
    @bot.command(name='comandos')
    async def comandos(ctx):
        """
        Muestra una lista de todos los comandos disponibles en el @bot.
        Si se utiliza un filtro (!comandos -<filtro>), muestra solo los comandos que contienen esa palabra.
        """
        await update_global_stats("xp_Astucia",ctx.author.name,0.15)
        if ctx.message.content.strip().startswith('!comandos -'):
            filtro = ctx.message.content.strip().split('-')[1].strip().lower()  # Obtener el filtro y convertirlo a minúsculas
            # Filtrar los comandos que contienen el filtro
            filtered_commands = [
                command.name for command in bot.commands.values() 
                if filtro in command.name.lower()
            ]
            if filtered_commands:
                filtered_command_string = ", ".join(filtered_commands)
                await ctx.send(f'[BOT] - 🤖 Comandos que coinciden con "{filtro}":')
                await send_large_message(ctx,filtered_command_string)
            else:
                await ctx.send(f'[BOT] - ⚠️ No se encontraron comandos que coincidan con "{filtro}".')
        elif ctx.message.content.strip().startswith('!comandos c-'):

            await ctx.send("buscar por categoria aun no funciona :c ")
            
        else:
            # Obtener los nombres de los comandos registrados
            # excluded_commands = ["ini", "end","cmsj", "nbug", "recompensas", "skin", "setskin",  "xp", "player", "nivel","top"]
            excluded_commands = wordslist("comandos_excluidos.txt")
            # Filtrar los comandos para excluir los no deseados
            command_list = [command.name for command in bot.commands.values() if command.name not in excluded_commands]
            command_string = '[BOT] - 🤖 𝗧𝗼𝗱𝗼𝘀 𝗹𝗼𝘀 𝗰𝗼𝗺𝗮𝗻𝗱𝗼𝘀: ⠀⠀⠀'
            command_string = command_string + " ⠀⠀⠀!".join(command_list)
            # Responder con la lista de comandos
            await send_large_message(ctx,command_string)
    
    @bot.command(name='bot')
    async def botgpt(ctx):
        texto = ctx.message.content.strip().split('!bot')[1].strip()
        prompt = texto.replace('!bot', '').strip()
        response = await chatgpt(prompt,ctx.author.name)
        if response is not None:
            await send_large_message(ctx,f'[BotGPT] - {response} @{ctx.author.name}')
        else:
            await ctx.send("[BotGPT] - Se acabó el money 🤑, no puedo responder más por hoy")


    @bot.command(name='so')
    async def so(ctx):
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!so @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !so @usuario")
                return
            mentioned_user = ctx.message.content.strip().split('@')[1].strip()
            await ctx.send(f'/shutout @{mentioned_user}')
            await ctx.send(f'[BOT] - Amigos! Vamos a seguir a @{mentioned_user} en su canal www.twitch.tv/{mentioned_user}')
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    
    @bot.command(name='memide')
    async def memide(ctx):
        lnCm = random.randint(0, 50)
        if lnCm <= 5: 
            lcExtra  ="🥺"
        elif lnCm > 5 and lnCm < 18:
            lcExtra ="👀"
        elif lnCm > 18 and lnCm < 25:
            lcExtra ="🥵"
        elif lnCm > 25 and lnCm  <35:
            lcExtra ="🤯"
        elif lnCm >= 35:
            lcExtra ="OMG  🤯🥵😈 increible"
        await ctx.send(f'[BOT] - A  @{ctx.author.name} le mide {lnCm}cm {lcExtra}')
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)
    
    @bot.command(name='ruleta')
    async def ruleta(ctx):
        await ctx.send(f'[BOT] - @{ctx.author.name} quiere jugar a la ruleta rusa... toma el arma, se prepara...')
        time.sleep(1)
        lnOpcion = random.randint(0,5)
        if lnOpcion == 0: 
            lcRespuesta  ="Bye, se ha matao mi hijo ☠️"
        else:
            lcRespuesta  ="La bala le dió en el pie... se salva 😎"
        await ctx.send(f'[BOT] - {lcRespuesta}')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    
    @bot.command(name='mecaben')
    async def mecaben(ctx):
        lnBoca = random.randint(1,3)
        lnCulo = random.randint(1,3)
        lnHoyos =random.randint(0,2)
        lcPluralB = 'n' if lnBoca > 1 else ''
        lcPluralc = 'n' if lnCulo > 1 else ''
        if lnHoyos==0:
            await ctx.send(f'[BOT] - A @{ctx.author.name} 😈 le caben {lnBoca} en la boca y {lnCulo} en el Qlo 🥵')
        elif lnHoyos==1:
            await ctx.send(f'[BOT] - A @{ctx.author.name} 🙈 le cabe{lcPluralB} {lnBoca} en la boca')
        elif lnHoyos==2:
            await ctx.send(f'[BOT] - A @{ctx.author.name} le cabe{lcPluralc} {lnCulo} en el qlo 🥵')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)

    @bot.command(name='bola8')
    async def bola8(ctx):
        lcRespuesta = gen_response("respuestas.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.author.name}')
        await update_global_stats("xp_Astucia",ctx.author.name,0.15)

    @bot.command(name='trivia')
    async def trivia(ctx):
        lcRespuesta = gen_response("trivias.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.author.name}')
        await update_global_stats("xp_Astucia",ctx.author.name,0.15)
    
    @bot.command(name='insultar')
    async def insultar(ctx):
        if not ctx.message.content.strip().startswith('!insultar @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !insultar @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        lcRespuesta = gen_response("insultos.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{mentioned_user}')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)

    @bot.command(name='halago')
    async def halago(ctx):
        if not ctx.message.content.strip().startswith('!halago @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !halago @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        lcRespuesta = gen_response("halagos.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{mentioned_user}')
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)

    @bot.command(name='caraocruz')
    async def caraocruz(ctx):
        lnResp = random.randint(0, 1)
        if lnResp == 0: lcRespuesta = "Cara" 
        else: lcRespuesta = "Cruz"
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.author.name}')
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)

    @bot.command(name='meporte')
    async def meporte(ctx):
        lcRespuesta = gen_response("meporte.txt")
        lnMonth=datetime.now().month
        lcMonth=datetime.now().strftime("%B")
        if lnMonth == 12 :
            await ctx.send(f'[BOT] - 🎅 {lcRespuesta} {ctx.author.name} 🎄')
        else:
            await ctx.send(f'[BOT] - espérate un rato, estamos en {lcMonth}')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)

    @bot.command(name='nalgada')
    async def nalgada(ctx):
        if not ctx.message.content.strip().startswith('!nalgada @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !nalgada @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        lcRespuesta = gen_response("nalgadas.txt")
        await ctx.send(f'[BOT] - {ctx.author.name} Le ha dado una nalgada a @{mentioned_user}... y le dijo: {lcRespuesta}')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)
    
    @bot.command(name='pies')
    async def pies(ctx):
        await ctx.send(f'[BOT] - {ctx.author.name} cochino, no andes pidiendo patas por aquí 🦶🦶🦶')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)
    
    @bot.command(name='abrazo')
    async def abrazo(ctx):
        if not ctx.message.content.strip().startswith('!abrazo @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !abrazo @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        lcRespuesta = gen_response("nalgadas.txt")
        await ctx.send(f'[BOT] - {ctx.author.name} le ha dado un abrazo a @{mentioned_user} ❤️❤️❤️')
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)

    @bot.command(name='duelo')
    async def duelo(ctx):
        if not ctx.message.content.strip().startswith('!duelo @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !duelo @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        await ctx.send(f'[BOT] - @{ctx.author.name} ha retado a @{mentioned_user} a un duelo de cuchillos...')
        lnResp = random.randint(1, 3)
        lnGanador = ctx.author.name if random.randint(0,1) else mentioned_user
        match lnResp:
            case 1:
                lcText = "Golpe certero: La hoja atraviesa el aire, final brutal. @"+lnGanador+" ha ganado"
            case 2:
                lcText = "Desenlace inesperado: Ambos sueltan los cuchillos y ríen."
            case 3:
                lcText = "Empate mortal: Caen juntos, aferrados a sus armas."
        time.sleep(1)
        await ctx.send(f'[BOT] - {lcText}')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)

    @bot.command(name='amor')
    async def amor(ctx):
        if not ctx.message.content.strip().startswith('!amor @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !amor @usuario o !amor @usuario1 @usuario2")
            return
        countUsers =ctx.message.content.strip().split('@')
        if len(countUsers) > 2:
            primerUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del primer '@' hasta el siguiente espacio
            segundoUsuario = normalize_username(countUsers[2].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        else:
            primerUsuario = normalize_username(ctx.author.name)  # Tomar el nombre de quien lo envía
            segundoUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        lnAmor = random.randint(1, 100)
        if lnAmor <= 33: 
            lcExtra  ="❤️"
        elif lnAmor > 33 and lnAmor < 66:
            lcExtra ="❤️❤️"
        elif lnAmor >= 66:
            lcExtra ="❤️❤️❤️"
        time.sleep(1)
        await ctx.send(f'[BOT] - El amor entre @{primerUsuario} y @{segundoUsuario} es del {lnAmor}% {lcExtra}')
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)
    
    @bot.command(name='odio')
    async def odio(ctx):
        if not ctx.message.content.strip().startswith('!odio @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !odio @usuario o !odio @usuario1 @usuario2")
            return
        countUsers =ctx.message.content.strip().split('@')
        if len(countUsers) > 2:
            primerUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del primer '@' hasta el siguiente espacio
            segundoUsuario = normalize_username(countUsers[2].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        else:
            primerUsuario = normalize_username(ctx.author.name)  # Tomar el nombre de quien lo envía
            segundoUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        lnAmor = random.randint(1, 100)
        if lnAmor <= 33: 
            lcExtra  ="🤬"
        elif lnAmor > 33 and lnAmor < 66:
            lcExtra ="🤬🤬"
        elif lnAmor >= 66:
            lcExtra ="🤬🤬🤬"
        time.sleep(1)
        await ctx.send(f'[BOT] - El odio entre @{primerUsuario} y @{segundoUsuario} es del {lnAmor}% {lcExtra}')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)

    @bot.command(name='midinero')
    async def midinero(ctx):
        lnBanco = random.randint(1, 10000)
        lnCartera = random.randint(1, 1000)
        await ctx.send(f'[BOT] - @{ctx.author.name} tiene {lnBanco}$ en el banco  y {lnCartera}$ en la cartera 💵💲')

    @bot.command(name='donar')
    async def donar(ctx):
        lnBits = random.randint(1,100)
        if not ctx.message.content.strip().startswith('!donar @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !donar @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        await ctx.send(f'[BOT] - Yo creo que @{mentioned_user} deberia donar {lnBits} bits 👀')

    @bot.command(name="juegos")
    async def juegos(ctx):
        if ctx.author.is_mod:
            library = get_steam_library()
            await ctx.send("[BOT] - Juegos en la biblioteca de danndato")
            juegosList=", ⠀⠀ ".join(library)
            await send_large_message(ctx,f"{juegosList}")
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.author.name}, este comando es solo para moderadores.')
    
    @bot.command(name='setso')
    async def setso(ctx):
        if not ctx.message.content.strip().startswith('!setso @'):
            await ctx.send("[BOT] - Por favor si vas a andar de lepero, usa el comando en el formato: !setso @usuario")
            return
        mentioned_user = ctx.message.content.strip().split('@')[1].strip()
        await ctx.send(f'[BOT] - 😈 @{ctx.author.name} quiere llevarse a @{mentioned_user} a hacer cositas...🥵 ¿será que acepta?')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)
    
    @bot.command(name='xeno')
    async def xeno(ctx):
        dt1 = date.fromisoformat('2024-12-19')
        dt2 = datetime.now().date()
        dtdays = (dt2 - dt1).days
        await ctx.send(f'[BOT] - Han pasado {dtdays} días y @danndato aun no le envía los audios al @xenogamegd1')

    @bot.command(name='ban?')
    async def ban(ctx):
        if normalize_username(ctx.author.name)!="dani_14k":
            logging.warning(normalize_username(ctx.author.name))
            await ctx.send(f'[BOT] - Lo siento, este comando solo lo puede ejecutar @dani_14k')
            return
        lnBan = random.randint(1, 10)
        if lnBan == 5 :
            lnTiempo=random.randint(1, 10)
            lnResponse=f"Está bien, autorizo ban de {lnTiempo} segundos 💣"
        else:
            lnResponse="NO, Lo siento. Lo dejaremos pasar por esta ocación para evitar conflictos...👀"
        await ctx.send(f'[BOT] - {lnResponse}')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.15)

    @bot.command(name='vips')
    async def vips(ctx):
        lcVips = await get_vips()
        await ctx.send("[BOT] - Los 💎VIP's del canal son:")
        await ctx.send(lcVips)
        await update_global_stats("xp_Astucia",ctx.author.name,0.15)

    @bot.command(name='joteria')
    async def joteria(ctx):
        if ctx.message.content.strip().startswith('!joteria @'):
            await ctx.send("[BOT] - No metas a nadie en tus joterías, pon el comando solo para ti (Sin el @)")
            return
        if ctx.author.name.lower() in ("marlightwi","lauunieves"):
            nivel=random.randint(80,100)
        else:
            nivel=random.randint(1,100)
        lcExtra=""
        if nivel >= 1:
            lcExtra="Algo aceptable 😒"
        if nivel >=33:
            lcExtra="Realmente ya me lo esperaba, se nota 😏"
        if nivel >=70:
            lcExtra="Oye... cuidao, comienza a preocuparme 👀"
        if nivel >=80:
            lcExtra="Aléjese gei (No es cierto, no a la homofobia) ❤️"
        if nivel >=95:
            lcExtra="Increible, tu nivel de joteria es realmente impresionante 🏳️‍🌈"
        
        await ctx.send(f"[BOT] - Tu nivel de joteria @{ctx.author.name} es de {nivel}% {lcExtra}")
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)