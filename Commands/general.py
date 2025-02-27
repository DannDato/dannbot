import logging
from twitchio.ext import commands

from Helpers.helpers_stats import update_global_stats

def general_commands(bot):
    """
                    COMANDOS GENERALES

        Los comandos generales son comandos que ofrecen
        una respuesta rápida en el chat
        
                INDICE:
    -hola
    -adios
    -lurk
    -onlyfans
    -koala
    -llama
    -daarlaaaaa
    -horario
    -pc
    -camara
    -microfono
    -instagram
    -youtube
    -whatsapp
    -wapp
    -discord
    -redes

    """
    @bot.command(name='hola')
    async def hola(ctx):
        logging.info(f"{ctx.author.name} saludo")
    bot.commands["hola"].category = "Basicos"

    @bot.command(name='adios')
    async def adios(ctx):
        logging.info(f"{ctx.author.name} se despidió")
    bot.commands["adios"].category = "Basicos"

    @bot.command(name='lurk')
    async def lurk(ctx):
        await ctx.send(f'Hummm... parece que @{ctx.author.name} se fue con las cariñosas! 🕵️‍♂️ Disfrutará del stream en modo sigiloso.')
        await update_global_stats("xp_Oscuridad",ctx.author.name,3)
    bot.commands["lurk"].category = "Basicos"

    @bot.command(name='onlyfans')
    async def onlyfans(ctx):
        await ctx.send(f'¡Señoraaaa! @{ctx.author.name} anda de cochin@!')
        await update_global_stats("xp_Oscuridad",ctx.author.name,0.55)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["onlyfans"].category = "Basicos"
    
            # amigos
    @bot.command(name='koala')
    async def koala(ctx):
        await ctx.send(f'Cállense todos, ya llego @elkoalam 👀🙄')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["koala"].category = "Amigos"
    
    @bot.command(name='llama')
    async def llama(ctx):
        await ctx.send(f'@loslordllama se la come doblada 🥵 dannda3Llamamo')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["llama"].category = "Amigos"
    
    @bot.command(name='daarlaaaaa')
    async def daarlaaaaa(ctx):
        await ctx.send(f' Como @DAARLAAAAA 🤯')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["daarlaaaaa"].category = "Amigos"

    @bot.command(name='maikol')
    async def maikol(ctx):
        await ctx.send(f' Abran paso al MOD + Anciano 👴 @maikolteve')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["maikol"].category = "Amigos"

            # informativo
    @bot.command(name='horario')
    async def horario(ctx):
        await ctx.send(f'Hola! @{ctx.author.name} Tenemos Stream los Lunes, Miercoles y Viernes ')
        await ctx.send(f'🇲🇽:7:00pm,   🇨🇴:8:00pm,   🇻🇪:9:00pm,  ')
        await ctx.send(f'🇦🇷:10:00pm,   🇪🇨:8:00pm,   🇧🇴:9:00pm, ')
        await ctx.send(f'🇪🇸:3:00am,   🇵🇪:8:00pm,   🇺🇾: 10:00pm, ')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
    bot.commands["horario"].category = "Informacion"
         
            # Componentes
    @bot.command(name='pc')
    async def pc(ctx):
        await ctx.send(f'[BOT] - Mi PC ❤️ está armada con estos componentes: ')
        await ctx.send(f'- [Asus RogStrix X670] ')
        await ctx.send(f'- [Ryzen 9 9900X]')
        await ctx.send(f'- [64gb 5600hz]')
        await ctx.send(f'- [RTX 3060Ti] ')
        await ctx.send(f'- [NZXT H440] ')
        await ctx.send(f'- [NZXT Kraken 360]')
        await ctx.send(f'- [LG 1440p 144Hz] ')
        await ctx.send(f'- [BENQ 1080 100Hz]')

        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["pc"].category = "Equipo"
    
    @bot.command(name='camara')
    async def camara(ctx):
        await ctx.send(f'Mi cámara es una: Canon Rebel T6icon un lente 18-135 f3.5')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["camara"].category = "Equipo"

    @bot.command(name='microfono')
    async def microfono(ctx):
        await ctx.send(f'Uso un micrófono super económico que encontré en Amazon: https://www.amazon.com.mx/gp/product/B08ZYB7NN2/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1 Con una interfaz (Tarjeta de audio) Focusrite Scarlett 2i2 Gen 1Y la mágia de la mezcla correcta de audio realizada en Dannprod ;)')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["microfono"].category = "Equipo"

            # Redes
    @bot.command(name='instagram')
    async def instagram(ctx):
        await ctx.send(f'📸Instagrm: https://www.instagram.com/datotovar ')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["instagram"].category = "Redes"
    
    @bot.command(name='youtube')
    async def youtube(ctx):
        await ctx.send(f' 🔥 Suscríbete a mi canal de Youtube 📹Youtube: https://www.youtube.com/@DatoTovar ')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["youtube"].category = "Redes"

    @bot.command(name='whatsapp')
    async def whatsapp(ctx):
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["whatsapp"].category = "Redes"

    @bot.command(name='wapp')
    async def wapp(ctx):
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["wapp"].category = "Redes"

    @bot.command(name='discord')
    async def discord(ctx):     
        invite_link = "https://discord.gg/PaqYUz69Zx"   
        await ctx.send(f'🎙Únete a mi canal de Discord y juega con nosotros! 🟢 {invite_link}')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["discord"].category = "Redes"

    @bot.command(name='spotify')
    async def spotify(ctx):        
        await ctx.send(f'🟢 Gracias por escucharme en Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["spotify"].category = "Redes"
    
    @bot.command(name='redes')
    async def redes(ctx):
        await ctx.send(f'[BOT] - Aquí están mis redes 😎! ')
        await ctx.send(f'📹Youtube: https://www.youtube.com/@DatoTovar ')
        await ctx.send(f'📸Instagrm: https://www.instagram.com/datotovar ')
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await ctx.send(f'🔥 Discord: https://discord.gg/PaqYUz69Zx')
        await ctx.send(f'🟢 Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A')
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
    bot.commands["redes"].category = "Redes"


    #_______DEFINICION DE COMANDOS EXTERNOS PARA EVITAR MENSAJE DE ERROR DE COMANDO
    @bot.command(name='sr')
    async def dona(ctx):
        logging.info(f"{ctx.author.name}Uso SR")
        await update_global_stats("xp_Voluntad",ctx.author.name,0.15)
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
        await update_global_stats("xp_Carisma",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
        await update_global_stats("xp_Bromista",ctx.author.name,0.15)
    bot.commands["sr"].category = "Otro"

    @bot.command(name='followage')
    async def followage(ctx):
        logging.info(f"{ctx.author.name}Uso followage")
        await update_global_stats("xp_Empatia",ctx.author.name,0.15)
    bot.commands["followage"].category = "Otro"

    @bot.command(name='clip')
    async def clip(ctx):
        logging.info(f"{ctx.author.name}Uso clip")
    bot.commands["clip"].category = "Otro"

    @bot.command(name='followers')
    async def followers(ctx):
        logging.info(f"{ctx.author.name}Uso followers")
    bot.commands["followers"].category = "Otro"

    @bot.command(name='life')
    async def life(ctx):
        logging.info(f"{ctx.author.name}Uso life")
    bot.commands["life"].category = "Otro"

    @bot.command(name='uptime')
    async def uptime(ctx):
        logging.info(f"{ctx.author.name}Uso uptime")
    bot.commands["uptime"].category = "Otro"

    @bot.command(name='viewers')
    async def viewers(ctx):
        logging.info(f"{ctx.author.name}Uso viewers")
    bot.commands["viewers"].category = "Otro"