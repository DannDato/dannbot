import asyncio
import time
from twitchio.ext import commands
import logging
import random
from datetime import datetime, date

from Helpers.helpers import is_authorized
from Helpers.helpers import send_large_message, validar_fecha, parse_flexible_date, normalize_username, wordslist
from Helpers.chatgpt import chatgpt
from Helpers.helpers_bot import get_chatters_total
from Helpers.helpers_moderator import create_stream_clip, list_basic_command_names
from Helpers.helpers_dynamic import (
    gen_response, get_steam_library, get_vips, get_followers_count, get_follow_age,
    get_viewers
)
from Helpers.helpers_stats import update_global_stats, save_user_bd, get_user_bd, get_twitch_id
from Helpers.printlog import printlog

class dynamic_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot
        self._clip_user_cooldown_seconds = 60
        self._clip_global_cooldown_seconds = 12
        self._clip_last_global_ts = 0.0
        self._clip_last_by_user = {}
    """
                    COMANDOS DINAMICOS

        Los comandos dinamicos son los que requieren programacion
        para arrojar un resultado, se define la funcion dentro
        del mismo comando

                INDICE
        -comandos
        -bot
        -so
        -memide
        -bd
        -cumpleaños
        -ruleta
        -mecaben
        -bola8
        -trivia
        -insultar
        -insultame
        -halago
        -caraocruz
        -meporte
        -nalgada
        -pies
        -abrazo
        -duelo
        -ip
        -amor
        -odio
        -midinero
        -donar
        -juegos
        -setso
        -xeno
        -ban?
        -vips
        -joteria
    """
    @commands.command(name='comandos', aliases=["help", "commands", "ayuda"])
    async def comandos(self, ctx):
        """
        Muestra una lista de todos los comandos disponibles en el bot.
        Si se utiliza un filtro (!comandos -<filtro>), muestra solo los comandos que contienen esa palabra.
        """
        await update_global_stats("xp_Astucia", ctx.chatter.id, 0.15)

        excluded_commands = {
            cmd.strip().lower().lstrip('!')
            for cmd in wordslist("comandos_excluidos.txt")
            if cmd.strip()
        }
        can_see_all = bool(getattr(ctx.chatter, "moderator", False)) or is_authorized(ctx)

        # Comandos hardcodeados cargados en el bot (nombre principal) + comandos de BD.
        hardcoded_commands = {
            cmd.name.strip().lower()
            for cmd in self.bot.commands.values()
            if getattr(cmd, "name", None)
        }
        db_commands = list_basic_command_names()
        command_names = hardcoded_commands | db_commands

        if not can_see_all:
            command_names = {
                cmd_name
                for cmd_name in command_names
                if cmd_name not in excluded_commands
            }

        # Construir el string
        sorted_commands = sorted(command_names)
        command_string = "[BOT] - 🤖 𝗧𝗼𝗱𝗼𝘀 𝗹𝗼𝘀 𝗰𝗼𝗺𝗮𝗻𝗱𝗼𝘀: "
        command_string += " ".join(f"!{command_name}" for command_name in sorted_commands)

        # Responder con la lista de comandos
        await send_large_message(ctx, command_string)



    @commands.command(name='followers', aliases=["seguidores"])
    async def followers(self, ctx):
        total = await get_followers_count()
        await ctx.send(f"[BOT] - Ahora mismo somos {total} siguiendo el canal!")
        printlog(f"{ctx.chatter.name}Uso followers")

    @commands.command(name='clip')
    async def clip(self, ctx):
        now_ts = time.monotonic()
        user_key = str(ctx.chatter.id)
        bypass_cooldown = bool(getattr(ctx.chatter, "moderator", False)) or is_authorized(ctx)

        if not bypass_cooldown:
            last_global = self._clip_last_global_ts
            if now_ts - last_global < self._clip_global_cooldown_seconds:
                remaining = int(self._clip_global_cooldown_seconds - (now_ts - last_global)) + 1
                await ctx.send(f"[BOT] - Esperen {remaining}s para crear otro clip")
                return

            last_user = self._clip_last_by_user.get(user_key, 0.0)
            if now_ts - last_user < self._clip_user_cooldown_seconds:
                remaining = int(self._clip_user_cooldown_seconds - (now_ts - last_user)) + 1
                await ctx.send(f"[BOT] - @{ctx.chatter.name} espera {remaining}s antes de usar !clip otra vez.")
                return

            self._clip_last_global_ts = now_ts
            self._clip_last_by_user[user_key] = now_ts

        ok, result = await create_stream_clip(has_delay=True)
        if ok:
            await ctx.send(f"[BOT] - @{ctx.chatter.name} listo, te deje el clip: {result.replace('Clip creado: ', '')}")
        else:
            await ctx.send(f"[BOT] - {result}")
        printlog(f"{ctx.chatter.name} uso clip -> {'ok' if ok else 'fail'}")

    @commands.command(name='bot',)
    async def botgpt(self,ctx):
        texto = ctx.message.text.strip().split('!bot')[1].strip()
        prompt = texto.replace('!bot', '').strip()
        printlog("Consultando con OpenAI","WARNING")
        response = await chatgpt(prompt,ctx.chatter.name)
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)
        if response is not None:
            await send_large_message(ctx,f'[BotGPT] - {response} @{ctx.chatter.name}')
        else:
            await ctx.send("[BotGPT] - mmmmmm, no me apetece mas responder hoy")

    @commands.command(name='so')
    async def so(self,ctx):
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)
        if ctx.chatter.moderator:
            if not ctx.message.text.strip().startswith('!so @'):
                await ctx.send("[BOT] - Por favor, usa el comando en el formato: !so @usuario")
                return
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            await ctx.send(f'/shutout @{mentioned_user}')
            await ctx.send(f'[BOT] - Amigos! Vamos a seguir a @{mentioned_user} en su canal www.twitch.tv/{mentioned_user}')
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')

    @commands.command(name='memide')
    async def memide(self,ctx):
        lnCm = random.randint(0, 35)
        if lnCm <= 5:
            lcExtra  ="🥺"
        elif lnCm > 5 and lnCm < 13:
            lcExtra ="👀"
        elif lnCm > 13 and lnCm < 20:
            lcExtra ="🥵"
        elif lnCm > 20 and lnCm  <30:
            lcExtra ="🤯"
        elif lnCm >= 30:
            lcExtra ="OMG  🤯🥵😈 increible"
        await ctx.send(f'[BOT] - A  @{ctx.chatter.name} le mide {lnCm}cm {lcExtra}')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='bd')
    async def bd(self,ctx):
        if ctx.message.text.strip() == '!bd':
            printlog("No ingresó texto para el comando !bd","WARNING")
            await ctx.send(f'[BOT] - @{ctx.chatter.name} Dame tu fecha de nacimiento! Puedes usar cualquier formato (ej: 2000-01-31, 31/1/2000, 31 de enero de 2000) y lo entenderé 😊')
            return;
        bd = ctx.message.text.strip().split(' ')[1].strip()
        bd = bd.strip()

        # Usar nueva función de parsing flexible
        pasa = await parse_flexible_date(bd)
        if pasa[0] == True:
            guardado = await save_user_bd(pasa[1], ctx.chatter.id)
            if guardado == True:
                await ctx.send(f'[BOT] - Perfecto @{ctx.chatter.name} ahora recordaré tu cumpleaños!')
        else:
            await ctx.send(f'[BOT] - @{ctx.chatter.name} No entendí ese formato 😅 Intenta de nuevo, por ejemplo: 31/12/1999 o 1999-12-31')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.55)

    @commands.command(name='cumpleaños', aliases=["cumple","birthday","cum"])
    async def cumpleaños(self,ctx):
        #______________Get mentioned user____________________
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
            user = await get_twitch_id(mentioned_user)
            if user is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}, quizás cambió su nombre o nunca lo registré 😢")
                return
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        #______________Get mentioned user____________________

        bd = await get_user_bd(user)

        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)
        if bd[0] == True:
            if bd[2]<10:
                complemento=f"Y falta{'n' if bd[2] > 1 else ''} {bd[2]} dia{'s' if bd[2] > 1 else ''} EEEEEEEH 🥳 Ya casi!"
            elif bd[2]<30:
                complemento=f"Y faltan {bd[2]} dias! En menos de un mes tenemos festejado!"
            else:
                complemento=f"Y faltan {bd[2]} dias!"

            await ctx.send(f"[BOT] - El cumpleaños 🎉 de @{mentioned_user} es el {bd[4]} de {bd[3]} {complemento}")
        else:
            await ctx.send(f"[BOT] - No se cuando es el cumpleaños de @{mentioned_user} 😔 díganle que lo guarde con el comando !bd YYYY-MM-DD ")

    @commands.command(name='ruleta')
    async def ruleta(self,ctx):
        await ctx.send(f'[BOT] - @{ctx.chatter.name} quiere jugar a la ruleta rusa... toma el arma, se prepara...')
        await asyncio.sleep(1)
        lnOpcion = random.randint(0,5)
        if lnOpcion == 0:
            lcRespuesta  ="Bye, se ha matao mi hijo ☠️"
        else:
            lcRespuesta  ="La bala le dió en el pie... se salva 😎"
        await ctx.send(f'[BOT] - {lcRespuesta}')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Habilidad",ctx.chatter.id,0.15)

    @commands.command(name='mecaben', aliases=["mecabe"])
    async def mecaben(self,ctx):
        lnBoca = random.randint(1,3)
        lnCulo = random.randint(1,3)
        lnHoyos =random.randint(0,2)
        lcPluralB = 'n' if lnBoca > 1 else ''
        lcPluralc = 'n' if lnCulo > 1 else ''
        if lnHoyos==0:
            await ctx.send(f'[BOT] - A @{ctx.chatter.name} 😈 le caben {lnBoca} en la boca y {lnCulo} en el Qlo 🥵')
        elif lnHoyos==1:
            await ctx.send(f'[BOT] - A @{ctx.chatter.name} 🙈 le cabe{lcPluralB} {lnBoca} en la boca')
        elif lnHoyos==2:
            await ctx.send(f'[BOT] - A @{ctx.chatter.name} le cabe{lcPluralc} {lnCulo} en el qlo 🥵')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='bola8', aliases=["genio"])
    async def bola8(self,ctx):
        lcRespuesta = gen_response("respuestas.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.chatter.name}')
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)

    @commands.command(name='trivia')
    async def trivia(self,ctx):
        lcRespuesta = gen_response("trivias.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.chatter.name}')
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Habilidad",ctx.chatter.id,0.15)

    @commands.command(name='insultar', aliases=["insulto", "insulta"])
    async def insultar(self,ctx):
        if '@' not in ctx.message.text:
            await ctx.send("[BOT] - Si andas de grocero minimo etiqueta a alquien qlo: !insultar @usuario o a ti solito con !insultame")
            return
        mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        lcRespuesta = gen_response("insultos.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{mentioned_user}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='insultame')
    async def insultame(self,ctx):
        mentioned_user = ctx.chatter.name
        lcRespuesta = gen_response("insultos.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{mentioned_user}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.25)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='halago')
    async def halago(self,ctx):
        if not ctx.message.text.strip().startswith('!halago @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !halago @usuario")
            return
        mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        lcRespuesta = gen_response("halagos.txt")
        await ctx.send(f'[BOT] - {lcRespuesta} @{mentioned_user}')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)

    @commands.command(name='caraocruz')
    async def caraocruz(self,ctx):
        lnResp = random.randint(0, 1)
        if lnResp == 0: lcRespuesta = "Cara"
        else: lcRespuesta = "Cruz"
        await ctx.send(f'[BOT] - {lcRespuesta} @{ctx.chatter.name}')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Habilidad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)

    @commands.command(name='meporte')
    async def meporte(self,ctx):
        lcRespuesta = gen_response("meporte.txt")
        lnMonth=datetime.now().month
        lcMonth=datetime.now().strftime("%B")
        if lnMonth == 12 :
            await ctx.send(f'[BOT] - 🎅 {lcRespuesta} {ctx.chatter.name} 🎄')
        else:
            await ctx.send(f'[BOT] - espérate un rato, estamos en {lcMonth}')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)

    @commands.command(name='nalgada')
    async def nalgada(self,ctx):
        if not ctx.message.text.strip().startswith('!nalgada @'):
            await ctx.send("[BOT] - ¿A quien? al aire o que?: !nalgada @usuario")
            return
        mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        lcRespuesta = gen_response("nalgadas.txt")
        await ctx.send(f'[BOT] - {ctx.chatter.name} Le ha dado una nalgada a @{mentioned_user}... y le dijo: {lcRespuesta}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='pies')
    async def pies(self,ctx):
        await ctx.send(f'[BOT] - {ctx.chatter.name} cochino, no andes pidiendo patas por aquí 🦶🦶🦶')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='abrazo', aliases=["abrazar","hug"])
    async def abrazo(self,ctx):
        #______________Get mentioned user____________________
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        else:
            mentioned_user = ctx.chatter.name
            user=ctx.chatter.id
        #______________Get mentioned user____________________
        lcRespuesta = gen_response("nalgadas.txt")
        await ctx.send(f'[BOT] - {ctx.chatter.name} le ha dado un abrazo a @{mentioned_user} ❤️❤️❤️')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)

    @commands.command(name='duelo', aliases=["duel","fight","pelea","retar"])
    async def duelo(self,ctx):
        #______________Get mentioned user____________________
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        else:
            mentioned_user = ctx.chatter.name
        #______________Get mentioned user____________________
        await ctx.send(f'[BOT] - @{ctx.chatter.name} ha retado a @{mentioned_user} a un duelo de cuchillos...')
        lnResp = random.randint(1, 3)
        lnGanador = ctx.chatter.name if random.randint(0,1) else mentioned_user
        match lnResp:
            case 1:
                lcText = "Golpe certero: La hoja atraviesa el aire, final brutal. @"+lnGanador+" ha ganado"
            case 2:
                lcText = "Desenlace inesperado: Ambos sueltan los cuchillos y ríen."
            case 3:
                lcText = "Empate mortal: Caen juntos, aferrados a sus armas."
        await asyncio.sleep(1)
        await ctx.send(f'[BOT] - {lcText}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Fuerza",ctx.chatter.id,0.15)
        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Habilidad",ctx.chatter.id,0.15)
        # await update_global_stats("xp_Fuerza",mentioned_user,0.15)
        # await update_global_stats("xp_Resistencia",mentioned_user,0.15)
        # await update_global_stats("xp_Habilidad",mentioned_user,0.15)

    @commands.command(name='ip')
    async def ip(self,ctx):
        parte1 = random.randint(1, 255)
        parte2 = random.randint(1, 255)
        parte3 = random.randint(1, 255)
        parte4 = random.randint(1, 255)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)
        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)
        await ctx.send(f"[BOT] - @{ctx.chatter.name} Te tengo ubicado, se que estás en la IP {parte1}.{parte2}.{parte3}.{parte4}")

    @commands.command(name='amor')
    async def amor(self,ctx):
        if not ctx.message.text.strip().startswith('!amor @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !amor @usuario o !amor @usuario1 @usuario2")
            return
        countUsers =ctx.message.text.strip().split('@')
        if len(countUsers) > 2:
            primerUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del primer '@' hasta el siguiente espacio
            segundoUsuario = normalize_username(countUsers[2].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        else:
            primerUsuario = normalize_username(ctx.chatter.name)  # Tomar el nombre de quien lo envía
            segundoUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        lnAmor = random.randint(1, 100)
        if lnAmor <= 33:
            lcExtra  ="❤️"
        elif lnAmor > 33 and lnAmor < 66:
            lcExtra ="❤️❤️"
        elif lnAmor >= 66:
            lcExtra ="❤️❤️❤️"
        await asyncio.sleep(1)
        await ctx.send(f'[BOT] - El amor entre @{primerUsuario} y @{segundoUsuario} es del {lnAmor}% {lcExtra}')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)

    @commands.command(name='odio')
    async def odio(self,ctx):
        if not ctx.message.text.strip().startswith('!odio @'):
            await ctx.send("[BOT] - Por favor, usa el comando en el formato: !odio @usuario o !odio @usuario1 @usuario2")
            return
        countUsers =ctx.message.text.strip().split('@')
        if len(countUsers) > 2:
            primerUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del primer '@' hasta el siguiente espacio
            segundoUsuario = normalize_username(countUsers[2].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        else:
            primerUsuario = normalize_username(ctx.chatter.name)  # Tomar el nombre de quien lo envía
            segundoUsuario = normalize_username(countUsers[1].split()[0])  # Tomar el texto después del segundo '@' hasta el siguiente espacio
        lnAmor = random.randint(1, 100)
        if lnAmor <= 33:
            lcExtra  ="🤬"
        elif lnAmor > 33 and lnAmor < 66:
            lcExtra ="🤬🤬"
        elif lnAmor >= 66:
            lcExtra ="🤬🤬🤬"
        await asyncio.sleep(1)
        await ctx.send(f'[BOT] - El odio entre @{primerUsuario} y @{segundoUsuario} es del {lnAmor}% {lcExtra}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='dinero', aliases=["midinero"])
    async def midinero(self,ctx):
        lnBanco = random.randint(1, 10000)
        lnCartera = random.randint(1, 1000)
        await ctx.send(f'[BOT] - @{ctx.chatter.name} tiene {lnBanco}$ en el banco  y {lnCartera}$ en la cartera 💵💲')

    @commands.command(name='donar', aliases=["donacion","dona"])
    async def donar(self,ctx):
        lnBits = random.randint(1,100)
        #______________Get mentioned user____________________
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        else:
            mentioned_user = ctx.chatter.name
        #______________Get mentioned user____________________
        await ctx.send(f'[BOT] - Yo creo que @{mentioned_user} deberia donar {lnBits} bits 👀')
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name="juegos", aliases=["games"])
    async def juegos(self,ctx):
        if ctx.chatter.moderator:
            printlog("a veeeeer")
            library = await get_steam_library()
            juegosList=", ⠀⠀ ".join(library)
            await ctx.send("[BOT] - Juegos en la biblioteca de danndato")
            await send_large_message(ctx,f"{juegosList}")
        else:
            await ctx.send(f'[BOT] - Lo siento {ctx.chatter.name}, este comando es solo para moderadores.')
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='setso')
    async def setso(self,ctx):
        if not ctx.message.text.strip().startswith('!setso @'):
            await ctx.send("[BOT] - Por favor si vas a andar de lepero, usa el comando en el formato: !setso @usuario")
            return
        mentioned_user = ctx.message.text.strip().split('@')[1].strip()
        await ctx.send(f'[BOT] - 😈 @{ctx.chatter.name} quiere llevarse a @{mentioned_user} a hacer cositas...🥵 ¿será que acepta?')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='xeno')
    async def xeno(self,ctx):
        dt1 = date.fromisoformat('2024-12-19')
        dt2 = datetime.now().date()
        dtdays = (dt2 - dt1).days
        await ctx.send(f'[BOT] - Han pasado {dtdays} días y @danndato aun no le envía los audios al @xenogamegd1')

    @commands.command(name='ban?')
    async def ban(self,ctx):
        if normalize_username(ctx.chatter.name)!="dani_14k" and not is_authorized(ctx):
            logging.warning(normalize_username(ctx.chatter.name))
            await ctx.send(f'[BOT] - Lo siento, este comando solo lo puede ejecutar @dani_14k')
            return
        lnBan = random.randint(1, 6)
        if lnBan == 5 :
            lnTiempo=random.randint(1, 30)
            lnResponse=f"Está bien, autorizo ban de {lnTiempo} segundos 💣"
        else:
            lnResponse="NO, Lo siento. Lo dejaremos pasar por esta ocación para evitar conflictos...👀"
        await ctx.send(f'[BOT] - {lnResponse}')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.15)

    @commands.command(name='vips')
    async def vips(self,ctx):
        lcVips = await get_vips()
        await ctx.send("[BOT] - Los 💎VIP's del canal son:")
        await ctx.send(lcVips)
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)

    @commands.command(name='joteria')
    async def joteria(self,ctx):
        if ctx.message.text.strip().startswith('!joteria @'):
            await ctx.send("[BOT] - No metas a nadie en tus joterías, pon el comando solo para ti (Sin el @)")
            return
        if ctx.chatter.name.lower() in ("marlightwi","lauunieves"):
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

        await ctx.send(f"[BOT] - Tu nivel de joteria @{ctx.chatter.name} es de {nivel}% {lcExtra}")
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    @commands.command(name='followage', aliases=["siguiendo","fa"])
    async def followage(self, ctx):
        if '@' in ctx.message.text:
            mentioned_user = ctx.message.text.strip().split('@')[1].strip().split()[0]
            user_id = await get_twitch_id(mentioned_user)
            if user_id is None:
                # Fallback a Helix por login si aun no está registrado en la BD local.
                users = await self.bot.fetch_users(logins=[mentioned_user])
                if users:
                    user_id = users[0].id
            if user_id is None:
                await ctx.send(f"[BOT] - No conozco el ID de @{mentioned_user}.")
                return
            target_name = mentioned_user
        else:
            user_id = ctx.chatter.id
            target_name = ctx.chatter.name

        if str(user_id) == str(self.bot.owner_id):
            await ctx.send(f"[BOT] - Como quieres saber eso si es tu propio canal... bro  @{target_name}")
            return

        delta, followed_dt = await get_follow_age(user_id)
        if followed_dt is None:
            # Si hay cache negativa antigua, intenta una consulta fresca.
            delta, followed_dt = await get_follow_age(user_id, force_refresh=True)
        if followed_dt is None:
            await ctx.send(f"[BOT] - @{target_name} no sigue el canal o no pude consultar su followage.")
            return

        days = delta.days
        years = days // 365
        months = (days % 365) // 30
        rem_days = (days % 365) % 30

        partes = []
        if years > 0:
            partes.append(f"{years} ano{'s' if years != 1 else ''}")
        if months > 0:
            partes.append(f"{months} mes{'es' if months != 1 else ''}")
        if rem_days > 0 or not partes:
            partes.append(f"{rem_days} dia{'s' if rem_days != 1 else ''}")

        follow_since = followed_dt.strftime('%Y-%m-%d')
        await ctx.send(
            f"[BOT] - @{target_name} lleva siguiendo el canal aproximadamente {' '.join(partes)} (desde {follow_since}) 😎"
        )

    @commands.command(name='viewers')
    async def viewers(self, ctx):
        total = await get_chatters_total(self.bot, force_refresh=True)
        await ctx.send(f'[BOT] - Ahora mismo hay {total} personas en el chat 😎!')