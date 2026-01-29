from twitchio.ext import commands
from Helpers.helpers_stats import update_global_stats
from Helpers.printlog import printlog

class general_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot
    """
                    COMANDOS GENERALES

        Los comandos generales son comandos que ofrecen
        una respuesta rápida en el chat
        
                INDICE:
    -hola
    -adios
    -lurk
    -unlurk
    -onlyfans
    -koala
    -llama
    -daarlaaaaa
    -maikol
    -horario
    -pc
    -camara
    -microfono
    -instagram
    -youtube
    -whatsapp
    -discord
    -spotify
    -redes
    """

    @commands.command(name='tdt', aliases=["tdt"])
    async def lurk(self, ctx):
        await ctx.send(f'[BOT] - Aquí está toda la información para entrar al servidor de miencraft https://dato.dannprod.com/tdt/info.html Tienes que leer las reglas para entender como funciona...')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,3)

    @commands.command(name='iptdt',)
    async def lurk(self, ctx):
        await ctx.send(f'[BOT] - La ip de TDT es: tierradetodos.vultam.host ')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,3)

    @commands.command(name='lurk', aliases=["ghost"])
    async def lurk(self, ctx):
        await ctx.send(f'[BOT] - Dice @{ctx.chatter.name} estará viendo el directo de fondo mientras platica con una cariñosa...')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,3)


    @commands.command(name='unlurk', aliases=["unghost"])
    async def unlurk(self, ctx):
        await ctx.send(f'[BOT] - 🤣... parece que @{ctx.chatter.name} regresó muy feliz de con las cariñosas!')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,3)


    @commands.command(name='onlyfans', aliases=["of"])
    async def onlyfans(self, ctx):
        await ctx.send(f'[BOT] - ¡Señoraaaa! @{ctx.chatter.name} anda de cochin@!')
        await update_global_stats("xp_Oscuridad",ctx.chatter.id,0.55)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    
            # amigos
    @commands.command(name='koala', aliases=["elkoala","koalafc"])
    async def koala(self, ctx):
        await ctx.send(f'[BOT] - Cállense todos, ya llego @elkoalam 👀🙄')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)

    
    @commands.command(name='daarlaaaaa', aliases=["darla"])
    async def daarlaaaaa(self, ctx):
        await ctx.send(f'[BOT] -  Como @DAARLAAAAA 🤯')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)


    @commands.command(name='maikol')
    async def maikol(self, ctx):
        await ctx.send(f'[BOT] -   Abran paso al MOD + Anciano 👴 @maikolteve')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)


            # informativo
    @commands.command(name='horario', aliases=["horarios","agenda"])
    async def horario(self, ctx):
        await ctx.send(f'Hola! @{ctx.chatter.name} Tenemos Stream los Lunes, Miercoles y Viernes ')
        await ctx.send(f'🇲🇽:7:00pm,   🇨🇴:8:00pm,   🇻🇪:9:00pm,  ')
        await ctx.send(f'🇦🇷:10:00pm,   🇪🇨:8:00pm,   🇧🇴:9:00pm, ')
        await ctx.send(f'🇪🇸:3:00am,   🇵🇪:8:00pm,   🇺🇾: 10:00pm, ')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)

         
            # Componentes
    @commands.command(name='pc', aliases=["componentes", "computadora", "computador"])
    async def pc(self, ctx):
        await ctx.send(f'[BOT] - Mi PC ❤️ está armada con estos componentes: ')
        await ctx.send(f'- [Asus RogStrix X670] ')
        await ctx.send(f'- [Ryzen 9 9900X]')
        await ctx.send(f'- [64gb 5600hz]')
        await ctx.send(f'- [RTX 3060Ti] ')
        await ctx.send(f'- [NZXT H440] ')
        await ctx.send(f'- [NZXT Kraken 360]')
        await ctx.send(f'- [LG 1440p 144Hz] ')
        await ctx.send(f'- [BENQ 1080 100Hz]')

        await update_global_stats("xp_Resistencia",ctx.chatter.id,0.15)

    
    @commands.command(name='camara', aliases=["cam", "webcam"])
    async def camara(self, ctx):
        await ctx.send(f'[BOT] -  Mi cámara es una: Canon Rebel T6i con un lente 18-135 f3.5')
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)


    @commands.command(name='microfono', aliases=["mic", "micro"])
    async def microfono(self, ctx):
        await ctx.send(f'[BOT] -  Uso un micrófono super económico que encontré en Amazon: https://www.amazon.com.mx/gp/product/B08ZYB7NN2/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1 Con una interfaz (Tarjeta de audio) Focusrite Scarlett 2i2 Gen 1Y la mágia de la mezcla correcta de audio realizada en Dannprod ;)')
        await update_global_stats("xp_Astucia",ctx.chatter.id,0.15)


            # Redes
    @commands.command(name='instagram', aliases=['insta','ig'])
    async def instagram(self, ctx):
        await ctx.send(f'[BOT] -  📸Instagrm: https://www.instagram.com/datotovar ')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Fuerza",ctx.chatter.id,0.15)

    
    @commands.command(name='youtube', aliases=["yt"])
    async def youtube(self, ctx):
        await ctx.send(f'[BOT] - 🔥 Suscríbete a mi canal de Youtube 📹Youtube: https://www.youtube.com/@DatoTovar ')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)


    @commands.command(name='whatsapp', aliases=['wapp', 'wsp'])
    async def whatsapp(self, ctx):
        await ctx.send(f'[BOT] - ✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)


    @commands.command(name='discord', aliases=["dc", "dis"])
    async def discord(self, ctx):     
        invite_link = "https://discord.gg/PaqYUz69Zx"   
        await ctx.send(f'[BOT] - 🎙Únete a mi canal de Discord y juega con nosotros! 🟢 {invite_link}')
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)


    @commands.command(name='spotify', aliases=["spoty", "spoti"])
    async def spotify(self, ctx):        
        await ctx.send(f'[BOT] - 🟢 Gracias por escucharme en Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)

    
    @commands.command(name='redes', aliases=["social", "socials"])
    async def redes(self, ctx):
        await ctx.send(f'[BOT] - Aquí están mis redes 😎! ')
        await ctx.send(f'📹Youtube: https://www.youtube.com/@DatoTovar ')
        await ctx.send(f'📸Instagrm: https://www.instagram.com/datotovar ')
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await ctx.send(f'🔥 Discord: https://discord.gg/PaqYUz69Zx')
        await ctx.send(f'🟢 Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A')
        await update_global_stats("xp_Voluntad",ctx.chatter.id,0.15)



    #_______DEFINICION DE COMANDOS EXTERNOS PARA EVITAR MENSAJE DE ERROR DE COMANDO
    @commands.command(name='sr')
    async def dona(self, ctx):
        printlog(f" {ctx.chatter.name} Uso SR")
        await update_global_stats("xp_Empatia",ctx.chatter.id,0.15)
        await update_global_stats("xp_Carisma",ctx.chatter.id,0.15)
        await update_global_stats("xp_Bromista",ctx.chatter.id,0.15)


    @commands.command(name='clip')
    async def clip(self, ctx):
        printlog(f"{ctx.chatter.name}Uso clip")

    @commands.command(name='speak', aliases=["spk", "voz"])
    async def speak(self, ctx):
        printlog(f"{ctx.chatter.name}Uso speak")


    @commands.command(name='life')
    async def life(self, ctx):
        printlog(f"{ctx.chatter.name}Uso life")



    

